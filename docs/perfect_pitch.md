# Perfect Pitch Design

## Purpose
This document outlines a music-training app to help a person rebuild lost perfect pitch (absolute pitch) through structured, daily ear training.

## Core Principle
Recovery should be gradual, measurable, and low-friction: short sessions, immediate feedback, and visible progress.

## Product Vision
An app that retrains note recognition by reconnecting sound, label, and memory cues:
- hear a note
- identify it quickly
- verify accuracy
- reinforce weak notes with adaptive repetition

## Target User
- Adults who previously had strong pitch identification and want to regain it.
- Musicians/singers with ear fatigue or lapse after years without deliberate training.
- Learners who can commit to 10-20 minutes per day.

## Key User Outcomes
- Faster, more accurate note naming without reference tones.
- Improved octave discrimination and timbre-invariant recognition.
- Retained accuracy over time (not just short-term quiz performance).

## Core App Experience

### 1. Daily Training Session
- Quick start from home screen ("Start 10-min session").
- Exercise mix:
  - Single-note identification
  - Octave-separated same-note recognition
  - Timbre variation (piano, sine, voice-like, strings)
  - Context drills (note inside a short melodic fragment)
- Immediate right/wrong feedback with replay.

### 2. Adaptive Weak-Note Loop
- Track confusion matrix (for example, C# often confused with D).
- Increase frequency of weak-note drills automatically.
- Reduce repetition when a note is stable across several sessions.

### 3. Progress and Retention
- Accuracy by note (A, A#, B...).
- Response-time trend per note.
- Weekly retention tests with no warm-up tones.
- Streak + consistency indicators.

## Suggested App Structure (Screens)
1. **Home**
   - Start session button
   - Today's goal
   - Last session summary
2. **Training**
   - Play note
   - Note input grid (12 semitones)
   - Confidence toggle ("guess" vs "certain")
   - Instant feedback
3. **Review**
   - Mistakes from current session
   - Replay + compare nearby notes
4. **Progress**
   - Accuracy heatmap by note
   - Confusion pairs
   - Response-time graph
5. **Settings**
   - A4 reference (440/442/etc.)
   - Instrument/timbre set
   - Session duration
   - Accessibility/audio options

## Training Design Suggestions
- Start with one octave and a small note set; expand as accuracy rises.
- Use spaced repetition windows (same day, next day, 3 days, 7 days).
- Interleave easy and hard items to avoid frustration.
- Prevent "relative-pitch cheating" by randomizing intervals and adding silence gaps.
- Include occasional environmental/context noise mode for robustness.

## Feedback Design Suggestions
- Keep feedback brief and specific:
  - "Correct: F#4"
  - "You chose G4 (common confusion with F#)"
- Show one learning tip after repeated confusion.
- Avoid long explanations during active drills.

## Data to Store
- Attempt-level records:
  - timestamp
  - played note + octave
  - user answer
  - correctness
  - response time
  - timbre/instrument
- Aggregates:
  - per-note accuracy
  - confusion matrix
  - moving average by day/week

## MVP Scope
- Single-note drills across 12 semitones in one octave.
- Basic adaptive repetition based on recent errors.
- Progress dashboard with per-note accuracy and streak.
- Local data storage and offline mode.

## Included Notes (MVP)
The MVP note set includes all 12 chromatic notes:

- C
- C# / Db
- D
- D# / Eb
- E
- F
- F# / Gb
- G
- G# / Ab
- A
- A# / Bb
- B

## Future Enhancements
- Voice input mode for singers (sing-the-note detection).
- Personalized calibration phase to detect bias patterns.
- Multi-instrument packs and genre-specific tone sets.
- Coach mode with guided weekly plans.

## Risks and Guardrails
- Avoid overconfidence from short-term gains: include delayed retention tests.
- Avoid ear fatigue: cap intense drills and insert short breaks.
- Avoid dependence on one timbre: rotate sounds by default.

## Success Metrics
- 30-day increase in blind note accuracy.
- Reduction in median response time at stable accuracy.
- Retention test performance after 7 days without practice.
- Weekly active training days per user.
