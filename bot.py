# bot.py
import math
from typing import Optional, List
from gameLogic import getAllTeamMoves, isKingSafe, detectCheckmate

def getCurrentBoard(gameStates):
    return gameStates[-1]

# Simple material values, uppercase = bot, lowercase = player
_PVAL = {'P':1,'N':3,'B':3,'R':5,'Q':9,'K':0}

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
    if detectCheckmate(board, 'player', botWhite, gameStates): score += 1_000_000.0
    if detectCheckmate(board, 'bot',    botWhite, gameStates): score -= 1_000_000.0
    # light king-safety nudges
    if not isKingSafe(board, 'player'): score += 0.5
    if not isKingSafe(board, 'bot'):    score -= 0.5
    score += _mobility(board, botWhite, gameStates)
    return score

def scoreMoveForEnemy(board, botWhite, gameStates) -> float:
    # Perspective of the human (player)
    return -scoreMove(board, botWhite, gameStates)

class Node:
    def __init__(self, gameState, score: Optional[float] = None):
        self.board = gameState
        self.score = score
        self.children: List["Node"] = []

    def add_child(self, child: 'Node'):
        self.children.append(child)

# --- Quiescence search (captures only) ---
def _is_capture(prev, nxt) -> bool:
    # crude: if the piece-count drops, treat as capture
    prev_cnt = sum(1 for p in prev if p is not None)
    nxt_cnt  = sum(1 for p in nxt  if p is not None)
    return nxt_cnt < prev_cnt

def quiesce(board, turn, alpha, beta, botWhite, gameStates, node_cap=64):
    stand_pat = scoreMove(board, botWhite, gameStates)
    if stand_pat >= beta:
        return beta
    if alpha < stand_pat:
        alpha = stand_pat

    moves = getAllTeamMoves(turn, board, botWhite, gameStates)
    next_turn = 'player' if turn == 'bot' else 'bot'
    visited = 0

    # consider only capturing moves
    for ms in moves:
        for m in ms:
            if not isKingSafe(m, turn):
                continue
            if not _is_capture(board, m):
                continue
            score = -quiesce(m, next_turn, -beta, -alpha, botWhite, gameStates, node_cap)
            visited += 1
            if score >= beta:
                return beta
            if score > alpha:
                alpha = score
            if visited >= node_cap:
                return alpha
    return alpha

def moveTreeBuilder(node: Node, depth: int, pruneRate: float, turn: str, botWhite: bool, gameStates,
                    alpha: float = float("-inf"), beta: float = float("inf")) -> float:
    # terminal or horizon: use quiescence at leaves
    if depth == 0 or detectCheckmate(node.board, turn, botWhite, gameStates):
        node.score = quiesce(node.board, turn, alpha, beta, botWhite, gameStates)
        return node.score

    # generate legal moves
    possible_moves = getAllTeamMoves(turn, node.board, botWhite, gameStates)
    children: List[Node] = []
    for moves in possible_moves:
        for m in moves:
            if isKingSafe(m, turn):
                c = Node(m)
                # shallow score only for ordering
                c.score = scoreMove(m, botWhite, gameStates)
                children.append(c)

    if not children:
        node.score = quiesce(node.board, turn, alpha, beta, botWhite, gameStates)
        return node.score

    # beam prune
    keep = max(1, int(len(children) * max(0.05, min(1.0, pruneRate))))
    maximizing = (turn == 'bot')
    children.sort(key=lambda x: x.score, reverse=maximizing)
    node.children = children[:keep]

    next_turn = 'player' if turn == 'bot' else 'bot'

    if maximizing:
        value = float("-inf")
        for c in node.children:
            val = moveTreeBuilder(c, depth-1, pruneRate, next_turn, botWhite, gameStates, alpha, beta)
            value = max(value, val)
            alpha = max(alpha, value)
            if alpha >= beta:
                break
        node.score = value
    else:
        value = float("inf")
        for c in node.children:
            val = moveTreeBuilder(c, depth-1, pruneRate, next_turn, botWhite, gameStates, alpha, beta)
            value = min(value, val)
            beta = min(beta, value)
            if alpha >= beta:
                break
        node.score = value

    return node.score

def calculateMove(moves, botWhite, gameStates, turn, depth, pruneRate):
    root = Node(getCurrentBoard(gameStates))
    moveTreeBuilder(root, depth, pruneRate, turn, botWhite, gameStates)
    if not root.children:
        return None
    if turn == 'bot':
        best = max(root.children, key=lambda c: c.score)
    else:
        best = min(root.children, key=lambda c: c.score)
    return best.board

def botMove(board, turn, gameStates, botWhite, depth: int = 3, pruneRate: float = 0.20):
    moves = getAllTeamMoves(turn, board, botWhite, gameStates)
    if not moves:
        return None
    return calculateMove(moves, botWhite, gameStates, turn, depth, pruneRate)

def checkMove(board, turn, gameStates, botWhite):
    # Generate all legal evasions if in check, then pick the one with best pessimistic 1-reply outcome
    allMoves = getAllTeamMoves(turn, board, botWhite, gameStates)
    legal = [m for moves in allMoves for m in moves if isKingSafe(m, turn)]
    if not legal:
        return None
    opp = 'player' if turn == 'bot' else 'bot'
    best_val = float("-inf")
    best_board = None
    for cand in legal:
        replies = getAllTeamMoves(opp, cand, botWhite, gameStates)
        worst = float("inf")
        any_reply = False
        for rset in replies:
            for r in rset:
                if isKingSafe(r, opp):
                    any_reply = True
                    worst = min(worst, scoreMove(r, botWhite, gameStates))
        val = worst if any_reply else scoreMove(cand, botWhite, gameStates)
        if val > best_val:
            best_val, best_board = val, cand
    return best_board
