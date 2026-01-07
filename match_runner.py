from __future__ import annotations

import argparse
import os
import selectors
import shlex
import subprocess
import sys
import time
from dataclasses import dataclass, field
from typing import List, Optional, TextIO, Tuple


def _uci_square(i: int) -> str:
    files = "abcdefgh"
    return f"{files[i % 8]}{8 - (i // 8)}"


def _format_moves_uci_as_pgn(moves: List[str]) -> str:
    out: List[str] = []
    move_no = 1
    for idx, mv in enumerate(moves):
        if idx % 2 == 0:
            out.append(f"{move_no}. {mv}")
            move_no += 1
        else:
            out.append(mv)
    return " ".join(out)


@dataclass
class UCIEngine:
    name: str
    cmd: List[str]
    proc: subprocess.Popen[bytes]
    log: Optional[TextIO] = None
    _selector: Optional[selectors.BaseSelector] = None
    _buf: bytearray = field(default_factory=bytearray)

    @staticmethod
    def start(name: str, cmd_str: str, cwd: Optional[str] = None, log_path: Optional[str] = None) -> "UCIEngine":
        cmd = shlex.split(cmd_str)
        log = open(log_path, "w", buffering=1) if log_path else None
        proc = subprocess.Popen(
            cmd,
            cwd=cwd,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=log or None,
            text=False,
            bufsize=0,
        )
        assert proc.stdin and proc.stdout
        engine = UCIEngine(name=name, cmd=cmd, proc=proc, log=log)
        try:
            sel = selectors.DefaultSelector()
            sel.register(proc.stdout, selectors.EVENT_READ)
            engine._selector = sel
        except Exception:
            engine._selector = None
        return engine

    def send(self, line: str):
        if self.proc.stdin is None:
            raise RuntimeError(f"{self.name}: stdin closed")
        if self.log:
            print(f">> {line}", file=self.log)
        self.proc.stdin.write((line + "\n").encode("utf-8"))
        self.proc.stdin.flush()

    def read_line(self, timeout_s: float = 10.0) -> str:
        if self.proc.stdout is None:
            raise RuntimeError(f"{self.name}: stdout closed")
        deadline = time.time() + timeout_s
        while True:
            nl = self._buf.find(b"\n")
            if nl != -1:
                raw = bytes(self._buf[:nl])
                del self._buf[: nl + 1]
                line = raw.decode("utf-8", errors="replace")
                if self.log:
                    print(f"<< {line}", file=self.log)
                return line

            if self.proc.poll() is not None:
                raise RuntimeError(f"{self.name} exited with {self.proc.returncode}")

            remaining = deadline - time.time()
            if remaining <= 0:
                raise TimeoutError(f"{self.name}: timed out waiting for output")

            if self._selector is not None:
                events = self._selector.select(timeout=remaining)
                if not events:
                    raise TimeoutError(f"{self.name}: timed out waiting for output")
                # Read some bytes from the underlying fd.
                data = os.read(self.proc.stdout.fileno(), 4096)
                if not data:
                    continue
                self._buf.extend(data)
                continue

            # Fallback: blocking read from stdout.
            data = self.proc.stdout.readline()
            if not data:
                continue
            self._buf.extend(data)

    def wait_for(self, needle: str, timeout_s: float = 10.0):
        t0 = time.time()
        while True:
            line = self.read_line(timeout_s=max(0.1, timeout_s - (time.time() - t0)))
            if line.strip() == needle:
                return

    def uci_handshake(self):
        self.send("uci")
        # Read until uciok
        while True:
            line = self.read_line(timeout_s=10.0)
            if line.strip() == "uciok":
                break
        self.send("isready")
        self.wait_for("readyok", timeout_s=10.0)

    def set_position(self, moves: List[str], fen: Optional[str] = None):
        if fen:
            self.send(f"position fen {fen} moves {' '.join(moves)}".rstrip())
        else:
            self.send(f"position startpos moves {' '.join(moves)}".rstrip())

    def go(self, depth: Optional[int], movetime_ms: Optional[int]) -> str:
        if movetime_ms is not None:
            self.send(f"go movetime {movetime_ms}")
        elif depth is not None:
            self.send(f"go depth {depth}")
        else:
            self.send("go depth 3")

        bestmove = None
        while True:
            line = self.read_line(timeout_s=120.0)
            if line.startswith("bestmove"):
                parts = line.split()
                bestmove = parts[1] if len(parts) > 1 else "0000"
                break
        return bestmove or "0000"

    def quit(self):
        try:
            self.send("quit")
        except Exception:
            pass
        try:
            self.proc.terminate()
        except Exception:
            pass
        try:
            self.proc.wait(timeout=2)
        except Exception:
            try:
                self.proc.kill()
            except Exception:
                pass
        if self._selector is not None:
            try:
                self._selector.close()
            except Exception:
                pass
        if self.log:
            self.log.close()


def play_game(
    white: UCIEngine,
    black: UCIEngine,
    depth: Optional[int],
    movetime_ms: Optional[int],
    white_movetime_ms: Optional[int],
    black_movetime_ms: Optional[int],
    max_plies: int,
    fen: Optional[str],
    out: TextIO,
) -> Tuple[List[str], str]:
    moves: List[str] = []
    result = "*"

    # Sync both
    white.send("ucinewgame")
    black.send("ucinewgame")
    white.send("isready")
    black.send("isready")
    white.wait_for("readyok")
    black.wait_for("readyok")

    for ply in range(max_plies):
        turn_engine = white if (ply % 2 == 0) else black
        other_engine = black if (ply % 2 == 0) else white

        turn_engine.set_position(moves, fen=fen)
        other_engine.set_position(moves, fen=fen)

        per_side_movetime = white_movetime_ms if (ply % 2 == 0) else black_movetime_ms
        effective_movetime = per_side_movetime if per_side_movetime is not None else movetime_ms

        try:
            mv = turn_engine.go(depth=depth, movetime_ms=effective_movetime)
        except TimeoutError as e:
            print(f"ERROR: {turn_engine.name} timed out waiting for bestmove ({e}).", file=sys.stderr, flush=True)
            print("Hint: re-run with --white-log/--black-log to capture engine stderr.", file=sys.stderr, flush=True)
            break
        except Exception as e:
            print(f"ERROR: {turn_engine.name} failed during go ({type(e).__name__}: {e}).", file=sys.stderr, flush=True)
            print("Hint: re-run with --white-log/--black-log to capture engine stderr.", file=sys.stderr, flush=True)
            raise
        if mv in ("0000", "(none)", "none"):
            # Treat as terminal.
            print(
                f"Terminal: {turn_engine.name} returned bestmove {mv} at ply {ply+1}.",
                file=sys.stderr,
                flush=True,
            )
            # Best-effort diagnosis (checkmate vs stalemate) using this repo's rules.
            try:
                from gameLogic import checkCheckmateOrStalemate  # type: ignore
                from uci import _parse_position, board_from_fen  # type: ignore

                if fen:
                    state = board_from_fen(fen)
                    toks = ["fen", *fen.split(), "moves", *moves]
                else:
                    state = board_from_fen("rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1")
                    toks = ["startpos", "moves", *moves]
                state = _parse_position(toks, state)
                terminal = checkCheckmateOrStalemate(state.board, state.turn, True, state.gameStates)
                if terminal in ("checkmate", "stalemate"):
                    side = "White" if state.turn == "bot" else "Black"
                    print(f"Terminal diagnosed: {terminal} (side to move: {side}).", file=sys.stderr, flush=True)
                    if terminal == "stalemate":
                        result = "1/2-1/2"
                    else:
                        result = "0-1" if state.turn == "bot" else "1-0"
                else:
                    print("Terminal diagnosed: unknown (engine reported no move).", file=sys.stderr, flush=True)
            except Exception:
                # Diagnosis is best-effort; ignore if helper imports aren't available.
                pass
            break

        moves.append(mv)
        side = "W" if (ply % 2 == 0) else "B"
        print(f"{ply+1:03d} {side} {turn_engine.name}: {mv}", file=out, flush=True)

    return moves, result


def write_pgn(path: str, white_name: str, black_name: str, moves: List[str], result: str):
    ts = time.strftime("%Y.%m.%d")
    with open(path, "w", encoding="utf-8") as f:
        f.write(f'[Event "UCI Match"]\n')
        f.write(f'[Site "local"]\n')
        f.write(f'[Date "{ts}"]\n')
        f.write(f'[Round "1"]\n')
        f.write(f'[White "{white_name}"]\n')
        f.write(f'[Black "{black_name}"]\n')
        f.write(f'[Result "{result}"]\n\n')
        f.write(_format_moves_uci_as_pgn(moves))
        f.write(f" {result}\n")


def main() -> int:
    ap = argparse.ArgumentParser(description="Run a simple OurBot vs Stockfish match over UCI.")
    ap.add_argument("--white", default=f"{sys.executable} uci.py", help='White engine command (default: "python uci.py")')
    ap.add_argument("--black", default="stockfish", help='Black engine command (default: "stockfish")')
    ap.add_argument("--movetime-ms", type=int, default=1000, help="Time per move in ms (default: 1000)")
    ap.add_argument("--white-movetime-ms", type=int, default=None, help="White time per move in ms (overrides movetime-ms)")
    ap.add_argument("--black-movetime-ms", type=int, default=None, help="Black time per move in ms (overrides movetime-ms)")
    ap.add_argument("--depth", type=int, default=None, help="Fixed depth (used only if movetime-ms is not set)")
    ap.add_argument("--max-plies", type=int, default=200, help="Max half-moves before stopping (default: 200)")
    ap.add_argument("--fen", type=str, default=None, help="Start from a FEN position instead of startpos")
    ap.add_argument("--pgnout", type=str, default=None, help="Write a simple PGN-like record (UCI moves) to file")
    ap.add_argument("--white-log", type=str, default=None, help="Redirect white stderr to file")
    ap.add_argument("--black-log", type=str, default=None, help="Redirect black stderr to file")
    args = ap.parse_args()

    white = UCIEngine.start("White", args.white, cwd=None, log_path=args.white_log)
    black = UCIEngine.start("Black", args.black, cwd=None, log_path=args.black_log)
    try:
        white.uci_handshake()
        black.uci_handshake()
        moves, result = play_game(
            white=white,
            black=black,
            depth=args.depth,
            movetime_ms=args.movetime_ms,
            white_movetime_ms=args.white_movetime_ms,
            black_movetime_ms=args.black_movetime_ms,
            max_plies=args.max_plies,
            fen=args.fen,
            out=sys.stdout,
        )
        if args.pgnout:
            write_pgn(args.pgnout, white.name, black.name, moves, result)
    except Exception:
        if args.white_log or args.black_log:
            print(
                f"Engine logs: white={args.white_log or '(none)'} black={args.black_log or '(none)'}",
                file=sys.stderr,
                flush=True,
            )
        else:
            print("Hint: re-run with --white-log/--black-log to capture engine stderr.", file=sys.stderr, flush=True)
        raise
    finally:
        white.quit()
        black.quit()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
