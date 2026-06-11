# Perfect Pitch Python App Implementation Plan

## Goal
Build a Python app that helps users regain absolute pitch through short daily exercises, adaptive repetition, and measurable progress tracking.

## Game Mode Extension: Perfect Pitch x Tetris
This app now includes a game-first mode:
- The app plays a tone first (no active falling piece yet).
- The player identifies the note.
- If correct, the matching tetromino auto-drops slowly into the best row-completing gap.
- If incorrect, a random tetromino starts falling and the player controls it (left/right/rotate).
- The run ends when the board is full and no new piece can spawn.

This keeps note training central while turning each mistake into a playable board-management consequence.

## Recommended Stack
- **UI**: `tkinter` (built-in, fast to ship)  
- **Audio playback**: `pygame` (reliable WAV playback)  
- **Data storage**: `sqlite3` (built-in, local-first)  
- **Charts (optional)**: `matplotlib` for progress views

## Python -> Flutter Transition Guidance
Using `tkinter` is acceptable for a prototype/reference build that validates gameplay rules and learning logic. It is not the right place to invest in long-term UI polish if the production target is Flutter.

Shift to Flutter when these conditions are met:
1. Core gameplay rules are stable for at least one week:
   - prompt flow, correct auto-drop, incorrect manual-drop, lock/clear, scoring, game-over.
2. Logic is UI-agnostic:
   - domain/controller behavior runs without tkinter-specific assumptions.
3. Deterministic tests are green:
   - state machine, placement heuristic, scoring, and end conditions.
4. Work is becoming UX-heavy:
   - touch controls, animation smoothness, responsive mobile layout, accessibility.

Practical handoff point:
- Finish Stage 7 logic tuning in Python.
- Move Stage 8+ UI-heavy refinement into Flutter/Dart.

## App Architecture
Use clear separation between layers:
- `ui/`: screens, widgets, event handlers
- `domain/`: training logic, scoring, adaptive scheduling
- `infra/`: audio generation/playback, sqlite repository, config
- `app/`: wiring/composition root (kept minimal)

Suggested root layout:
```text
perfect_pitch_app/
  main.py
  app/
    bootstrap.py
  ui/
    home_view.py
    training_view.py
    review_view.py
    progress_view.py
    settings_view.py
  domain/
    models.py
    note_engine.py
    session_service.py
    adaptation_service.py
    progress_service.py
  infra/
    db/
      connection.py
      schema.py
      repositories.py
    audio/
      tone_generator.py
      player.py
    config.py
  tests/
    test_note_engine.py
    test_adaptation_service.py
    test_progress_service.py
```

## Core Features (MVP)
1. Start a 10-minute training session.
2. Play random note (single octave first).
3. Let user choose note name (12 semitone buttons).
4. Record correctness + response time.
5. Adapt next questions toward weak notes.
6. Show end-of-session summary.
7. Show progress page with per-note accuracy.

## Note -> Tetromino -> Color Mapping (12 Notes)
Natural notes use standard tetromino colors. Accidentals use lighter shades of their natural-note family.

| Note | Tetromino | Shape | Color |
| --- | --- | --- | --- |
| C | I | Straight line | Cyan |
| C# / Db | I | Straight line | Light cyan |
| D | O | Square | Yellow |
| D# / Eb | O | Square | Light yellow |
| E | T | T-shape | Purple |
| F | S | Right-leaning zigzag | Green |
| F# / Gb | S | Right-leaning zigzag | Light green |
| G | Z | Left-leaning zigzag | Red |
| G# / Ab | Z | Left-leaning zigzag | Light red |
| A | J | Left L-shape | Blue |
| A# / Bb | J | Left L-shape | Light blue |
| B | L | Right L-shape | Orange |

Accidental set for the 12-tone mode: `C#/Db`, `D#/Eb`, `F#/Gb`, `G#/Ab`, `A#/Bb`.

## Domain Model
Main entities:
- `NoteAttempt`: timestamp, target_note, guessed_note, correct, response_ms, timbre
- `TrainingSession`: id, started_at, ended_at, total_attempts, accuracy
- `NoteStats`: note_name, total, correct, avg_response_ms
- `ConfusionPair`: from_note, to_note, count

## Database Schema (SQLite)
Tables:
- `attempts`
- `sessions`
- `note_stats` (or compute on demand)
- `settings`

Important fields:
- `attempts(target_note TEXT, guessed_note TEXT, correct INTEGER, response_ms INTEGER, timbre TEXT, created_at TEXT)`
- `sessions(started_at TEXT, ended_at TEXT, total_attempts INTEGER, accuracy REAL)`
- `settings(key TEXT PRIMARY KEY, value TEXT)`

Indexes:
- `attempts(created_at)`
- `attempts(target_note)`
- `attempts(correct)`

## Training Logic
- Phase 1: one octave, all 12 notes.
- Random note selection with weighted boost for weak notes.
- Weak-note score example:
  - `weakness = (1 - accuracy) + confusion_penalty + slow_response_penalty`
- Increase chance of weak notes in future prompts.
- Include periodic unbiased checks (fully random) to avoid overfitting.

## Audio Design
- Start with generated sine tones or bundled piano-note WAV files.
- Default duration: 1.2s tone + 0.5s silence.
- Prevent clipping and normalize output volume.
- Add optional A4 reference play button (toggleable in settings).

## UI Flow
1. **Home**: start session, last score, streak.
2. **Training**: play note, answer buttons, immediate feedback.
3. **Review**: common mistakes and replay drills.
4. **Progress**: accuracy by note, response-time trend.
5. **Settings**: A4 frequency, session length, timbre.

## Stage-by-Stage Implementation Plan (Whole App)
This extends the existing plan into a complete delivery path for the game mode.

### Stage 1: Foundation and Data Contracts
Deliverables:
- Finalize domain enums/constants for 12 notes, enharmonic labels, 7 tetromino families, and color palette (base + light variants).
- Define board constants (10x20), spawn rules, rotation system, collision rules, line-clear rules, and game-over condition.
- Extend DB schema with game fields:
  - `attempts`: selected_note, selected_family, generated_piece, placement_outcome, board_height_after, lines_cleared_after
  - `sessions`: mode (`training`, `game`), total_lines, max_streak, survival_seconds
- Add migration/versioning for schema upgrades.

Acceptance:
- App starts with migrated DB and no data loss.
- Domain layer can serialize/deserialize all new entities.

### Stage 2: Audio Round Engine (Prompt First, No Falling Piece)
Deliverables:
- Implement round state machine:
  1. `PROMPT_NOTE` (play tone, idle board)
  2. `AWAIT_ANSWER`
  3. `RESOLVE_ANSWER`
  4. `DROP_PHASE`
  5. `LOCK_AND_CLEAR`
  6. `NEXT_ROUND`
- Ensure no piece falls until answer submission.
- Add replay-note action (`R` key/button).

Acceptance:
- Tone plays reliably before any block movement.
- Round transitions are deterministic and test-covered.

### Stage 3: Correct-Answer Auto-Placement
Deliverables:
- Convert correct note answer -> exact mapped tetromino family/color.
- Implement "most suitable hole" selection heuristic:
  - Priority 1: placements that complete at least one line immediately
  - Priority 2: lowest aggregate column height increase
  - Priority 3: fewest enclosed holes created
- Auto-spawn and slow auto-drop to chosen target with no player control in this branch.

Acceptance:
- Correct answer always drops mapped piece automatically.
- If at least one line-completing placement exists, engine chooses one.

### Stage 4: Incorrect-Answer Controlled Random Piece
Deliverables:
- On wrong answer, select random tetromino (standard 7-bag or pure random; use 7-bag by default).
- Spawn falling piece with player controls enabled:
  - Left/right movement
  - Rotate
  - Soft drop
- Lock piece on landing, then evaluate line clears.

Acceptance:
- Wrong answer never auto-corrects to target piece.
- Controls remain responsive during descent and lock behavior is stable.

### Stage 5: Full Board Loop, Scoring, and End Conditions
Deliverables:
- Continuous round loop with increasing pressure configuration per level.
- Implement scoring split:
  - Pitch score (correctness, response speed, streak)
  - Board score (line clears, survival)
- End session when spawn collision indicates no room for new piece.
- Build post-run summary (accuracy by note, confusion pairs, lines cleared, survival time).

Acceptance:
- Game ends only on true board exhaustion.
- Summary metrics match recorded attempt/session rows.

### Stage 6: UI Integration (Tkinter MVP)
Deliverables:
- Main game screen:
  - Board canvas with target feedback
  - Note input controls (`C D E F G A B` + accidental selection method)
  - Replay-tone control
  - Score/streak/lives-or-errors indicators
- Visual distinction between natural and accidental colors (light variants readable on dark background).
- Keyboard controls for wrong-answer falling piece.

Acceptance:
- Core gameplay is fully playable with keyboard only.
- Color mapping and piece identity are visually consistent with table above.

### Stage 7: Adaptive Training in Game Context
Deliverables:
- Bias note generation toward weak notes/confusion pairs while preserving unpredictability.
- Add periodic unbiased rounds to avoid overfitting.
- Difficulty progression:
  - Level 1: natural notes only
  - Level 2: add accidentals
  - Level 3+: timbre variation, optional octave variation, faster board pressure

Acceptance:
- Weak-note bias is measurable in generated note distribution.
- Difficulty transitions occur by configured thresholds.

### Stage 8: Testing and Stabilization
Deliverables:
- Unit tests:
  - Note-family mapping and accidental labeling
  - Auto-placement heuristic ranking
  - Collision, rotation, line clear logic
  - Adaptive note weighting
- Integration tests:
  - Correct-answer branch end-to-end
  - Incorrect-answer branch end-to-end
  - Session persistence and reload
- Manual test checklist for latency, input repeat, and long-session stability.

Acceptance:
- Green automated tests for domain/services.
- No gameplay-breaking defects in manual MVP checklist.

### Stage 9: Packaging and Release
Deliverables:
- Config profiles (`dev`, `default`, `balanced difficulty`).
- Seed data/settings bootstrap.
- Build script and release notes for first internal playable.

Acceptance:
- One-command local run from clean checkout.
- Reproducible build and migration path documented.

## Implementation Milestones
1. **Project scaffold + DB init**
2. **Audio playback pipeline**
3. **Training screen + attempt capture**
4. **Adaptive weak-note logic**
5. **Progress calculations + UI graphs**
6. **Settings persistence**
7. **Tests + polish**

## Testing Plan
Unit tests:
- Note generation boundaries and note-label mapping
- Adaptive selection weights
- Accuracy/confusion matrix calculations

Integration tests:
- Session flow: start -> attempt -> summary -> persistence
- Settings changes reflected in training behavior

Manual tests:
- Verify no crashes on rapid button input
- Verify audio latency remains acceptable
- Verify DB persists across app restarts

## Minimal Build Order (Fastest Path)
1. Build CLI prototype first (`domain` + `infra`) to validate learning loop.
2. Add SQLite persistence.
3. Add Tkinter UI once core loop is stable.
4. Add adaptive logic and progress dashboards.

## Example `main.py` Responsibility
`main.py` should only:
- initialize app config
- initialize database schema
- wire services into UI
- run event loop

No domain rules or direct SQL inside `main.py`.

## Next Step
After this plan, implement the scaffold and a CLI MVP first, then layer in the GUI.

## Immediate Next Implementation Sequence
1. Implement Stage 1 and Stage 2 together (data contracts + round state machine).
2. Implement Stage 3 and Stage 4 (branch behavior for correct vs incorrect answers).
3. Implement Stage 5 scoring/end-loop and persist metrics.
4. Wire Stage 6 UI and controls.
5. Add Stage 7 adaptive tuning, then Stage 8 hardening.
