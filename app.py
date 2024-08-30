from flask import Flask, request, redirect, url_for, session, render_template, flash, jsonify
from gameLogic import *
from bot import botMove, checkMove, scoreMoveForEnemy
import logging
import random
import os
import dotenv
import json

config = json.load(open("config.json"))
dotenv.load_dotenv()

app = Flask(__name__, static_folder='static', template_folder='templates')
app.secret_key = os.getenv('SECRET_KEY')  # Use a real key in production
logging.basicConfig(level=logging.DEBUG)

default_prune_rate = 0.3  # Initial prune rate

def adjust_prune_rate(move_rank, total_moves):
    # Adjust prune rate, scaling based on player's move rank
    if total_moves <= 1:
        return default_prune_rate  # No adjustment if only one move is possible

    rank_percentage = move_rank / total_moves
    adjusted_prune_rate = max(0.05, default_prune_rate * (1 - rank_percentage))  # Minimum prune rate of 0.05
    return adjusted_prune_rate

@app.route('/', methods=['GET'])
def index():
    logging.debug("Index called")
    session['botWhite'] = random.choice([True, False])
    session['board'] = newBoard(session['botWhite'])
    session['gameStates'] = [session['board']]
    session['turn'] = 'bot' if session['botWhite'] else 'player'
    session['promote'] = False
    session['prune_rate'] = default_prune_rate  # Initialize prune rate with the default value

    logging.debug(f"New game started with botWhite: {session['botWhite']}")

    if session['turn'] == 'bot':
        logging.debug("Bot starts, making the first move.")
        new_board = botMove(session['board'], session['turn'], session['gameStates'], session['botWhite'], pruneRate=session['prune_rate'])
        if new_board:
            session['board'] = new_board
            session['gameStates'].append(new_board)
            session['turn'] = 'player'
            logging.debug("Bot made the first move, switching to player.")

    return redirect(url_for('active'))

@app.route('/active', methods=['GET'])
def active():
    logging.debug("Active page called")
    return render_template('index.html', board=session['board'], turn=session['turn'], promote=session['promote'], botWhite=session['botWhite'])

@app.route('/make_move', methods=['POST'])
def make_move():
    logging.debug("Make move called")
    response = {}
    move_input = request.json.get('move')
    if move_input:
        validity, piece, dest = inputValidate(move_input, session['board'], session['botWhite'], session['turn'], session['gameStates'])
        if validity == "castle":
            session['board'] = castle(session['turn'], session['board'], session['botWhite'])
            session['gameStates'].append(session['board'])
            session['turn'] = 'bot'
            response['status'] = 'castle'
        elif validity:
            session['board'] = movePiece(piece, dest, session['board'], session['gameStates'], session['turn'])
            session['gameStates'].append(session['board'])

            if piece.lower().startswith('p') and (dest // 8 == 0 or dest // 8 == 7):
                session['promote'] = True
                session['promotion_piece'] = piece
                session['promotion_dest'] = dest
                response['status'] = 'promote'
            else:
                status = checkCheckmateOrStalemate(session['board'], 'player', session['botWhite'], session['gameStates'])
                if status == 'checkmate':
                    response['status'] = 'checkmate'
                    response['winner'] = 'player' if session['turn'] == 'player' else 'bot'
                elif status == 'stalemate':
                    response['status'] = 'stalemate'
                else:
                    session['turn'] = 'bot'
                    # Adjust prune rate based on player's move
                    session['prune_rate'] = adjust_prune_rate_based_on_move(session['board'], session['gameStates'], session['botWhite'], session['prune_rate'])
                    response['status'] = 'success'
        else:
            response['status'] = 'invalid'

    response['board'] = session['board']
    response['turn'] = session['turn']
    response['promote'] = session['promote']
    response['botWhite'] = session['botWhite']
    return jsonify(response)

@app.route('/bot_move', methods=['POST'])
def bot_move():
    logging.debug("Bot Move called")
    response = {}
    if session['turn'] == 'bot':
        if not isKingSafe(session['board'], session['turn']):
            new_board = checkMove(session['board'], session['turn'], session['gameStates'], session['botWhite'])
        else:
            new_board = botMove(session['board'], session['turn'], session['gameStates'], session['botWhite'], pruneRate=session['prune_rate'])
        
        if new_board:
            logging.debug("Board exists")
            if isKingSafe(new_board, session['turn']):
                logging.debug("King is safe")
                session['board'] = new_board
                session['gameStates'].append(new_board)  
                status = checkCheckmateOrStalemate(session['board'], 'bot', session['botWhite'], session['gameStates'])
                if status == 'checkmate':
                    response['status'] = 'checkmate'
                    response['winner'] = 'bot'
                elif status == 'stalemate':
                    response['status'] = 'stalemate'
                else:   
                    session['turn'] = 'player'
                    response['status'] = 'success'
        else:
            logging.error("Error: No valid board state returned")
            response['status'] = 'error'

    response['board'] = session['board']
    response['turn'] = session['turn']
    response['botWhite'] = session['botWhite']
    return jsonify(response)

def adjust_prune_rate_based_on_move(board, gameStates, botWhite, current_prune_rate):
    player_moves = getAllTeamMoves('player', board, botWhite, gameStates)
    move_scores = [scoreMoveForEnemy(move, botWhite, gameStates) for moves in player_moves for move in moves]

    sorted_scores = sorted(move_scores, reverse=True)
    best_score = sorted_scores[0] if sorted_scores else 0

    if best_score:
        current_score = scoreMoveForEnemy(board, botWhite, gameStates)
        move_rank = sorted_scores.index(current_score) + 1
        total_moves = len(sorted_scores)

        new_prune_rate = adjust_prune_rate(move_rank, total_moves)

        logging.debug(f"Player move ranked {move_rank}/{total_moves}. Adjusted prune rate: {new_prune_rate}")
        return new_prune_rate
    
    return current_prune_rate

if __name__ == '__main__':
    app.run(debug=config["debugMode"])
