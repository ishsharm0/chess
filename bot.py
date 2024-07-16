from gameLogic import *
import random, datetime
    

def scoreMove(board, botWhite, gameStates):
    # Define values for each piece type
    values = {
        'K': 5, 'Q': 4, 'R': 3.5, 'B': 3, 'N': 2.5, 'P': 1,
        'k': 0, 'q': -4, 'r': -3.5, 'b': -3, 'n': -2.5, 'p': -1
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
        score += 10  
    # Is bot checkmate
    if detectCheckmate(board, 'bot', botWhite, gameStates): 
        score -= 10

    if not (isKingSafe(board, 'player')): 
        score += 2
    elif not isKingSafe(board, 'bot'):
        score -= 2

    return score
    
def scoreMoveForEnemy(board, botWhite, gameStates):
    # Define values for each piece type, negative for bot's pieces since we're scoring for the enemy
    values = {
        'K': -5, 'Q': -4, 'R': -3.5, 'B': -3, 'N': -2.5, 'P': -1,
        'k': 5, 'q': 4, 'r': 3.5, 'b': 3, 'n': 2.5, 'p': 1
    }

    score = 0
    for piece in board:
        if piece:
            # Add or subtract the value of the piece from the score
            score += values.get(piece[0], 0)

    # Add a small random number to the score to avoid ties
    score += random.random() * 0.000001

    # Is enemy (bot) checkmate
    if detectCheckmate(board, 'bot', botWhite, gameStates):
        score += 10  # Positive for enemy if bot is in checkmate

    # Is player (enemy) checkmate
    if detectCheckmate(board, 'player', botWhite, gameStates): 
        score -= 10  # Negative if enemy is in checkmate, we don't want this

    # Check king safety and adjust score accordingly
    if not isKingSafe(board, 'bot'):
        score += 2  # Positive for enemy if bot's king is not safe
    elif not isKingSafe(board, 'player'):
        score -= 2  # Negative if enemy's king is not safe, we don't want this

    return score

def minimax(board, depth, is_maximizing_player, botWhite, gameStates):
    if depth == 0 or detectCheckmate(board, 'player', botWhite, gameStates) or detectCheckmate(board, 'bot', botWhite, gameStates):
        return scoreMove(board, botWhite, gameStates) if is_maximizing_player else scoreMoveForEnemy(board, botWhite, gameStates)

    if is_maximizing_player:
        max_eval = float('-inf')
        moves = getAllTeamMoves('bot', board, botWhite, gameStates)  # Assuming it's bot's turn
        for piece_moves in moves:
            for move in piece_moves:
                eval = minimax(move, depth - 1, False, botWhite, gameStates)
                max_eval = max(max_eval, eval)
        return max_eval
    else:
        min_eval = float('inf')
        moves = getAllTeamMoves('player', board, botWhite, gameStates)  # Assuming it's player's turn
        for piece_moves in moves:
            for move in piece_moves:
                eval = minimax(move, depth - 1, True, botWhite, gameStates)
                min_eval = min(min_eval, eval)
        return min_eval

def calculateMove(moves, botWhite, gameStates, depth):
    best_score = float('-inf')
    best_move = None

    # Iterate through all moves and calculate their scores using minimax
    for piece_moves in moves:
        if piece_moves:  # Ensure there are moves available for the piece
            for move in piece_moves:
                current_score = minimax(move, depth - 1, False, botWhite, gameStates)  # Start with the opponent's move (minimizing player)
                if current_score > best_score:
                    best_score = current_score
                    best_move = move

    if best_move:
        print("Best move score:", best_score)
        return best_move
    else:
        print("No valid moves found.")
        return None

def botMove(board, turn, gameStates, botWhite, depth=2):
    moves = getAllTeamMoves(turn, board, botWhite, gameStates)
    if not moves:
        print("Failed to generate any moves for the bot.")
        return None
    
    return calculateMove(moves, botWhite, gameStates, depth)