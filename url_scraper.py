# url_scraper.py - BONUS: scrape books from an Open Library URL typed into the UI
import csv
import threading
import time
from urllib.parse import parse_qs, unquote, urlparse
import requests
from PyQt5.QtCore import QThread, pyqtSignal

API_URL = "https://openlibrary.org/search.json"
HEADERS = {"User-Agent": "DSA-Course-Project (student project; alishwarizwan3@gmail.com)"}  # change email
FIELDS = ("title,author_name,first_publish_year,publisher,subject,language,isbn,"
          "number_of_pages_median,ratings_average,want_to_read_count,"
          "currently_reading_count,already_read_count,key")
COLUMNS = ["title", "author", "first_publish_year", "publisher", "subject", "language",
           "isbn", "pages", "rating", "want_to_read", "currently_reading",
           "already_read", "key"]
ALLOWED_PARAMS = {"q", "title", "author", "subject", "publisher", "language",
                  "isbn", "place", "person", "first_publish_year", "sort"}
DELAY = 0.5                                      # seconds between pages (be polite)
OUT_FILE = "books_url.csv"                       # separate file: books_data.csv stays untouched


def parse_url(url):
    """Turn a pasted Open Library link into API search parameters."""
    url = url.strip()
    if not url:
        raise ValueError("Paste an Open Library URL first.")
    if "://" not in url:
        url = "https://" + url
    u = urlparse(url)
    host = u.netloc.lower()
    if not (host == "openlibrary.org" or host.endswith(".openlibrary.org")):
        raise ValueError("Only openlibrary.org URLs are supported.")
    path = u.path.rstrip("/")
    params = {k: v[0] for k, v in parse_qs(u.query).items() if k in ALLOWED_PARAMS and v}
    if path.startswith("/subjects/") and len(path.split("/")) >= 3:
        name = unquote(path.split("/")[2]).replace("_", " ")
        params["q"] = f'subject:"{name}"'
    elif path not in ("/search", "/search.json"):
        raise ValueError("Unsupported link. Use a search link such as\n"
                         "https://openlibrary.org/search?q=history\n"
                         "or a subject link such as https://openlibrary.org/subjects/love")
    if not params:
        raise ValueError("The link has no search words (for example ?q=history).")
    return params


def _join(v, k=3):
    return ", ".join(str(x) for x in (v or [])[:k]) or None


def _num(v):
    try:
        return float(v) if v not in (None, "") else None
    except (TypeError, ValueError):
        return None


def doc_to_row(d):
    """One API result -> dict with the same 13 columns as books_data.csv."""
    if not d.get("key") or not d.get("title"):
        return None
    rating = _num(d.get("ratings_average"))
    return {"title": d["title"].strip(), "author": _join(d.get("author_name")),
            "first_publish_year": _num(d.get("first_publish_year")),
            "publisher": _join(d.get("publisher")), "subject": _join(d.get("subject")),
            "language": _join(d.get("language")), "isbn": _join(d.get("isbn")),
            "pages": _num(d.get("number_of_pages_median")),
            "rating": round(rating, 2) if rating is not None else None,
            "want_to_read": _num(d.get("want_to_read_count")),
            "currently_reading": _num(d.get("currently_reading_count")),
            "already_read": _num(d.get("already_read_count")),
            "key": d["key"]}


class UrlScraper(QThread):
    batch = pyqtSignal(list)            # new rows (list of dicts) from one page
    progress = pyqtSignal(int, int)     # collected, target
    status = pyqtSignal(str)
    finished_ok = pyqtSignal(int)
    error = pyqtSignal(str)

    def __init__(self, params, target, known_keys, parent=None):
        super().__init__(parent)
        self.params, self.target = params, target
        self.known = set(known_keys)    # keys already in the table -> skip duplicates
        self._can_run = threading.Event()
        self._can_run.set()
        self._stopped = False

    def pause(self):
        self._can_run.clear()

    def resume(self):
        self._can_run.set()

    def stop(self):
        self._stopped = True
        self._can_run.set()             # wake a paused thread so it can exit

    def _fetch(self, page):
        p = dict(self.params, limit=100, page=page, fields=FIELDS)
        last = None
        for attempt in range(3):
            try:
                r = requests.get(API_URL, params=p, headers=HEADERS, timeout=15)
                if r.status_code == 429:
                    time.sleep(10)
                    continue
                r.raise_for_status()
                return r.json().get("docs", [])
            except requests.RequestException as e:
                last = e
                time.sleep(2 ** attempt)
        raise RuntimeError(f"Network problem: {last}")

    def run(self):
        count, page = 0, 1
        try:
            with open(OUT_FILE, "w", newline="", encoding="utf-8") as f:
                w = csv.writer(f)
                w.writerow(COLUMNS)
                while count < self.target:
                    self._can_run.wait()                    # Pause blocks here
                    if self._stopped:
                        break
                    self.status.emit(f"Fetching page {page} ...")
                    docs = self._fetch(page)
                    if not docs:
                        break                               # no more results
                    rows = []
                    for d in docs:
                        row = doc_to_row(d)
                        if row is None or row["key"] in self.known:
                            continue
                        self.known.add(row["key"])
                        rows.append(row)
                        w.writerow(["N/A" if row[c] is None else row[c] for c in COLUMNS])
                        count += 1
                        if count >= self.target:
                            break
                    f.flush()
                    if rows:
                        self.batch.emit(rows)
                    self.progress.emit(count, self.target)
                    page += 1
                    time.sleep(DELAY)
            self.status.emit("Stopped." if self._stopped else "Done.")
            self.finished_ok.emit(count)
        except Exception as e:
            self.error.emit(str(e))
