# ConsensusProbe — Deep Flaw & Logic Audit Report

> Full cat-and-hunt across every layer: research engine, backend API, frontend, auth, canary system, experiment runner, and security tooling.

---

## Severity Legend

| Symbol | Severity | Meaning |
|--------|----------|---------|
| 🔴 | **CRITICAL** | Causes wrong results, data loss, security breach, or silent corruption |
| 🟠 | **HIGH** | Causes incorrect logic under observable conditions, meaningful data integrity risk |
| 🟡 | **MEDIUM** | Incorrect behaviour in edge cases, design flaw that degrades research validity |
| 🔵 | **LOW** | Code smell, minor inconsistency, or maintainability gap |

---

## 1. Research Engine (`research/`)

### 🔴 CRITICAL-1 — `plan_to_patch` silently swallows ALL exceptions

**File:** [`research/consensus.py` L28–33](file:///c:/Users/koush/ConsensusProbe/research/consensus.py#L28-L33)

```python
try:
    curr_df, p = execute_op(curr_df, op_name, params)
    accum_patch = accum_patch.merge(p)
except Exception:
    # If an op fails to apply, continue or record as-is
    continue
```

**What is wrong:**
The bare `except Exception: continue` discards the exception entirely — including `KeyError`, `OperationError`, schema failures, and even `MemoryError`. When an op silently fails, `curr_df` is left at its pre-op state but `accum_patch` is not updated. The *next* op then runs on a stale `curr_df` that never received the previous transformation. This cascade invalidates the patch. For example, if Plan 0's `deduplicate` silently fails, Plan 0 records *zero* deletions. The disagreement score between Plan 0 and Plan 1 (which succeeded) is artificially inflated — triggering spurious clarification questions on disagreement that doesn't actually exist.

**Fix:** Collect failures structurally. Never continue silently on `OperationError`:

```python
try:
    curr_df, p = execute_op(curr_df, op_name, params)
    accum_patch = accum_patch.merge(p)
except OperationError as e:
    failed_ops.append((op_name, str(e)))
    continue
# Let unexpected exceptions propagate — they indicate a bug
```

---

### 🔴 CRITICAL-2 — `majority_vote_patch` reconstructs values through `repr`/`ast.literal_eval` round-trip, corrupting floats

**File:** [`research/consensus.py` L172–183](file:///c:/Users/koush/ConsensusProbe/research/consensus.py#L172-L183)

```python
val_repr = a[3]
try:
    val = ast.literal_eval(val_repr)
except Exception:
    val = val_repr   # ← falls back to the repr-string itself
```

**What is wrong:**
Values are stored as `repr(value)` strings in atoms. When majority vote reconstitutes them via `ast.literal_eval`, any value whose `repr()` is not a valid Python literal silently falls back to being stored as a *string*. For example: `repr(float('nan'))` → `'nan'`, and `ast.literal_eval('nan')` raises `ValueError` → the fallback stores the string `"nan"` into a numeric column. Any numpy scalar, `pandas.NA`, `NaT`, or custom object can trigger this. The patched DataFrame receives incorrect dtypes without any error — this is silent data corruption.

**Fix:** Store `(rid, col) → actual_value` in patch directly. Use a stable hash for atom-based disagreement comparison rather than encoding the value as `repr`:

```python
# In atoms() — for set comparison only, use a content hash
atoms.append(("edit", rid, col, _hash_value(value)))
# majority_vote_patch reads from patch.cell_edits_dict() (which stores real values)
```

---

### 🔴 CRITICAL-3 — Firebase API key committed to README and source; security scanner is blind to it

**File:** [`README.md` L78–85](file:///c:/Users/koush/ConsensusProbe/README.md#L78-L85)

```javascript
apiKey: "AIzaSy[REDACTED_API_KEY]",
```

**What is wrong:**
The Firebase `apiKey`, `appId`, and `measurementId` are verbatim in the public README. The `check_security.py` scanner only looks for `sk-...`, `AKIA...`, and PEM keys — it completely misses Firebase keys (`AIzaSy...`), Google OAuth client IDs, and `appId`. Anyone can use this key to write to your Firestore `cleaning_runs` collection (data poisoning), identify your project for phishing, or exhaust Firebase quotas.

**Fix:**
1. Move Firebase config to `VITE_FIREBASE_API_KEY` env var, load at build time
2. Add `re.compile(r'AIzaSy[a-zA-Z0-9_-]{33}')` to `SECRET_PATTERNS`
3. Harden Firestore rules to require auth on all writes

---

## 2. High Severity

### 🟠 HIGH-1 — `generate_clarification_question` picks `param_name` alphabetically across ALL params — not the contested one

**File:** [`research/consensus.py` L122–127](file:///c:/Users/koush/ConsensusProbe/research/consensus.py#L122-L127)

```python
diff_params = set()
for p in plans:
    for op in p.get("ops", []):
        for k in op.get("params", {}).keys():
            diff_params.add(k)
param_name = list(sorted(diff_params))[0] if diff_params else "cleaning_strategy"
```

**What is wrong:**
This collects *all* parameter keys from *all* ops across all plans, then picks the lexicographically first one. It makes no attempt to find which parameter *actually differs* between plans. If plans disagree on `keep` (first vs last) in a deduplicate op but `by` is constant, the code surfaces `by` as the contested param because `'b' < 'k'` alphabetically. The user sees: *"Multiple conflicting plans detected regarding 'by'."* — which is factually wrong. This directly corrupts `question_precision` measurements.

**Fix:**
```python
# Collect only keys whose values differ across plans
all_op_params = [op.get("params", {}) for p in plans for op in p.get("ops", [])]
contested_keys = {k for k in {k for p in all_op_params for k in p}
                  if len({repr(p.get(k)) for p in all_op_params}) > 1}
param_name = sorted(contested_keys)[0] if contested_keys else "cleaning_strategy"
```

---

### 🟠 HIGH-2 — `_ACTIVE_PATCHES` is a process-global dict — multi-worker deployments corrupt each other silently

**File:** [`backend/app/main.py` L90](file:///c:/Users/koush/ConsensusProbe/backend/app/main.py#L90)

```python
_ACTIVE_PATCHES: dict[str, Patch] = {}
```

**What is wrong:**
With `uvicorn --workers 4`, each worker process has its own copy of `_ACTIVE_PATCHES`. `/upload` on Worker 1 and `/clean` on Worker 2 leaves the patch in Worker 2's dict. If `/export` hits Worker 1, the patch is not found — the endpoint silently exports the **uncleaned** original dataset with no error raised. After any server restart, all patches are lost and exports silently serve pre-patch data.

**Fix:** Persist the active patch to the `OperationRun` table as a serializable JSON blob. Load from DB in `/profile` and `/export` instead of the in-memory dict.

---

### 🟠 HIGH-3 — `handle_missing` with `fill_mean`/`fill_median` stores numpy scalars — NaN mean case corrupts patch

**File:** [`research/operations.py` L155–172](file:///c:/Users/koush/ConsensusProbe/research/operations.py#L155-L172)

**What is wrong:**
`df[col].mean()` on an all-null column returns `numpy.float64(nan)`. This is stored as `fill_val` in `cell_edits`. `repr(numpy.float64(nan))` = `'nan'`. `ast.literal_eval('nan')` raises `ValueError` → majority vote patch silently inserts the string `"nan"` into numeric cells (see CRITICAL-2). Additionally, `result[col].fillna(NaN)` is a no-op in pandas, so the DataFrame is not actually changed, while the patch claims cells were edited — patch is inconsistent with the DataFrame.

**Fix:**
```python
if isinstance(fill_val, float) and pd.isna(fill_val):
    raise OperationError(f"handle_missing: computed fill is NaN for '{col}' (all values null?)")
fill_val = float(fill_val) if isinstance(fill_val, (int, float)) else fill_val
```

---

### 🟠 HIGH-4 — `track_s.py` gold edits use hardcoded positional indices 0–5, not stable `_rid` values

**File:** [`research/track_s.py` L90–143](file:///c:/Users/koush/ConsensusProbe/research/track_s.py#L90-L143)

```python
df.at[0, "product_name"] = "Laptop Pro"
required_edits.append(("del", 1))   # hardcoded rid=1
```

**What is wrong:**
`df.at[0, ...]` uses the pandas **integer index label**, while `_rid` is a separate column. At initialization they coincide. But if any prior test or operation resets the index (`.reset_index()`, after `deduplicate()` on a copy), they diverge. The gold `("del", 1)` assumes `_rid=1` matches pandas label `1`, which only holds for the pristine DataFrame. Under index drift, gold comparison via `patch.atoms()` will fail to find the match — causing false task failures or false successes.

**Fix:**
```python
df = _inject_rid(pd.DataFrame(rows))
rid_at = lambda pos: int(df.iloc[pos]['_rid'])
required_edits.append(("del", rid_at(1)))
```

---

### 🟠 HIGH-5 — Canary rows inject hardcoded Track-S schema columns onto arbitrary user datasets

**File:** [`research/canary.py` L25–60](file:///c:/Users/koush/ConsensusProbe/research/canary.py#L25-L60)

```python
canary_rows.append({"sku": canary_sku, "product_name": "Canary Sensor Pod", ...})
```

**What is wrong:**
If System F runs on any non-retail dataset, `pd.concat` creates a DataFrame where real rows have `NaN` in `sku`/`product_name`/`price` and canary rows have `NaN` in that dataset's actual columns. Cleaning ops then process this contaminated schema — `handle_missing` sees artificially inflated null counts, `deduplicate` deduplicates on wrong columns. The canary verification runs against this corrupted DataFrame and produces meaningless safety results.

**Fix:** Inject canaries by modifying copies of actual rows from `df` rather than constructing hardcoded-schema rows.

---

### 🟠 HIGH-6 — Backend's `/clean` endpoint synthesizes plans from DataFrame structure, bypassing the research engine

**File:** [`backend/app/main.py` L208–250](file:///c:/Users/koush/ConsensusProbe/backend/app/main.py#L208-L250)

**What is wrong:**
The backend hand-crafts 3 candidate plans directly from column names rather than calling `MockProvider` or any real LLM. For a dataset with no nulls and no duplicates, all 3 plans are identical (empty ops). `consensus_score = 0.0`, `should_ask = False`, `status: "applied"` with zero changes. The user sees a "successful clean" with no feedback about what (if anything) was done. This is not the ConsensusGate algorithm — the entire research contribution is bypassed in the production backend.

---

### 🟠 HIGH-7 — `handleRunConsensus` calls `recordCleaningRun` twice; first call uses stale React state

**File:** [`frontend/src/App.tsx` L261–281](file:///c:/Users/koush/ConsensusProbe/frontend/src/App.tsx#L261-L281)

```javascript
// First call — stale state (previous run, or null on first run)
recordCleaningRun({ consensusScore: consensusScore, ... });

// Second call — correct fresh value
recordCleaningRun({ consensusScore: data.consensus_score, ... });
```

**What is wrong:**
Two Firestore writes per clean. The first writes the *old* score (or `null`). If Firestore uses `addDoc`, two documents are created — one corrupt. This pollutes the cloud dataset on every single cleaning operation.

---

### 🟠 HIGH-8 — `applyToSimilar` from `ClarificationModal.onConfirm` is received but never used

**File:** [`frontend/src/App.tsx` L750–754](file:///c:/Users/koush/ConsensusProbe/frontend/src/App.tsx#L750-L754)

```javascript
onConfirm={(optId, applyToSimilar) => {
    setSelectedOption(optId);
    handleResolveClarification();   // applyToSimilar silently dropped
    setIsClarifyModalOpen(false);
}}
```

The UI offers "Apply to similar cases" but the app discards the flag. Users who check it believe they're setting a policy; they are not. This is a broken UI contract.

---

### 🟠 HIGH-9 — Security scanner misses Firebase and OAuth credential patterns

**File:** [`scripts/check_security.py` L7–12](file:///c:/Users/koush/ConsensusProbe/scripts/check_security.py#L7-L12)

The scanner checks for `sk-...` (OpenAI), `AKIA...` (AWS), and PEM keys only. Firebase `apiKey` (`AIzaSy...`), Google OAuth `clientId`, `appId`, and `measurementId` — all committed in the repo — produce zero findings. The scanner passes, giving false confidence.

Add:
```python
re.compile(r'AIzaSy[a-zA-Z0-9_-]{33}'),
re.compile(r'\d{6,}-[a-z0-9]+\.apps\.googleusercontent\.com'),
```

---

## 3. Medium Severity

### 🟡 MEDIUM-1 — Calibration evaluates `should_ask` as a classifier for `is_ambiguous` — a category error

**File:** [`research/calibrate_dev.py` L57–92](file:///c:/Users/koush/ConsensusProbe/research/calibrate_dev.py#L57-L92)

A task can be genuinely ambiguous but all plans agree (all deviate in the same direction, `score=0.0`, `should_ask=False`). This correct behavior is counted as a false negative (`fn += 1`), which inflates FN, suppresses recall, and biases the calibrated `tau_d`. The claim that `tau_d=0.0` maximizes F1 is built partly on this error.

---

### 🟡 MEDIUM-2 — `UserSimulator.rng` is shared across tasks — not independently seeded per trial

**File:** [`research/simulators.py` L38](file:///c:/Users/koush/ConsensusProbe/research/simulators.py#L38)

A single `self.rng` instance is advanced by every `answer_question` call. When the same simulator is reused across tasks (as in `run_block`), the random outcomes of task N+1 depend on how many questions were asked in tasks 1…N. The pre-registration claim of independent trial seeds is violated.

---

### 🟡 MEDIUM-3 — Block cache validated only by record count, not content integrity

**File:** [`research/run_experiments.py` L36–38](file:///c:/Users/koush/ConsensusProbe/research/run_experiments.py#L36-L38)

```python
if len(data) == len(tasks) * TRIALS:
    return data
```

A partially written or parameter-stale cache file with the right record count is returned as valid. Code changes between runs that don't alter `TRIALS` count will silently serve old results.

---

### 🟡 MEDIUM-4 — `convert_type` uses `repr`-equality for change detection, wrong for numpy integer dtypes

**File:** [`research/operations.py` L194](file:///c:/Users/koush/ConsensusProbe/research/operations.py#L194)

`repr(numpy.int64(5))` = `'5'` and `repr(int(5))` = `'5'` — so columns already containing numpy integers never produce change records. The gold `required_edits` for `type_coercion` tasks will not be satisfied, causing silent false task failures.

---

### 🟡 MEDIUM-5 — Export links bypass `apiClient`, fail silently when auth is enforced

**File:** [`frontend/src/App.tsx` L662–681](file:///c:/Users/koush/ConsensusProbe/frontend/src/App.tsx#L662-L681)

```jsx
<a href={`${API_BASE}/export/${currentDataset.id}?format=csv`}>CSV</a>
```

Plain `<a href>` sends no Bearer token. With `AUTH_ENFORCE=true`, backend returns 401 and the browser shows a JSON error page instead of downloading the file. No user-visible error is shown.

---

### 🟡 MEDIUM-6 — Demo session token is not a JWT; session never expires

**File:** [`frontend/src/context/AuthContext.tsx` L197](file:///c:/Users/koush/ConsensusProbe/frontend/src/context/AuthContext.tsx#L197)

```javascript
const demoToken = 'demo-session-token-' + Date.now();
```

`decodeJwtPayload` returns `null` for this. On page refresh, `payload.exp` is never checked — the demo session is accepted as authenticated forever. Demo sessions on shared machines never expire.

---

### 🟡 MEDIUM-7 — `shell=True` detection misses aliased `subprocess` imports

**File:** [`scripts/check_security.py` L35–43](file:///c:/Users/koush/ConsensusProbe/scripts/check_security.py#L35-L43)

Only matches `subprocess.run(shell=True)`, not `sp.run(...)`, `proc.run(...)` etc. The check is trivially bypassed by renaming the import.

---

### 🟡 MEDIUM-8 — H1 hypothesis test applies asymmetric CI criteria to oracle vs noisy modes

**File:** [`research/run_experiments.py` L197](file:///c:/Users/koush/ConsensusProbe/research/run_experiments.py#L197)

```python
h1_supported = (h1_noisy[0] < 0 and h1_noisy[2] < 0) and (h1_oracle[0] <= 0)
```

Noisy requires `CI_upper < 0` (strict, CI-based). Oracle only requires `mean_diff <= 0` (no CI check). This double standard is not in the pre-registration and means oracle mode could show E slightly worse than A with a CI including positive values, yet H1 is still claimed as supported.

---

### 🟡 MEDIUM-9 — Bootstrap p-value double-counts the zero boundary

**File:** [`research/run_experiments.py` L189](file:///c:/Users/koush/ConsensusProbe/research/run_experiments.py#L189)

```python
p_val = float(2.0 * min(np.mean(boot_means >= 0), np.mean(boot_means <= 0)))
```

When any bootstrap mean equals exactly 0, `P(x >= 0) + P(x <= 0) > 1`. The two-sided p-value double-counts the boundary mass. Use `>` on one side: `min(mean(x > 0), mean(x < 0))`.

---

### 🟡 MEDIUM-10 — `_ACTIVE_PATCHES` accumulates forever; no eviction policy

**File:** [`backend/app/main.py` L90](file:///c:/Users/koush/ConsensusProbe/backend/app/main.py#L90)

The `backend/storage/` directory already has 50+ uploaded files from prior sessions. Each `/clean` call adds an entry. Under sustained use this causes unbounded memory growth and eventual OOM crash with no warning.

---

## 4. Low Severity

### 🔵 LOW-1 — `fill_mode` with empty column stores `None` — patch inconsistent with DataFrame state

**File:** [`research/operations.py` L160–161](file:///c:/Users/koush/ConsensusProbe/research/operations.py#L160-L161)

If the column is entirely null, `fill_val = None`. `result[col].fillna(None)` is a no-op in pandas for most dtypes. The DataFrame is unchanged but the patch claims cells were edited. Patch and DataFrame are inconsistent.

---

### 🔵 LOW-2 — `deduplicate` implementation allows `keep=False` but its schema entry does not

**File:** [`research/operations.py` L32, L206](file:///c:/Users/koush/ConsensusProbe/research/operations.py#L32)

The function accepts `keep=False`. The `OPERATIONS` registry schema lists only `'first'` and `'last'`. A plan specifying JSON `false` passes the function but would be rejected by any schema validator. Latent inconsistency.

---

### 🔵 LOW-3 — Two identical upload handlers in `App.tsx` — copy-paste divergence risk

**File:** [`frontend/src/App.tsx` L140–232](file:///c:/Users/koush/ConsensusProbe/frontend/src/App.tsx#L140-L232)

`handleIngestFile` (for dropzone) and `handleFileUpload` (for `<input>`) are line-for-line duplicates. Any future change (adding auth headers, error handling, progress tracking) must be applied twice or will silently diverge.

---

## Summary Table

| ID | Severity | File | Issue |
|----|----------|------|-------|
| CRITICAL-1 | 🔴 | `consensus.py:28` | Silent exception swallow corrupts multi-op patch execution |
| CRITICAL-2 | 🔴 | `consensus.py:172` | `repr/literal_eval` round-trip corrupts majority-vote values |
| CRITICAL-3 | 🔴 | `README.md:78` | Firebase API key hardcoded; scanner blind to it |
| HIGH-1 | 🟠 | `consensus.py:122` | Clarification param_name picks non-contested param alphabetically |
| HIGH-2 | 🟠 | `main.py:90` | Global in-memory patch dict fails under multi-worker/restart |
| HIGH-3 | 🟠 | `operations.py:167` | numpy NaN fill value → `repr("nan")` → data corruption in patch |
| HIGH-4 | 🟠 | `track_s.py:90` | Gold edits use hardcoded indices, not stable `_rid` values |
| HIGH-5 | 🟠 | `canary.py:25` | Canary rows inject hardcoded Track-S schema onto arbitrary datasets |
| HIGH-6 | 🟠 | `main.py:208` | Backend plan synthesis bypasses research engine entirely |
| HIGH-7 | 🟠 | `App.tsx:261` | Double Firestore write; first call uses stale React state score |
| HIGH-8 | 🟠 | `App.tsx:750` | `applyToSimilar` from clarification modal silently discarded |
| HIGH-9 | 🟠 | `check_security.py:7` | Firebase/OAuth keys invisible to secret scanner |
| MEDIUM-1 | 🟡 | `calibrate_dev.py:57` | Calibration objective is a category error (disagreement ≠ ambiguity) |
| MEDIUM-2 | 🟡 | `simulators.py:38` | Shared RNG state bleeds across tasks; not independently seeded |
| MEDIUM-3 | 🟡 | `run_experiments.py:36` | Block cache validated by length only, not content integrity |
| MEDIUM-4 | 🟡 | `operations.py:194` | `repr`-based change detection wrong for numpy int dtypes |
| MEDIUM-5 | 🟡 | `App.tsx:662` | Export links bypass `apiClient`; fail with no error when auth enforced |
| MEDIUM-6 | 🟡 | `AuthContext.tsx:197` | Demo token not JWT; session never expires |
| MEDIUM-7 | 🟡 | `check_security.py:35` | `shell=True` check misses aliased subprocess imports |
| MEDIUM-8 | 🟡 | `run_experiments.py:197` | H1 uses asymmetric CI criteria across oracle/noisy modes |
| MEDIUM-9 | 🟡 | `run_experiments.py:189` | Bootstrap p-value double-counts zero boundary |
| MEDIUM-10 | 🟡 | `main.py:90` | `_ACTIVE_PATCHES` never evicted — unbounded memory growth |
| LOW-1 | 🔵 | `operations.py:160` | `fill_mode` on empty column produces inconsistent patch |
| LOW-2 | 🔵 | `operations.py:206` | `deduplicate` schema omits `keep=False` variant |
| LOW-3 | 🔵 | `App.tsx:140` | Two identical upload handlers — copy-paste divergence risk |

---

> **Not checked:** `make_numbers.py` LaTeX macro generation (needs live experiment run to validate), Playwright golden snapshot logic, and `firestore.rules` depth. These are the remaining highest-risk uncovered areas.
