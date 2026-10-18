"""
Phase 1 - scraping logic for Open Library (no windows in this file, so it is easy to test).
The window (scraper_phase1.py) only calls run_scrape() and shows what it reports.
"""

import csv
import os
import time
import requests

BASE_URL = "https://openlibrary.org/search.json"
# Open Library asks every program to say who it is.
HEADERS = {"User-Agent": "DSA-Project1-student (university project)"}
# Ask only for the fields we need: the reply is smaller and much faster than the default (everything).
FIELDS = ("key,title,author_name,first_publish_year,publisher,subject,language,isbn,"
          "number_of_pages_median,ratings_average,want_to_read_count,"
          "currently_reading_count,already_read_count")
COLUMNS = ["title", "author", "first_publish_year", "publisher", "subject", "language", "isbn",
           "pages", "rating", "want_to_read", "currently_reading", "already_read", "key"]
CSV_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "books_data.csv")

# Real topic words. Single letters like "a" match almost every book and make the server slow.
QUERIES = [
    "history", "science", "fiction", "art", "mathematics", "computer", "world", "life", "love", "war",
    "music", "nature", "space", "ocean", "human", "digital", "python", "data", "engineering", "design",
    "philosophy", "religion", "poetry", "biography", "medicine", "law", "economics", "education",
    "travel", "cooking", "children", "fantasy", "mystery", "romance", "politics", "psychology",
    "physics", "chemistry", "biology", "geography",
]
MAX_PAGES_PER_QUERY = 40          # 40 pages x 100 books = at most 4,000 books per search word


def join_list(value, limit=3):
    """['a','b','c','d'] -> 'a, b, c'.  Missing or empty -> 'N/A'."""
    if not value:
        return "N/A"
    return ", ".join(str(v) for v in value[:limit])


def doc_to_book(doc):
    """Turn one book from the API reply (a dictionary) into one row of our table."""
    rating = doc.get("ratings_average")
    return {
        "title": doc.get("title") or "N/A",
        "author": join_list(doc.get("author_name")),
        "first_publish_year": doc.get("first_publish_year", "N/A"),
        "publisher": join_list(doc.get("publisher")),
        "subject": join_list(doc.get("subject")),
        "language": join_list(doc.get("language")),
        "isbn": join_list(doc.get("isbn")),
        "pages": doc.get("number_of_pages_median", "N/A"),
        "rating": round(rating, 2) if isinstance(rating, (int, float)) else "N/A",
        "want_to_read": doc.get("want_to_read_count", "N/A"),
        "currently_reading": doc.get("currently_reading_count", "N/A"),
        "already_read": doc.get("already_read_count", "N/A"),
        "key": doc.get("key", "N/A"),
    }


def fetch_page(query, page, status, is_stopped, wait_if_paused, sleep, max_tries=5, get=requests.get):
    """Ask the API for one page. Try up to max_tries times, then give up (return None)
    instead of retrying forever on the same page."""
    for attempt in range(1, max_tries + 1):
        if is_stopped():
            return None
        wait_if_paused()                                   # blocks here while the user has paused
        if is_stopped():
            return None
        try:
            reply = get(BASE_URL,
                        params={"q": query, "page": page, "limit": 100, "fields": FIELDS},
                        headers=HEADERS, timeout=45)
            if reply.status_code == 200:
                return reply.json().get("docs", [])
            if reply.status_code == 429:                   # "too many requests": slow down
                try:
                    wait = int(reply.headers.get("Retry-After", 10))
                except ValueError:
                    wait = 10
                status("Server says slow down (429). Waiting %d s... (try %d/%d)" % (wait, attempt, max_tries))
            else:
                wait = 3 * attempt
                status("HTTP %d for '%s' page %d. Waiting %d s... (try %d/%d)"
                       % (reply.status_code, query, page, wait, attempt, max_tries))
        except requests.exceptions.Timeout:
            wait = 3 * attempt
            status("Timed out for '%s' page %d. Waiting %d s... (try %d/%d)" % (query, page, wait, attempt, max_tries))
        except requests.exceptions.ConnectionError:
            wait = 5 * attempt
            status("Cannot reach the site (connection error). Waiting %d s... (try %d/%d)" % (wait, attempt, max_tries))
        except Exception as error:
            wait = 3 * attempt
            status("Error: %s. Waiting %d s... (try %d/%d)" % (str(error)[:60], wait, attempt, max_tries))
        sleep(wait)
    return None


def run_scrape(target, on_book, status, is_stopped, wait_if_paused, sleep,
               csv_path=CSV_FILE, queries=QUERIES, get=requests.get):
    """Scrape until `target` unique books are saved. Every page is written to the CSV at once,
    so nothing is lost if the program stops. Returns how many books were saved."""
    seen = set()                                           # keys of books already saved (no duplicates)
    total = 0
    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=COLUMNS)
        writer.writeheader()
        f.flush()
        for query in queries:
            page = 1
            while page <= MAX_PAGES_PER_QUERY and total < target and not is_stopped():
                status("Searching '%s' - page %d | saved %d/%d" % (query, page, total, target))
                docs = fetch_page(query, page, status, is_stopped, wait_if_paused, sleep, get=get)
                if docs is None:
                    if not is_stopped():
                        status("Giving up on '%s' page %d, moving on to the next word." % (query, page))
                    break
                if not docs:                               # no more results for this word
                    break
                new_rows = []
                for doc in docs:
                    if total + len(new_rows) >= target:
                        break
                    book = doc_to_book(doc)
                    if book["title"] == "N/A" or book["key"] in seen:
                        continue
                    seen.add(book["key"])
                    new_rows.append(book)
                writer.writerows(new_rows)
                f.flush()                                  # force the rows onto the disk now
                for book in new_rows:
                    total += 1
                    on_book(book, total)
                page += 1
                sleep(0.5)                                 # be polite to the server
            if total >= target or is_stopped():
                break
    return total
