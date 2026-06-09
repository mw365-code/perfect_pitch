import unittest

from domain.tetris_rules import (
    BOARD_HEIGHT,
    BOARD_WIDTH,
    can_spawn,
    clear_full_lines,
    collides,
    create_empty_board,
    default_spawn,
    drop_until_collision,
    is_game_over,
    lock_piece,
)


class TetrisRulesTests(unittest.TestCase):
    def test_default_spawn_does_not_collide_on_empty_board(self) -> None:
        board = create_empty_board()
        piece = default_spawn("T")
        self.assertFalse(collides(board, piece))
        self.assertTrue(can_spawn(board, "T"))

    def test_line_clear_removes_full_row(self) -> None:
        board = create_empty_board()
        board[-1] = [1] * BOARD_WIDTH
        updated, cleared = clear_full_lines(board)
        self.assertEqual(cleared, 1)
        self.assertEqual(len(updated), BOARD_HEIGHT)
        self.assertEqual(updated[0], [0] * BOARD_WIDTH)

    def test_drop_and_lock_marks_cells(self) -> None:
        board = create_empty_board()
        resting_piece = drop_until_collision(board, default_spawn("O"))
        locked = lock_piece(board, resting_piece)
        occupied = sum(cell for row in locked for cell in row)
        self.assertEqual(occupied, 4)

    def test_game_over_when_spawn_area_is_blocked(self) -> None:
        board = create_empty_board()
        for x in range(BOARD_WIDTH):
            board[0][x] = 1
            board[1][x] = 1
        self.assertTrue(is_game_over(board, "I"))


if __name__ == "__main__":
    unittest.main()
