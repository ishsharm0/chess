from gameLogic import *
import random

def calculateMove(moves):
    piece = moves[random.randint(0, len(moves)-1)]
    move = moves[moves.index(piece)][random.randint(0, len(piece)-1)]
    return move

movesList = [
    ("P2", findSquare("b3")), 
    ("P3", findSquare("c4")),
    ("P8", findSquare("h3")),
    ("P7", findSquare("g3"))
 ]

def botMove(board, turn, gameStates, botWhite):
    moves = getAllTeamMoves(turn, board, botWhite)
    #print(moves[0][0])
    return calculateMove(moves)

