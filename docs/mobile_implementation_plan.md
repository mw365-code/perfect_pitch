# Mobile Implementation Plan

## Goal
Build the Perfect Pitch Tetris game as a mobile-first app experience that fits naturally inside a phone screen and can later be translated into Flutter.

The plan should keep game rules, pitch-training logic, audio, persistence, and UI layout separate. That makes the first implementation easier to test and makes the later Flutter version a translation of clear parts instead of a rewrite from scratch.

## Target Mobile Shape
Design against a portrait phone screen first.

Recommended baseline:

- Logical canvas: 390 x 844 points.
- Safe content width: 360 points.
- Minimum supported width: 320 points.
- Primary orientation: portrait.
- Board aspect: 10 columns by 20 rows.
- Main interaction zone: lower half of the screen for thumb access.

The game should not require landscape mode. The board should remain visible while the player chooses a piece.

## Primary Screen Layout
The MVP should use one main game screen with compact overlays instead of switching screens during active play.

```text
┌──────────────────────────────┐
│ Safe area                    │
│ Score   Streak   Level       │
│ Mistakes / Lives             │
├──────────────────────────────┤
│          Replay tone         │
│       Current prompt state   │
├──────────────────────────────┤
│                              │
│          10 x 20 board       │
│      target space outline    │
│                              │
│                              │
│                              │
├──────────────────────────────┤
│ Feedback / correction text   │
├──────────────────────────────┤
│ I    O    T    S             │
│ C    D    E    F             │
│ Z    J    L    Replay        │
│ G    A    B                  │
├──────────────────────────────┤
│ ←        rotate        →      │
└──────────────────────────────┘
```

The bottom controls change by game state:

- During note selection: show the 7 note-piece buttons.
- During incorrect-piece descent: show left, rotate, and right controls.
- During feedback: keep replay and continue controls visible.

## Mobile Layout Rules
- Keep every touch target at least 44 x 44 points.
- Keep the 7 tetromino selectors reachable without stretching.
- Use a fixed board width based on available screen width.
- Derive cell size from board width: `cellSize = boardWidth / 10`.
- Board height is `cellSize * 20`.
- If vertical space is tight, shrink the board before shrinking controls.
- Keep text short and avoid wrapping inside buttons.
- Use icon buttons for replay, left, right, rotate, and pause in the final UI.

## Core App States
The app should be driven by an explicit state machine.

| State | Purpose | Primary UI |
| --- | --- | --- |
| `loading` | Load settings, stats, audio resources | Splash or simple loading view |
| `ready` | Session is ready but not started | Start button and mode selector |
| `playingTone` | Tone is being played | Board visible, selectors disabled |
| `awaitingAnswer` | Player chooses the note-piece | Board and 7 selectors |
| `correctDrop` | Correct block drops into target space | Board animation, selectors disabled |
| `incorrectFalling` | Wrong block falls slowly | Board plus move controls |
| `feedback` | Show result and learning feedback | Correction text, replay, continue |
| `lineClear` | Animate cleared rows | Board animation |
| `gameOver` | Board topped out or mistakes exhausted | Summary and restart |

Only the state machine should decide which inputs are accepted.

## Core Domain Modules
These modules should remain UI-framework independent.

### `PieceCatalog`
Owns the note-to-tetromino mapping.

Responsibilities:

- Map C, D, E, F, G, A, B to the 7 tetromino shapes.
- Map accidentals to lighter color variants.
- Return display labels, shape cells, base color, and accidental color.
- Keep the mapping consistent across Python and Flutter.

### `BoardEngine`
Owns board rules.

Responsibilities:

- Maintain the 10 x 20 grid.
- Spawn pieces.
- Validate placement.
- Move pieces left and right.
- Rotate pieces when the current level allows it.
- Lock pieces.
- Detect and clear lines.
- Detect game over.

### `PromptEngine`
Owns pitch-training prompt selection.

Responsibilities:

- Choose the next note.
- Respect level difficulty.
- Bias toward weak notes.
- Avoid impossible target-piece placements.
- Track whether the prompt is natural or accidental.

### `ScoringService`
Owns points and streaks.

Responsibilities:

- Award correct-answer points.
- Apply speed bonuses.
- Track streaks.
- Award line-clear bonuses.
- Reset or reduce streaks after mistakes.

### `AttemptRecorder`
Owns attempt records.

Responsibilities:

- Record played note, selected note, correctness, response time, timbre, level, and board outcome.
- Feed aggregate stats back into adaptive scheduling.
- Keep the persistence API small so it can be backed by SQLite now and another Flutter storage layer later.

### `AudioService`
Owns tone playback.

Responsibilities:

- Play the current prompt tone.
- Replay the tone.
- Later support timbre and octave variation.
- Avoid background music during training mode.

## Flutter Translation Targets
The later Flutter app should map cleanly to these concepts.

| Concept | Flutter target |
| --- | --- |
| Game screen | `GamePage` |
| State machine/controller | `GameController` or `GameCubit` |
| Board renderer | `CustomPainter` or grid widget |
| Tetromino selector | Stateless widget using `PieceCatalog` data |
| Audio service | Platform audio plugin wrapper |
| Persistence | SQLite or local database wrapper |
| Progress data | Repository plus pure stats service |

The Flutter UI should treat the game state as immutable snapshots. Rendering should be a function of state, and input handlers should call controller methods instead of mutating board widgets directly.

## Suggested File Structure For Future Flutter App
```text
lib/
  main.dart
  app/
    app.dart
    routes.dart
  game/
    domain/
      board_engine.dart
      game_state.dart
      piece_catalog.dart
      prompt_engine.dart
      scoring_service.dart
      tetromino.dart
    application/
      game_controller.dart
      game_effects.dart
      game_timer.dart
    presentation/
      game_page.dart
      board_view.dart
      piece_selector.dart
      hud_view.dart
      feedback_panel.dart
      touch_controls.dart
  training/
    domain/
      note.dart
      note_stats.dart
      adaptation_service.dart
    data/
      attempt_repository.dart
      local_database.dart
  audio/
    audio_service.dart
    tone_player.dart
  settings/
    settings_page.dart
    settings_repository.dart
  progress/
    progress_page.dart
    progress_service.dart
```

Keep `main.dart` thin. Wiring should live in `app/`, not in the entrypoint.

## MVP Build Order
### Phase 1: Static Mobile Mock
Build a phone-shaped single-screen mock without live game rules.

Deliverables:

- Portrait game screen.
- HUD.
- 10 x 20 board.
- Highlighted target space.
- 7 note-piece selector buttons.
- Replay button.
- Placeholder feedback panel.

Purpose:

- Validate the mobile proportions.
- Confirm the board and controls fit on small screens.
- Prepare for Flutter layout translation.

### Phase 2: Piece Mapping
Implement the note-piece catalog.

Deliverables:

- 7 natural note mappings.
- 5 accidental lighter-color variants.
- Tetromino shape definitions.
- Unit tests for mapping and labels.

Purpose:

- Lock down the visual language before building game logic.

### Phase 3: Board Engine
Implement board behavior without audio.

Deliverables:

- Grid model.
- Piece spawn.
- Placement validation.
- Correct-piece fast drop.
- Incorrect-piece slow descent.
- Left/right movement.
- Line clear detection.
- Game-over detection.

Purpose:

- Prove that the Tetris-like system works independently from pitch training.

### Phase 4: Audio Prompt Loop
Connect tone prompts to piece choices.

Deliverables:

- Play tone at round start.
- Replay tone.
- Select note-piece answer.
- Correct vs incorrect result.
- Response-time measurement.

Purpose:

- Establish the main pitch-training loop.

### Phase 5: Scoring And Feedback
Add reward and learning feedback.

Deliverables:

- Base score.
- Speed bonus.
- Streak bonus.
- Line-clear bonus.
- Brief correction text.
- End-of-session summary.

Purpose:

- Make the loop feel complete enough for repeated play.

### Phase 6: Persistence And Adaptation
Record attempts and adapt future prompts.

Deliverables:

- Local attempt storage.
- Accuracy by note.
- Confusion pairs.
- Weak-note weighting.
- Practice and arcade mode settings.

Purpose:

- Make the game useful as a training tool, not only a puzzle.

### Phase 7: Flutter Port
Translate the working model into Flutter.

Deliverables:

- Flutter project scaffold.
- Domain models ported first.
- Board renderer.
- Game controller.
- Audio wrapper.
- Persistence wrapper.
- Widget tests for core UI states.
- Integration tests for a short play session.

Purpose:

- Move the app to mobile while preserving tested behavior.

## Input Design
### Selection Input
The 7 note-piece selectors should be visible during `awaitingAnswer`.

Each selector should show:

- Tetromino silhouette.
- Note label.
- Color family.
- Lighter accent marker if accidentals are enabled.

The selector should not show long instructional text during play.

### Falling Piece Input
When the player selects incorrectly, replace the selector area with movement controls:

- Left.
- Rotate, if enabled.
- Right.
- Optional soft drop in later levels.

This prevents the bottom area from becoming crowded.

## Animation Plan
Use simple animations first.

- Correct answer: quick drop into the target space.
- Incorrect answer: timed descent by grid row.
- Line clear: short row flash, then collapse.
- Feedback: small text change, no modal during active play.

The first implementation should prefer deterministic grid-step animation over physics.

## Data Model
Suggested attempt record:

```text
GameAttempt
  id
  session_id
  created_at
  played_note
  note_family
  accidental
  octave
  timbre
  selected_note
  selected_piece
  correct
  response_ms
  level
  score_delta
  line_clears
  board_result
```

Suggested session record:

```text
GameSession
  id
  started_at
  ended_at
  mode
  level_reached
  score
  attempts
  correct_attempts
  lines_cleared
```

## Testing Plan
Prioritize pure logic tests before UI tests.

Unit tests:

- Note-to-piece mapping.
- Accidental color variant lookup.
- Board placement validation.
- Line clear logic.
- Correct vs incorrect answer handling.
- Scoring rules.
- Weak-note prompt weighting.

Widget/UI tests for Flutter:

- `awaitingAnswer` shows board and selectors.
- `incorrectFalling` shows movement controls.
- Replay button calls audio service.
- Feedback text appears after a landed incorrect block.
- Small phone width still fits board and controls.

Manual tests:

- Play on a small phone-sized viewport.
- Verify thumb reach for selectors.
- Verify no overlap with safe areas.
- Verify audio replay latency feels acceptable.
- Verify rapid taps do not double-submit answers.

## MVP Acceptance Criteria
The mobile MVP is ready when:

- A full round can be played on a portrait phone screen.
- The player can hear a tone and choose one of 7 note-piece buttons.
- Correct choices drop the correct piece into the highlighted target.
- Incorrect choices create a slow falling piece that can be moved left or right.
- The app records correctness and response time.
- The board, selector, replay control, and feedback all fit without overlap on a 320-point-wide screen.

## Implementation Notes
- Keep the board renderer separate from board rules.
- Keep audio playback behind a service interface.
- Keep persistence behind a repository interface.
- Keep the state machine explicit and testable.
- Do not put game rules inside UI widgets.
- Treat the mobile screen mock as the source for Flutter layout proportions.
