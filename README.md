# CognoDB Cloud vs. Managed Graph Databases: A Reproducible Benchmark

A fair, scripted comparison of [CognoDB Cloud](https://console.cognodb.com) against four other managed/self-managed graph databases on the same dataset, same queries, same client, and matched resource tiers.

**TL;DR:** CognoDB Cloud (free tier) loaded and served the full 170k-node / 100k-edge IMDb dataset with stable ~264 ms median latency on point lookups and 1/2/3-hop traversals, and ~1.38s median on full aggregation scans. Throughput scaled from 3.27 qps at concurrency 1 to 70.67 qps at concurrency 40, with tail latency (p95) rising sharply to ~1.1s at the highest concurrency level. This run only covers CognoDB — Neo4j Aura, Neo4j+, Memgraph, Neptune, and ArangoDB have not yet been benchmarked (see §9).

---

## 1. Databases compared

| Platform | Query language | Why it's in this comparison |
|---|---|---|
| **CognoDB Cloud** (c0 free) | Cypher (Bolt) | The subject of the benchmark. |
| **Neo4j Aura Free** | Cypher (Bolt) | The most direct comparator — same query language and wire protocol as CognoDB, so any latency gap reflects the backend, not syntax or driver differences. |
| **Neo4j+** (self-managed, Docker-capped) | Cypher (Bolt) | Same engine as Aura but self-hosted and explicitly resource-capped (`docker-compose.neo4j-plus.yml`) to CognoDB's exact 0.5 vCPU / 256MB / 1GB spec — isolates "managed service overhead" from "raw engine performance." |
| **Memgraph Cloud** | Cypher (Bolt) | Also Cypher/Bolt, but an in-memory-first architecture — a genuine architectural contrast rather than another Neo4j-family engine. |
| **Amazon Neptune** (Serverless, min capacity) | openCypher (HTTPS) | A major managed graph offering with no free tier — included to test the harness against a different wire protocol (HTTPS + optional SigV4) and to make the resource-parity trade-off explicit. |
| **ArangoDB Oasis** | AQL | A different query language and multi-model engine, included for breadth. Its free trial tier is larger than CognoDB's (see §4) — treat its raw numbers as directional unless run alongside the capped self-hosted variant. |

Four of five comparators share Cypher-over-Bolt with CognoDB, which lets the harness reuse one query template for most platforms (`src/workloads.py`) — maximizing confidence that "same logical query" really means the same query, not a best-effort translation.

## 2. Repository layout

```
config/platforms.yaml          Platform registry: adapter type, credentials env-var prefix, advertised specs
src/
  config.py                    Loads platforms.yaml + .env
  adapters/                    One adapter per wire protocol/dialect (base.py defines the interface)
    cypher_bolt_adapter.py     CognoDB, Neo4j Aura, Neo4j+, Memgraph (identical Cypher/Bolt)
    neptune_adapter.py         Amazon Neptune (openCypher over HTTPS)
    arango_adapter.py          ArangoDB (AQL)
  dataset_prep.py              Builds the sized movie/actor dataset from public IMDb data
  loader.py                    Streams the dataset into any adapter, times ingest throughput
  workloads.py                 Query templates for every required metric, per dialect
  runner.py                    Warm-up, latency percentiles, mixed-workload concurrency sweep
  metrics.py                   Percentile/statistics helpers (unit-tested, see tests/)
scripts/
  run_all.py                   One-command benchmark runner across all configured platforms
  generate_readme_tables.py    Turns results/results.json into the markdown tables in §7
docker-compose.neo4j-plus.yml  Resource-capped self-managed Neo4j+ instance
tests/test_metrics.py          Unit tests for the percentile math
results/                       JSON output per platform + combined results.json (gitignored except .gitkeep)
```

## 3. Dataset

**Source:** [IMDb non-commercial datasets](https://datasets.imdbws.com/) (free for personal/non-commercial use, updated daily by IMDb — see [terms](https://www.imdb.com/interfaces/)).

**Graph shape:** `(:Person)-[:ACTED_IN {ordering, category}]->(:Movie {year, genres, runtime_minutes})`

Built by `src/dataset_prep.py`, which:
1. Downloads `title.basics.tsv.gz`, `name.basics.tsv.gz`, `title.principals.tsv.gz`.
2. Filters to `titleType=movie` with a known release year, and credits with `category in {actor, actress}`.
3. Samples ACTED_IN edges down to a target within the assignment's **100,000–500,000 relationship** range (default target: 250,000), then keeps only the Movie/Person rows actually referenced by the sampled edges — no orphaned nodes.
4. Writes `data/processed/{movies.csv, persons.csv, acted_in.csv}` — the single source of truth every platform loader reads, guaranteeing an identical dataset rather than five independent downloads that might drift.

**This run's dataset:**

| Metric | Count |
|---|---|
| Movies | 90,172 |
| Persons | 80,318 |
| ACTED_IN relationships | 99,989 |
| Total nodes | 170,490 |

**Load method (identical across platforms):** driver-side batched `UNWIND`/AQL bulk insert via `src/loader.py`, batch size 2000 rows, nodes first then edges (edges matched to already-created nodes by id). No platform-specific bulk-import tool was used, so the load numbers measure driver-batched ingest specifically — native bulk tools (e.g. `neo4j-admin import`) were intentionally excluded to keep the load *method* identical across platforms, not just the data.

## 4. Fairness: resource parity

| Platform | vCPU | RAM | Storage | Region | Caveats |
|---|---|---|---|---|---|
| CognoDB Cloud | 0.5 (burstable) | 256 MB | 1 GB | *(fill in region picked)* | Baseline tier — every other platform is matched or capped to this. |
| Neo4j Aura Free | shared, not published | 1 GB | ~0.5 GB usable | *(fill in)* | RAM is 4x CognoDB's — documented, not hidden; Aura Free also auto-pauses after inactivity, excluded from cold-start numbers unless noted. |
| Neo4j+ (self-managed) | 0.5 (container-capped) | 256 MB (container-capped) | 1 GB (volume-capped) | same client region | Exact match to CognoDB by construction (`docker-compose.neo4j-plus.yml`) — the strongest fairness data point in this comparison. |
| Memgraph Cloud | *(fill in from console at run time)* | *(fill in)* | *(fill in)* | *(fill in)* | In-memory engine is an architectural difference independent of the resource tier — call this out in the analysis, don't let it read as an unfair advantage. |
| Amazon Neptune | min Neptune Capacity Units (NCU) | not published per-NCU | pay-per-GB (uncapped) | must match client region | **No free tier — the clearest resource-parity violation in the set.** Included anyway per the assignment's "your choice" latitude, with this caveat stated up front. |
| ArangoDB Oasis | 2 (free trial) | 4 GB (free trial) | 10 GB (free trial) | *(fill in)* | Free trial tier is materially larger than CognoDB's. Numbers here are **not resource-matched** — treat as directional. |

**Dataset sizing:** the dataset is sized (100k–500k relationships, ~250k default) so it fits inside CognoDB's 1GB free tier, per the assignment's fairness note — the same dataset is loaded everywhere, so no platform benefits from a smaller effective working set.

## 5. Methodology

- **Same dataset, same queries, same client, matched resources** (§4) for every platform.
- **Warm-up:** 20 unmeasured calls per read workload before the 100 measured iterations (both configurable via `.env`: `BENCH_WARMUP_ITERATIONS`, `BENCH_ITERATIONS`).
- **Percentiles, not just averages:** every read workload reports p50/p95/p99 (`src/metrics.py`, unit-tested in `tests/test_metrics.py`).
- **Mixed workload concurrency sweep:** 1 / 10 / 40 concurrent clients (`BENCH_CONCURRENCY_LEVELS`), 80/20 read/write mix, 15s sustained load per level, one connection per worker thread (`src/runner.py::run_mixed_workload`).
- **Automation:** `python scripts/run_all.py` loads data, runs every workload, and writes `results/results.json` for every configured platform in one command. `scripts/generate_readme_tables.py` turns that JSON into the tables in §7 — the tables are generated, not hand-typed, so they can't silently drift from the raw numbers.
- **Query correspondence across dialects:** `src/workloads.py` documents each workload's logical intent once, then gives the Cypher and AQL implementations side by side, so a reviewer can verify they're really the same query and not just similarly named.

### Required metrics → where they're implemented

| Metric (assignment §5.2) | Implementation |
|---|---|
| Ingest throughput | `src/loader.py::load_all` — nodes/sec, rels/sec, wall-clock |
| 1/2/3-hop traversal latency | `workloads.py::traversal_1hop/2hop/3hop`, p50/p95 via `runner.py` |
| Point lookup / indexed lookup | `workloads.py::point_lookup`, `indexed_filtered_lookup` (year is indexed on every platform that supports index DDL — Neptune auto-indexes, see adapter notes) |
| Aggregation | `workloads.py::aggregation_by_category` — count grouped by ACTED_IN.category |
| Mixed read/write throughput | `runner.py::run_mixed_workload`, swept at 1/10/40 clients |
| Footprint | `adapters/*.py::footprint()` — reports node/rel counts everywhere; storage/memory reported as "not observable via driver" where a platform doesn't expose it through Cypher/AQL, with a pointer to check the provider console manually |

## 6. Reproducing this benchmark

**Prerequisites:** Python 3.11+, free/trial accounts on each platform in §1, Docker (for Neo4j+).

```bash
git clone <this-repo-url>
cd benchmark-graphdb
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

cp .env.example .env
# Fill in .env with your own connection details for each platform.
# Never commit .env — it's gitignored.

# 1. Bring up the resource-capped self-managed Neo4j+ instance
docker compose -f docker-compose.neo4j-plus.yml up -d

# 2. Build the dataset (one-time, ~1.5GB download from IMDb)
python src/dataset_prep.py

# 3. Run the full benchmark suite across every configured platform
python scripts/run_all.py
# or a subset while iterating: python scripts/run_all.py --only cognodb memgraph_cloud

# 4. Generate the results tables
python scripts/generate_readme_tables.py > results/tables.md
# paste results/tables.md into section 7 below
```

Any platform without credentials in `.env` is automatically skipped (not failed) and marked accordingly in `results.json`, so you can run the suite incrementally as you provision each account.

## 7. Results

*Generated by `scripts/generate_readme_tables.py` — CognoDB Cloud only. Other platforms will populate their own rows once benchmarked (see §9).*

### Data loading

| Platform | Nodes/sec | Rels/sec | Total load time | Notes |
|---|---|---|---|---|
| CognoDB Cloud (c0 free) | 2324.2 | 1729.7 | 131.168s | Free tier (0.5 vCPU, 256 MB RAM) |

### Traversals (p50 / p95, n=100)

| Platform | 1-hop | 2-hop | 3-hop |
|---|---|---|---|
| CognoDB Cloud (c0 free) | 264.25 / 267.19 ms | 264.14 / 274.70 ms | 264.24 / 283.61 ms |

### Lookups (p50 / p95, n=100)

| Platform | Point lookup | Indexed/filtered lookup | Indexed properties |
|---|---|---|---|
| CognoDB Cloud (c0 free) | 264.28 / 280.43 ms | 279.40 / 856.13 ms | movie_id, person_id, year |

### Aggregation (p50 / p95, n=100)

| Platform | Count-by-category |
|---|---|
| CognoDB Cloud (c0 free) | 1382.62 / 1631.94 ms |

### Mixed workload (80/20 read/write, concurrency sweep)

| Platform | Concurrency | Throughput | p95 latency |
|---|---|---|---|
| CognoDB Cloud (c0 free) | 1 | 3.27 qps | 300.54 ms |
| CognoDB Cloud (c0 free) | 10 | 33.93 qps | 317.69 ms |
| CognoDB Cloud (c0 free) | 40 | 70.67 qps | 1105.65 ms |

### Footprint

| Platform | Node count | Rel count | Storage/memory |
|---|---|---|---|
| CognoDB Cloud (c0 free) | 170,490 | 99,989 | Not exposed via Cypher driver |

## 8. Analysis

**Performance summary.** CognoDB Cloud successfully loaded 170,490 nodes and 99,989 relationships using the same dataset and workload definitions used throughout the benchmark.

**Read performance.** Point lookups and traversal workloads showed stable median latency around 264 ms. The 1-hop, 2-hop, and 3-hop traversals performed similarly, suggesting the traversal cost on this dataset size is dominated by fixed per-query overhead (connection/round-trip) rather than hop depth.

**Aggregation performance.** Aggregation queries were significantly more expensive than lookups and traversals, with median latency above 1.3 seconds — expected, since the query scans and groups all ACTED_IN relationships.

**Mixed workload.** Throughput increased from 3.27 qps at concurrency 1 to 70.67 qps at concurrency 40. Higher concurrency increased throughput but also increased tail latency, with p95 reaching roughly 1.1 seconds at the highest concurrency level — consistent with the free tier's 0.5 vCPU limit becoming the bottleneck under load.

**Limitations.** Results were collected entirely on the CognoDB free tier (0.5 vCPU, 256 MB RAM). Network latency and free-tier resource limits may affect results. Only one platform has been benchmarked so far; the comparison against Neo4j Aura, Neo4j+, Memgraph, Neptune, and ArangoDB is still outstanding (§9).

## 9. Known caveats / outstanding work

- [ ] Benchmark Neo4j Aura Free, Neo4j+, Memgraph Cloud, Amazon Neptune, and ArangoDB Oasis and populate their rows in §7.
- [ ] Free-tier throttling observed on: *(platform, symptom, workaround)*
- [ ] Network variance: *(client region vs. each platform's region, if not identical)*
- [ ] Any failed/timed-out runs and how they were handled
- [ ] Query-language differences beyond what's captured in `workloads.py` (e.g. Neptune openCypher quirks vs. Neo4j Cypher)
- [ ] Aura Free auto-pause affecting any cold-start numbers
- [ ] Whether the supplementary capped self-hosted ArangoDB run was included alongside the uncapped Oasis trial numbers

---

**License/attribution:** IMDb dataset used under IMDb's non-commercial terms (https://www.imdb.com/interfaces/). This is a technical benchmark, not an endorsement of any platform.
