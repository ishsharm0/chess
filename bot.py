# bot.py
import random
from typing import Optional
from gameLogic import getAllTeamMoves, isKingSafe, detectCheckmate

def getCurrentBoard(gameStates):
    return gameStates[-1]

# Simple material values, uppercase = bot, lowercase = player
_PVAL = {'P':1,'N':3,'B':3,'R':5,'Q':9,'K':0}

def _material_score(board) -> float:
    score = 0.0
    for p in board:
        if not p:
            continue
        base = _PVAL.get(p[0].upper(), 0)
        score += base if p[0].isupper() else -base
    return score

def scoreMove(board, botWhite, gameStates) -> float:
    score = _material_score(board)
    if detectCheckmate(board, 'player', botWhite, gameStates): score += 1e6
    if detectCheckmate(board, 'bot', botWhite, gameStates): score -= 1e6
    if not isKingSafe(board, 'player'): score += 0.5
    if not isKingSafe(board, 'bot'):    score -= 0.7
    score += random.random()*1e-6  # tie-break jitter
    return score

def scoreMoveForEnemy(board, botWhite, gameStates) -> float:
    # Perspective of the human (player)
    return -scoreMove(board, botWhite, gameStates)

class Node:
    def __init__(self, gameState, score: Optional[float] = None):
        self.board = gameState
        self.score = score
        self.children = []

    def add_child(self, child: 'Node'):
        self.children.append(child)

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

def botMove(board, turn, gameStates, botWhite, depth: int = 2, pruneRate: float = 0.30):
    moves = getAllTeamMoves(turn, board, botWhite, gameStates)
    if not moves:
        return None
    return calculateMove(moves, botWhite, gameStates, turn, depth, pruneRate)

def checkMove(board, turn, gameStates, botWhite):
    allMoves = getAllTeamMoves(turn, board, botWhite, gameStates)
    legal = [m for moves in allMoves for m in moves if isKingSafe(m, turn)]
    if not legal:
        return None
    best = max(legal, key=lambda b: scoreMove(b, botWhite, gameStates))
    return best

def moveTreeBuilder(node: Node, depth: int, pruneRate: float, turn: str, botWhite: bool, gameStates):
    if depth == 0 or detectCheckmate(node.board, turn, botWhite, gameStates):
        node.score = scoreMove(node.board, botWhite, gameStates)
        return node.score

    possible_moves = getAllTeamMoves(turn, node.board, botWhite, gameStates)
    children = []
    for moves in possible_moves:
        for m in moves:
            if isKingSafe(m, turn):
                c = Node(m)
                c.score = scoreMove(m, botWhite, gameStates)
                children.append(c)

    if not children:
        node.score = scoreMove(node.board, botWhite, gameStates)
        return node.score

    keep = max(1, int(len(children) * max(0.05, min(1.0, pruneRate))))
    reverse = (turn == 'bot')  # max if bot, min if player
    children.sort(key=lambda x: x.score, reverse=reverse)
    pruned = children[:keep]
    node.children = pruned

    next_turn = 'player' if turn == 'bot' else 'bot'
    for c in pruned:
        moveTreeBuilder(c, depth-1, pruneRate, next_turn, botWhite, gameStates)

    node.score = sum(ch.score for ch in pruned) / len(pruned)
    return node.score
