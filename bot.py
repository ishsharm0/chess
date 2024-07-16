from gameLogic import *
import random
    

def scoreMove(board):
    # Define values for each piece type
    values = {
        'K': 5, 'Q': 4, 'R': 3.5, 'B': 3, 'N': 2.5, 'P': 1,
        'k': 0, 'q': -4, 'r': -3.5, 'b': -3, 'n': -2.5, 'p': -1
    }

    score = 0
    # Iterate through all squares on the board
    for piece in board:
        if piece:
            # Add or subtract the value of the piece from the score
            score += values.get(piece[0], 0)

    # Add a small random number to the score to avoid ties
    score += random.random() * 0.000001

    # Is enemy checkmate
    if detectCheckmate(board, 'player'):
        score += 10  

    # Is bot checkmate
    if detectCheckmate(board, 'bot'): 
        score -= 10

    return score
    

def calculateMove(moves):
    if not moves:  # Check if moves list is empty
        print("No moves available.")
        return None

    best_score = float('-inf')
    best_move = None

    # Iterate through all moves and calculate their scores
    for piece_moves in moves:
        if piece_moves:  # Ensure there are moves available for the piece
            for move in piece_moves:
                current_score = scoreMove(move)
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
    
    return calculateMove(moves)
