# consoleMode.py
import os, colorama
from colorama import Style, init, Fore
from bot import botMove, scoreMoveForEnemy
from gameLogic import *

init(autoreset=True)

#12345678 is bottom to top, abcdefgh is left to right

def startGame(botWhite): 
    board = newBoard(botWhite)
    turn = "bot" if botWhite else "player"
    oppositeTurn = "player" if turn == "bot" else "bot"
    pruneRate = 0.3  # Default pruning rate

    terminated = False    
    gameStates = []
    gameStates.append(board)

    while not terminated: 
        printBoard(board)
        print("\nTurn:", turn.upper(), "\n")

        if not isKingSafe(board, turn):
            if detectCheckmate(board, turn, botWhite, gameStates): 
                winner = "bot" if turn == 'player' else "player"
                print("Checkmate! Game over,", winner, "wins!")
                terminated = True
                break 
            print("Check! You must make a move to get out of check.")

        if detectStalemate(board, turn, botWhite, gameStates):
            print("Stalemate! Game over.")
            terminated = True
            break

        if turn == "bot":
            move = botMove(board, turn, gameStates, botWhite, pruneRate=pruneRate)  # Pass dynamic prune rate
            if move is not None and isKingSafe(move, turn):
                board = move
                gameStates.append(board)
                turn, oppositeTurn = oppositeTurn, turn  # Switch turns
        else:   
            playerInput = input("Enter the move in format 'P3 e5'. To castle, say 'castle'. \n\n").strip() 
            validity, piece, dest = inputValidate(playerInput, board, botWhite, turn, gameStates)
            if validity:  
                if validity == "castle":
                    board = castle(turn, board, botWhite)
                else:
                    testBoard = movePiece(piece, dest, list(board), gameStates, turn)
                    if isKingSafe(testBoard, turn):
                        board = testBoard

                        # **Evaluate the player's move skill using scoreMoveForEnemy**
                        skill_score = scoreMoveForEnemy(board, botWhite, gameStates)
                        print(f"Player move skill score: {skill_score}")

                        # Adjust the bot's prune rate based on the player's move skill
                        pruneRate = adjustPruneRate(skill_score)
                        print(f"Bot prune rate adjusted to: {pruneRate}")
                        
                        gameStates.append(board)
                        turn, oppositeTurn = oppositeTurn, turn  # Switch turns
                    else:
                        print("Invalid move. This move does not resolve the check.")
            else: 
                print("Invalid move. Try again!")

# Function to adjust the pruning rate based on player's move skill
def adjustPruneRate(skill_score):
    base_prune_rate = 0.3  # Default
    # Inverse relationship: Higher skill score = lower prune rate (deeper search)
    return max(0.1, min(1.0, base_prune_rate - (skill_score / 100)))

startGame(True)