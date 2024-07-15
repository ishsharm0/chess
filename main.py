
def newBoard(): 
    board = (
        'r1', 'n1', 'b1', 'q', 'k', 'b2', 'n2', 'r2',  # player's back rank
        'p1', 'p2', 'p3', 'p4', 'p5', 'p6', 'p7', 'p8',  # player's pawn rank
        None, None, None, None, None, None, None, None,  # Empty rank
        None, None, None, None, None, None, None, None,  # Empty rank
        None, None, None, None, None, None, None, None,  # Empty rank
        None, None, None, None, None, None, None, None,  # Empty rank
        'P1', 'P2', 'P3', 'P4', 'P5', 'P6', 'P7', 'P8',  # bot's pawn rank
        'R1', 'N1', 'B1', 'Q', 'K', 'B2', 'N2', 'R2'   # bot's back rank
    )
    return board

#12345678 is bottom to top, abcdefgh is left to right

def findIndex(square):
    colIndex = ord(square[0]) - ord('a')
    rowIndex = int(square[1]) - 1
    index = (7 - rowIndex) * 8 + colIndex
    
    return index

def findPiece(piece, board):
    return board.index(piece)

def movePiece(piece, dest, board):
    currLoc = findPiece(piece, board)
    destLoc = findIndex(dest)
    board = list(board)

    board[currLoc] = None
    board[destLoc] = piece

    return tuple(board)

def moveValidate(piece, dest, turn, board):
    # Err handling
    validPiece = piece in board
    validDest = dest[0] in ['a','b','c','d','e','f','g','h'] and int(dest[1]) in [1,2,3,4,5,6,7,8]
    validTurn = (piece[0].islower() and turn == 'player') or (piece[0].isupper() and turn == 'bot') # In the game loop we will check return output
    
    if (validPiece and validDest and validTurn):
        pass
    else:
        return "Error handling"
    
     # Finding current and destination indices on the board
    currIndex = findPiece(piece, board)
    destIndex = findIndex(dest)
    colDiff = abs((currIndex % 8) - (destIndex % 8))
    rowDiff = (currIndex // 8) - (destIndex // 8)

    #Move validity checking
    match piece[0].lower():
        case "r":
            pass
        case "n":
            pass
        case "b":
            pass
        case "q":
            pass
        case "k":
            pass
        case "p":
            if turn == "player":
                # 1 square
                if rowDiff == -1 and colDiff == 0 and board[destIndex] is None:
                    return True
                # 2 squares
                elif rowDiff == -2 and colDiff == 0 and currIndex // 8 == 6 and board[destIndex] is None and board[currIndex + 8] is None:
                    return True
                # kill
                elif rowDiff == -1 and colDiff == 1 and board[destIndex] is not None and board[destIndex][0].isupper():
                    return True     
            elif turn == "bot":
                if rowDiff == 1 and colDiff == 0 and board[destIndex] is None:
                    return True
                elif rowDiff == 2 and colDiff == 0 and currIndex // 8 == 1 and board[destIndex] is None and board[currIndex - 8] is None:
                    return True
                elif rowDiff == 1 and colDiff == 1 and board[destIndex] is not None and board[destIndex][0].islower():
                    return True
    print(f"rowDiff: {rowDiff} colDiff: {colDiff} currIndex: {currIndex} currIndex // 8: {currIndex // 8} board[destIndex]: {board[destIndex]} board[currIndex + 8]: {board[currIndex + 8]}")
    return "Case issue"


## fix move 2 up issue


board = (
        'r1', 'n1', 'b1', 'q', 'k', 'b2', 'n2', 'r2',  # player's back rank
        'p1', 'p2', 'p3', None, 'p5', 'p6', 'p7', 'p8',  # player's pawn rank
        None, None, None, 'P4', None, None, None, None,  # Empty rank
        None, None, None, None, None, None, None, None,  # Empty rank
        None, None, None, None, None, None, None, None,  # Empty rank
        None, None, None, 'p4', None, None, None, None,  # Empty rank
        'P1', 'P2', 'P3', None, 'P5', 'P6', 'P7', 'P8',  # bot's pawn rank
        'R1', 'N1', 'B1', 'Q', 'K', 'B2', 'N2', 'R2'   # bot's back rank
    )

print("Index of b3 (should be empty):", board[findIndex('b3')])
print("Index of b4 (should be empty):", board[findIndex('b4')])
print("Starting row of P2:", findIndex('b2') // 8)


# Valid moves for bot's pawn (Uppercase)
print("Bot's Pawn Test 1 (Forward 1):", moveValidate('P1', 'a3', 'bot', board))  # Expect True for valid forward movement
print("Bot's Pawn Test 2 (Forward 2):", moveValidate('P2', 'b4', 'bot', board))  # Expect True for valid forward movement
print("Bot's Pawn Test 3 (Diagonal):", moveValidate('P5', 'd3', 'bot', board))  # Expect True for valid forward movement
