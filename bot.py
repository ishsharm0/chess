# bot.py
from gameLogic import *
import random
import logging

def scoreMove(board, botWhite, gameStates):
    # Define values for each piece type
    values = {
        'K': 5, 'Q': 4, 'R': 3.5, 'B': 3, 'N': 2.5, 'P': 1,
        'k': 0, 'q': -6, 'r': -5, 'b': -4, 'n': -3, 'p': -2
    }

    score = 0
    for piece in board:
        if piece:
            # Add or subtract the value of the piece from the score
            score += values.get(piece[0], 0)

    # Add a small random number to the score to avoid ties
    score += random.random() * 0.000001

    # Is enemy checkmate
    if detectCheckmate(board, 'player', botWhite, gameStates):
        score += 15  
    # Is bot checkmate
    if detectCheckmate(board, 'bot', botWhite, gameStates): 
        score -= 15

    if not (isKingSafe(board, 'player')): 
        score += 4
    elif not isKingSafe(board, 'bot'):
        score -= 10

    return score
    
def scoreMoveForEnemy(board, botWhite, gameStates):
    values = {
        'K': -5, 'Q': -4, 'R': -3.5, 'B': -3, 'N': -2.5, 'P': -1,
        'k': 5, 'q': 4, 'r': 3.5, 'b': 3, 'n': 2.5, 'p': 1
    }

    score = 0
    for piece in board:
        if piece:
            # Subtract bot's piece values and add enemy's piece values
            score += values.get(piece[0], 0)

    # Add a small random number to the score to avoid ties
    score += random.random() * 0.000001

    # Adjust the scoring to be more aggressive:
    # Significantly penalize the bot's king being unsafe
    if not isKingSafe(board, 'bot'):
        score += 7

    # Highly reward player's moves leading to bot's checkmate
    if detectCheckmate(board, 'bot', botWhite, gameStates):
        score += 20

    # Penalize enemy's king being unsafe less significantly than bot's king safety
    if not isKingSafe(board, 'player'):
        score -= 5

    # Significantly reward player's moves leading to player's checkmate
    if detectCheckmate(board, 'player', botWhite, gameStates):
        score -= 20

    return score


def calculateMove(moves, botWhite, gameStates, turn, depth, pruneRate):
    # Initialize the root node with the current board state
    root = Node(getCurrentBoard(gameStates))

    # Build the game tree
    moveTreeBuilder(root, depth, pruneRate, turn, botWhite, gameStates)

    # After building the tree, select the move corresponding to the highest (or lowest for minimizing player) score
    if not root.children:
        return None

    # Find the move with the best score
    best_move = None
    if turn == 'bot':  # Bot is maximizing player
        best_score = float('-inf')
        for child in root.children:
            if child.score > best_score:
                best_score = child.score
                best_move = child.board
    else:  # Bot is minimizing player (opponent's turn)
        best_score = float('inf')
        for child in root.children:
            if child.score < best_score:
                best_score = child.score
                best_move = child.board

    return best_move

def getCurrentBoard(gameStates):
    # Assuming gameStates stores the history of the game, return the current board state
    return gameStates[-1]  # Modify this line as necessary to fit your implementation


def botMove(board, turn, gameStates, botWhite, depth=2, pruneRate=0.3):
    moves = getAllTeamMoves(turn, board, botWhite, gameStates)
    if not moves:
        return None
    return calculateMove(moves, botWhite, gameStates, turn, depth, pruneRate)

class Node:
    def __init__(self, gameState, score=None):
        self.board = gameState
        self.score = score
        self.children = []

    def add_child(self, child):
        self.children.append(child)

    def __repr__(self):  # For easier debugging
        return f"Node(score={self.score})"

def moveTreeBuilder(node, depth, pruneRate, turn, botWhite, gameStates):
    if depth == 0 or detectCheckmate(node.board, turn, botWhite, gameStates):
        # Evaluate leaf node using the appropriate scoring function
        node.score = scoreMove(node.board, botWhite, gameStates) if turn == 'bot' else scoreMoveForEnemy(node.board, botWhite, gameStates)
        return node.score

    # Generate possible moves
    possible_moves = getAllTeamMoves(turn, node.board, botWhite, gameStates)
    child_nodes = []

    # Evaluate each move and create nodes without recursion yet
    for moves in possible_moves:
        for move in moves:
            child_node = Node(move)
            # Score the move immediately
            child_node.score = scoreMove(move, botWhite, gameStates) if turn == 'bot' else scoreMoveForEnemy(move, botWhite, gameStates)
            child_nodes.append(child_node)

    # Prune branches: keep only top 'pruneRate' percent moves
    sorted_child_nodes = sorted(child_nodes, key=lambda x: x.score, reverse=turn == 'bot')
    pruned_children = sorted_child_nodes[:int(len(sorted_child_nodes) * pruneRate)]

    # Add only the pruned nodes to the tree
    for child in pruned_children:
        # Ensure the king is safe after the move before adding the child to the tree
        if isKingSafe(child.board, turn):
            node.add_child(child)
            # Recursively build the tree for the pruned moves
            moveTreeBuilder(child, depth - 1, pruneRate, 'player' if turn == 'bot' else 'bot', botWhite, gameStates)

    # Calculate the node score based on the average of child scores
    if pruned_children:
        node.score = sum(child.score for child in pruned_children) / len(pruned_children)
    else:
        node.score = 0

    return node.score