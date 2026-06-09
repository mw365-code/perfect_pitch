from dataclasses import dataclass

BOARD_WIDTH = 10
BOARD_HEIGHT = 20
ROTATION_SYSTEM = "SRS"
SPAWN_ROW = -2

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


def is_game_over(board: Board, next_piece_kind: str) -> bool:
    spawn_piece = default_spawn(next_piece_kind)
    if collides(board, spawn_piece):
        return True
    return collides(board, move(spawn_piece, dx=0, dy=1))


def lock_piece(board: Board, piece: FallingPiece) -> Board:
    result = [row[:] for row in board]
    for x, y in piece_cells(piece):
        if y < 0:
            continue
        result[y][x] = 1
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


def _rotate_clockwise(cell: Cell) -> Cell:
    dx, dy = cell
    return dy, 3 - dx
