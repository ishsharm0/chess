import os, colorama
from colorama import Style, init, Fore
from bot import botMove
from gameLogic import *

init(autoreset=True)

#12345678 is bottom to top, abcdefgh is left to right

def startGame(botWhite): 
    # for every turn set the bot's local gameState to the board (to feed in moves)
    # gets the bots moves which will also be a local variable

    board = newBoard(botWhite)
    turn = "bot" if botWhite else "player"
    oppositeTurn = "player" if turn == "bot" else "bot"

    # Starts game loop
    terminated = False    
    gameStates = []
    gameStates.append(board)

    while not terminated: 

        while True: # Checking if move is valid

            # Printing board and turn information
            printBoard(board)
            print("\nTurn:", turn.upper(), "\n")

            # If the king is in check, notify the player
            if not isKingSafe(board, turn):
                
                # Detecting checkmate 
                if detectCheckmate(board, turn, botWhite, gameStates): 
                    winner = "bot" if turn == 'player' else "player"
                    print("Checkmate! Game over,", winner, "wins!")
                    terminated = True
                    break 
                # Else, print below: 
                print("Check! You must make a move to get out of check.")
                

            # Stalemate checker
            if detectStalemate(board, turn, botWhite, gameStates):
                print("Stalemate! Game over.")
                terminated = True
                break

            # Player input and validity checking
            if turn == "bot":
                move = botMove(board, turn, gameStates, botWhite)
                if isKingSafe(move, turn):
                        board = move
                        break
                else:
                    print("Invalid move. This move does not resolve the check.")
            else:   
                playerInput = input("Enter the move in format 'P3 e5'. To castle, say 'castle'. \n\n").strip() 
                
                if playerInput.lower() == "quit":
                    terminated = True
                    break

                validity, piece, dest = inputValidate(playerInput, board, botWhite, turn, gameStates)
                if validity:  
                    # Check if move results in check
                    testBoard = movePiece(piece, dest, list(board), gameStates, turn)
                    if isKingSafe(testBoard, turn):
                        board = testBoard
                        break
                    else:
                        print("Invalid move. This move does not resolve the check.")
                else: 
                    print("Invalid move. Try again!")
        
        # Update game state after a successful move
        gameStates.append(board)
        
        # Switch turns
        turn, oppositeTurn = oppositeTurn, turn


startGame(True)