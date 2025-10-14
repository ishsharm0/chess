# app.py
from flask import Flask, request, redirect, url_for, session, render_template, jsonify
from gameLogic import (
    newBoard, inputValidate, castle, movePiece, isKingSafe,
    checkCheckmateOrStalemate, getAllTeamMoves, promotePawn, castleValidate
)
from bot import botMove, checkMove, scoreMoveForEnemy
import logging, random, os, json
import dotenv

# --- Config / init ---
dotenv.load_dotenv()
config = json.load(open("config.json"))
app = Flask(__name__, static_folder='static', template_folder='templates')
app.secret_key = os.getenv('SECRET_KEY', 'dev-please-change')  # Use a real key in prod
logging.basicConfig(level=logging.DEBUG)

DEFAULT_PRUNE = 0.30  # starting prune rate

def adjust_prune_rate(rank, total):
    """Lower prune rate (search wider) if player is playing strong moves."""
    if total <= 1:
        return DEFAULT_PRUNE
    pct = rank / total
    return max(0.05, DEFAULT_PRUNE * (1 - pct))

def adjust_prune_rate_based_on_move(board, gameStates, botWhite, current_prune_rate):
    """Re-score player's latest board vs all their options and adjust prune."""
    player_moves = getAllTeamMoves('player', board, botWhite, gameStates)
    move_scores = [scoreMoveForEnemy(m, botWhite, gameStates) for moves in player_moves for m in moves]
    if not move_scores:
        return current_prune_rate
    move_scores.sort(reverse=True)
    current_score = scoreMoveForEnemy(board, botWhite, gameStates)
    # find rank (1-based)
    try:
        rank = move_scores.index(current_score) + 1
    except ValueError:
        # if float jitter made exact equality miss, approximate by nearest
        closest = min(range(len(move_scores)), key=lambda i: abs(move_scores[i] - current_score))
        rank = closest + 1
    new_rate = adjust_prune_rate(rank, len(move_scores))
    logging.debug(f"Player move rank {rank}/{len(move_scores)} -> prune {new_rate:.3f}")
    return new_rate

def side_in_check(board, side, botWhite, gameStates):
    """Convenience: True if 'side' is currently in check."""
    return not isKingSafe(board, side)

# --- Routes ---
@app.get('/')
def index():
    logging.debug("Index called")
    session.clear()
    session['botWhite'] = random.choice([True, False])
    session['board'] = newBoard(session['botWhite'])
    session['gameStates'] = [session['board']]
    session['turn'] = 'bot' if session['botWhite'] else 'player'
    session['promote'] = False
    session['promotion_piece'] = None
    session['promotion_dest'] = None
    session['prune_rate'] = DEFAULT_PRUNE

    logging.debug(f"New game botWhite={session['botWhite']}, turn={session['turn']}")

    # Bot may open
    if session['turn'] == 'bot':
        new_board = botMove(session['board'], session['turn'], session['gameStates'], session['botWhite'], pruneRate=session['prune_rate'])
        if new_board:
            session['board'] = new_board
            session['gameStates'].append(new_board)
            session['turn'] = 'player'
            logging.debug("Bot made the first move.")
    return redirect(url_for('active'))

@app.get('/active')
def active():
    return render_template(
        'index.html',
        board=session.get('board'),
        turn=session.get('turn'),
        promote=session.get('promote'),
        botWhite=session.get('botWhite')
    )

@app.post('/make_move')
def make_move():
    response = {}
    move_input = request.json.get('move')
    if move_input:
        validity, piece, dest = inputValidate(move_input, session['board'], session['botWhite'], session['turn'], session['gameStates'])
        if validity == "castle":
            # Validate castling (side to move is 'player' here)
            if not castleValidate(session['botWhite'], session['turn'], session['board']):
                response['status'] = 'invalid-castle'
            else:
                session['board'] = castle(session['turn'], session['board'], session['botWhite'])
                session['gameStates'].append(session['board'])
                # Player just moved -> evaluate bot side
                outcome = checkCheckmateOrStalemate(session['board'], 'bot', session['botWhite'], session['gameStates'])
                if outcome == 'checkmate':
                    response['status'] = 'checkmate'
                    response['winner'] = 'player'
                elif outcome == 'stalemate':
                    response['status'] = 'stalemate'
                else:
                    # Not game over; report if bot is now in check
                    response['status'] = 'castle'
                    response['in_check'] = side_in_check(session['board'], 'bot', session['botWhite'], session['gameStates'])
                    session['turn'] = 'bot'
        elif validity:
            # Make player move
            session['board'] = movePiece(piece, dest, session['board'], session['gameStates'], session['turn'])
            session['gameStates'].append(session['board'])

            # Pawn promotion trigger
            if piece[0].lower() == 'p' and (dest // 8 in (0, 7)):
                session['promote'] = True
                session['promotion_piece'] = piece
                session['promotion_dest'] = dest
                response['status'] = 'promote'
            else:
                # Player moved -> check bot side
                status = checkCheckmateOrStalemate(session['board'], 'bot', session['botWhite'], session['gameStates'])
                if status == 'checkmate':
                    response['status'] = 'checkmate'
                    response['winner'] = 'player'
                elif status == 'stalemate':
                    response['status'] = 'stalemate'
                else:
                    session['turn'] = 'bot'
                    session['prune_rate'] = adjust_prune_rate_based_on_move(session['board'], session['gameStates'], session['botWhite'], session['prune_rate'])
                    response['status'] = 'success'
                    response['in_check'] = side_in_check(session['board'], 'bot', session['botWhite'], session['gameStates'])
        else:
            response['status'] = 'invalid'

    response.update({
        'board': session['board'],
        'turn': session['turn'],
        'promote': session['promote'],
        'botWhite': session['botWhite']
    })
    return jsonify(response)

@app.post('/promote')
def promote():
    """Promote a pending pawn then pass turn to bot (if game not done)."""
    if not session.get('promote'):
        return jsonify({'status': 'no-promotion', 'board': session['board'], 'turn': session['turn']})
    choice = request.json.get('piece', 'QUEEN').upper()
    piece = session['promotion_piece']
    dest = session['promotion_dest']
    session['board'] = promotePawn(piece, dest, choice, session['board'], 'player')
    session['gameStates'].append(session['board'])
    session['promote'] = False
    session['promotion_piece'] = None
    session['promotion_dest'] = None

    # Player just finished a move via promotion -> check bot side now
    status = checkCheckmateOrStalemate(session['board'], 'bot', session['botWhite'], session['gameStates'])
    if status == 'checkmate':
        return jsonify({'status': 'checkmate', 'winner': 'player', 'board': session['board'], 'turn': 'player'})
    if status == 'stalemate':
        return jsonify({'status': 'stalemate', 'board': session['board'], 'turn': 'player'})

    session['turn'] = 'bot'
    return jsonify({
        'status': 'promoted',
        'board': session['board'],
        'turn': session['turn'],
        'in_check': side_in_check(session['board'], 'bot', session['botWhite'], session['gameStates'])
    })

@app.post('/bot_move')
def bot_move():
    response = {}
    if session['turn'] == 'bot':
        if not isKingSafe(session['board'], session['turn']):
            new_board = checkMove(session['board'], session['turn'], session['gameStates'], session['botWhite'])
        else:
            new_board = botMove(session['board'], session['turn'], session['gameStates'], session['botWhite'], pruneRate=session['prune_rate'])
        if new_board and isKingSafe(new_board, session['turn']):
            session['board'] = new_board
            session['gameStates'].append(new_board)
            # Bot moved -> check player side
            status = checkCheckmateOrStalemate(session['board'], 'player', session['botWhite'], session['gameStates'])
            if status == 'checkmate':
                response['status'] = 'checkmate'
                response['winner'] = 'bot'
            elif status == 'stalemate':
                response['status'] = 'stalemate'
            else:
                session['turn'] = 'player'
                response['status'] = 'success'
                response['in_check'] = side_in_check(session['board'], 'player', session['botWhite'], session['gameStates'])
        else:
            logging.error("Bot couldn't find a valid board.")
            response['status'] = 'error'
    response.update({
        'board': session['board'],
        'turn': session['turn'],
        'botWhite': session['botWhite']
    })
    return jsonify(response)

if __name__ == '__main__':
    app.run(debug=config.get("debugMode", False))
