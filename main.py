# main.py - DSA Project 1: Book Explorer (table + sort + search + benchmark)
import random
import sys

from PyQt5.QtCore import Qt, QThread, pyqtSignal
from PyQt5.QtWidgets import (QApplication, QCheckBox, QComboBox, QDialog, QGroupBox,
                             QHBoxLayout, QLabel, QLineEdit, QMainWindow,
                             QMessageBox, QProgressBar, QPushButton, QSpinBox,
                             QScrollArea, QFrame, QHeaderView, QTableWidget, QTableWidgetItem, QTextEdit, QVBoxLayout,
                             QWidget, QGridLayout)

from data_loader import load_books
from search_engine import EXACT_ALGOS, NUM_MODES, TEXT_MODES, composite_search
from theme import apply_theme
from url_scraper import UrlScraper, parse_url
from sorting_engine import ALGORITHMS, NUMERIC_ONLY, benchmark, sort_rows, sort_rows_multi

PAGE_SIZE = 100
NUMERIC_COLS = {"first_publish_year", "pages", "rating",
                "want_to_read", "currently_reading", "already_read"}


class Worker(QThread):
    """Runs any function off the UI thread so big sorts never freeze the window."""
    done = pyqtSignal(object)
    failed = pyqtSignal(str)

    def __init__(self, func, *args):
        super().__init__()
        self.func, self.args = func, args

    def run(self):
        try:
            self.done.emit(self.func(*self.args))
        except Exception as e:
            self.failed.emit(str(e))


class BenchmarkDialog(QDialog):
    def __init__(self, title, rows, parent=None):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.resize(1020, 470)
        heads = ["Algorithm", "Time (ms)", "Comparisons", "Swaps/Moves",
                 "Complexity", "Stable", "Note"]
        t = QTableWidget(len(rows), len(heads))
        t.setHorizontalHeaderLabels(heads)
        for r, d in enumerate(rows):
            vals = [d["algorithm"], d["time_ms"], d["comparisons"], d["swaps"],
                    d["complexity"], "Yes" if d["stable"] else "No", d.get("note", "")]
            for c, v in enumerate(vals):
                t.setItem(r, c, QTableWidgetItem("-" if v is None else str(v)))
        t.resizeColumnsToContents()
        t.setEditTriggers(QTableWidget.NoEditTriggers)
        t.setAlternatingRowColors(True)
        t.verticalHeader().setVisible(False)
        t.setShowGrid(False)
        t.horizontalHeader().setStretchLastSection(True)
        lay = QVBoxLayout(self)
        lay.addWidget(t)


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Book Explorer - DSA Project 1")
        self.resize(1300, 800)
        self.names, self.cols, self.n = load_books("books_data.csv")
        self.base = list(range(self.n))      # order of the FULL dataset
        self.filtered = None                 # None = no filter, else list of row indices
        self.view = list(self.base)          # what the table shows right now
        self.page = 0
        self.worker = None                   # keep a reference or Qt may crash
        self.scraper = None                  # URL scraper thread (bonus)
        self.new_rows = []                   # indices of rows added by the URL scraper
        self._build_ui()
        self.refresh_table()

    # ------------------------------------------------------------ UI
    def _build_ui(self):
        root = QWidget()
        root.setObjectName("root")
        scroll = QScrollArea()                 # small screens can scroll instead of cutting things off
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setWidget(root)
        self.setCentralWidget(scroll)
        main = QVBoxLayout(root)
        main.setContentsMargins(18, 14, 18, 14)
        main.setSpacing(8)
        title = QLabel("Book Explorer"); title.setObjectName("title")
        sub = QLabel("15,000 books  |  sort  |  search  |  benchmark"); sub.setObjectName("subtitle")
        main.addWidget(title); main.addWidget(sub)

        # ---- search box
        self.sbox = sbox = QGroupBox("Search  (AND binds tighter than OR; rows with empty value are ignored)")
        g = QGridLayout(sbox)
        self.cond = []
        for r in range(3):
            join = QComboBox(); join.addItems(["AND", "OR"])
            notb = QCheckBox("NOT")
            col = QComboBox(); col.addItems(self.names)
            mode = QComboBox()
            val = QLineEdit(); val.setPlaceholderText("value")
            algo = QComboBox(); algo.addItems(list(EXACT_ALGOS))
            col.currentTextChanged.connect(lambda _t, i=r: self._update_modes(i))
            if r == 0:
                join.setVisible(False)
            g.addWidget(join, r, 0); g.addWidget(notb, r, 1); g.addWidget(col, r, 2)
            g.addWidget(mode, r, 3); g.addWidget(val, r, 4); g.addWidget(algo, r, 5)
            self.cond.append(dict(join=join, notb=notb, col=col, mode=mode, val=val, algo=algo))
            self._update_modes(r)
        self.in_results = QCheckBox("Search only inside current results")
        b_search = QPushButton("Search"); b_search.setObjectName("primary"); b_search.clicked.connect(self.do_search)
        b_reset = QPushButton("Reset all"); b_reset.clicked.connect(self.do_reset)
        g.addWidget(self.in_results, 3, 2, 1, 2)
        g.addWidget(b_search, 3, 4); g.addWidget(b_reset, 3, 5)
        hint = QLabel("Algorithm applies to 'equals' only; contains/starts/ends are linear scans.")
        hint.setObjectName("hint")
        g.addWidget(hint, 4, 0, 1, 6)
        main.addWidget(sbox)

        # ---- sort box
        self.tbox = tbox = QGroupBox("Sort (up to 3 levels)")
        h = QGridLayout(tbox)                 # two rows so the window stays narrow
        self.lv_col, self.lv_ord = [], []
        for k in range(3):
            c = QComboBox()
            c.addItems((["(none)"] if k else []) + self.names)
            o = QComboBox(); o.addItems(["Ascending", "Descending"])
            h.addWidget(QLabel("Sort by" if k == 0 else "then"), 0, k * 3)
            h.addWidget(c, 0, k * 3 + 1); h.addWidget(o, 0, k * 3 + 2)
            self.lv_col.append(c); self.lv_ord.append(o)
        self.sort_algo = QComboBox(); self.sort_algo.addItems(list(ALGORITHMS))
        self.sort_algo.currentTextChanged.connect(self._algo_info)
        self.scope = QComboBox(); self.scope.addItems(["Full dataset", "Current filtered results"])
        b_sort = QPushButton("Sort"); b_sort.setObjectName("primary"); b_sort.clicked.connect(self.do_sort)
        self.sample = QCheckBox("Benchmark 3,000-row sample")
        self.sample.setChecked(True)
        b_bench = QPushButton("Benchmark"); b_bench.clicked.connect(self.do_benchmark)
        h.addWidget(QLabel("Algorithm"), 1, 0)
        h.addWidget(self.sort_algo, 1, 1); h.addWidget(self.scope, 1, 2)
        h.addWidget(b_sort, 1, 3); h.addWidget(self.sample, 1, 4, 1, 3)
        h.addWidget(b_bench, 1, 7, 1, 2)
        main.addWidget(tbox)
        self.algo_label = QLabel(); main.addWidget(self.algo_label)
        self._algo_info(self.sort_algo.currentText())

        # ---- BONUS: scrape from URL
        ubox = QGroupBox("Bonus: scrape from an Open Library URL")
        ubv = QVBoxLayout(ubox)
        uh = QHBoxLayout()
        ubv.addLayout(uh)
        self.url_in = QLineEdit()
        self.url_in.setPlaceholderText("https://openlibrary.org/search?q=history   or   https://openlibrary.org/subjects/love")
        self.url_max = QSpinBox(); self.url_max.setRange(1, 5000); self.url_max.setValue(300)
        self.url_max.setPrefix("max ")
        self.b_uscrape = QPushButton("Scrape URL"); self.b_uscrape.setObjectName("primary")
        self.b_upause = QPushButton("Pause"); self.b_uresume = QPushButton("Resume")
        self.b_ustop = QPushButton("Stop")
        self.url_bar = QProgressBar()
        self.url_status = QLabel("")
        self.b_uscrape.clicked.connect(self.start_url_scrape)
        self.b_upause.clicked.connect(lambda: self._url_ctl("pause"))
        self.b_uresume.clicked.connect(lambda: self._url_ctl("resume"))
        self.b_ustop.clicked.connect(lambda: self._url_ctl("stop"))
        for w_ in (self.url_in, self.url_max, self.b_uscrape, self.b_upause,
                   self.b_uresume, self.b_ustop):
            uh.addWidget(w_)
        uh.setStretch(0, 1)
        row2 = QHBoxLayout()
        row2.addWidget(self.url_bar, 1); row2.addWidget(self.url_status)
        ubv.addLayout(row2)
        main.addWidget(ubox)
        self._url_state("idle")
        for cb in self.findChildren(QComboBox):          # keep dropdowns compact
            cb.setSizeAdjustPolicy(QComboBox.AdjustToMinimumContentsLengthWithIcon)
            cb.setMinimumContentsLength(7)
        for c_ in self.cond:
            c_["algo"].setMinimumContentsLength(12)

        # ---- table
        self.table = QTableWidget()
        self.table.setColumnCount(len(self.names))
        self.table.setHorizontalHeaderLabels(self.names)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table.setAlternatingRowColors(True)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.verticalHeader().setVisible(False)
        self.table.setShowGrid(False)
        self.table.setMinimumHeight(300)
        hdr = self.table.horizontalHeader()
        hdr.setDefaultSectionSize(150)
        hdr.setSectionResizeMode(QHeaderView.Interactive)
        hdr.setStretchLastSection(True)
        self.table.setColumnWidth(0, 320)       # title
        self.table.setColumnWidth(1, 200)       # author
        main.addWidget(self.table, 1)

        # ---- pagination
        pg = QHBoxLayout()
        self.b_prev = QPushButton("< Prev"); self.b_next = QPushButton("Next >")
        self.b_prev.clicked.connect(lambda: self.go_page(-1))
        self.b_next.clicked.connect(lambda: self.go_page(1))
        self.page_label = QLabel()
        pg.addStretch(); pg.addWidget(self.b_prev); pg.addWidget(self.page_label)
        pg.addWidget(self.b_next); pg.addStretch()
        main.addLayout(pg)

        # ---- results panel
        self.results = QTextEdit(); self.results.setReadOnly(True)
        self.results.setMaximumHeight(90)
        main.addWidget(self.results)

    def _update_modes(self, r):
        c = self.cond[r]
        c["mode"].clear()
        c["mode"].addItems(NUM_MODES if c["col"].currentText() in NUMERIC_COLS else TEXT_MODES)

    def _algo_info(self, name):
        _, cx, stable, int_only = ALGORITHMS[name]
        extra = ("  | integer columns only" if int_only else
                 "  | numeric columns only" if name in NUMERIC_ONLY else "")
        self.algo_label.setText(f"{name}: time {cx}  |  stable: {'Yes' if stable else 'No'}{extra}")

    # ------------------------------------------------------------ URL scraper (bonus)
    def _url_state(self, s):
        self.b_uscrape.setEnabled(s == "idle")
        self.b_upause.setEnabled(s == "running")
        self.b_uresume.setEnabled(s == "paused")
        self.b_ustop.setEnabled(s in ("running", "paused"))
        busy = s != "idle"
        self.sbox.setEnabled(not busy)       # no sort/search while rows are being added
        self.tbox.setEnabled(not busy)
        self.url_in.setEnabled(not busy); self.url_max.setEnabled(not busy)

    def start_url_scrape(self):
        if self.worker is not None and self.worker.isRunning():
            QMessageBox.information(self, "Scrape", "Wait for the running sort to finish.")
            return
        try:
            params = parse_url(self.url_in.text())
        except ValueError as e:
            QMessageBox.warning(self, "URL", str(e))
            return
        target = self.url_max.value()
        self.new_rows = []
        self.scraper = UrlScraper(params, target, set(self.cols["key"]))
        self.scraper.batch.connect(self._add_rows)
        self.scraper.progress.connect(lambda c, t: (self.url_bar.setMaximum(t), self.url_bar.setValue(c)))
        self.scraper.status.connect(self.url_status.setText)
        self.scraper.finished_ok.connect(self._url_done)
        self.scraper.error.connect(self._url_error)
        self.url_bar.setValue(0); self.url_bar.setMaximum(target)
        self._url_state("running")
        self.log(f"URL scrape started: {params} (max {target})")
        self.scraper.start()

    def _url_ctl(self, what):
        if self.scraper is None:
            return
        getattr(self.scraper, what)()
        if what == "pause":
            self._url_state("paused"); self.url_status.setText("Paused")
        elif what == "resume":
            self._url_state("running")

    def _add_rows(self, rows):                # runs on the UI thread (signal slot)
        for row in rows:
            for name in self.names:
                self.cols[name].append(row.get(name))
            self.base.append(self.n)
            self.new_rows.append(self.n)
            self.n += 1

    def _url_done(self, count):
        self._url_state("idle")
        if self.new_rows:
            self.filtered = list(self.new_rows)       # show the new books as current results
            self.view = list(self.new_rows)
            self.page = 0
            self.refresh_table()
        self.log(f"URL scrape finished: {count} new books (saved to books_url.csv). "
                 f"Shown as current results - press 'Reset all' to see the whole dataset.")

    def _url_error(self, msg):
        self._url_state("idle")
        QMessageBox.warning(self, "URL scrape", msg)
        if self.new_rows:
            self._url_done(len(self.new_rows))

    def closeEvent(self, ev):
        if self.scraper is not None and self.scraper.isRunning():
            self.scraper.stop()
            self.scraper.wait(3000)
        ev.accept()

    # ------------------------------------------------------------ table
    def refresh_table(self):
        total = len(self.view)
        pages = max(1, (total + PAGE_SIZE - 1) // PAGE_SIZE)
        self.page = min(self.page, pages - 1)
        start = self.page * PAGE_SIZE
        chunk = self.view[start:start + PAGE_SIZE]
        self.table.setRowCount(len(chunk))
        for r, idx in enumerate(chunk):
            for c, name in enumerate(self.names):
                v = self.cols[name][idx]
                if v is None:
                    text = ""
                elif isinstance(v, float) and v.is_integer():
                    text = str(int(v))
                else:
                    text = str(v)
                self.table.setItem(r, c, QTableWidgetItem(text))
        self.page_label.setText(f"Page {self.page + 1} / {pages}   ({total} rows shown, {self.n} total)")
        self.b_prev.setEnabled(self.page > 0)
        self.b_next.setEnabled(self.page < pages - 1)

    def go_page(self, d):
        self.page += d
        self.refresh_table()

    def log(self, text):
        self.results.append(text)

    # ------------------------------------------------------------ search
    def do_search(self):
        conds = []
        for k, c in enumerate(self.cond):
            if not c["val"].text().strip():
                continue
            conds.append({"column": c["col"].currentText(), "mode": c["mode"].currentText(),
                          "value": c["val"].text().strip(), "algo": c["algo"].currentText(),
                          "not": c["notb"].isChecked(),
                          "join": c["join"].currentText() if k else "AND"})
        if not conds:
            QMessageBox.information(self, "Search", "Type a value in at least one row.")
            return
        scope = self.view if (self.in_results.isChecked() and self.filtered is not None) else None
        try:
            hits, st = composite_search(self.cols, self.n, conds, scope)
        except ValueError:
            QMessageBox.warning(self, "Search", "A numeric column needs a number as the value.")
            return
        hit_set = set(hits)
        self.filtered = hits
        self.view = [i for i in self.base if i in hit_set]   # keep current sort order
        self.page = 0
        self.refresh_table()
        self.log(f"SEARCH: {len(hits)} matches | comparisons: {st['comparisons']} | time: {st['time_ms']} ms")

    def do_reset(self):
        self.base = list(range(self.n)); self.filtered = None
        self.view = list(self.base); self.page = 0
        self.refresh_table(); self.log("Reset: full dataset, original order.")

    # ------------------------------------------------------------ sort
    def _levels(self):
        levels = []
        for k in range(3):
            name = self.lv_col[k].currentText()
            if name != "(none)":
                levels.append((name, self.lv_ord[k].currentIndex() == 1))
        return levels

    def _target_rows(self):
        use_filtered = self.scope.currentIndex() == 1
        if use_filtered and self.filtered is None:
            return None
        return list(self.view) if use_filtered else list(range(self.n))

    def _sort_job(self, rows, levels, algo):
        if len(levels) == 1:
            name, desc = levels[0]
            order, st = sort_rows([self.cols[name][i] for i in rows], algo, desc)
        else:
            lv = [([self.cols[nm][i] for i in rows], d) for nm, d in levels]
            order, st = sort_rows_multi(lv, algo)
        return [rows[p] for p in order], st

    def _run(self, job, on_done, *args):
        if self.worker is not None and self.worker.isRunning():
            return
        self.setEnabled(False)
        self.worker = Worker(job, *args)
        self.worker.done.connect(lambda res: (self.setEnabled(True), on_done(res)))
        self.worker.failed.connect(self._failed)
        self.worker.start()

    def _failed(self, msg):
        self.setEnabled(True)
        QMessageBox.warning(self, "Error", msg)

    def do_sort(self):
        rows = self._target_rows()
        if rows is None:
            QMessageBox.information(self, "Sort", "No filtered results yet. Run a search first.")
            return
        levels, algo = self._levels(), self.sort_algo.currentText()
        self.log(f"Sorting {len(rows)} rows with {algo} ... (O(n^2) sorts can take 10-30 s)")
        self._run(self._sort_job, lambda res: self._sorted(res, levels), rows, levels, algo)

    def _sorted(self, res, levels):
        new_order, st = res
        if self.scope.currentIndex() == 0:               # full dataset
            self.base = new_order
            if self.filtered is None:
                self.view = list(self.base)
            else:
                fs = set(self.filtered)
                self.view = [i for i in self.base if i in fs]
        else:
            self.view = new_order
        self.page = 0
        self.refresh_table()
        lv = ", ".join(f"{n} {'DESC' if d else 'ASC'}" for n, d in levels)
        self.log(f"SORT [{lv}] {st['algorithm']}: {st['time_ms']} ms | comparisons: "
                 f"{st['comparisons']} | swaps/moves: {st['swaps']} | {st['complexity']} | "
                 f"stable: {'Yes' if st['stable'] else 'No'}")

    # ------------------------------------------------------------ benchmark
    def _bench_job(self, values):
        return benchmark(values)

    def do_benchmark(self):
        rows = self._target_rows()
        if rows is None:
            QMessageBox.information(self, "Benchmark", "No filtered results yet. Run a search first.")
            return
        col = self.lv_col[0].currentText()
        if self.sample.isChecked() and len(rows) > 3000:
            random.seed(1)
            rows = random.sample(rows, 3000)
        values = [self.cols[col][i] for i in rows]
        self.log(f"Benchmark on '{col}' with {len(values)} rows ... please wait")
        self._run(self._bench_job, lambda res: self._bench_done(res, col, len(values)), values)

    def _bench_done(self, rows, col, n):
        self.log("Benchmark finished.")
        BenchmarkDialog(f"Benchmark - column '{col}', {n} rows", rows, self).exec_()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    apply_theme(app)
    w = MainWindow()
    w.show()
    sys.exit(app.exec_())
