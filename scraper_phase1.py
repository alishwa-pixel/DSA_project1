"""
Phase 1: Open Library book scraper with a PyQt5 window.
Buttons: Start, Pause, Resume, Stop.  A progress bar shows how many books are saved.
The scraping itself is in scraper_core.py (keep both files in the same folder).
Every page is saved to books_data.csv straight away, so nothing is lost if you close the window.
"""

import sys
import csv
import time
import threading
from PyQt5.QtWidgets import (QApplication, QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
                             QProgressBar, QLabel, QTextEdit, QFileDialog)
from PyQt5.QtCore import QThread, pyqtSignal, Qt

import scraper_core as core


class ScraperWorker(QThread):
    """Runs the scraping in the background so the window never freezes."""
    progress_update = pyqtSignal(int, int)      # saved so far, target
    book_found = pyqtSignal(dict)
    status_message = pyqtSignal(str)
    finished_scraping = pyqtSignal(int)

    def __init__(self, target_count=15000):
        super().__init__()
        self.target_count = target_count
        self._pause_event = threading.Event()   # set = running, cleared = paused
        self._stop_flag = False
        self._pause_event.set()

    def _sleep(self, seconds):
        """Sleep in small steps so Stop reacts quickly."""
        end = time.time() + seconds
        while time.time() < end and not self._stop_flag:
            time.sleep(0.1)

    def run(self):
        self._stop_flag = False
        self._pause_event.set()

        def on_book(book, total):
            self.book_found.emit(book)
            self.progress_update.emit(total, self.target_count)

        total = core.run_scrape(
            self.target_count, on_book, self.status_message.emit,
            lambda: self._stop_flag,            # is_stopped
            self._pause_event.wait,             # wait_if_paused: blocks while paused
            self._sleep)
        self.finished_scraping.emit(total)

    def pause(self):
        self._pause_event.clear()
        self.status_message.emit("PAUSED (it stops before the next request)")

    def resume(self):
        self._pause_event.set()
        self.status_message.emit("RESUMED")

    def stop(self):
        self._stop_flag = True
        self._pause_event.set()                 # release the thread if it is paused


def make_button(text, color):
    b = QPushButton(text)
    b.setStyleSheet("QPushButton { background-color: %s; color: white; font-size: 14px; padding: 8px;"
                    " border-radius: 5px; } QPushButton:disabled { background-color: #cccccc; }" % color)
    return b


class ScraperWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.worker = None
        self.books_data = []
        self.setWindowTitle("Phase 1 - Open Library Book Scraper")
        self.setMinimumSize(700, 500)

        layout = QVBoxLayout(self)
        title = QLabel("Open Library Scraper - Target: 15,000 Books")
        title.setStyleSheet("font-size: 16px; font-weight: bold; padding: 10px;")
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)

        self.progress_bar = QProgressBar()
        self.progress_bar.setMaximum(15000)
        layout.addWidget(self.progress_bar)

        self.count_label = QLabel("Saved: 0 / 15,000")
        self.count_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.count_label)

        row = QHBoxLayout()
        self.btn_start = make_button("Start", "#4CAF50")
        self.btn_pause = make_button("Pause", "#FF9800")
        self.btn_resume = make_button("Resume", "#2196F3")
        self.btn_stop = make_button("Stop", "#f44336")
        self.btn_save = make_button("Save a copy", "#9C27B0")
        for b in (self.btn_start, self.btn_pause, self.btn_resume, self.btn_stop, self.btn_save):
            row.addWidget(b)
        layout.addLayout(row)
        self.btn_start.clicked.connect(self.start_scraping)
        self.btn_pause.clicked.connect(self.pause_scraping)
        self.btn_resume.clicked.connect(self.resume_scraping)
        self.btn_stop.clicked.connect(self.stop_scraping)
        self.btn_save.clicked.connect(self.save_copy)
        self.set_buttons(running=False)

        self.log_area = QTextEdit()
        self.log_area.setReadOnly(True)
        self.log_area.setMaximumHeight(200)
        layout.addWidget(self.log_area)

    def set_buttons(self, running, paused=False):
        self.btn_start.setEnabled(not running)
        self.btn_pause.setEnabled(running and not paused)
        self.btn_resume.setEnabled(running and paused)
        self.btn_stop.setEnabled(running)
        self.btn_save.setEnabled((not running) and len(self.books_data) > 0)

    def log(self, message):
        self.log_area.append(message)

    def start_scraping(self):
        self.books_data = []
        self.progress_bar.setValue(0)
        self.count_label.setText("Saved: 0 / 15,000")
        self.log_area.clear()
        self.log("Starting. Books are saved to: " + core.CSV_FILE)
        self.worker = ScraperWorker(15000)
        self.worker.progress_update.connect(self.on_progress)
        self.worker.book_found.connect(self.books_data.append)
        self.worker.status_message.connect(self.log)
        self.worker.finished_scraping.connect(self.on_finished)
        self.worker.start()
        self.set_buttons(running=True)

    def pause_scraping(self):
        if self.worker:
            self.worker.pause()
            self.set_buttons(running=True, paused=True)

    def resume_scraping(self):
        if self.worker:
            self.worker.resume()
            self.set_buttons(running=True, paused=False)

    def stop_scraping(self):
        if self.worker:
            self.worker.stop()
            self.log("Stop requested...")

    def on_progress(self, current, total):
        self.progress_bar.setMaximum(total)
        self.progress_bar.setValue(current)
        self.count_label.setText("Saved: {:,} / {:,}".format(current, total))

    def on_finished(self, total):
        reached = total >= 15000
        self.log(("COMPLETE" if reached else "STOPPED") + " - %s books are in books_data.csv" % format(total, ","))
        self.set_buttons(running=False)

    def save_copy(self):
        path, _ = QFileDialog.getSaveFileName(self, "Save a copy", "books_copy.csv", "CSV Files (*.csv)")
        if path:
            with open(path, "w", newline="", encoding="utf-8") as f:
                writer = csv.DictWriter(f, fieldnames=core.COLUMNS)
                writer.writeheader()
                writer.writerows(self.books_data)
            self.log("Saved a copy to " + path)

    def closeEvent(self, event):
        if self.worker and self.worker.isRunning():
            self.worker.stop()
            self.worker.wait(3000)
        event.accept()


def main():
    app = QApplication(sys.argv)
    window = ScraperWindow()
    window.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
