from __future__ import annotations

import sys
import time
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple

from bot import botMove
from gameLogic import findSquare, isKingSafe, movePiece, moveValidate, promotePawn


# UCI wrapper assumptions:
# - We run standard chess orientation (white pieces start on rank 1, king on e1, etc.).
# - In this project, "bot" == uppercase pieces. We'll map:
#     - White-to-move => turn="bot"
#     - Black-to-move => turn="player"
# - `botWhite=True` matches the standard king/queen placement in gameLogic.newBoard(True).
BOT_WHITE = True


Board = Tuple[Optional[str], ...]


@dataclass
class EngineState:
    board: Board
    gameStates: List[Board]
    turn: str  # "bot" for white, "player" for black


def _turn_from_fen(stm: str) -> str:
    return "bot" if stm == "w" else "player"

def _opponent(turn: str) -> str:
    return "player" if turn == "bot" else "bot"


def _fresh_piece_names() -> Dict[str, int]:
    return {k: 0 for k in ["P", "N", "B", "R", "Q", "p", "n", "b", "r", "q"]}


def _named_piece(letter: str, counts: Dict[str, int]) -> str:
    """
    Convert a single-letter FEN piece to this engine's unique-name format.
    Kings must be exactly K/k for isKingSafe() and other logic.
    """
    if letter in ("K", "k"):
        return letter
    counts[letter] = counts.get(letter, 0) + 1
    n = counts[letter]

    # Prefer traditional labels for first pieces (R1/R2 etc.).
    base = letter
    if base.upper() == "Q" and n == 1:
        return "Q" if letter.isupper() else "q"
    return f"{base}{n}"


def board_from_fen(fen: str) -> EngineState:
    parts = fen.strip().split()
    if len(parts) < 2:
        raise ValueError("FEN must include board and side-to-move")
    board_part, stm = parts[0], parts[1]
    rows = board_part.split("/")
    if len(rows) != 8:
        raise ValueError("FEN board must have 8 ranks")

    counts = _fresh_piece_names()
    squares: List[Optional[str]] = []
    for r in rows:
        for ch in r:
            if ch.isdigit():
                squares.extend([None] * int(ch))
            else:
                squares.append(_named_piece(ch, counts))
    if len(squares) != 64:
        raise ValueError(f"FEN expanded to {len(squares)} squares, expected 64")

    board = tuple(squares)
    turn = _turn_from_fen(stm)
    return EngineState(board=board, gameStates=[board], turn=turn)


def _idx_to_uci(i: int) -> str:
    files = "abcdefgh"
    file = files[i % 8]
    rank = 8 - (i // 8)
    return f"{file}{rank}"


def _infer_move(prev: Board, nxt: Board, turn: str) -> Optional[str]:
    """
    Infer a UCI move string (e2e4, e7e8q, e1g1, etc.) from board diffs.
    """
    diffs = [i for i in range(64) if prev[i] != nxt[i]]
    if not diffs:
        return None

    # Castling: rook+king move => 4 diffs. Encode as king move.
    if len(diffs) >= 4:
        if turn == "bot":  # white
            # e1g1 or e1c1
            if prev[60] and prev[60][0] == "K" and nxt[62] and nxt[62][0] == "K":
                return "e1g1"
            if prev[60] and prev[60][0] == "K" and nxt[58] and nxt[58][0] == "K":
                return "e1c1"
        else:  # black
            if prev[4] and prev[4][0] == "k" and nxt[6] and nxt[6][0] == "k":
                return "e8g8"
            if prev[4] and prev[4][0] == "k" and nxt[2] and nxt[2][0] == "k":
                return "e8c8"

    # Normal move/promotion: usually 2 diffs; en passant: 3 diffs.
    from_candidates = [i for i in diffs if prev[i] is not None and nxt[i] is None]
    to_candidates = [i for i in diffs if nxt[i] is not None and (prev[i] is None or prev[i] != nxt[i])]
    if len(from_candidates) != 1 or len(to_candidates) != 1:
        return None

    from_sq = from_candidates[0]
    to_sq = to_candidates[0]

    uci = f"{_idx_to_uci(from_sq)}{_idx_to_uci(to_sq)}"

    moved_after = nxt[to_sq]
    moved_before = prev[from_sq]
    if moved_after and moved_before and moved_before[0].lower() == "p" and moved_after[0].lower() != "p":
        # Promotion: uci wants lowercase piece letter.
        uci += moved_after[0].lower()
    return uci


def _apply_uci_move(state: EngineState, uci: str) -> EngineState:
    uci = uci.strip()
    if len(uci) < 4:
        return state
    frm = uci[0:2]
    to = uci[2:4]
    promo = uci[4:5].lower() if len(uci) >= 5 else None

    from_idx = findSquare(frm)
    to_idx = findSquare(to)
    if from_idx is False or to_idx is False:
        return state

    piece = state.board[from_idx]
    if piece is None:
        return state

    # Castling (UCI uses king move like e1g1). The core engine doesn't model castling as a normal
    # king move, so handle it explicitly for position syncing.
    if piece[0] in ("K", "k") and frm in ("e1", "e8") and to in ("g1", "c1", "g8", "c8"):
        b = list(state.board)
        mover = state.turn
        if mover == "bot" and frm == "e1" and piece[0] == "K":
            if to == "g1":  # king side: rook h1 (R2) to f1
                if b[61] is not None or b[62] is not None or b[63] != "R2":
                    return state
                if not isKingSafe(tuple(b), mover):
                    return state
                t = b[:]
                t[60] = None
                t[61] = "K"
                if not isKingSafe(tuple(t), mover):
                    return state
                t[61] = None
                t[62] = "K"
                if not isKingSafe(tuple(t), mover):
                    return state
                b[60] = None
                b[62] = "K"
                b[63] = None
                b[61] = "R2"
            elif to == "c1":  # queen side: rook a1 (R1) to d1
                if b[59] is not None or b[58] is not None or b[57] is not None or b[56] != "R1":
                    return state
                if not isKingSafe(tuple(b), mover):
                    return state
                t = b[:]
                t[60] = None
                t[59] = "K"
                if not isKingSafe(tuple(t), mover):
                    return state
                t[59] = None
                t[58] = "K"
                if not isKingSafe(tuple(t), mover):
                    return state
                b[60] = None
                b[58] = "K"
                b[56] = None
                b[59] = "R1"
            else:
                return state
        elif mover == "player" and frm == "e8" and piece[0] == "k":
            if to == "g8":  # king side: rook h8 (r2) to f8
                if b[5] is not None or b[6] is not None or b[7] != "r2":
                    return state
                if not isKingSafe(tuple(b), mover):
                    return state
                t = b[:]
                t[4] = None
                t[5] = "k"
                if not isKingSafe(tuple(t), mover):
                    return state
                t[5] = None
                t[6] = "k"
                if not isKingSafe(tuple(t), mover):
                    return state
                b[4] = None
                b[6] = "k"
                b[7] = None
                b[5] = "r2"
            elif to == "c8":  # queen side: rook a8 (r1) to d8
                if b[3] is not None or b[2] is not None or b[1] is not None or b[0] != "r1":
                    return state
                if not isKingSafe(tuple(b), mover):
                    return state
                t = b[:]
                t[4] = None
                t[3] = "k"
                if not isKingSafe(tuple(t), mover):
                    return state
                t[3] = None
                t[2] = "k"
                if not isKingSafe(tuple(t), mover):
                    return state
                b[4] = None
                b[2] = "k"
                b[0] = None
                b[3] = "r1"
            else:
                return state
        else:
            return state

        new_board = tuple(b)
        gs = state.gameStates + [new_board]
        gs = gs[-2:]
        return EngineState(board=new_board, gameStates=gs, turn=_opponent(state.turn))

    if not moveValidate(piece, to_idx, state.turn, state.board, BOT_WHITE, state.gameStates):
        return state

    new_board = movePiece(piece, to_idx, state.board, state.gameStates, state.turn)
    if not isKingSafe(new_board, state.turn):
        return state

    # Promotion (engine uses promotePawn which assigns a new unique name)
    if promo and piece[0].lower() == "p":
        name = {"q": "QUEEN", "r": "ROOK", "b": "BISHOP", "n": "KNIGHT"}.get(promo)
        if name:
            new_board = promotePawn(piece, to_idx, name, new_board, state.turn)

    gs = state.gameStates + [new_board]
    gs = gs[-2:]
    return EngineState(board=new_board, gameStates=gs, turn=("player" if state.turn == "bot" else "bot"))


def _parse_position(tokens: List[str], state: EngineState) -> EngineState:
    if not tokens:
        return state
    if tokens[0] == "startpos":
        # Standard start FEN
        state = board_from_fen("rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1")
        tokens = tokens[1:]
    elif tokens[0] == "fen":
        # position fen <fen...> [moves ...]
        if "moves" in tokens:
            mi = tokens.index("moves")
            fen = " ".join(tokens[1:mi])
            rest = tokens[mi + 1 :]
        else:
            fen = " ".join(tokens[1:])
            rest = []
        state = board_from_fen(fen)
        tokens = ["moves"] + rest if rest else []

    if tokens and tokens[0] == "moves":
        for mv in tokens[1:]:
            state = _apply_uci_move(state, mv)
    return state


def main() -> int:
    state = board_from_fen("rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1")

    try:
        while True:
            line = sys.stdin.readline()
            if not line:
                break
            line = line.strip()
            if not line:
                continue

            parts = line.split()
            cmd = parts[0]

            if cmd == "uci":
                print("id name chess-python-bot")
                print("id author local")
                print("uciok")
                sys.stdout.flush()
                continue

            if cmd == "isready":
                print("readyok")
                sys.stdout.flush()
                continue

            if cmd == "ucinewgame":
                state = board_from_fen("rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1")
                continue

            if cmd == "position":
                state = _parse_position(parts[1:], state)
                continue

            if cmd == "go":
                # Support: go depth N | go movetime MS | go wtime/btime/winc/binc/movestogo
                depth = 3
                movetime_ms: Optional[int] = None
                wtime_ms: Optional[int] = None
                btime_ms: Optional[int] = None
                winc_ms: int = 0
                binc_ms: int = 0
                movestogo: Optional[int] = None

                def _get_int(key: str) -> Optional[int]:
                    if key in parts:
                        i = parts.index(key)
                        if i + 1 < len(parts):
                            try:
                                return int(parts[i + 1])
                            except Exception:
                                return None
                    return None

                depth_v = _get_int("depth")
                if depth_v is not None:
                    depth = depth_v
                movetime_ms = _get_int("movetime")
                wtime_ms = _get_int("wtime")
                btime_ms = _get_int("btime")
                winc_ms = _get_int("winc") or 0
                binc_ms = _get_int("binc") or 0
                movestogo = _get_int("movestogo")

                # Time budgeting: prefer explicit movetime. Otherwise, derive a safe budget from remaining time.
                time_limit_s: Optional[float]
                if movetime_ms is not None:
                    time_limit_s = max(0.01, movetime_ms / 1000.0 * 0.95)
                elif wtime_ms is not None and btime_ms is not None:
                    if state.turn == "bot":  # white
                        remain_ms = wtime_ms
                        inc_ms = winc_ms
                    else:
                        remain_ms = btime_ms
                        inc_ms = binc_ms
                    # Spend a small fraction of remaining time; keep margin to avoid flagging.
                    mtg = movestogo if movestogo and movestogo > 0 else 30
                    base = remain_ms / 1000.0
                    inc = inc_ms / 1000.0
                    time_limit_s = max(0.01, min(base / mtg + 0.8 * inc, max(0.05, base * 0.2)))
                else:
                    time_limit_s = None

                start = time.perf_counter()
                best_board = botMove(
                    state.board,
                    state.turn,
                    state.gameStates,
                    BOT_WHITE,
                    depth=depth,
                    time_limit_s=time_limit_s,
                )
                elapsed = time.perf_counter() - start

                if best_board is None:
                    print("bestmove 0000")
                    sys.stdout.flush()
                    continue

                uci_move = _infer_move(state.board, best_board, state.turn) or "0000"

                print(f"info string time={elapsed:.3f}s depth={depth}")
                print(f"bestmove {uci_move}")
                sys.stdout.flush()
                continue

            if cmd == "stop":
                # This engine is synchronous; we respect time limits via `go` parsing above.
                continue

            if cmd == "quit":
                break

            continue
    except KeyboardInterrupt:
        # Exit quietly if the controller aborts the match.
        return 0

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
