# CURRENT_STATE

## Code prompt

### Architecture & Separation of Concerns
- Establish an architecture that sets explicit boundaries between UI, domain, and infrastructure layers. This should be reflected in the directory structure.
- Avoid dumping new files in the project root; just keep main.py there.
- `main.py` or `main.dart` must not contain any wiring, domain logic, or infrastructure.
- Keep UI wiring, domain logic, and infrastructure separated. Domain must not import infra or UI.
- Prefer thin orchestrators and small, focused services. Use explicit service helpers for UI side effects.
- Avoid direct dialog/widget mutations across layers; use adapters/services (for example, `CategoryManagerUIService`, `AddEditStateService`).
- Keep init/builders as composition roots; do not leak logic into UI builders.
- Prefer explicit dependencies via small dataclasses/services rather than hidden attribute reach-through.

### Readability & Maintainability
- Use clear, short functions with a single responsibility. Extract helpers when logic grows.
- Avoid `getattr`/duck typing in production flow unless truly necessary; prefer adapters/registries.
- Write defensive UI code (best-effort; never crash), but keep error handling narrow and intentional.
- Keep naming consistent with existing patterns: `*Service`, `*Controller`, `*Coordinator`, `*Effects`, `*Rules`.
- Always add explicit error types in try/catch.
- Avoid code duplication.
- Avoid overly clever abstractions.

### File Size Constraint
- Keep each file under 300 lines. If a file approaches 300, split it into focused modules.
- Make a script to do this at regular intervals, adjusted for the local project.

### Testing & Refactors
- Always consider adding new tests, even small ones, and always make appropriate suggestions.
- Add small pure tests for new services/helpers when behavior might regress.
- Preserve behavior; refactors should be test-driven and avoid hidden side effects.
- Add Flutter integration tests to test the UI, especially for iOS.
- Consider using Patrol for Android UI tests.
- Remind me to run tests when appropriate.
- Remind me to run manual tests when appropriate.
- Avoid leaving brittle wrappers behind when refactoring code.
- Always start major refactoring in a new branch.

### Coding Style
- Prefer explicit imports. Avoid large inline logic inside UI event handlers.
- Keep log noise low; log failures only in hot paths.

### Output
- Make changes in one pass; keep diffs minimal and focused.
- Maintain a `CURRENT_STATE.md` file that contains this prompt at the top of the file, then the state of the code base architecture, then a report of running any tests.

### Debugging
- Add a debugging code system that allows all debug code to be turned off.
- When debug code is added, make sure it complies with this prerequisite.

### Git
- Remind me to commit and push when appropriate.
- Before doing large-scale refactoring, remind me to change to a refactoring branch.

## If a database is required

### Database requirements
- Use the built-in `sqlite3` library unless there is a strong reason otherwise.
- Organize the code clearly, with separation between:
  1. database connection/setup
  2. schema creation
  3. CRUD operations
  4. utility/helper functions
- Include clear comments throughout.
- Use parameterized queries everywhere to prevent SQL injection.
- Use context managers or another safe pattern to ensure connections and transactions are handled correctly.
- Include proper error handling for database operations.
- Design the code so it can be reused in a larger application.

### Database expectations
- Create the database file if it does not already exist.
- Define a schema using `CREATE TABLE IF NOT EXISTS`.
- Include a primary key for each table.
- Add appropriate foreign keys, unique constraints, default values, and indexes where sensible.
- Enable foreign key enforcement.
- Include a function to initialize the database schema.

### Database coding expectations
- Use classes or well-structured functions, whichever is more appropriate for clarity and maintainability.
- Include type hints where reasonable.
- Avoid overly clever abstractions; prefer readable, practical code.
- Make the design easy to extend with additional tables later.
- Return query results in a convenient format, such as tuples, dictionaries, or lightweight objects, and be consistent.

### Database functionality to include
- Connect to the SQLite database.
- Initialize schema.
- Insert records.
- Fetch one record.
- Fetch multiple records.
- Update records.
- Delete records.
- Optionally search/filter records.
- Optionally support soft delete if appropriate.

### Database testing/demo expectations
- Include a short example showing how to initialize the database and perform basic CRUD operations.
- Include sample table definitions and example usage data.

### Database output expectations
- After the code, briefly explain the structure and design decisions.
- Do not omit important implementation details.

## Architecture state (2026-05-26)

- `main.py` is now a thin entrypoint only.
- Composition root and wiring are in `app/bootstrap.py`.
- Domain logic is in `domain/`:
  - note model dataclasses
  - note/frequency engine
  - adaptation service
  - progress service
  - session service
  - ports/protocols
- Infrastructure is in `infra/`:
  - sqlite connection/schema/repository
  - audio tone generator/player
  - app config
- UI is split:
  - `ui/cli_app.py` for CLI MVP
  - `ui/tk_app.py` for Tkinter GUI
- Support:
  - `scripts/check_file_sizes.sh`
  - `tests/` with pure unit tests

## Test report (2026-05-26)

- File-size check: `./scripts/check_file_sizes.sh .` -> pass
- Unit tests: `python3 -m unittest discover -s tests -p 'test_*.py' -v` -> 6 passed
- Syntax check: `python3 -m compileall -q .` -> pass

#### Ideas
- Purfect Pitch
- Pawfect Pitch