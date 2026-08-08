# benchmark-graphdb

Scripted, reproducible latency/throughput benchmark for **CognoDB Cloud**, run against the same IMDb-derived graph dataset that will also be used to test Neo4j Aura, self-hosted Neo4j+, Memgraph Cloud, Amazon Neptune, and ArangoDB Oasis under matched conditions.

> **Status:** CognoDB Cloud run complete. Other four platforms not yet benchmarked — this repo is built so each one drops into the same tables the moment credentials are added to `.env`.

---

## Why this exists

Graph database vendors publish their own benchmarks, on their own hardware, with their own queries. This repo does the opposite: one dataset, one set of query templates, one client, and — as much as free tiers allow — matched CPU/RAM/storage, so the numbers in §5 are actually comparable to each other instead of just comparable to marketing pages.

## At a glance

- **Engine under test:** CognoDB Cloud, `c0` free tier (0.5 vCPU / 256 MB RAM / 1 GB storage)
- **Comparators queued:** Neo4j Aura Free, Neo4j+ (self-hosted, resource-capped to match CognoDB), Memgraph Cloud, Amazon Neptune Serverless, ArangoDB Oasis
- **Dataset:** IMDb non-commercial data → 170,490 nodes / 99,989 `ACTED_IN` edges
- **Query surface:** ingest, 1/2/3-hop traversal, point lookup, indexed lookup, aggregation, mixed 80/20 read-write sweep, storage footprint
- **This run's headline numbers:** ~264 ms median for lookups/traversals, ~1.38 s median for full-scan aggregation, 3.27 → 70.67 qps across the concurrency sweep (1 → 40 clients), p95 climbing to ~1.1 s at the top end

---

## 1. Platforms

| # | Platform | Protocol / language | Role in the comparison |
|---|---|---|---|
| 1 | **CognoDB Cloud** (free) | Bolt / Cypher | Subject of the benchmark |
| 2 | Neo4j Aura (free) | Bolt / Cypher | Nearest apples-to-apples comparator — identical wire protocol and query language |
| 3 | Neo4j+ (self-hosted, Docker) | Bolt / Cypher | Same engine as #2, but hardware-capped to CognoDB's exact spec via `docker-compose.neo4j-plus.yml` — isolates "managed overhead" from "engine performance" |
| 4 | Memgraph Cloud | Bolt / Cypher | In-memory-first architecture — a real design contrast, not just another Neo4j clone |
| 5 | Amazon Neptune (Serverless, min NCU) | HTTPS / openCypher | No free tier, included anyway to stress-test the harness against a different transport and to be transparent about the resource mismatch |
| 6 | ArangoDB Oasis (trial) | AQL | Different query language and multi-model engine; trial tier is larger than CognoDB's, so treat its numbers as directional, not matched |

Five of six speak Cypher over Bolt, which was deliberate — it lets one query template (`src/workloads.py`) cover most platforms, so "same query" isn't a translation exercise.

## 2. Layout

```
config/platforms.yaml            adapter type + env-var prefix + advertised specs, per platform
src/
├─ config.py                     loads platforms.yaml + .env
├─ adapters/
│  ├─ base.py                    shared adapter interface
│  ├─ cypher_bolt_adapter.py     CognoDB / Aura / Neo4j+ / Memgraph
│  ├─ neptune_adapter.py         openCypher over HTTPS
│  └─ arango_adapter.py          AQL
├─ dataset_prep.py               builds the sized dataset from raw IMDb files
├─ loader.py                     batched ingest + throughput timing
├─ workloads.py                  one query template per metric, per dialect
├─ runner.py                     warm-up, percentiles, concurrency sweep
└─ metrics.py                    percentile math (unit-tested)
scripts/
├─ run_all.py                    runs every configured platform in one command
└─ generate_readme_tables.py     results.json → the markdown tables in §5
docker-compose.neo4j-plus.yml    resource-capped self-hosted Neo4j
tests/test_metrics.py
results/                         per-platform JSON + combined results.json (gitignored)
```

## 3. Dataset

Sourced from the [IMDb non-commercial datasets](https://datasets.imdbws.com/) ([terms](https://www.imdb.com/interfaces/)), shaped as:

```
(:Person)-[:ACTED_IN {ordering, category}]->(:Movie {year, genres, runtime_minutes})
```

`src/dataset_prep.py` downloads `title.basics`, `name.basics`, and `title.principals`, filters to movies with a known year and `actor`/`actress` credits, then samples edges down into the assignment's 100k–500k relationship band (default target 250k) and drops any node not referenced by a sampled edge. Output goes to `data/processed/{movies,persons,acted_in}.csv` — one file set every adapter loads from, so all five platforms see byte-identical data.

**This run:**

| | Count |
|---|---:|
| Movies | 90,172 |
| Persons | 80,318 |
| ACTED_IN edges | 99,989 |
| Total nodes | 170,490 |

**Ingest method** is identical everywhere: driver-side `UNWIND` (or AQL bulk insert), batches of 2,000 rows, nodes before edges. Native bulk-import tools (`neo4j-admin import`, etc.) were deliberately skipped so the *method*, not just the data, stays constant across platforms.

## 4. Fairness notes

Matching hardware across five different vendors' free tiers is only ever approximate — here's exactly where it does and doesn't hold:

- **Neo4j+** is the strongest data point: it's the same Neo4j engine as Aura, but Docker-capped to CognoDB's precise 0.5 vCPU / 256 MB / 1 GB. Any gap between Neo4j+ and CognoDB is close to a clean read on engine performance.
- **Neo4j Aura Free** ships ~4x CognoDB's RAM and auto-pauses after inactivity — both noted rather than hidden, and cold-start numbers are excluded unless flagged.
- **Memgraph** is in-memory by design, which is an architectural choice independent of its resource tier — a Memgraph win shouldn't be read as "CognoDB is just under-provisioned."
- **Amazon Neptune has no free tier at all** — the one clear resource-parity violation in the set. Included anyway per the assignment's latitude on platform choice, with the caveat stated up front instead of buried.
- **ArangoDB Oasis's trial tier (2 vCPU / 4 GB / 10 GB)** dwarfs CognoDB's. Its numbers are directional only unless paired with a capped self-hosted run.
- The dataset itself (100k–500k relationships) was deliberately sized to fit inside CognoDB's 1 GB tier, so no platform benefits from a smaller working set than any other.

## 5. Results — CognoDB Cloud

*Auto-generated by `scripts/generate_readme_tables.py`. Rows for the remaining five platforms will appear here once benchmarked — see §7.*

**Ingest**

| Nodes/sec | Rels/sec | Total load time |
|---:|---:|---:|
| 2,324.2 | 1,729.7 | 131.17 s |

**Traversal latency, ms (p50 / p95, n=100)**

| 1-hop | 2-hop | 3-hop |
|---|---|---|
| 264.25 / 267.19 | 264.14 / 274.70 | 264.24 / 283.61 |

**Lookup latency, ms (p50 / p95, n=100)**

| Point lookup | Indexed/filtered lookup |
|---|---|
| 264.28 / 280.43 | 279.40 / 856.13 |

*Indexed properties: `movie_id`, `person_id`, `year`.*

**Aggregation latency, ms (p50 / p95, n=100)**

| Count-by-category |
|---|
| 1,382.62 / 1,631.94 |

**Mixed workload — 80/20 read/write sweep**

| Concurrency | Throughput | p95 latency |
|---:|---:|---:|
| 1 | 3.27 qps | 300.54 ms |
| 10 | 33.93 qps | 317.69 ms |
| 40 | 70.67 qps | 1,105.65 ms |

**Footprint**

| Nodes | Relationships | Storage/memory |
|---:|---:|---|
| 170,490 | 99,989 | not exposed via Cypher driver |

## 6. Reading the results

- **Lookups and traversals cluster tightly around 264 ms**, regardless of hop count — on a dataset this size, fixed per-query round-trip cost dominates over actual traversal depth. Don't read the flat 1/2/3-hop numbers as "CognoDB handles deep traversals for free"; it likely means the query time is latency-bound, not compute-bound, at this scale.
- **Aggregation is the outlier**, ~5x slower than lookups, because `count-by-category` has to scan every `ACTED_IN` edge rather than hit an index.
- **Concurrency scaling is real but not free**: throughput goes up 21x from 1→40 clients, but p95 latency goes up almost 4x in the same step — the 0.5 vCPU ceiling on the free tier is visibly the limiting factor once load gets heavy.
- All of the above describes **CognoDB in isolation**. None of it is a comparative claim yet — that's what §7 is blocked on.

## 7. Reproducing / extending this benchmark

```bash
git clone <this-repo-url>
cd benchmark-graphdb
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

cp .env.example .env        # fill in per-platform credentials; never commit this file

docker compose -f docker-compose.neo4j-plus.yml up -d   # bring up capped self-hosted Neo4j+
python src/dataset_prep.py                              # one-time, ~1.5 GB IMDb download

python scripts/run_all.py                    # every configured platform
python scripts/run_all.py --only cognodb memgraph_cloud # or just a subset

python scripts/generate_readme_tables.py > results/tables.md
```

Platforms missing credentials in `.env` are skipped automatically (not failed) and marked as such in `results.json` — the suite can be run incrementally as accounts get provisioned.

**Requires:** Python 3.11+, Docker (for Neo4j+), and a free/trial account on whichever platforms you're adding.

## 8. Open items

- [ ] Run Aura Free, Neo4j+, Memgraph Cloud, Neptune, and ArangoDB Oasis; populate their rows in §5
- [ ] Log any free-tier throttling per platform (symptom + workaround)
- [ ] Note client-region vs. platform-region mismatches, if any
- [ ] Document failed/timed-out runs and how they were handled
- [ ] Capture dialect quirks not already covered in `workloads.py` (e.g. Neptune's openCypher vs. Neo4j's Cypher)
- [ ] Flag any Aura cold-start numbers caused by auto-pause
- [ ] Decide whether to report the capped self-hosted ArangoDB run alongside the uncapped Oasis trial

---

*Dataset used under IMDb's non-commercial terms: https://www.imdb.com/interfaces/. This is a technical benchmark, not an endorsement of any vendor.*
