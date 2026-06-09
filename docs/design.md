# Perfect Pitch Tetris Design

## Purpose
This document describes a game mode that combines perfect-pitch note identification with Tetris-inspired falling block play.

The goal is to make note recognition fast, visual, and repeatable: the player hears a tone, identifies the note family, and places the matching tetromino into the board.

## Core Concept
Each round starts with a tone. The player must choose the tetromino shape and color that matches the played note.

- If the player chooses correctly, the selected block drops directly into the highlighted space.
- If the player chooses incorrectly, the block enters the board slowly and the player can still move it left or right before it lands.
- Correct answers reward pitch recognition.
- Incorrect answers become recoverable placement challenges instead of ending the flow immediately.

This keeps the app useful as ear training while still feeling like an active puzzle game.

## Note and Tetromino Mapping
The perfect-pitch design includes the 12 chromatic notes, while Tetris has 7 tetromino shapes. This game mode treats the 7 natural notes as the primary shape families and maps sharps/flats to lighter versions of the same family color.

For single-answer gameplay, each accidental pitch belongs to the lower natural note family and displays both enharmonic labels.

| Note target | Tetromino | Shape description | Base color | Accidental color |
| --- | --- | --- | --- | --- |
| C | I | Straight line | Cyan | C# / Db = Light cyan |
| D | O | Square | Yellow | D# / Eb = Light yellow |
| E | T | T-shape | Purple | None in the 12-note set |
| F | S | Right-leaning zigzag | Green | F# / Gb = Light green |
| G | Z | Left-leaning zigzag | Red | G# / Ab = Light red |
| A | J | Left L-shape | Blue | A# / Bb = Light blue |
| B | L | Right L-shape | Orange | None in the 12-note set |

### Rationale
- The player only needs to learn 7 shape families.
- Accidentals remain visually related to nearby natural notes.
- The mapping uses standard tetromino colors from `tetris.md`.
- The design can support both a 7-note natural-note mode and a 12-note chromatic mode.

## Game Screen
The main game screen should contain:

- A Tetris-style board with a highlighted target space.
- A currently played note control with replay.
- A compact note-piece selector showing the 7 tetromino families.
- A score, streak, level, and remaining lives/mistakes display.
- A next-tone preview only after the current block lands, not before.

The game should avoid a quiz-like grid as the primary interface. The main interaction is choosing a piece that visually represents the heard tone.

## Core Round Flow
1. The app plays a tone.
2. The board highlights the space that needs to be filled.
3. The player selects the matching tetromino shape/color.
4. The app evaluates the selected piece against the played note.
5. Correct selection:
   - The block snaps above the target column.
   - The block drops quickly into the highlighted space.
   - The player receives pitch feedback and score.
6. Incorrect selection:
   - The chosen block appears at the top of the board.
   - The block descends slowly.
   - The player can move it left or right, rotate if allowed, and attempt a useful placement.
   - The app shows the correct note after the block lands.
7. Completed rows clear and award bonus points.
8. The next tone plays.

## Player Input
Primary inputs:

- Click/tap a tetromino from the selector.
- Use keyboard shortcuts for faster play:
  - `C D E F G A B` for note families.
  - Arrow keys for moving a falling incorrect block.
  - Up arrow or space for rotate, if rotation is enabled.
  - `R` to replay the tone.

For mobile, the selector should be reachable with one thumb and use large touch targets.

## Correct Answer Behavior
A correct answer should feel immediate and satisfying.

- The block uses the exact shape/color mapped to the target note.
- The block animates into the highlighted space.
- Feedback is brief:
  - `Correct: F`
  - `Correct: F# / Gb`
- Score increases based on speed and current streak.
- The app records response time and accuracy for the note.

## Incorrect Answer Behavior
An incorrect answer should preserve the game flow without hiding the learning moment.

- The selected block becomes playable and starts descending at a slower speed than normal.
- The player can move it left or right to reduce board damage.
- The app does not immediately replace the selected block with the correct one.
- Once the incorrect block lands, the app shows:
  - played note
  - selected note family
  - correct tetromino
  - replay button for the original tone

This makes mistakes meaningful in both systems: the player loses pitch accuracy and must handle a harder board state.

## Board Design
Recommended MVP board:

- 10 columns by 20 rows.
- Target spaces appear as ghost outlines inside the board.
- Early levels should create simple gaps that clearly fit one piece.
- Later levels can require orientation awareness and faster selection.

The board should support a training-first mode where the target space always has a valid correct piece placement. It should not generate impossible placements.

## Difficulty Progression
Difficulty should increase through both music and puzzle complexity.

### Level 1: Natural Notes
- Notes: C, D, E, F, G, A, B.
- One octave.
- Piano or sine timbre.
- Generous response time.
- No rotation required.

### Level 2: Accidentals
- Adds C# / Db, D# / Eb, F# / Gb, G# / Ab, A# / Bb.
- Accidentals use lighter family colors.
- Player must distinguish natural vs accidental by color shade.

### Level 3: Timbre Variation
- Randomizes instrument/timbre.
- Includes piano, sine, strings, and voice-like tones.
- Keeps one octave.

### Level 4: Octave Variation
- Adds octave changes while preserving note identity.
- Scoring rewards correct note class, not octave, unless octave mode is enabled.

### Level 5: Faster Board Pressure
- Shorter answer window.
- Faster incorrect-block descent.
- More complex target spaces.
- Optional rotation requirement.

## Scoring
Scoring should reward pitch skill first and puzzle survival second.

- Correct note: base points.
- Fast correct note: time bonus.
- Consecutive correct notes: streak multiplier.
- Line clear: board bonus.
- Incorrect note: no pitch points, but placement can still prevent board loss.
- Repeated confusion on the same note pair: lower score and increased review frequency.

Suggested MVP scoring:

| Event | Points |
| --- | --- |
| Correct note | 100 |
| Correct within 2 seconds | +50 |
| Streak of 5 | +100 |
| Single line clear | +100 |
| Multi-line clear | +250 |
| Incorrect note | 0 |

## Training Data
The game should reuse the perfect-pitch app's training data model where possible.

Record each attempt:

- timestamp
- played note
- note family
- accidental flag
- octave
- timbre
- selected piece/note
- correctness
- response time
- board outcome
- line clears
- current level

Aggregate:

- accuracy by note
- accuracy by natural note family
- accidental accuracy
- confusion pairs
- median response time by note
- streak history
- weak notes for adaptive scheduling

## Adaptive Behavior
The game should use errors to choose future tones.

- Notes with low accuracy appear more often.
- Common confusion pairs are placed near each other in review.
- If the player repeatedly misses accidentals, the app temporarily slows gameplay and increases color contrast.
- If accuracy is high, the app increases board speed or adds timbre/octave variation.

## Visual Design
The visual system should make note identity readable without feeling like a plain flashcard quiz.

- Use the standard tetromino colors from `tetris.md`.
- Use lighter variants for accidentals:
  - cyan to light cyan
  - yellow to pale yellow
  - purple to lavender
  - green to mint
  - red to coral/pink
  - blue to sky blue
  - orange to peach
- Keep the board background dark enough for blocks to stand out.
- Make the highlighted target space a subtle outline, not a filled block.
- Avoid relying only on color: show note labels or shape silhouettes for accessibility.

## Audio Design
Audio should stay consistent with the perfect-pitch training purpose.

- Play the tone at the start of each round.
- Allow one-tap replay with a small score penalty or no penalty in practice mode.
- Randomize octave only after the player is stable in one octave.
- Randomize timbre only after basic note mapping is learned.
- Avoid background music during training mode because it can interfere with pitch identification.

## Modes
### Practice Mode
- No game over.
- Slow timing.
- Unlimited replay.
- Strong feedback after every answer.
- Best for learning the mapping.

### Arcade Mode
- Standard scoring.
- Board can top out.
- Replay has a score penalty.
- Difficulty rises over time.

### Review Mode
- Focuses only on weak notes.
- Uses simpler board states.
- Shows confusion feedback after every miss.

## MVP Scope
The first playable version should include:

- One board.
- Seven natural note families.
- Five accidental variants.
- Tone playback.
- Piece selector.
- Correct-piece fast drop.
- Incorrect-piece slow descent with left/right movement.
- Basic scoring.
- Attempt logging.
- Accuracy by note.

Rotation, multi-timbre support, octave variation, and advanced board generation can come after the core loop feels good.

## Open Design Questions
- Should chromatic accidentals always use the lower natural note family, or should the app include a spelling mode where C# and Db can be trained separately?
- Should the target space always be visible before answering, or should advanced levels require identifying the piece before seeing the space?
- Should incorrect blocks allow rotation, or should rotation be reserved for later levels?
- Should replay be free in practice mode but penalized in arcade mode?

## Success Criteria
This mode is successful if it improves pitch recognition without turning the game into a distraction.

Key signals:

- Players can learn the 7 shape families quickly.
- Natural-note accuracy improves before accidentals are introduced.
- Mistakes create useful review data.
- Board pressure increases focus without overwhelming pitch listening.
- The player wants to repeat short sessions daily.
