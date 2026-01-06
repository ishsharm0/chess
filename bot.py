# bot.py
import math
from dataclasses import dataclass
from typing import Optional, List, Dict, Tuple
from gameLogic import getAllTeamMoves, isKingSafe, checkCheckmateOrStalemate

def getCurrentBoard(gameStates):
    return gameStates[-1]

# Simple material values, uppercase = bot, lowercase = player
_PVAL = {'P':1,'N':3,'B':3,'R':5,'Q':9,'K':0}

MATE_SCORE = 1_000_000.0

# --- Piece-Square Tables (coarse midgame, small centipawn-ish values) ---
_PST_P = [
     0,  0,  0,  5,  5,  0,  0,  0,
     5, 10, 10, 15, 15, 10, 10,  5,
     4,  8,  8, 12, 12,  8,  8,  4,
     3,  6,  6, 10, 10,  6,  6,  3,
     2,  4,  4,  6,  6,  4,  4,  2,
     1,  2,  2,  3,  3,  2,  2,  1,
     0,  0,  0, -1, -1,  0,  0,  0,
     0,  0,  0,  0,  0,  0,  0,  0,
]
_PST_N = [
   -5, -3, -2, -2, -2, -2, -3, -5,
   -3,  0,  1,  2,  2,  1,  0, -3,
   -2,  1,  3,  4,  4,  3,  1, -2,
   -2,  2,  4,  6,  6,  4,  2, -2,
   -2,  2,  4,  6,  6,  4,  2, -2,
   -2,  1,  3,  4,  4,  3,  1, -2,
   -3,  0,  1,  2,  2,  1,  0, -3,
   -5, -3, -2, -2, -2, -2, -3, -5,
]
_PST_B = [
   -2, -1, -1, -1, -1, -1, -1, -2,
   -1,  1,  1,  2,  2,  1,  1, -1,
   -1,  1,  2,  3,  3,  2,  1, -1,
   -1,  2,  3,  4,  4,  3,  2, -1,
   -1,  2,  3,  4,  4,  3,  2, -1,
   -1,  1,  2,  3,  3,  2,  1, -1,
   -1,  1,  1,  2,  2,  1,  1, -1,
   -2, -1, -1, -1, -1, -1, -1, -2,
]
_PST_R = [
     0,  0,  1,  2,  2,  1,  0,  0,
     0,  1,  2,  3,  3,  2,  1,  0,
     0,  1,  2,  3,  3,  2,  1,  0,
     0,  1,  2,  3,  3,  2,  1,  0,
     0,  1,  2,  3,  3,  2,  1,  0,
     0,  1,  2,  3,  3,  2,  1,  0,
     0,  1,  2,  3,  3,  2,  1,  0,
     0,  0,  1,  2,  2,  1,  0,  0,
]
_PST_Q = [
    0,  0,  0,  1,  1,  0,  0,  0,
    0,  1,  2,  2,  2,  2,  1,  0,
    0,  2,  3,  3,  3,  3,  2,  0,
    1,  2,  3,  4,  4,  3,  2,  1,
    1,  2,  3,  4,  4,  3,  2,  1,
    0,  2,  3,  3,  3,  3,  2,  0,
    0,  1,  2,  2,  2,  2,  1,  0,
    0,  0,  0,  1,  1,  0,  0,  0,
]

def _pst_score(piece: str, idx: int) -> int:
    t = piece[0].upper()
    tbl = _PST_P if t=='P' else _PST_N if t=='N' else _PST_B if t=='B' else _PST_R if t=='R' else _PST_Q if t=='Q' else None
    if tbl is None:
        return 0
    # uppercase = bot uses tbl as-is; lowercase = player mirrored vertically
    return tbl[idx] if piece.isupper() else -tbl[63 - idx]

def _material_positional(board, botWhite, gameStates) -> float:
    score = 0.0
    for i, p in enumerate(board):
        if not p:
            continue
        base = _PVAL.get(p[0].upper(), 0)
        score += base if p[0].isupper() else -base
        score += _pst_score(p, i) / 10.0
    return score

def _mobility(board, botWhite, gameStates) -> float:
    bot_sets = getAllTeamMoves('bot', board, botWhite, gameStates)
    bot_cnt = sum(1 for ms in bot_sets for m in ms if isKingSafe(m, 'bot'))
    pl_sets = getAllTeamMoves('player', board, botWhite, gameStates)
    pl_cnt = sum(1 for ms in pl_sets for m in ms if isKingSafe(m, 'player'))
    return 0.02 * (bot_cnt - pl_cnt)

def scoreMove(board, botWhite, gameStates) -> float:
    score = _material_positional(board, botWhite, gameStates)
    # light king-safety nudges
    if not isKingSafe(board, 'player'): score += 0.5
    if not isKingSafe(board, 'bot'):    score -= 0.5
    score += _mobility(board, botWhite, gameStates)
    return score

def scoreMoveForEnemy(board, botWhite, gameStates) -> float:
    # Perspective of the human (player)
    return -scoreMove(board, botWhite, gameStates)

def _opponent(turn: str) -> str:
    return "player" if turn == "bot" else "bot"

def _eval_for_side_to_move(board, turn: str, botWhite, gameStates) -> float:
    """
    Negamax-compatible evaluation:
    - positive means good for side-to-move.
    """
    s = scoreMove(board, botWhite, gameStates)  # bot-centric
    return s if turn == "bot" else -s

# --- Quiescence search (captures only) ---
def _is_side_piece(piece: Optional[str], turn: str) -> bool:
    if not piece:
        return False
    return piece[0].isupper() if turn == "bot" else piece[0].islower()

def _is_enemy_piece(piece: Optional[str], turn: str) -> bool:
    if not piece:
        return False
    return piece[0].islower() if turn == "bot" else piece[0].isupper()

def _is_capture(prev, nxt, turn: str) -> bool:
    """
    Detect whether prev->nxt is a capturing move by side `turn`.

    We infer the move from board diffs. This handles normal captures and en passant.
    Castling (4-square diff) is treated as non-capture.
    """
    diffs = [i for i in range(64) if prev[i] != nxt[i]]
    if len(diffs) < 2:
        return False
    if len(diffs) >= 4:
        return False

    # Typical move/capture/promotion: exactly 2 squares change (from, to).
    if len(diffs) == 2:
        d0, d1 = diffs
        from_idx = None
        to_idx = None

        if _is_side_piece(prev[d0], turn) and nxt[d0] is None and _is_side_piece(nxt[d1], turn):
            from_idx, to_idx = d0, d1
        elif _is_side_piece(prev[d1], turn) and nxt[d1] is None and _is_side_piece(nxt[d0], turn):
            from_idx, to_idx = d1, d0
        else:
            # Fallback for promotions or odd encodings: infer by "side piece disappeared" / "side piece appeared".
            gone = [i for i in diffs if _is_side_piece(prev[i], turn) and not _is_side_piece(nxt[i], turn)]
            came = [i for i in diffs if _is_side_piece(nxt[i], turn) and not _is_side_piece(prev[i], turn)]
            if len(gone) == 1 and len(came) == 1:
                from_idx, to_idx = gone[0], came[0]
            else:
                return False

        return _is_enemy_piece(prev[to_idx], turn)

    # En passant: 3 squares change (from pawn removed, pawn appears diagonally, captured pawn removed).
    d0, d1, d2 = diffs
    from_candidates = [i for i in diffs if _is_side_piece(prev[i], turn) and nxt[i] is None]
    to_candidates = [i for i in diffs if _is_side_piece(nxt[i], turn)]
    cap_candidates = [i for i in diffs if _is_enemy_piece(prev[i], turn) and nxt[i] is None]
    if len(from_candidates) != 1 or len(to_candidates) != 1 or len(cap_candidates) != 1:
        return False

    from_idx = from_candidates[0]
    to_idx = to_candidates[0]
    cap_idx = cap_candidates[0]
    moved_piece = nxt[to_idx]
    if not moved_piece or moved_piece[0].lower() != "p":
        return False
    # In en passant, destination square was empty in prev, captured pawn removed elsewhere.
    if prev[to_idx] is not None:
        return False
    # Pawn must move diagonally by 7/9 squares.
    if abs(to_idx - from_idx) not in (7, 9):
        return False
    return True

def quiesce(board, turn, alpha, beta, botWhite, gameStates, node_cap=64, ply: int = 0):
    terminal = checkCheckmateOrStalemate(board, turn, botWhite, gameStates)
    if terminal == "checkmate":
        # Side-to-move is mated.
        return -MATE_SCORE + ply
    if terminal == "stalemate":
        return 0.0

    stand_pat = _eval_for_side_to_move(board, turn, botWhite, gameStates)
    if stand_pat >= beta:
        return beta
    if alpha < stand_pat:
        alpha = stand_pat

    moves = getAllTeamMoves(turn, board, botWhite, gameStates)
    next_turn = _opponent(turn)
    visited = 0

    # consider only capturing moves
    for ms in moves:
        for m in ms:
            if not isKingSafe(m, turn):
                continue
            if not _is_capture(board, m, turn):
                continue
            score = -quiesce(m, next_turn, -beta, -alpha, botWhite, gameStates, node_cap, ply + 1)
            visited += 1
            if score >= beta:
                return beta
            if score > alpha:
                alpha = score
            if visited >= node_cap:
                return alpha
    return alpha

@dataclass
class _TTEntry:
    depth: int
    score: float
    flag: str  # "EXACT" | "LOWER" | "UPPER"
    best: Optional[tuple]

_TTKey = Tuple[tuple, str]
_TransTable = Dict[_TTKey, _TTEntry]

def _legal_moves_flat(turn: str, board, botWhite, gameStates) -> List[tuple]:
    all_moves = getAllTeamMoves(turn, board, botWhite, gameStates)
    return [m for ms in all_moves for m in ms if isKingSafe(m, turn)]

def _order_score(prev_board, next_board, turn: str, botWhite, gameStates) -> float:
    """
    Cheap-ish move ordering heuristic.
    Higher is better for the side `turn` (negamax viewpoint).
    """
    s = _material_positional(next_board, botWhite, gameStates)  # bot-centric
    if turn == "player":
        s = -s
    if _is_capture(prev_board, next_board, turn):
        s += 0.75
    if not isKingSafe(next_board, _opponent(turn)):
        s += 0.25
    return s

def _ordered_moves(turn: str, board, botWhite, gameStates, tt: _TransTable, depth: int) -> List[tuple]:
    moves = _legal_moves_flat(turn, board, botWhite, gameStates)
    if not moves:
        return moves

    key: _TTKey = (board, turn)
    tt_best = tt.get(key).best if key in tt else None
    if tt_best is not None and tt_best in moves:
        moves.remove(tt_best)
        moves.sort(key=lambda m: _order_score(board, m, turn, botWhite, gameStates), reverse=True)
        return [tt_best] + moves

    moves.sort(key=lambda m: _order_score(board, m, turn, botWhite, gameStates), reverse=True)
    return moves

def _negamax(board, turn: str, depth: int, alpha: float, beta: float, botWhite, gameStates, tt: _TransTable, ply: int) -> float:
    terminal = checkCheckmateOrStalemate(board, turn, botWhite, gameStates)
    if terminal == "checkmate":
        return -MATE_SCORE + ply
    if terminal == "stalemate":
        return 0.0

    if depth == 0:
        return quiesce(board, turn, alpha, beta, botWhite, gameStates, ply=ply)

    key: _TTKey = (board, turn)
    entry = tt.get(key)
    if entry is not None and entry.depth >= depth:
        if entry.flag == "EXACT":
            return entry.score
        if entry.flag == "LOWER":
            alpha = max(alpha, entry.score)
        elif entry.flag == "UPPER":
            beta = min(beta, entry.score)
        if alpha >= beta:
            return entry.score

    alpha_orig = alpha
    beta_orig = beta
    best_move = None
    best_score = float("-inf")

    moves = _ordered_moves(turn, board, botWhite, gameStates, tt, depth)
    if not moves:
        # Should be handled by terminal detection, but keep safe fallback.
        return 0.0

    nxt = _opponent(turn)
    for m in moves:
        score = -_negamax(m, nxt, depth - 1, -beta, -alpha, botWhite, gameStates, tt, ply + 1)
        if score > best_score:
            best_score = score
            best_move = m
        if score > alpha:
            alpha = score
        if alpha >= beta:
            break

    flag = "EXACT"
    if best_score <= alpha_orig:
        flag = "UPPER"
    elif best_score >= beta_orig:
        flag = "LOWER"
    tt[key] = _TTEntry(depth=depth, score=best_score, flag=flag, best=best_move)
    return best_score

def _root_search(board, turn: str, depth: int, botWhite, gameStates, tt: _TransTable) -> Optional[tuple]:
    moves = _ordered_moves(turn, board, botWhite, gameStates, tt, depth)
    if not moves:
        return None
    alpha = float("-inf")
    beta = float("inf")
    best_move: Optional[tuple] = None
    best_score: float = float("-inf")
    nxt = _opponent(turn)
    for m in moves:
        score = -_negamax(m, nxt, depth - 1, -beta, -alpha, botWhite, gameStates, tt, ply=1)
        if score > best_score:
            best_score = score
            best_move = m
        if score > alpha:
            alpha = score
    # Store the PV move at the root too.
    tt[(board, turn)] = _TTEntry(depth=depth, score=best_score, flag="EXACT", best=best_move)
    return best_move, best_score

def calculateMove(board, botWhite, gameStates, turn: str, depth: int) -> Optional[tuple]:
    tt: _TransTable = {}
    best = None
    for d in range(1, depth + 1):
        res = _root_search(board, turn, d, botWhite, gameStates, tt)
        best = res[0] if res is not None else None
        if best is None:
            return None
    return best

def botMove(board, turn, gameStates, botWhite, depth: int = 3, pruneRate: float = 0.20):
    # `pruneRate` kept for API compatibility; beam pruning was replaced by iterative deepening + TT.
    return calculateMove(board, botWhite, gameStates, turn, depth)

def evaluate_move_quality(
    before_board,
    after_board,
    turn: str,
    botWhite,
    gameStates,
    depth: int = 2,
) -> Optional[tuple]:
    """
    Return (best_score, played_score) from the perspective of `turn` on `before_board`.

    Scores are negamax values ("good for side-to-move").
    `played_score` is the value after choosing `after_board` then letting the opponent play optimally.
    """
    if depth < 1:
        return None

    tt: _TransTable = {}
    res = _root_search(before_board, turn, depth, botWhite, gameStates, tt)
    if res is None:
        return None
    _, best_score = res

    # Value of the played move, assuming optimal response from the opponent.
    opp = _opponent(turn)
    played_score = -_negamax(
        after_board,
        opp,
        depth - 1,
        float("-inf"),
        float("inf"),
        botWhite,
        gameStates,
        tt,
        ply=1,
    )
    return best_score, played_score

def checkMove(board, turn, gameStates, botWhite):
    # Generate all legal evasions if in check, then pick the one with best pessimistic 1-reply outcome
    def _pos_score(pos_board, side_to_move: str) -> float:
        terminal = checkCheckmateOrStalemate(pos_board, side_to_move, botWhite, gameStates)
        if terminal == "checkmate":
            return -MATE_SCORE if side_to_move == "bot" else MATE_SCORE
        if terminal == "stalemate":
            return 0.0
        return scoreMove(pos_board, botWhite, gameStates)

    allMoves = getAllTeamMoves(turn, board, botWhite, gameStates)
    legal = [m for moves in allMoves for m in moves if isKingSafe(m, turn)]
    if not legal:
        return None
    opp = 'player' if turn == 'bot' else 'bot'
    best_val = float("-inf")
    best_board = None
    for cand in legal:
        # After our evasion, it's opponent's turn.
        cand_score = _pos_score(cand, opp)
        if cand_score >= MATE_SCORE:
            return cand
        replies = getAllTeamMoves(opp, cand, botWhite, gameStates)
        worst = float("inf")
        any_reply = False
        for rset in replies:
            for r in rset:
                if isKingSafe(r, opp):
                    any_reply = True
                    # After opponent replies, it's our turn again.
                    worst = min(worst, _pos_score(r, turn))
        val = worst if any_reply else cand_score
        if val > best_val:
            best_val, best_board = val, cand
    return best_board
