# Chess
A Python chess game where you can play against a bot.

Game, bot, and website all developed by [starryxvii](https://github.com/starryxvii/) and [rosharma719](https://github.com/rosharma719/).
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