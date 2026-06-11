from dataclasses import dataclass

from domain.game_constants import CHROMATIC_NOTES, NOTE_TO_TETROMINO

BOARD_WIDTH = 12
BOARD_HEIGHT = 20
ROTATION_SYSTEM = "SRS"
SPAWN_ROW = -2
NOTE_TO_VALUE: dict[str, int] = {note: index + 1 for index, note in enumerate(CHROMATIC_NOTES)}
VALUE_TO_NOTE: dict[int, str] = {value: note for note, value in NOTE_TO_VALUE.items()}
PIECE_KIND_TO_VALUE: dict[str, int] = {
    "I": 101,
    "O": 102,
    "T": 103,
    "S": 104,
    "Z": 105,
    "J": 106,
    "L": 107,
}
VALUE_TO_PIECE_KIND: dict[int, str] = {value: kind for kind, value in PIECE_KIND_TO_VALUE.items()}
VALUE_TO_PIECE_KIND.update({value: NOTE_TO_TETROMINO[note] for value, note in VALUE_TO_NOTE.items()})

Cell = tuple[int, int]
Board = list[list[int]]

TETROMINO_SHAPES: dict[str, tuple[Cell, ...]] = {
    "I": ((0, 1), (1, 1), (2, 1), (3, 1)),
    "O": ((1, 0), (2, 0), (1, 1), (2, 1)),
    "T": ((1, 0), (0, 1), (1, 1), (2, 1)),
    "S": ((1, 0), (2, 0), (0, 1), (1, 1)),
    "Z": ((0, 0), (1, 0), (1, 1), (2, 1)),
    "J": ((0, 0), (0, 1), (1, 1), (2, 1)),
    "L": ((2, 0), (0, 1), (1, 1), (2, 1)),
}


@dataclass(frozen=True)
class FallingPiece:
    kind: str
    rotation: int
    x: int
    y: int


@dataclass(frozen=True)
class AutoPlacementPlan:
    piece: FallingPiece
    lines_cleared: int
    aggregate_height_increase: int
    enclosed_holes: int
    row_fill_score: int


def create_empty_board() -> Board:
    return [[0 for _ in range(BOARD_WIDTH)] for _ in range(BOARD_HEIGHT)]


def default_spawn_x(kind: str) -> int:
    if kind == "I":
        return 3
    if kind == "O":
        return 4
    return 3


def default_spawn(kind: str) -> FallingPiece:
    return FallingPiece(kind=kind, rotation=0, x=default_spawn_x(kind), y=SPAWN_ROW)


def piece_cells(piece: FallingPiece) -> list[Cell]:
    cells = list(TETROMINO_SHAPES[piece.kind])
    steps = piece.rotation % 4
    for _ in range(steps):
        cells = [_rotate_clockwise(cell) for cell in cells]
    return [(piece.x + dx, piece.y + dy) for dx, dy in cells]


def move(piece: FallingPiece, dx: int, dy: int) -> FallingPiece:
    return FallingPiece(kind=piece.kind, rotation=piece.rotation, x=piece.x + dx, y=piece.y + dy)


def rotate(piece: FallingPiece, clockwise: bool = True) -> FallingPiece:
    delta = 1 if clockwise else -1
    return FallingPiece(kind=piece.kind, rotation=(piece.rotation + delta) % 4, x=piece.x, y=piece.y)


def collides(board: Board, piece: FallingPiece) -> bool:
    for x, y in piece_cells(piece):
        if x < 0 or x >= BOARD_WIDTH or y >= BOARD_HEIGHT:
            return True
        if y >= 0 and board[y][x]:
            return True
    return False


def can_spawn(board: Board, kind: str) -> bool:
    return not collides(board, default_spawn(kind))


def can_spawn_any(board: Board, kinds: list[str] | tuple[str, ...]) -> bool:
    return any(can_spawn(board, kind) for kind in kinds)


def is_game_over(board: Board, next_piece_kind: str) -> bool:
    spawn_piece = default_spawn(next_piece_kind)
    if collides(board, spawn_piece):
        return True
    return collides(board, move(spawn_piece, dx=0, dy=1))


def lock_piece(board: Board, piece: FallingPiece, cell_value: int | None = None) -> Board:
    result = [row[:] for row in board]
    value = cell_value if cell_value is not None else PIECE_KIND_TO_VALUE.get(piece.kind, 101)
    for x, y in piece_cells(piece):
        if y < 0:
            continue
        result[y][x] = value
    return result


def clear_full_lines(board: Board) -> tuple[Board, int]:
    kept = [row for row in board if not all(row)]
    cleared = BOARD_HEIGHT - len(kept)
    new_rows = [[0 for _ in range(BOARD_WIDTH)] for _ in range(cleared)]
    return new_rows + kept, cleared


def drop_until_collision(board: Board, piece: FallingPiece) -> FallingPiece:
    current = piece
    while True:
        next_piece = move(current, dx=0, dy=1)
        if collides(board, next_piece):
            return current
        current = next_piece


def plan_best_auto_placement(board: Board, kind: str) -> AutoPlacementPlan | None:
    base_height = aggregate_column_heights(board)
    candidates: list[AutoPlacementPlan] = []
    for rotation in range(4):
        for x in range(-2, BOARD_WIDTH + 2):
            spawn_piece = FallingPiece(kind=kind, rotation=rotation, x=x, y=SPAWN_ROW)
            if collides(board, spawn_piece):
                continue
            resting_piece = drop_until_collision(board, spawn_piece)
            if any(cell_y < 0 for _, cell_y in piece_cells(resting_piece)):
                continue
            with_piece = lock_piece(board, resting_piece)
            row_fill = row_fill_score(board, resting_piece)
            cleared_board, lines_cleared = clear_full_lines(with_piece)
            height_delta = aggregate_column_heights(cleared_board) - base_height
            holes = enclosed_holes(cleared_board)
            candidates.append(
                AutoPlacementPlan(
                    piece=resting_piece,
                    lines_cleared=lines_cleared,
                    aggregate_height_increase=height_delta,
                    enclosed_holes=holes,
                    row_fill_score=row_fill,
                )
            )
    if not candidates:
        return None
    return min(
        candidates,
        key=lambda item: (
            0 if item.lines_cleared > 0 else 1,
            -item.lines_cleared,
            -item.row_fill_score,
            item.enclosed_holes,
            item.aggregate_height_increase,
            item.piece.y,
            item.piece.x,
            item.piece.rotation,
        ),
    )


def apply_auto_placement(board: Board, plan: AutoPlacementPlan, cell_value: int | None = None) -> tuple[Board, int]:
    with_piece = lock_piece(board, plan.piece, cell_value=cell_value)
    return clear_full_lines(with_piece)


def row_fill_score(board: Board, piece: FallingPiece) -> int:
    with_piece = lock_piece(board, piece)
    return sum(sum(1 for cell in row if cell) ** 2 for row in with_piece)


def aggregate_column_heights(board: Board) -> int:
    total = 0
    for x in range(BOARD_WIDTH):
        total += _column_height(board, x)
    return total


def enclosed_holes(board: Board) -> int:
    holes = 0
    for x in range(BOARD_WIDTH):
        seen_block = False
        for y in range(BOARD_HEIGHT):
            cell = board[y][x]
            if cell:
                seen_block = True
            elif seen_block:
                holes += 1
    return holes


def _rotate_clockwise(cell: Cell) -> Cell:
    dx, dy = cell
    return dy, 3 - dx


def _column_height(board: Board, x: int) -> int:
    for y in range(BOARD_HEIGHT):
        if board[y][x]:
            return BOARD_HEIGHT - y
    return 0
