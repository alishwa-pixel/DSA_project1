# sorting_engine.py  -  DSA Project 1, Step 4
# Every algorithm sorts a list of (key, row_index) pairs by key only.
# row_index lets us map the sorted result back to the table row.
import random
import time


class Counter:
    """Counts comparisons and swaps/moves for one sort run."""
    def __init__(self):
        self.comparisons = 0
        self.swaps = 0

    def less(self, a, b):          # the ONLY place keys are compared
        self.comparisons += 1
        return a[0] < b[0]


# ---------------- comparison sorts ----------------
def bubble_sort(a, c):
    n = len(a)
    for i in range(n - 1):
        swapped = False
        for j in range(n - 1 - i):
            if c.less(a[j + 1], a[j]):          # strict < keeps it stable
                a[j], a[j + 1] = a[j + 1], a[j]
                c.swaps += 1
                swapped = True
        if not swapped:                          # early exit: already sorted
            break
    return a


def selection_sort(a, c):
    n = len(a)
    for i in range(n - 1):
        m = i
        for j in range(i + 1, n):
            if c.less(a[j], a[m]):
                m = j
        if m != i:
            a[i], a[m] = a[m], a[i]
            c.swaps += 1
    return a


def insertion_sort(a, c):
    for i in range(1, len(a)):
        cur = a[i]
        j = i - 1
        while j >= 0 and c.less(cur, a[j]):
            a[j + 1] = a[j]                      # shift = 1 move
            c.swaps += 1
            j -= 1
        a[j + 1] = cur
    return a


def merge_sort(a, c):
    if len(a) <= 1:
        return a
    mid = len(a) // 2
    left = merge_sort(a[:mid], c)
    right = merge_sort(a[mid:], c)
    out, i, j = [], 0, 0
    while i < len(left) and j < len(right):
        if c.less(right[j], left[i]):            # take left on ties = stable
            out.append(right[j]); j += 1
        else:
            out.append(left[i]); i += 1
        c.swaps += 1                             # each element written = 1 move
    rest = left[i:] + right[j:]
    c.swaps += len(rest)
    return out + rest


def quick_sort(a, c):
    # iterative (explicit stack) so 15,000 rows never hit Python's recursion limit
    stack = [(0, len(a) - 1)]
    while stack:
        lo, hi = stack.pop()
        if lo >= hi:
            continue
        r = random.randint(lo, hi)               # random pivot avoids O(n^2) on sorted data
        a[r], a[hi] = a[hi], a[r]
        pivot, i = a[hi], lo
        for j in range(lo, hi):
            if c.less(a[j], pivot):
                a[i], a[j] = a[j], a[i]
                c.swaps += 1
                i += 1
        a[i], a[hi] = a[hi], a[i]
        c.swaps += 1
        stack.append((lo, i - 1))
        stack.append((i + 1, hi))
    return a


def heap_sort(a, c):
    n = len(a)

    def sift_down(root, end):
        while True:
            child = 2 * root + 1
            if child >= end:
                return
            if child + 1 < end and c.less(a[child], a[child + 1]):
                child += 1
            if c.less(a[root], a[child]):
                a[root], a[child] = a[child], a[root]
                c.swaps += 1
                root = child
            else:
                return

    for s in range(n // 2 - 1, -1, -1):          # build max-heap
        sift_down(s, n)
    for end in range(n - 1, 0, -1):
        a[0], a[end] = a[end], a[0]
        c.swaps += 1
        sift_down(0, end)
    return a


def shell_sort(a, c):
    gap = len(a) // 2
    while gap > 0:
        for i in range(gap, len(a)):
            cur, j = a[i], i
            while j >= gap and c.less(cur, a[j - gap]):
                a[j] = a[j - gap]
                c.swaps += 1
                j -= gap
            a[j] = cur
        gap //= 2
    return a


# ---------------- non-comparison sorts (integer keys only) ----------------
def counting_sort(a, c):
    if not a:
        return a
    lo = min(x[0] for x in a)
    hi = max(x[0] for x in a)
    count = [0] * (hi - lo + 1)
    for x in a:
        count[x[0] - lo] += 1
    for i in range(1, len(count)):
        count[i] += count[i - 1]
    out = [None] * len(a)
    for x in reversed(a):                        # reversed keeps it stable
        count[x[0] - lo] -= 1
        out[count[x[0] - lo]] = x
        c.swaps += 1
    return out


def radix_sort(a, c):
    if not a:
        return a
    lo = min(x[0] for x in a)
    shifted = [(x[0] - lo, x[1]) for x in a]     # make all keys >= 0
    exp, mx = 1, max(x[0] for x in shifted)
    while mx // exp > 0:
        buckets = [[] for _ in range(10)]
        for x in shifted:
            buckets[(x[0] // exp) % 10].append(x)
            c.swaps += 1
        shifted = [x for b in buckets for x in b]
        exp *= 10
    return [(x[0] + lo, x[1]) for x in shifted]



def _merge(left, right, c):
    out, i, j = [], 0, 0
    while i < len(left) and j < len(right):
        if c.less(right[j], left[i]):            # take left on ties = stable
            out.append(right[j]); j += 1
        else:
            out.append(left[i]); i += 1
        c.swaps += 1
    rest = left[i:] + right[j:]
    c.swaps += len(rest)
    return out + rest


def hybrid_merge_sort(a, c, threshold=16):
    # Merge sort that hands small pieces to insertion sort (class "hybrid merge")
    if len(a) <= threshold:
        return insertion_sort(list(a), c)
    mid = len(a) // 2
    return _merge(hybrid_merge_sort(a[:mid], c, threshold),
                  hybrid_merge_sort(a[mid:], c, threshold), c)


def bucket_sort(a, c):
    # Numeric keys only. Spread into ~sqrt(n) buckets, insertion-sort each bucket.
    n = len(a)
    if n <= 1:
        return a
    lo = min(x[0] for x in a)
    hi = max(x[0] for x in a)
    nb = max(1, int(n ** 0.5))
    width = (hi - lo) / nb or 1                  # all-equal keys -> width 1
    buckets = [[] for _ in range(nb)]
    for x in a:
        buckets[min(int((x[0] - lo) / width), nb - 1)].append(x)
        c.swaps += 1                             # placing into a bucket = 1 move
    out = []
    for b in buckets:
        out.extend(insertion_sort(b, c))         # insertion sort counts its own work
    return out


NUMERIC_ONLY = {"Bucket Sort"}                   # need numbers, not necessarily integers

# name -> (function, time complexity, stable?, integer keys only?)
ALGORITHMS = {
    "Bubble Sort":    (bubble_sort,    "O(n^2)",                 True,  False),
    "Selection Sort": (selection_sort, "O(n^2)",                 False, False),
    "Insertion Sort": (insertion_sort, "O(n^2)",                 True,  False),
    "Merge Sort":     (merge_sort,     "O(n log n)",             True,  False),
    "Hybrid Merge Sort": (hybrid_merge_sort, "O(n log n)",          True,  False),
    "Quick Sort":     (quick_sort,     "O(n log n) avg, O(n^2) worst", False, False),
    "Heap Sort":      (heap_sort,      "O(n log n)",             False, False),
    "Shell Sort":     (shell_sort,     "O(n log n) to O(n^2)",   False, False),
    "Counting Sort":  (counting_sort,  "O(n + k)",               True,  True),
    "Radix Sort":     (radix_sort,     "O(d * (n + b))",         True,  True),
    "Bucket Sort":    (bucket_sort,    "O(n + k) avg, O(n^2) worst", True, False),
}


def sort_rows(values, algo_name, descending=False):
    """
    values: list of column values, one per table row (None/NaN = missing).
    Returns (order, stats): order = row indices in sorted order.
    Missing values are always placed LAST (decision stated on purpose).
    """
    func, complexity, stable, int_only = ALGORITHMS[algo_name]
    present, missing = [], []
    for idx, v in enumerate(values):
        if v is None or v != v or v == "":       # v != v is True only for NaN
            missing.append(idx)
        else:
            present.append((v, idx))

    if algo_name in NUMERIC_ONLY:
        try:
            for k, _ in present:
                float(k)
        except (TypeError, ValueError):
            raise ValueError(f"{algo_name} needs numeric keys; this column is text.")
    try:
        bad_int = int_only and any(not float(k).is_integer() for k, _ in present)
    except (TypeError, ValueError):
        bad_int = True
    if bad_int:
        raise ValueError(f"{algo_name} needs integer keys; this column is not integer.")
    if int_only:
        present = [(int(k), i) for k, i in present]

    c = Counter()
    t0 = time.perf_counter()
    result = func(list(present), c)
    ms = (time.perf_counter() - t0) * 1000

    if descending:
        result = result[::-1]                    # note: reverses ties too
    order = [i for _, i in result] + missing
    stats = {"algorithm": algo_name, "time_ms": round(ms, 2),
             "comparisons": c.comparisons, "swaps": c.swaps,
             "complexity": complexity, "stable": stable}
    return order, stats


def benchmark(values, skip_slow_above=None):
    """Run every applicable algorithm on one column -> list of stats dicts."""
    rows = []
    n = sum(1 for v in values if v is not None and v == v and v != "")
    for name, (_, cx, st, int_only) in ALGORITHMS.items():
        if skip_slow_above and n > skip_slow_above and cx == "O(n^2)":
            rows.append({"algorithm": name, "time_ms": None, "comparisons": None,
                         "swaps": None, "complexity": cx, "stable": st,
                         "note": "skipped (too slow)"})
            continue
        try:
            rows.append(sort_rows(values, name)[1])
        except ValueError as e:
            rows.append({"algorithm": name, "time_ms": None, "comparisons": None,
                         "swaps": None, "complexity": cx, "stable": st,
                         "note": "not applicable (needs numeric/integer column)"})
    return rows


def sort_rows_multi(levels, algo_name):
    """
    Multi-level sort. levels = [(values, descending), ...] most important first.
    Each row gets a tuple key made of per-level RANKS, so ONE sort (with the
    chosen algorithm) orders by level 1, then level 2, then level 3...
    Descending = negative rank. Missing values always last.
    Counting/Radix are not allowed here (tuple keys are not integers).
    """
    func, complexity, stable, int_only = ALGORITHMS[algo_name]
    if int_only or algo_name in NUMERIC_ONLY:
        raise ValueError(f"{algo_name} cannot do multi-level sort; pick a comparison sort.")
    n = len(levels[0][0])
    rank_cols = []
    for values, desc in levels:
        uniq = sorted({v for v in values if v is not None and v == v})
        rank = {v: r for r, v in enumerate(uniq)}
        col = []
        for v in values:
            if v is None or v != v:
                col.append(1 if desc else len(uniq))      # missing -> always last
            else:
                col.append(-rank[v] if desc else rank[v])
        rank_cols.append(col)
    pairs = [(tuple(rc[i] for rc in rank_cols), i) for i in range(n)]
    c = Counter()
    t0 = time.perf_counter()
    result = func(pairs, c)
    ms = (time.perf_counter() - t0) * 1000
    return [i for _, i in result], {"algorithm": algo_name, "time_ms": round(ms, 2),
                                   "comparisons": c.comparisons, "swaps": c.swaps,
                                   "complexity": complexity, "stable": stable}
