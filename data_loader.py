# data_loader.py - loads books_data.csv into plain Python column lists
import pandas as pd

NUMERIC = ["first_publish_year", "pages", "rating",
           "want_to_read", "currently_reading", "already_read"]


def load_books(path="books_data.csv"):
    df = pd.read_csv(path)                       # 'N/A' becomes NaN
    for col in NUMERIC:
        df[col] = pd.to_numeric(df[col], errors="coerce")   # bad text -> NaN
    columns = {}
    for col in df.columns:
        vals = df[col].tolist()
        # NaN -> None so the rest of the program has ONE meaning for "missing"
        columns[col] = [None if (v is None or v != v) else v for v in vals]
    return list(df.columns), columns, len(df)


if __name__ == "__main__":
    names, cols, n = load_books()
    print(n, "rows;", len(names), "columns")
    print({c: cols[c][0] for c in names})
