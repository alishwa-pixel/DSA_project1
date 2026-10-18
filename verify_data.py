import pandas as pd

FILE = "books_data.csv"

df = pd.read_csv(FILE)

print("Rows   :", len(df), "   (need at least 15,000)")
print("Columns:", len(df.columns), "  (need at least 8)")
print("Column names:", list(df.columns))

print("\nData type of each column:")
print(df.dtypes)

print("\nMissing values (N/A) in each column:")
missing = df.isna().sum()
print(pd.DataFrame({"missing": missing, "percent": (missing / len(df) * 100).round(1)}))

print("\nCompletely duplicated rows:", df.duplicated().sum())
title_column = next((c for c in df.columns if c.lower() == "title"), None)
if title_column:
    same_title = df[title_column].str.lower().duplicated().sum()
    print("Repeated titles (ignoring case):", same_title)

print("\nFirst 5 rows:")
print(df.head().to_string())

print("\nQuick verdict:")
print(" - 15,000 rows reached:", len(df) >= 15000)
print(" - 8 or more columns   :", len(df.columns) >= 8)