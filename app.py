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
app.secret_key = os.getenv('SECRET_KEY', 'dev-please-change')
logging.basicConfig(level=logging.DEBUG)

DEFAULT_PRUNE = 0.20  # default beam/prune

def adjust_prune_rate(rank, total):
    if total <= 1:
        return DEFAULT_PRUNE
    pct = rank / total
    return max(0.05, DEFAULT_PRUNE * (1 - pct))

def adjust_prune_rate_based_on_move(board, gameStates, botWhite, current_prune_rate):
    player_moves = getAllTeamMoves('player', board, botWhite, gameStates)
    move_scores = [scoreMoveForEnemy(m, botWhite, gameStates) for moves in player_moves for m in moves]
    if not move_scores:
        return current_prune_rate
    move_scores.sort(reverse=True)
    current_score = scoreMoveForEnemy(board, botWhite, gameStates)
    EPS = 1e-6
    higher = sum(1 for s in move_scores if s > current_score + EPS)
    rank = higher + 1
    new_rate = adjust_prune_rate(rank, len(move_scores))
    logging.debug(f"Player move rank {rank}/{len(move_scores)} -> prune {new_rate:.3f}")
    return new_rate

def side_in_check(board, side, botWhite, gameStates):
    return not isKingSafe(board, side)

def _check_terminal_for(turn_side):
    """Return 'checkmate'/'stalemate'/'none' for the side-to-move."""
    return checkCheckmateOrStalemate(session['board'], turn_side, session['botWhite'], session['gameStates'])

def _end_game(status, winner=None):
    session['game_over'] = True
    session['winner'] = winner
    return {'status': status, 'winner': winner, 'board': session['board'], 'turn': session['turn']}

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
    session['game_over'] = False
    session['winner'] = None

    logging.debug(f"New game botWhite={session['botWhite']}, turn={session['turn']}")

    # If bot opens, make its move and check terminal on player's side.
    if session['turn'] == 'bot':
        new_board = botMove(session['board'], session['turn'], session['gameStates'], session['botWhite'], pruneRate=session['prune_rate'])
        if new_board:
            session['board'] = new_board
            session['gameStates'].append(new_board)
            # Check if player is already mated/stalemated before handing turn
            status = _check_terminal_for('player')
            if status == 'checkmate':
                _end = _end_game('checkmate', winner='bot')
                return redirect(url_for('active'))
            if status == 'stalemate':
                _end = _end_game('stalemate', winner=None)
                return redirect(url_for('active'))
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
        botWhite=session.get('botWhite'),
        game_over=session.get('game_over'),
        winner=session.get('winner')
    )

@app.post('/make_move')
def make_move():
    # If game is already over, refuse further moves.
    if session.get('game_over'):
        return jsonify({
            'status': 'game-over',
            'winner': session.get('winner'),
            'board': session['board'],
            'turn': session['turn'],
            'promote': session['promote'],
            'botWhite': session['botWhite']
        })

    # Before processing, if the side-to-move is already checkmated/stalemated, end immediately.
    pre_status = _check_terminal_for(session['turn'])
    if pre_status == 'checkmate':
        winner = 'bot' if session['turn'] == 'player' else 'player'
        payload = _end_game('checkmate', winner=winner)
        payload.update({'promote': session['promote'], 'botWhite': session['botWhite']})
        return jsonify(payload)
    if pre_status == 'stalemate':
        payload = _end_game('stalemate', winner=None)
        payload.update({'promote': session['promote'], 'botWhite': session['botWhite']})
        return jsonify(payload)

    response = {}
    move_input = request.json.get('move')

    if move_input:
        validity, piece, dest = inputValidate(move_input, session['board'], session['botWhite'], session['turn'], session['gameStates'])
        if validity == "castle":
            if not castleValidate(session['botWhite'], session['turn'], session['board']):
                response['status'] = 'invalid-castle'
            else:
                session['board'] = castle(session['turn'], session['board'], session['botWhite'])
                session['gameStates'].append(session['board'])

                # After player's move, check terminal on bot side immediately
                outcome = _check_terminal_for('bot')
                if outcome == 'checkmate':
                    endp = _end_game('checkmate', winner='player')
                    return jsonify(endp)
                if outcome == 'stalemate':
                    endp = _end_game('stalemate', winner=None)
                    return jsonify(endp)

                response['status'] = 'castle'
                response['in_check'] = side_in_check(session['board'], 'bot', session['botWhite'], session['gameStates'])
                session['turn'] = 'bot'

        elif validity:
            # Normal move
            session['board'] = movePiece(piece, dest, session['board'], session['gameStates'], session['turn'])
            session['gameStates'].append(session['board'])

            # Promotion trigger
            if piece[0].lower() == 'p' and (dest // 8 in (0, 7)):
                session['promote'] = True
                session['promotion_piece'] = piece
                session['promotion_dest'] = dest
                response['status'] = 'promote'
            else:
                # After player's move, check terminal on bot side immediately
                status = _check_terminal_for('bot')
                if status == 'checkmate':
                    endp = _end_game('checkmate', winner='player')
                    return jsonify(endp)
                if status == 'stalemate':
                    endp = _end_game('stalemate', winner=None)
                    return jsonify(endp)

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
        'botWhite': session['botWhite'],
        'game_over': session['game_over'],
        'winner': session['winner']
    })
    return jsonify(response)

@app.post('/promote')
def promote():
    if session.get('game_over'):
        return jsonify({
            'status': 'game-over',
            'winner': session.get('winner'),
            'board': session['board'],
            'turn': session['turn']
        })

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

    # After promotion completes, check terminal on bot side immediately
    status = _check_terminal_for('bot')
    if status == 'checkmate':
        return jsonify(_end_game('checkmate', winner='player'))
    if status == 'stalemate':
        return jsonify(_end_game('stalemate', winner=None))

    session['turn'] = 'bot'
    return jsonify({
        'status': 'promoted',
        'board': session['board'],
        'turn': session['turn'],
        'in_check': side_in_check(session['board'], 'bot', session['botWhite'], session['gameStates']),
        'game_over': session['game_over'],
        'winner': session['winner']
    })

@app.post('/bot_move')
def bot_move():
    # If game is already over, refuse further moves.
    if session.get('game_over'):
        return jsonify({
            'status': 'game-over',
            'winner': session.get('winner'),
            'board': session['board'],
            'turn': session['turn'],
            'botWhite': session['botWhite']
        })

    response = {}
    if session['turn'] == 'bot':
        # If bot's turn but bot is already mated/stalemated, end immediately.
        pre_status = _check_terminal_for('bot')
        if pre_status == 'checkmate':
            return jsonify(_end_game('checkmate', winner='player'))
        if pre_status == 'stalemate':
            return jsonify(_end_game('stalemate', winner=None))

        if not isKingSafe(session['board'], session['turn']):
            new_board = checkMove(session['board'], session['turn'], session['gameStates'], session['botWhite'])
        else:
            new_board = botMove(session['board'], session['turn'], session['gameStates'], session['botWhite'], pruneRate=session['prune_rate'])

        if new_board and isKingSafe(new_board, session['turn']):
            session['board'] = new_board
            session['gameStates'].append(new_board)

            # After bot's move, check terminal on player's side immediately
            status = _check_terminal_for('player')
            if status == 'checkmate':
                return jsonify(_end_game('checkmate', winner='bot'))
            if status == 'stalemate':
                return jsonify(_end_game('stalemate', winner=None))

            session['turn'] = 'player'
            response['status'] = 'success'
            response['in_check'] = side_in_check(session['board'], 'player', session['botWhite'], session['gameStates'])
        else:
            logging.error("Bot couldn't find a valid board.")
            response['status'] = 'error'

    response.update({
        'board': session['board'],
        'turn': session['turn'],
        'botWhite': session['botWhite'],
        'game_over': session['game_over'],
        'winner': session['winner']
    })
    return jsonify(response)

if __name__ == '__main__':
    app.run(debug=config.get("debugMode", False))
