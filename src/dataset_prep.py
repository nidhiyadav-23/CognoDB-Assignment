from pathlib import Path
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
RAW_DIR = ROOT / "data" / "raw"
PROCESSED_DIR = ROOT / "data" / "processed"

TARGET_MIN_RELS = 100_000
TARGET_MAX_RELS = 500_000
TARGET_RELS = 100_000


def read_tsv_gz(filename, usecols):
    return pd.read_csv(
        RAW_DIR / filename,
        sep="\t",
        compression="gzip",
        usecols=usecols,
        na_values="\\N",
        low_memory=False,
    )


def build_dataset():
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)

    print("Loading movies...")
    movies = read_tsv_gz(
        "title.basics.tsv.gz",
        [
            "tconst",
            "titleType",
            "primaryTitle",
            "startYear",
            "runtimeMinutes",
            "genres",
        ],
    )

    movies = movies[
        (movies["titleType"] == "movie")
        & (movies["startYear"].notna())
    ].copy()

    print("Loading principals...")
    principals = read_tsv_gz(
        "title.principals.tsv.gz",
        [
            "tconst",
            "ordering",
            "nconst",
            "category",
        ],
    )

    principals = principals[
        principals["category"].isin(["actor", "actress"])
    ]

    principals = principals[
        principals["tconst"].isin(movies["tconst"])
    ]

    if len(principals) > TARGET_RELS:
        principals = principals.sample(
            n=TARGET_RELS,
            random_state=42,
        )

    used_movies = set(principals["tconst"].unique())
    movies = movies[movies["tconst"].isin(used_movies)]

    print("Loading persons...")
    persons = read_tsv_gz(
        "name.basics.tsv.gz",
        [
            "nconst",
            "primaryName",
            "birthYear",
        ],
    )

    used_persons = set(principals["nconst"].unique())
    persons = persons[persons["nconst"].isin(used_persons)]

    movies_out = movies.rename(
        columns={
            "tconst": "movie_id",
            "primaryTitle": "title",
            "startYear": "year",
            "runtimeMinutes": "runtime_minutes",
            "genres": "genres",
        }
    )

    movies_out = movies_out[
        [
            "movie_id",
            "title",
            "year",
            "runtime_minutes",
            "genres",
        ]
    ]

    movies_out["year"] = pd.to_numeric(
        movies_out["year"],
        errors="coerce"
    ).fillna(0).astype(int)

    movies_out["runtime_minutes"] = pd.to_numeric(
        movies_out["runtime_minutes"],
        errors="coerce"
    ).fillna(0).astype(int)

    movies_out["title"] = movies_out["title"].fillna("").astype(str)
    movies_out["genres"] = movies_out["genres"].fillna("").astype(str)

    # REMOVE ALL NaN VALUES
    movies_out = movies_out.replace({pd.NA: "", float("nan"): ""})
    movies_out = movies_out.fillna("")

    persons_out = persons.rename(
        columns={
            "nconst": "person_id",
            "primaryName": "name",
            "birthYear": "birth_year",
        }
    )

    persons_out = persons_out[
        [
            "person_id",
            "name",
            "birth_year",
        ]
    ]

    persons_out["birth_year"] = pd.to_numeric(
        persons_out["birth_year"],
        errors="coerce"
    ).fillna(0).astype(int)

    persons_out["name"] = persons_out["name"].fillna("").astype(str)

    persons_out = persons_out.replace({pd.NA: "", float("nan"): ""})
    persons_out = persons_out.fillna("")

    edges_out = principals.rename(
        columns={
            "nconst": "from_id",
            "tconst": "to_id",
        }
    )

    edges_out = edges_out[
        [
            "from_id",
            "to_id",
            "ordering",
            "category",
        ]
    ]

    edges_out["ordering"] = pd.to_numeric(
        edges_out["ordering"],
        errors="coerce"
    ).fillna(0).astype(int)

    edges_out["category"] = edges_out["category"].fillna("").astype(str)

    edges_out = edges_out.replace({pd.NA: "", float("nan"): ""})
    edges_out = edges_out.fillna("")

    movies_out.to_csv(
        PROCESSED_DIR / "movies.csv",
        index=False,
    )

    persons_out.to_csv(
        PROCESSED_DIR / "persons.csv",
        index=False,
    )

    edges_out.to_csv(
        PROCESSED_DIR / "acted_in.csv",
        index=False,
    )

    print("\nDataset created successfully")
    print(f"Movies: {len(movies_out):,}")
    print(f"Persons: {len(persons_out):,}")
    print(f"Relationships: {len(edges_out):,}")

    if not (
        TARGET_MIN_RELS
        <= len(edges_out)
        <= TARGET_MAX_RELS
    ):
        raise ValueError(
            f"Relationship count {len(edges_out)} outside required range "
            f"({TARGET_MIN_RELS}-{TARGET_MAX_RELS})"
        )


if __name__ == "__main__":
    build_dataset()