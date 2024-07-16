from gameLogic import *
import random
    

def scoreMove(board, botWhite):
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
    if detectCheckmate(board, 'player', botWhite):
        score += 10  
    # Is bot checkmate
    if detectCheckmate(board, 'bot', botWhite): 
        score -= 10

    if not (isKingSafe(board, 'player')): 
        score += 2
    elif not isKingSafe(board, 'bot'):
        score -= 2

    return score
    
def scoreMoveForEnemy(board, botWhite):
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
    if detectCheckmate(board, 'bot', botWhite):
        score += 10  # Positive for enemy if bot is in checkmate

    # Is player (enemy) checkmate
    if detectCheckmate(board, 'player', botWhite): 
        score -= 10  # Negative if enemy is in checkmate, we don't want this

    # Check king safety and adjust score accordingly
    if not isKingSafe(board, 'bot'):
        score += 2  # Positive for enemy if bot's king is not safe
    elif not isKingSafe(board, 'player'):
        score -= 2  # Negative if enemy's king is not safe, we don't want this

    return score

def calculateMove(moves, botWhite):
    if not moves:  # Check if moves list is empty
        print("No moves available.")
        return None

    best_score = float('-inf')
    best_move = None

    # Iterate through all moves and calculate their scores
    for piece_moves in moves:
        if piece_moves:  # Ensure there are moves available for the piece
            for move in piece_moves:
                current_score = scoreMove(move, botWhite)
                if current_score > best_score:
                    best_score = current_score
                    best_move = move

    if best_move:
        #print("Best move selected:", best_move, "with score:", best_score)
        print("Best move score: ",best_score)
        return best_move
    else:
        print("No valid moves found.")
        return None
    
    # Currently randomly picks move
    # In future, will call each possible move, and from there, call each of the opponent's possible moves. 
    # It'll cut off the top N moves, average them, and pick the one with the highest average


def botMove(board, turn, gameStates, botWhite):
    moves = getAllTeamMoves(turn, board, botWhite)
    if not moves:
        print("Failed to generate any moves for the bot.")
        return None
    
    return calculateMove(moves, botWhite)
