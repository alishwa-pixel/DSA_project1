DSA Project 1 - Book Explorer (Open Library)
Author: Alishwa  |  UET Lahore  |  Section: GAMING A
Roll no.: 2025-GA-20

REQUIREMENTS
- Python 3.x (check with: python --version)
- Install packages:  pip install PyQt5 requests pandas

FILES
- phase1_scraper.py  : PyQt5 scraper window (Start/Pause/Resume/Stop + progress bar). Scrapes 15,000 books from the Open Library API into books_data.csv.
- books_data.csv     : the scraped dataset (15,000 rows, 13 columns). Missing values are stored as N/A.
- data_loader.py     : loads the CSV, converts numeric columns, turns missing values into None.
- sorting_engine.py  : 11 sorting algorithms (Bubble, Selection, Insertion, Merge, Hybrid Merge, Quick, Heap, Shell, Counting, Radix, Bucket) with comparison/swap counters, single-level and multi-level sort, and the benchmark function.
- search_engine.py   : Linear, Binary and Jump search (exact match), contains/starts with/ends with filters, numeric comparisons, and AND/OR/NOT combined search.
- url_scraper.py     : BONUS - scrapes books from an Open Library URL typed into the main window (Pause/Resume/Stop, progress bar). Results are saved to books_url.csv.
- theme.py           : colours and styling only (dark theme). No logic.
- main.py            : the main PyQt5 window (paged table, search, sort, benchmark).

HOW TO RUN
1. (Optional) Re-scrape the data:   python phase1_scraper.py
   A ready-made books_data.csv is already included, so this step can be skipped.
2. Start the application:           python main.py
   Keep books_data.csv in the same folder as main.py.
@
NOTES
- Missing values are always placed last when sorting.
- Counting and Radix Sort work on integer columns only; Bucket Sort needs numeric columns. None of the three can do multi-level sort.
- "Swaps/Moves" counts exchanges for swap-based sorts and element moves for Insertion, Shell, Merge, Counting and Radix.
- Bubble, Selection and Insertion Sort take 10-30 seconds on all 15,000 rows. The window stays responsive because sorting runs in a background thread.
- Benchmark uses a 3,000-row sample by default (untick the box for the full data set).
- URL bonus: paste a link like https://openlibrary.org/search?q=history or https://openlibrary.org/subjects/love into the box in main.py and press 'Scrape URL'. New books appear as the current results; 'Reset all' shows the whole dataset.
