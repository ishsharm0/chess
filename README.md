# Chess
A Python chess game where you can play against a bot that matches your skill level adaptively.

Game, bot, and website all developed by [ishsharm0](https://github.com/ishsharm0/) and [rosharma719](https://github.com/rosharma719/).
## Setup + Running Locally (Windows)

Prerequisites:
- [Python 3.8+](https://www.python.org/downloads/)
- [Git](https://git-scm.com/download/)

Run these commands in a directory of your choice:

```bat
git clone https://github.com/starryxvii/chess.git
cd chess
pip install -r requirements.txt
echo SECRET_KEY=MySecretKey > .env
python app.py
```

To play the game in your console, simply run `python consoleMode.py` instead of `python app.py`.

## Engine Testing (Optional)

This repo includes a minimal UCI wrapper (`uci.py`) so you can play games against other engines like Stockfish.

- Run a direct OurBot vs Stockfish match (prints moves live):
  - `python match_runner.py --black stockfish --movetime-ms 30000 --pgnout matches.pgn`
- Run move-generation correctness checks (perft):
  - `python perft.py startpos 4`
