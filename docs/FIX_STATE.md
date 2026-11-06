# Audit Fix State
# Format: ID | STATUS | NOTE

C1 | DONE | plan_to_patch logs failed ops with logging.warning instead of silently swallowing
C2 | DONE | majority_vote_patch reads actual values from patch.cell_edits_dict() instead of repr/literal_eval roundtrip
C3 | DONE | README.md lines 77-85 replaced with placeholders; firebase.ts uses VITE_FIREBASE_* env vars; frontend/.env.example created
H1 | DONE | generate_clarification_question picks param where values actually differ across plans, not first alphabetically
H2 | TODO | backend/app/main.py:90 _ACTIVE_PATCHES fails multi-worker
H3 | DONE | fill_mean/fill_median/fill_mode on empty column raises OperationError
H4 | TODO | research/track_s.py:90 gold edits use hardcoded indices
H5 | TODO | research/canary.py:25 canary injects hardcoded schema
H6 | TODO | backend/app/main.py:208 /clean bypasses research engine
H7 | TODO | frontend/src/App.tsx:261 double Firestore write stale state
H8 | TODO | frontend/src/App.tsx:750 applyToSimilar silently dropped
H9 | DONE | Added Firebase/OAuth patterns to SECRET_PATTERNS; .env.example in SKIP_FILES; dist in SKIP_DIRS
M1 | TODO | research/calibrate_dev.py:57 calibration category error
M2 | TODO | research/simulators.py:38 shared RNG bleeds across tasks
M3 | TODO | research/run_experiments.py:36 block cache validated by length only
M4 | DONE | convert_type uses direct value comparison instead of repr strings
M5 | TODO | frontend/src/App.tsx:662 export links bypass apiClient
M6 | TODO | frontend/src/context/AuthContext.tsx:197 demo token no expiry
M7 | DONE | shell=True check no longer requires exact 'subprocess' module name; catches aliased imports
M8 | TODO | research/run_experiments.py:197 H1 asymmetric CI criteria
M9 | TODO | research/run_experiments.py:189 bootstrap p-value double-counts zero
M10 | TODO | backend/app/main.py:90 _ACTIVE_PATCHES never evicted
L1 | DONE | fill_mode on empty column raises OperationError with clear message
L2 | DONE | deduplicate schema includes keep=False in enum
L3 | TODO | frontend/src/App.tsx:140 two identical upload handlers
