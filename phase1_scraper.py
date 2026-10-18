"""
Phase 1: Open Library Book Scraper
Scrapes 15,000+ books using Open Library Search API
PyQt5 GUI with Start/Pause/Resume/Stop controls and progress bar
"""

import sys
import csv
import time
import threading
import requests
from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QProgressBar, QLabel, QTextEdit, QFileDialog
)
from PyQt5.QtCore import QThread, pyqtSignal, Qt


class ScraperWorker(QThread):
    """Background thread that scrapes Open Library API"""
    progress_update = pyqtSignal(int, int)       # current, total
    book_found = pyqtSignal(dict)                 # single book dict
    status_message = pyqtSignal(str)              # log message
    finished_scraping = pyqtSignal(int)           # total scraped

    def __init__(self, target_count=15000):
        super().__init__()
        self.target_count = target_count
        self._pause_event = threading.Event()
        self._stop_flag = False
        self._pause_event.set()  # Not paused by default
        self.scraped_books = []
        self.total_scraped = 0

    def run(self):
        """Main scraping loop"""
        self._stop_flag = False
        self._pause_event.set()
        self.total_scraped = 0
        self.scraped_books = []

        # Open Library API endpoint
        base_url = "https://openlibrary.org/search.json"
        
        # We'll search by common letters/words to get diverse results
        search_queries = [
            "a", "b", "c", "d", "e", "f", "g", "h", "i", "j",
            "k", "l", "m", "n", "o", "p", "q", "r", "s", "t",
            "u", "v", "w", "x", "y", "z",
            "the", "and", "of", "history", "science", "art",
            "math", "computer", "world", "life", "book",
            "python", "data", "engineer", "design", "music",
            "nature", "space", "ocean", "human", "digital"
        ]

        for query in search_queries:
            if self._stop_flag:
                break

            page = 1
            while not self._stop_flag:
                # Check pause
                self._pause_event.wait()

                if self._stop_flag:
                    break

                if self.total_scraped >= self.target_count:
                    break

                try:
                    params = {
                        "q": query,
                        "page": page,
                        "limit": 100
                    }
                    
                    self.status_message.emit(
                        f"Searching '{query}' - Page {page} | "
                        f"Scraped: {self.total_scraped}/{self.target_count}"
                    )

                    response = requests.get(base_url, params=params, timeout=15)
                    
                    if response.status_code != 200:
                        self.status_message.emit(
                            f"API returned status {response.status_code}, retrying..."
                        )
                        time.sleep(2)
                        continue

                    data = response.json()
                    docs = data.get("docs", [])

                    if not docs:
                        break  # No more results for this query

                    for doc in docs:
                        if self._stop_flag or self.total_scraped >= self.target_count:
                            break

                        # Check pause again inside loop
                        self._pause_event.wait()

                        book = {
                            "title": doc.get("title", "N/A"),
                            "author": ", ".join(doc.get("author_name", ["N/A"])),
                            "first_publish_year": doc.get("first_publish_year", "N/A"),
                            "publisher": ", ".join(doc.get("publisher", ["N/A"])[:3]),
                            "subject": ", ".join(doc.get("subject", ["N/A"])[:3]),
                            "language": ", ".join(doc.get("language", ["N/A"])),
                            "isbn": ", ".join(doc.get("isbn", ["N/A"])[:3]),
                            "pages": doc.get("number_of_pages_median", "N/A"),
                            "rating": doc.get("ratings_average", "N/A"),
                            "want_to_read": doc.get("want_to_read_count", "N/A"),
                            "currently_reading": doc.get("currently_reading_count", "N/A"),
                            "already_read": doc.get("already_read_count", "N/A"),
                        }

                        # Skip books with no title
                        if book["title"] == "N/A":
                            continue

                        self.scraped_books.append(book)
                        self.total_scraped += 1
                        self.book_found.emit(book)
                        self.progress_update.emit(self.total_scraped, self.target_count)

                    page += 1
                    time.sleep(0.5)  # Be nice to the API (rate limiting)

                except requests.exceptions.Timeout:
                    self.status_message.emit("Request timed out, retrying in 3s...")
                    time.sleep(3)
                    continue
                except requests.exceptions.ConnectionError:
                    self.status_message.emit("Connection error, retrying in 5s...")
                    time.sleep(5)
                    continue
                except Exception as e:
                    self.status_message.emit(f"Error: {str(e)[:80]}")
                    time.sleep(2)
                    continue

            if self.total_scraped >= self.target_count:
                break

        self.finished_scraping.emit(self.total_scraped)

    def pause(self):
        self._pause_event.clear()
        self.status_message.emit("⏸ Scraping PAUSED")

    def resume(self):
        self._pause_event.set()
        self.status_message.emit("▶ Scraping RESUMED")

    def stop(self):
        self._stop_flag = True
        self._pause_event.set()  # Unblock if paused


class ScraperWindow(QWidget):
    """Main PyQt5 Window for the scraper"""

    def __init__(self):
        super().__init__()
        self.worker = None
        self.books_data = []
        self.init_ui()

    def init_ui(self):
        self.setWindowTitle("Phase 1 - Open Library Book Scraper")
        self.setMinimumSize(700, 500)

        layout = QVBoxLayout()

        # Title label
        title = QLabel("📚 Open Library Scraper - Target: 15,000 Books")
        title.setStyleSheet("font-size: 16px; font-weight: bold; padding: 10px;")
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)

        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setMinimum(0)
        self.progress_bar.setMaximum(15000)
        self.progress_bar.setValue(0)
        self.progress_bar.setStyleSheet(
            "QProgressBar { border: 2px solid grey; border-radius: 5px; text-align: center; }"
            "QProgressBar::chunk { background-color: #4CAF50; }"
        )
        layout.addWidget(self.progress_bar)

        # Count label
        self.count_label = QLabel("Scraped: 0 / 15,000")
        self.count_label.setStyleSheet("font-size: 14px; padding: 5px;")
        self.count_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.count_label)

        # Buttons
        btn_layout = QHBoxLayout()

        self.btn_start = QPushButton("▶ Start")
        self.btn_start.setStyleSheet(
            "QPushButton { background-color: #4CAF50; color: white; "
            "font-size: 14px; padding: 8px; border-radius: 5px; }"
            "QPushButton:hover { background-color: #45a049; }"
        )
        self.btn_start.clicked.connect(self.start_scraping)

        self.btn_pause = QPushButton("⏸ Pause")
        self.btn_pause.setStyleSheet(
            "QPushButton { background-color: #FF9800; color: white; "
            "font-size: 14px; padding: 8px; border-radius: 5px; }"
            "QPushButton:hover { background-color: #e68a00; }"
            "QPushButton:disabled { background-color: #ccc; }"
        )
        self.btn_pause.clicked.connect(self.pause_scraping)
        self.btn_pause.setEnabled(False)

        self.btn_resume = QPushButton("▶ Resume")
        self.btn_resume.setStyleSheet(
            "QPushButton { background-color: #2196F3; color: white; "
            "font-size: 14px; padding: 8px; border-radius: 5px; }"
            "QPushButton:hover { background-color: #1976D2; }"
            "QPushButton:disabled { background-color: #ccc; }"
        )
        self.btn_resume.clicked.connect(self.resume_scraping)
        self.btn_resume.setEnabled(False)

        self.btn_stop = QPushButton("⏹ Stop")
        self.btn_stop.setStyleSheet(
            "QPushButton { background-color: #f44336; color: white; "
            "font-size: 14px; padding: 8px; border-radius: 5px; }"
            "QPushButton:hover { background-color: #d32f2f; }"
            "QPushButton:disabled { background-color: #ccc; }"
        )
        self.btn_stop.clicked.connect(self.stop_scraping)
        self.btn_stop.setEnabled(False)

        self.btn_save = QPushButton("💾 Save CSV")
        self.btn_save.setStyleSheet(
            "QPushButton { background-color: #9C27B0; color: white; "
            "font-size: 14px; padding: 8px; border-radius: 5px; }"
            "QPushButton:hover { background-color: #7B1FA2; }"
            "QPushButton:disabled { background-color: #ccc; }"
        )
        self.btn_save.clicked.connect(self.save_to_csv)
        self.btn_save.setEnabled(False)

        btn_layout.addWidget(self.btn_start)
        btn_layout.addWidget(self.btn_pause)
        btn_layout.addWidget(self.btn_resume)
        btn_layout.addWidget(self.btn_stop)
        btn_layout.addWidget(self.btn_save)

        layout.addLayout(btn_layout)

        # Log area
        self.log_area = QTextEdit()
        self.log_area.setReadOnly(True)
        self.log_area.setStyleSheet(
            "QTextEdit { background-color: #1e1e1e; color: #00ff00; "
            "font-family: Consolas, monospace; font-size: 12px; padding: 5px; }"
        )
        self.log_area.setMaximumHeight(180)
        layout.addWidget(self.log_area)

        self.setLayout(layout)

    def log(self, message):
        self.log_area.append(message)

    def start_scraping(self):
        self.books_data = []
        self.progress_bar.setValue(0)
        self.count_label.setText("Scraped: 0 / 15,000")
        self.log_area.clear()
        self.log("🚀 Starting scraper... Fetching books from Open Library API")

        self.worker = ScraperWorker(target_count=15000)
        self.worker.progress_update.connect(self.on_progress)
        self.worker.book_found.connect(self.on_book_found)
        self.worker.status_message.connect(self.on_status)
        self.worker.finished_scraping.connect(self.on_finished)

        self.worker.start()

        # Update button states
        self.btn_start.setEnabled(False)
        self.btn_pause.setEnabled(True)
        self.btn_resume.setEnabled(False)
        self.btn_stop.setEnabled(True)
        self.btn_save.setEnabled(False)

    def pause_scraping(self):
        if self.worker:
            self.worker.pause()
            self.btn_pause.setEnabled(False)
            self.btn_resume.setEnabled(True)

    def resume_scraping(self):
        if self.worker:
            self.worker.resume()
            self.btn_pause.setEnabled(True)
            self.btn_resume.setEnabled(False)

    def stop_scraping(self):
        if self.worker:
            self.worker.stop()
            self.worker.wait(3000)  # Wait up to 3s for thread to finish
            self.log("⏹ Scraping STOPPED by user")
        
        self.btn_start.setEnabled(True)
        self.btn_pause.setEnabled(False)
        self.btn_resume.setEnabled(False)
        self.btn_stop.setEnabled(False)
        self.btn_save.setEnabled(len(self.books_data) > 0)

    def on_progress(self, current, total):
        self.progress_bar.setValue(current)
        self.progress_bar.setMaximum(total)
        self.count_label.setText(f"Scraped: {current:,} / {total:,}")

    def on_book_found(self, book):
        self.books_data.append(book)

    def on_status(self, message):
        self.log(message)

    def on_finished(self, total):
        self.log(f"\n✅ Scraping COMPLETE! Total books: {total:,}")
        self.btn_start.setEnabled(True)
        self.btn_pause.setEnabled(False)
        self.btn_resume.setEnabled(False)
        self.btn_stop.setEnabled(False)
        self.btn_save.setEnabled(True)

    def save_to_csv(self):
        if not self.books_data:
            self.log("❌ No data to save!")
            return

        filepath, _ = QFileDialog.getSaveFileName(
            self, "Save Books Data", "books_data.csv", "CSV Files (*.csv)"
        )

        if filepath:
            try:
                fieldnames = [
                    "title", "author", "first_publish_year", "publisher",
                    "subject", "language", "isbn", "pages", "rating",
                    "want_to_read", "currently_reading", "already_read"
                ]
                with open(filepath, "w", newline="", encoding="utf-8") as f:
                    writer = csv.DictWriter(f, fieldnames=fieldnames)
                    writer.writeheader()
                    writer.writerows(self.books_data)

                self.log(f"💾 Saved {len(self.books_data):,} books to {filepath}")
            except Exception as e:
                self.log(f"❌ Error saving: {str(e)}")


def main():
    app = QApplication(sys.argv)
    window = ScraperWindow()
    window.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
