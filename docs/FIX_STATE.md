# Audit Fix State
# Format: ID | STATUS | NOTE

C1 | DONE | plan_to_patch logs failed ops with logging.warning instead of silently swallowing
C2 | DONE | majority_vote_patch reads actual values from patch.cell_edits_dict() instead of repr/literal_eval roundtrip
C3 | DONE | README.md lines 77-85 replaced with placeholders; firebase.ts uses VITE_FIREBASE_* env vars; frontend/.env.example created
H1 | DONE | generate_clarification_question picks param where values actually differ across plans, not first alphabetically
H2 | TODO | backend/app/main.py:90 _ACTIVE_PATCHES fails multi-worker
H3 | DONE | fill_mean/fill_median/fill_mode on empty column raises OperationError
H4 | DONE | research/track_s.py uses _set/_get by _rid instead of positional index
H5 | DONE | research/canary.py clones existing row to avoid hardcoded schema
H6 | TODO | backend/app/main.py:208 /clean bypasses research engine
H7 | TODO | frontend/src/App.tsx:261 double Firestore write stale state
H8 | TODO | frontend/src/App.tsx:750 applyToSimilar silently dropped
H9 | DONE | Added Firebase/OAuth patterns to SECRET_PATTERNS; .env.example in SKIP_FILES; dist in SKIP_DIRS
M1 | DONE | research/calibrate_dev.py documented category error limitation
M2 | DONE | research/simulators.py RNG seeded per-call with task/call key
M3 | DONE | research/run_experiments.py validates cache with content and structure checks
M4 | DONE | convert_type uses direct value comparison instead of repr strings
M5 | TODO | frontend/src/App.tsx:662 export links bypass apiClient
M6 | TODO | frontend/src/context/AuthContext.tsx:197 demo token no expiry
M7 | DONE | shell=True check no longer requires exact 'subprocess' module name; catches aliased imports
M8 | DONE | research/run_experiments.py H1 uses symmetric CI criteria
M9 | DONE | research/run_experiments.py bootstrap p-value calculation fixed for zero boundary
M10 | TODO | backend/app/main.py:90 _ACTIVE_PATCHES never evicted
L1 | DONE | fill_mode on empty column raises OperationError with clear message
L2 | DONE | deduplicate schema includes keep=False in enum
L3 | TODO | frontend/src/App.tsx:140 two identical upload handlers
