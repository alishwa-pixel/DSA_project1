# search_engine.py - DSA Project 1, Step 5
# Works on ONE column (a list of values, None = missing) and returns the
# list of matching ROW INDICES plus comparison count and time.
import math
import time

# ---------- single-column search algorithms (exact match) ----------
def linear_search(values, target, counter):
    hits = []
    for i, v in enumerate(values):
        if v is None:
            continue
        counter[0] += 1
        if v == target:
            hits.append(i)
    return hits


def _sorted_pairs(values):
    # binary/jump need sorted data. Sorting cost is NOT counted as search cost,
    # but we tell the user (see notes in the UI/report).
    return sorted(((v, i) for i, v in enumerate(values) if v is not None),
                  key=lambda p: p[0])


def binary_search(values, target, counter):
    pairs = _sorted_pairs(values)
    lo, hi, first = 0, len(pairs) - 1, -1
    while lo <= hi:
        mid = (lo + hi) // 2
        counter[0] += 1
        if pairs[mid][0] == target:
            first = mid
            hi = mid - 1                       # keep going left: find FIRST match
        elif pairs[mid][0] < target:
            lo = mid + 1
        else:
            hi = mid - 1
    hits = []
    if first != -1:
        j = first
        while j < len(pairs) and pairs[j][0] == target:   # collect all duplicates
            counter[0] += 1
            hits.append(pairs[j][1])
            j += 1
    return sorted(hits)


def jump_search(values, target, counter):
    pairs = _sorted_pairs(values)
    n = len(pairs)
    if n == 0:
        return []
    step = int(math.sqrt(n))
    prev, cur = 0, step
    while prev < n and pairs[min(cur, n) - 1][0] < target:
        counter[0] += 1
        prev, cur = cur, cur + step
    hits = []
    for j in range(prev, min(cur, n)):
        counter[0] += 1
        if pairs[j][0] == target:
            hits.append(pairs[j][1])
    # duplicates can spill across a block edge: scan neighbours
    j = min(cur, n)
    while j < n and pairs[j][0] == target:
        counter[0] += 1
        hits.append(pairs[j][1]); j += 1
    return sorted(set(hits))


EXACT_ALGOS = {"Linear Search": linear_search,
               "Binary Search": binary_search,
               "Jump Search": jump_search}

# ---------- filter modes ----------
TEXT_MODES = ["contains", "starts with", "ends with", "equals"]
NUM_MODES = ["equals", "greater than", "less than", ">=", "<="]


def search_column(values, query, mode, algo="Linear Search"):
    """Returns (row_indices, stats). contains/starts/ends are always linear scans."""
    counter = [0]
    t0 = time.perf_counter()
    is_num = any(isinstance(v, (int, float)) for v in values[:50] if v is not None)

    if is_num:
        q = float(query)
        if mode == "equals":
            hits = EXACT_ALGOS[algo](values, q, counter)
        else:
            ops = {"greater than": lambda a: a > q, "less than": lambda a: a < q,
                   ">=": lambda a: a >= q, "<=": lambda a: a <= q}
            f, hits = ops[mode], []
            for i, v in enumerate(values):
                if v is not None:
                    counter[0] += 1
                    if f(v):
                        hits.append(i)
    else:
        q = str(query).lower()
        if mode == "equals":
            low = [None if v is None else str(v).lower() for v in values]
            hits = EXACT_ALGOS[algo](low, q, counter)
        else:
            tests = {"contains": lambda s: q in s,
                     "starts with": lambda s: s.startswith(q),
                     "ends with": lambda s: s.endswith(q)}
            f, hits = tests[mode], []
            for i, v in enumerate(values):
                if v is not None:
                    counter[0] += 1
                    if f(str(v).lower()):
                        hits.append(i)

    ms = (time.perf_counter() - t0) * 1000
    return hits, {"comparisons": counter[0], "time_ms": round(ms, 2)}


# ---------- composite search: AND / OR / NOT ----------
def composite_search(columns, n_rows, conditions, scope=None):
    """
    conditions: list of dicts, in order:
      {"column": "title", "mode": "contains", "value": "war",
       "algo": "Linear Search", "not": False, "join": "AND"}
    'join' links a condition to the PREVIOUS one (ignored for the first).
    AND binds tighter than OR:  A AND B OR C  ==  (A AND B) OR C.
    scope: optional list of row indices (search only inside current results).
    """
    universe = set(range(n_rows))
    groups = []                                  # each group = AND-chain; groups are OR-ed
    total_cmp, t0 = 0, time.perf_counter()
    for k, cond in enumerate(conditions):
        hits, st = search_column(columns[cond["column"]], cond["value"],
                                 cond["mode"], cond.get("algo", "Linear Search"))
        total_cmp += st["comparisons"]
        s = set(hits)
        if cond.get("not"):
            s = universe - s                     # NOT = everything except the matches
        if k == 0 or cond.get("join", "AND") == "OR":
            groups.append(s)                     # start a new OR-group
        else:
            groups[-1] &= s                      # AND = intersection
    result = set().union(*groups) if groups else set()
    if scope is not None:
        result &= set(scope)
    ms = (time.perf_counter() - t0) * 1000
    return sorted(result), {"comparisons": total_cmp, "time_ms": round(ms, 2)}
