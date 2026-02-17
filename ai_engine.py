import math
import random
import time

MATE_SCORE = 100000

PIECE_VALUES = {
    "K": 0,
    "Q": 900,
    "R": 500,
    "B": 330,
    "N": 320,
    "P": 100,
}

PAWN_TABLE = [
    [0, 0, 0, 0, 0, 0, 0, 0],
    [50, 50, 50, 50, 50, 50, 50, 50],
    [10, 10, 20, 30, 30, 20, 10, 10],
    [5, 5, 10, 25, 25, 10, 5, 5],
    [0, 0, 0, 20, 20, 0, 0, 0],
    [5, -5, -10, 0, 0, -10, -5, 5],
    [5, 10, 10, -20, -20, 10, 10, 5],
    [0, 0, 0, 0, 0, 0, 0, 0],
]

KNIGHT_TABLE = [
    [-50, -40, -30, -30, -30, -30, -40, -50],
    [-40, -20, 0, 0, 0, 0, -20, -40],
    [-30, 0, 10, 15, 15, 10, 0, -30],
    [-30, 5, 15, 20, 20, 15, 5, -30],
    [-30, 0, 15, 20, 20, 15, 0, -30],
    [-30, 5, 10, 15, 15, 10, 5, -30],
    [-40, -20, 0, 5, 5, 0, -20, -40],
    [-50, -40, -30, -30, -30, -30, -40, -50],
]

BISHOP_TABLE = [
    [-20, -10, -10, -10, -10, -10, -10, -20],
    [-10, 0, 0, 0, 0, 0, 0, -10],
    [-10, 0, 5, 10, 10, 5, 0, -10],
    [-10, 5, 5, 10, 10, 5, 5, -10],
    [-10, 0, 10, 10, 10, 10, 0, -10],
    [-10, 10, 10, 10, 10, 10, 10, -10],
    [-10, 5, 0, 0, 0, 0, 5, -10],
    [-20, -10, -10, -10, -10, -10, -10, -20],
]

ROOK_TABLE = [
    [0, 0, 0, 5, 5, 0, 0, 0],
    [-5, 0, 0, 0, 0, 0, 0, -5],
    [-5, 0, 0, 0, 0, 0, 0, -5],
    [-5, 0, 0, 0, 0, 0, 0, -5],
    [-5, 0, 0, 0, 0, 0, 0, -5],
    [-5, 0, 0, 0, 0, 0, 0, -5],
    [5, 10, 10, 10, 10, 10, 10, 5],
    [0, 0, 0, 0, 0, 0, 0, 0],
]

QUEEN_TABLE = [
    [-20, -10, -10, -5, -5, -10, -10, -20],
    [-10, 0, 0, 0, 0, 0, 0, -10],
    [-10, 0, 5, 5, 5, 5, 0, -10],
    [-5, 0, 5, 5, 5, 5, 0, -5],
    [0, 0, 5, 5, 5, 5, 0, -5],
    [-10, 5, 5, 5, 5, 5, 0, -10],
    [-10, 0, 5, 0, 0, 0, 0, -10],
    [-20, -10, -10, -5, -5, -10, -10, -20],
]

KING_TABLE = [
    [-30, -40, -40, -50, -50, -40, -40, -30],
    [-30, -40, -40, -50, -50, -40, -40, -30],
    [-30, -40, -40, -50, -50, -40, -40, -30],
    [-30, -40, -40, -50, -50, -40, -40, -30],
    [-20, -30, -30, -40, -40, -30, -30, -20],
    [-10, -20, -20, -20, -20, -20, -20, -10],
    [20, 20, 0, 0, 0, 0, 20, 20],
    [20, 30, 10, 0, 0, 10, 30, 20],
]

PIECE_SQUARE_TABLES = {
    "P": PAWN_TABLE,
    "N": KNIGHT_TABLE,
    "B": BISHOP_TABLE,
    "R": ROOK_TABLE,
    "Q": QUEEN_TABLE,
    "K": KING_TABLE,
    "p": PAWN_TABLE[::-1],
    "n": KNIGHT_TABLE[::-1],
    "b": BISHOP_TABLE[::-1],
    "r": ROOK_TABLE[::-1],
    "q": QUEEN_TABLE[::-1],
    "k": KING_TABLE[::-1],
}


class SearchTimeout(Exception):
    pass


def _count_legal_moves(gs, white_to_move):
    current_turn = gs.whiteToMove
    current_checkmate = gs.checkmate
    current_stalemate = gs.stalemate
    cached_moves = gs._valid_moves_cache
    cached_key = gs._valid_moves_cache_key
    gs.whiteToMove = white_to_move
    moves = len(gs.get_valid_moves())
    gs.whiteToMove = current_turn
    gs.checkmate = current_checkmate
    gs.stalemate = current_stalemate
    gs._valid_moves_cache = cached_moves
    gs._valid_moves_cache_key = cached_key
    return moves


def evaluate_board(gs):
    status = gs.get_game_status()
    if status == "checkmate":
        return -MATE_SCORE if gs.whiteToMove else MATE_SCORE
    if status == "stalemate":
        return 0

    value = 0
    for r in range(8):
        for c in range(8):
            piece = gs.board[r][c]
            if piece == "--":
                continue
            color = piece[0].lower()
            symbol = piece[1].upper()
            sign = 1 if color == "w" else -1

            value += sign * PIECE_VALUES.get(symbol, 0)

            table_key = symbol if color == "w" else symbol.lower()
            table = PIECE_SQUARE_TABLES.get(table_key)
            if table is not None:
                value += sign * table[r][c]

    white_moves = _count_legal_moves(gs, True)
    black_moves = _count_legal_moves(gs, False)
    value += (white_moves - black_moves) * 3
    return value


def _is_promotion_move(move):
    return move.pieceMoved[1].lower() == "p" and move.endRow in (0, 7)


def order_moves(moves):
    def move_score(move):
        score = 0
        if move.pieceCaptured != "--":
            victim = move.pieceCaptured[1].upper()
            attacker = move.pieceMoved[1].upper()
            score += 10 * PIECE_VALUES.get(victim, 0) - PIECE_VALUES.get(attacker, 0)
        if _is_promotion_move(move):
            score += 800
        if move.isCastleMove:
            score += 50
        if (move.endRow, move.endCol) in ((3, 3), (3, 4), (4, 3), (4, 4)):
            score += 10
        return score

    return sorted(moves, key=move_score, reverse=True)


def minimax(gs, depth, alpha, beta, maximizing_player, start_time, time_limit):
    if (time.time() - start_time) > time_limit:
        raise SearchTimeout()

    if depth == 0:
        return evaluate_board(gs), None

    valid_moves = gs.get_valid_moves()
    if not valid_moves:
        return evaluate_board(gs), None

    valid_moves = order_moves(valid_moves)
    best_move = valid_moves[0]

    if maximizing_player:
        max_eval = -math.inf
        for move in valid_moves:
            gs.makeMove(move)
            try:
                eval_score, _ = minimax(gs, depth - 1, alpha, beta, False, start_time, time_limit)
            finally:
                # Always unwind state, even if a timeout bubbles up from deeper recursion.
                gs.undoMove()
            if eval_score > max_eval:
                max_eval = eval_score
                best_move = move
            alpha = max(alpha, max_eval)
            if beta <= alpha:
                break
        return max_eval, best_move

    min_eval = math.inf
    for move in valid_moves:
        gs.makeMove(move)
        try:
            eval_score, _ = minimax(gs, depth - 1, alpha, beta, True, start_time, time_limit)
        finally:
            # Always unwind state, even if a timeout bubbles up from deeper recursion.
            gs.undoMove()
        if eval_score < min_eval:
            min_eval = eval_score
            best_move = move
        beta = min(beta, min_eval)
        if beta <= alpha:
            break
    return min_eval, best_move


def find_best_move(gs, level="intermediate"):
    lvl = (level or "intermediate").lower()
    if lvl == "beginner":
        max_depth, time_limit = 2, 1.5
    elif lvl == "intermediate":
        max_depth, time_limit = 3, 3.0
    elif lvl == "advanced":
        max_depth, time_limit = 4, 6.0
    else:
        max_depth, time_limit = 3, 3.0

    start_time = time.time()
    maximizing = gs.whiteToMove
    best_move = None

    # Iterative deepening keeps a usable move even when the time limit is hit mid-search.
    for depth in range(1, max_depth + 1):
        try:
            _, move = minimax(gs, depth, -math.inf, math.inf, maximizing, start_time, time_limit)
            if move is not None:
                best_move = move
        except SearchTimeout:
            break

    if lvl == "beginner" and best_move is not None and random.random() < 0.25:
        candidates = gs.get_valid_moves()
        if candidates:
            return random.choice(candidates)

    if best_move is None:
        candidates = gs.get_valid_moves()
        return random.choice(candidates) if candidates else None
    return best_move
