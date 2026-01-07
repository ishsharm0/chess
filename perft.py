from __future__ import annotations

import argparse
from dataclasses import dataclass
from typing import Dict, Iterable, Iterator, List, Optional, Set, Tuple

from gameLogic import isKingSafe


Board = Tuple[Optional[str], ...]  # 64-length tuple; pieces are single letters like "P"/"k"


@dataclass(frozen=True)
class State:
    board: Board
    turn: str  # "bot" (white) or "player" (black)
    castling: frozenset[str]  # any of {"K","Q","k","q"}
    ep: Optional[int] = None  # en-passant target square index (0..63) or None


@dataclass(frozen=True)
class Move:
    to_state: State
    capture: bool = False
    en_passant: bool = False
    castle: bool = False
    promotion: bool = False
    gives_check: bool = False


def _opponent(turn: str) -> str:
    return "player" if turn == "bot" else "bot"


def _is_white(turn: str) -> bool:
    return turn == "bot"


def _piece_is_side(p: str, turn: str) -> bool:
    return p.isupper() if _is_white(turn) else p.islower()


def _on_board(i: int) -> bool:
    return 0 <= i < 64


def _valid_step(prev: int, curr: int, step: int) -> bool:
    if not _on_board(prev) or not _on_board(curr):
        return False
    dr = (curr // 8) - (prev // 8)
    dc = (curr % 8) - (prev % 8)
    if step == 1:
        return dr == 0 and dc == 1
    if step == -1:
        return dr == 0 and dc == -1
    if step == 8:
        return dr == 1 and dc == 0
    if step == -8:
        return dr == -1 and dc == 0
    if step == 9:
        return dr == 1 and dc == 1
    if step == -9:
        return dr == -1 and dc == -1
    if step == 7:
        return dr == 1 and dc == -1
    if step == -7:
        return dr == -1 and dc == 1
    return False


def _find_king(board: Board, turn: str) -> int:
    k = "K" if turn == "bot" else "k"
    try:
        return board.index(k)
    except ValueError:
        return -1


def _is_legal_after(board: Board, turn: str) -> bool:
    # A move is legal if it doesn't leave the mover's king in check.
    return isKingSafe(board, turn)


def _gives_check(board_after: Board, mover: str) -> bool:
    return not isKingSafe(board_after, _opponent(mover))


def _castle_rights_after_move(castling: Set[str], from_sq: int, to_sq: int, moved: str, captured: Optional[str]) -> Set[str]:
    rights = set(castling)
    # Moving a king removes only that side's castling rights.
    if moved == "K":
        rights.discard("K")
        rights.discard("Q")
    elif moved == "k":
        rights.discard("k")
        rights.discard("q")
    # Move rook off its home square removes that side's right.
    if moved == "R":
        if from_sq == 63:
            rights.discard("K")
        elif from_sq == 56:
            rights.discard("Q")
    if moved == "r":
        if from_sq == 7:
            rights.discard("k")
        elif from_sq == 0:
            rights.discard("q")
    # Capturing a rook on its home square removes opponent right.
    if captured == "R":
        if to_sq == 63:
            rights.discard("K")
        elif to_sq == 56:
            rights.discard("Q")
    if captured == "r":
        if to_sq == 7:
            rights.discard("k")
        elif to_sq == 0:
            rights.discard("q")
    return rights


def _apply_move_base(state: State, from_sq: int, to_sq: int, promo: Optional[str], en_passant: bool, castle: bool) -> Optional[Move]:
    board = list(state.board)
    mover = state.turn
    piece = board[from_sq]
    if piece is None or not _piece_is_side(piece, mover):
        return None

    captured = board[to_sq]
    is_capture = captured is not None
    ep_capture = False
    if en_passant:
        # capture pawn behind the target square
        if state.ep is None or to_sq != state.ep or piece.lower() != "p":
            return None
        # Captured pawn is on the square "behind" the EP target.
        # White (bot) pawn moves up (-8), so the captured pawn is one rank down (+8).
        # Black (player) pawn moves down (+8), so the captured pawn is one rank up (-8).
        cap_sq = to_sq + (8 if mover == "bot" else -8)
        if not _on_board(cap_sq):
            return None
        captured = board[cap_sq]
        if captured is None or captured.lower() != "p":
            return None
        board[cap_sq] = None
        is_capture = True
        ep_capture = True

    # Basic move
    board[to_sq] = piece
    board[from_sq] = None

    # Castling rook move
    if castle:
        if mover == "bot":
            # e1g1 / e1c1
            if from_sq != 60:
                return None
            if to_sq == 62:  # king side
                if board[63] != "R":
                    return None
                board[63] = None
                board[61] = "R"
            elif to_sq == 58:  # queen side
                if board[56] != "R":
                    return None
                board[56] = None
                board[59] = "R"
            else:
                return None
        else:
            # e8g8 / e8c8
            if from_sq != 4:
                return None
            if to_sq == 6:
                if board[7] != "r":
                    return None
                board[7] = None
                board[5] = "r"
            elif to_sq == 2:
                if board[0] != "r":
                    return None
                board[0] = None
                board[3] = "r"
            else:
                return None

    # Promotion
    promoted = False
    if promo is not None:
        if piece.lower() != "p":
            return None
        rank = to_sq // 8
        if mover == "bot" and rank != 0:
            return None
        if mover == "player" and rank != 7:
            return None
        board[to_sq] = promo if mover == "bot" else promo.lower()
        promoted = True

    # Update en-passant square
    new_ep = None
    if piece.lower() == "p" and abs(to_sq - from_sq) == 16:
        new_ep = (from_sq + to_sq) // 2

    # Update castling rights
    rights = _castle_rights_after_move(set(state.castling), from_sq, to_sq, piece, captured)

    next_turn = _opponent(mover)
    board_t = tuple(board)
    if not _is_legal_after(board_t, mover):
        return None

    gives_check = _gives_check(board_t, mover)
    return Move(
        to_state=State(board=board_t, turn=next_turn, castling=frozenset(rights), ep=new_ep),
        capture=is_capture,
        en_passant=ep_capture,
        castle=castle,
        promotion=promoted,
        gives_check=gives_check,
    )


def _gen_slider(state: State, from_sq: int, steps: Iterable[int]) -> Iterator[Move]:
    board = state.board
    mover = state.turn
    for step in steps:
        i = from_sq + step
        prev = from_sq
        while _on_board(i) and _valid_step(prev, i, step):
            p = board[i]
            if p is None:
                mv = _apply_move_base(state, from_sq, i, promo=None, en_passant=False, castle=False)
                if mv:
                    yield mv
            else:
                if not _piece_is_side(p, mover):
                    mv = _apply_move_base(state, from_sq, i, promo=None, en_passant=False, castle=False)
                    if mv:
                        yield mv
                break
            prev = i
            i += step


_KNIGHT_OFFS = (15, 17, -15, -17, 10, 6, -10, -6)


def _gen_knight(state: State, from_sq: int) -> Iterator[Move]:
    board = state.board
    mover = state.turn
    sr, sc = from_sq // 8, from_sq % 8
    for off in _KNIGHT_OFFS:
        to_sq = from_sq + off
        if not _on_board(to_sq):
            continue
        dr = abs((to_sq // 8) - sr)
        dc = abs((to_sq % 8) - sc)
        if (dr, dc) not in {(1, 2), (2, 1)}:
            continue
        p = board[to_sq]
        if p is None or not _piece_is_side(p, mover):
            mv = _apply_move_base(state, from_sq, to_sq, promo=None, en_passant=False, castle=False)
            if mv:
                yield mv


def _gen_king(state: State, from_sq: int) -> Iterator[Move]:
    board = state.board
    mover = state.turn
    for step in (-1, 1, -8, 8, -9, -7, 9, 7):
        to_sq = from_sq + step
        if not _on_board(to_sq) or not _valid_step(from_sq, to_sq, step):
            continue
        p = board[to_sq]
        if p is None or not _piece_is_side(p, mover):
            mv = _apply_move_base(state, from_sq, to_sq, promo=None, en_passant=False, castle=False)
            if mv:
                yield mv

    # Castling (only if king on home square)
    if mover == "bot" and from_sq == 60:
        if "K" in state.castling:
            if board[61] is None and board[62] is None and board[63] == "R":
                # Squares must not be attacked; test with king moved
                if isKingSafe(state.board, mover):
                    temp = list(state.board)
                    temp[60] = None
                    temp[61] = "K"
                    if isKingSafe(tuple(temp), mover):
                        temp[61] = None
                        temp[62] = "K"
                        if isKingSafe(tuple(temp), mover):
                            mv = _apply_move_base(state, 60, 62, promo=None, en_passant=False, castle=True)
                            if mv:
                                yield mv
        if "Q" in state.castling:
            if board[59] is None and board[58] is None and board[57] is None and board[56] == "R":
                if isKingSafe(state.board, mover):
                    temp = list(state.board)
                    temp[60] = None
                    temp[59] = "K"
                    if isKingSafe(tuple(temp), mover):
                        temp[59] = None
                        temp[58] = "K"
                        if isKingSafe(tuple(temp), mover):
                            mv = _apply_move_base(state, 60, 58, promo=None, en_passant=False, castle=True)
                            if mv:
                                yield mv
    if mover == "player" and from_sq == 4:
        if "k" in state.castling:
            if board[5] is None and board[6] is None and board[7] == "r":
                if isKingSafe(state.board, mover):
                    temp = list(state.board)
                    temp[4] = None
                    temp[5] = "k"
                    if isKingSafe(tuple(temp), mover):
                        temp[5] = None
                        temp[6] = "k"
                        if isKingSafe(tuple(temp), mover):
                            mv = _apply_move_base(state, 4, 6, promo=None, en_passant=False, castle=True)
                            if mv:
                                yield mv
        if "q" in state.castling:
            if board[3] is None and board[2] is None and board[1] is None and board[0] == "r":
                if isKingSafe(state.board, mover):
                    temp = list(state.board)
                    temp[4] = None
                    temp[3] = "k"
                    if isKingSafe(tuple(temp), mover):
                        temp[3] = None
                        temp[2] = "k"
                        if isKingSafe(tuple(temp), mover):
                            mv = _apply_move_base(state, 4, 2, promo=None, en_passant=False, castle=True)
                            if mv:
                                yield mv


def _gen_pawn(state: State, from_sq: int) -> Iterator[Move]:
    board = state.board
    mover = state.turn
    forward = -8 if mover == "bot" else 8
    start_rank = 6 if mover == "bot" else 1
    promo_rank = 0 if mover == "bot" else 7

    one = from_sq + forward
    if _on_board(one) and _valid_step(from_sq, one, forward) and board[one] is None:
        if (one // 8) == promo_rank:
            for p in ("Q", "R", "B", "N"):
                mv = _apply_move_base(state, from_sq, one, promo=p, en_passant=False, castle=False)
                if mv:
                    yield mv
        else:
            mv = _apply_move_base(state, from_sq, one, promo=None, en_passant=False, castle=False)
            if mv:
                yield mv

        two = from_sq + 2 * forward
        if (from_sq // 8) == start_rank and _on_board(two) and board[two] is None:
            mv = _apply_move_base(state, from_sq, two, promo=None, en_passant=False, castle=False)
            if mv:
                yield mv

    # captures + en passant
    for step in (forward - 1, forward + 1):
        to_sq = from_sq + step
        if not _on_board(to_sq) or not _valid_step(from_sq, to_sq, step):
            continue
        target = board[to_sq]
        if target is not None and not _piece_is_side(target, mover):
            if (to_sq // 8) == promo_rank:
                for p in ("Q", "R", "B", "N"):
                    mv = _apply_move_base(state, from_sq, to_sq, promo=p, en_passant=False, castle=False)
                    if mv:
                        yield mv
            else:
                mv = _apply_move_base(state, from_sq, to_sq, promo=None, en_passant=False, castle=False)
                if mv:
                    yield mv
            continue
        if state.ep is not None and to_sq == state.ep:
            mv = _apply_move_base(state, from_sq, to_sq, promo=None, en_passant=True, castle=False)
            if mv:
                yield mv


def legal_moves(state: State) -> Iterator[Move]:
    b = state.board
    for i, p in enumerate(b):
        if p is None:
            continue
        if not _piece_is_side(p, state.turn):
            continue
        t = p.lower()
        if t == "p":
            yield from _gen_pawn(state, i)
        elif t == "n":
            yield from _gen_knight(state, i)
        elif t == "b":
            yield from _gen_slider(state, i, (7, -7, 9, -9))
        elif t == "r":
            yield from _gen_slider(state, i, (1, -1, 8, -8))
        elif t == "q":
            yield from _gen_slider(state, i, (1, -1, 8, -8, 7, -7, 9, -9))
        elif t == "k":
            yield from _gen_king(state, i)


def perft(state: State, depth: int) -> Dict[str, int]:
    """
    Perft with basic stats, counted at the final ply (standard convention).
    """
    if depth <= 0:
        return {"nodes": 1, "captures": 0, "en_passant": 0, "castles": 0, "promotions": 0, "checks": 0}

    if depth == 1:
        out = {"nodes": 0, "captures": 0, "en_passant": 0, "castles": 0, "promotions": 0, "checks": 0}
        for mv in legal_moves(state):
            out["nodes"] += 1
            out["captures"] += 1 if mv.capture else 0
            out["en_passant"] += 1 if mv.en_passant else 0
            out["castles"] += 1 if mv.castle else 0
            out["promotions"] += 1 if mv.promotion else 0
            out["checks"] += 1 if mv.gives_check else 0
        return out

    out = {"nodes": 0, "captures": 0, "en_passant": 0, "castles": 0, "promotions": 0, "checks": 0}
    for mv in legal_moves(state):
        child = perft(mv.to_state, depth - 1)
        for k, v in child.items():
            out[k] += v
    return out


def _fen_piece(c: str) -> str:
    # Use single-letter pieces to avoid relying on unique IDs; isKingSafe only cares about case and first char.
    return c


def from_fen(fen: str) -> State:
    parts = fen.strip().split()
    if len(parts) < 4:
        raise ValueError("FEN must have at least 4 fields: board turn castling ep")

    board_part, stm, castling, ep = parts[:4]
    rows = board_part.split("/")
    if len(rows) != 8:
        raise ValueError("FEN board must have 8 ranks")

    board: List[Optional[str]] = []
    for r in rows:
        for ch in r:
            if ch.isdigit():
                board.extend([None] * int(ch))
            else:
                board.append(_fen_piece(ch))
    if len(board) != 64:
        raise ValueError(f"FEN expanded to {len(board)} squares, expected 64")

    # Convert to our index convention (rank8 at indices 0..7 already matches FEN parse order).
    board_t: Board = tuple(board)
    turn = "bot" if stm == "w" else "player"
    rights: Set[str] = set() if castling == "-" else set(castling)
    ep_sq = None
    if ep != "-" and len(ep) == 2:
        file = ord(ep[0].lower()) - ord("a")
        rank = int(ep[1]) - 1  # 0-based from rank1
        ep_sq = (7 - rank) * 8 + file
    return State(board=board_t, turn=turn, castling=frozenset(rights), ep=ep_sq)


STANDARD = {
    # Standard chess start position
    "startpos": ("rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1", {1: 20, 2: 400, 3: 8902, 4: 197281}),
    # Kiwipete (classic perft)
    "kiwipete": ("r3k2r/p1ppqpb1/bn2pnp1/3PN3/1p2P3/2N2Q1p/PPPBBPPP/R3K2R w KQkq - 0 1", {1: 48, 2: 2039, 3: 97862, 4: 4085603}),
}


def main() -> int:
    ap = argparse.ArgumentParser(description="Perft correctness benchmark for this chess engine.")
    ap.add_argument("position", help="Named position (startpos/kiwipete) or a FEN string")
    ap.add_argument("depth", type=int, help="Depth to run")
    ap.add_argument("--stats", action="store_true", help="Print captures/ep/castles/promotions/checks at final ply")
    args = ap.parse_args()

    if args.position in STANDARD:
        fen, expected = STANDARD[args.position]
        state = from_fen(fen)
    else:
        expected = None
        state = from_fen(args.position)

    res = perft(state, args.depth)
    print(f"nodes: {res['nodes']}")
    if args.stats:
        print(f"captures: {res['captures']}")
        print(f"en-passant: {res['en_passant']}")
        print(f"castles: {res['castles']}")
        print(f"promotions: {res['promotions']}")
        print(f"checks: {res['checks']}")

    if expected is not None and args.depth in expected:
        exp = expected[args.depth]
        ok = "OK" if res["nodes"] == exp else f"FAIL expected {exp}"
        print(ok)
        return 0 if res["nodes"] == exp else 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
