import pandas as pd

movies = pd.read_csv("data/processed/movies.csv")
persons = pd.read_csv("data/processed/persons.csv")
acted = pd.read_csv("data/processed/acted_in.csv")

print("=" * 50)
print("IMDb Dataset Verification")
print("=" * 50)

print(f"Movies        : {len(movies):,}")
print(f"Persons       : {len(persons):,}")
print(f"Relationships : {len(acted):,}")

print("\nMovies Sample:")
print(movies.head())

print("\nPersons Sample:")
print(persons.head())

print("\nRelationships Sample:")
print(acted.head())