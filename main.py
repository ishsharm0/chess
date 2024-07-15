import os


def newBoard(startingWhite): 
    if startingWhite: 
        board = (
            'r1', 'n1', 'b1', 'q', 'k', 'b2', 'n2', 'r2',  # player
            'p1', 'p2', 'p3', 'p4', 'p5', 'p6', 'p7', 'p8',  
            None, None, None, None, None, None, None, None,  
            None, None, None, None, None, None, None, None,  
            None, None, None, None, None, None, None, None,  
            None, None, None, None, None, None, None, None,  
            'P1', 'P2', 'P3', 'P4', 'P5', 'P6', 'P7', 'P8', 
            'R1', 'N1', 'B1', 'Q', 'K', 'B2', 'N2', 'R2'   # bot
        )
    else: 
        board = (
            'r1', 'n1', 'b1', 'k', 'q', 'b2', 'n2', 'r2',  # player
            'p1', 'p2', 'p3', 'p4', 'p5', 'p6', 'p7', 'p8',  
            None, None, None, None, None, None, None, None,  
            None, None, None, None, None, None, None, None,  
            None, None, None, None, None, None, None, None,  
            None, None, None, None, None, None, None, None,  
            'P1', 'P2', 'P3', 'P4', 'P5', 'P6', 'P7', 'P8', 
            'R1', 'N1', 'B1', 'K', 'Q', 'B2', 'N2', 'R2'   # bot
        )
    return board

#12345678 is bottom to top, abcdefgh is left to right

def printBoard(board):
    os.system('cls')
    for i in range(8):
        rowText = ""

        for j in range(8):
            square = (board[(i*8)+j])
            rowText += f"{(square if square is not None else '·'):>3} "
        print(rowText)


def findSquare(square):
    try:
        colIndex = ord(square[0]) - ord('a')
        rowIndex = int(square[1]) - 1
        index = (7 - rowIndex) * 8 + colIndex
        print(f"findSquare({square}) = {index}")  # Debug output
        return index
    except Exception as e:
        print(f"Error in findSquare with input '{square}': {e}")
        return False

def findPiece(piece, board): # Returns the index of a piece like P5

    # Check if pieces are in board 
    
    return board.index(piece)

def movePiece(piece, dest_index, board):
    try:
        curr_index = findPiece(piece, board)
        if curr_index == -1:
            print(f"Piece {piece} not found on the board.")
            return board

        board = list(board)
        print(f"Moving {piece} from index {curr_index} to index {dest_index}")

        if board[dest_index] is not None:
            print(f"Capturing piece at {dest_index}")

        board[dest_index] = piece
        board[curr_index] = None
        return tuple(board)
    except Exception as e:
        print(f"Error moving piece: {e}")
        return board

def castle(turn, board, startingWhite): 
    board = list(board)
    if startingWhite: 
        if turn == 'bot': 
            board[60] = None
            board[61] = 'R2'
            board[62] = 'K'
            board[63] = None
        else: 
            board[7] = None
            board[6] = 'k'
            board[5] = 'r2'
            board[4] = None
    else: 
        if turn == 'bot': 
            board[59] = None
            board[58] = 'R1'
            board[57] = 'K'
            board[56] = None
        else: 
            board[3] = None
            board[2] = 'r1'
            board[1] = 'k'
            board[0] = None
    return tuple(board)

def promotePawn(piece, board): 
    pass

def castleValidate(startingWhite, turn, board): 
    # Check if pieces are in board

    if startingWhite: 
        if turn == 'player' and ('k') in board and ('r2') in board:
                if findPiece('k', board) == 4 and findPiece('r2', board) == 7: 
                    if board[5] is None and board[6] is None: 
                        return True
        elif turn == 'bot' and ('K') in board and ('R2') in board: 
            if findPiece('K', board) == 60 and findPiece('R2', board) == 63: 
                if board[61] is None and board[62] is None:
                    return True
    else:
        if turn == 'player' and ('k') in board and ('r2') in board:
            if findPiece('k', board) == 3 and findPiece('r1', board) == 0: 
                if board[1] is None and board[2] is None:
                    return True            
        elif turn == 'bot' and ('K') in board and ('R2') in board: 
            if findPiece('K', board) == 59 and findPiece('R1', board) == 56: 
                if board[57] is None and board[58] is None:
                    return True
            
    return False 

def pawnPromotionValidate(piece, turn, board):
    # Check if piece is in board 
    if piece in board and ((piece[0].islower() and turn == 'player') or (piece[0].isupper() and turn == 'bot')): 
        pass
    else: return False
    
    currLoc = findPiece(piece, board)
    if turn == 'player' and currLoc // 8 == 7:
        return True
    elif turn == 'bot' and currLoc // 8 == 0:  
        return True
    else: 
        return False

def moveValidate(piece, dest, turn, board):
    print(dest)
    # Error handling
    validTurn = (piece[0].islower() and turn == 'player') or (piece[0].isupper() and turn == 'bot')
    
    if not validTurn:
        return False 

    # Ensuring dest is a string before finding index
    if isinstance(dest, str):
        destIndex = findSquare(dest)
    else:
        destIndex = dest  # Assuming dest is already an index if not a string

    # Finding current index of the piece on the board
    currIndex = findPiece(piece, board)

    if destIndex is False:
        return False  # Early exit if destination index was not found due to invalid input

    # Calculate column and row differences
    colDiff = (destIndex % 8) - (currIndex % 8)  # Positive if dest is to the right
    rowDiff = (destIndex // 8) - (currIndex // 8)  # Positive if dest is below



    #Move validity checking
    match piece[0].lower():
        case "r":
            if colDiff == 0:  # Vertical movement
                step = 8 if rowDiff > 0 else -8
                nextIndex = currIndex + step

                while nextIndex != destIndex:  
                    if board[nextIndex] is not board[destIndex]:
                        if board[nextIndex] is not None:  
                            return False  
                        nextIndex += step
                    else: 
                        break
                
            elif rowDiff == 0:  # Horizontal movement
                step = 1 if colDiff > 0 else -1  
                nextIndex = currIndex + step  
                while nextIndex != destIndex: 
                    if board[nextIndex] is not None:  
                        return False  
                    nextIndex += step  
            else: 
                return False
            
        case "n":
            if abs(colDiff) == 2: 
                if abs(rowDiff) == 1: 
                    pass
                else: return False
            elif abs(colDiff) == 1: 
                if abs(rowDiff) == 2: 
                    pass
                else: return False
            else: return False
            
        case "b":
            if abs(colDiff) == abs(rowDiff):  # Diagonal movement
                step = 9 if colDiff > 0 and rowDiff > 0 else -9  
                if colDiff < 0 and rowDiff > 0:
                    step = 7  # Bottom left
                elif colDiff > 0 and rowDiff < 0:
                    step = -7  # Top right

                nextIndex = currIndex + step
                while nextIndex != destIndex:
                    if board[nextIndex] is not None:  # Check if the path is clear
                        return False
                    nextIndex += step
            else: return False

        case "q":  # Queen
            if colDiff == 0:  # Vertical movement
                step = 8 if rowDiff > 0 else -8
                nextIndex = currIndex + step

                while nextIndex != destIndex:  
                    if board[nextIndex] is not board[destIndex]:
                        if board[nextIndex] is not None:  
                            return False  
                        nextIndex += step
                    else: 
                        break
                
            elif rowDiff == 0:  # Horizontal movement
                step = 1 if colDiff > 0 else -1  
                nextIndex = currIndex + step  
                while nextIndex != destIndex: 
                    if board[nextIndex] is not None:  
                        return False  
                    nextIndex += step  

            elif abs(colDiff) == abs(rowDiff):  # Diagonal movement
                step = 9 if colDiff > 0 and rowDiff > 0 else -9  
                if colDiff < 0 and rowDiff > 0:
                    step = 7  # Bottom left
                elif colDiff > 0 and rowDiff < 0:
                    step = -7  # Top right

                nextIndex = currIndex + step
                while nextIndex != destIndex:
                    if board[nextIndex] is not None:  # Check if the path is clear
                        return False
                    nextIndex += step

            else: 
                return False
        
        case "k":  # King movement validation
            # Check for single square movement in any direction
            if abs(rowDiff) <= 1 and abs(colDiff) <= 1:
                if board[destIndex] is None: 
                    return True
                elif turn == 'bot' and board[destIndex][0].islower(): 
                    return True
                elif turn == 'player' and board[destIndex][0].isupper(): 
                    return True
                else: return False
            else: return False

        case "p":
            if turn == "player":
                # 1 square
                if rowDiff == 1 and colDiff == 0 and board[destIndex] is None:
                    return True
                # 2 squares
                elif rowDiff == 2 and colDiff == 0 and currIndex // 8 == 1 and board[destIndex] is None and board[currIndex + 8] is None:
                    return True
                # kill
                elif rowDiff == 1 and (colDiff == 1 or colDiff == -1) and board[destIndex] is not None and board[destIndex][0].isupper():
                    return True     
                else: return False 
            elif turn == "bot":
                if rowDiff == -1 and colDiff == 0 and board[destIndex] is None:
                    return True
                elif rowDiff == -2 and colDiff == 0 and currIndex // 8 == 6 and board[destIndex] is None and board[currIndex - 8] is None:
                    return True  
                elif rowDiff == -1 and (colDiff == 1 or colDiff == -1) and board[destIndex] is not None and board[destIndex][0].islower():
                    return True
                else: return False

            # ADD EN PASSANT 

    if turn == 'bot':
            return True if board[destIndex] is None or (board[destIndex][0].islower()) else False
    elif turn == 'player':
        return True if board[destIndex] is None or (board[destIndex][0].isupper()) else False

def inputValidate(input_str, board, startingWhite, turn):
    input_parts = input_str.strip().split()  # Ensure input is properly split

    if len(input_parts) == 2 and input_parts[0] in board:
        piece = input_parts[0]
        dest = input_parts[1]
        dest_index = findSquare(dest)

        if dest_index is not False:
            print(f"Command parsed as move: {piece} to {dest} (index {dest_index})")
            if moveValidate(piece, dest_index, turn, board):
                return (True, piece, dest_index)
            else:
                print("Move validation failed.")
        else:
            print("Destination square is invalid.")
    elif input_str.lower() == "castle":
        if castleValidate(startingWhite, turn, board):
            return ("castle", None, None)
        else:
            return (False, None, None)
    elif input_parts[0].lower() == "promote":
        piece = input_parts[1]
        if pawnPromotionValidate(piece, turn, board):
            return (piece, None, None)
        else:
            return (False, None, None)
    
    print("Input does not match any valid command format.")
    return (False, None, None) 

def startGame(startingWhite): 
    board = newBoard(startingWhite)

    turn = "bot" if startingWhite else "player"

    # Starts game loop
    terminated = False    
    while (terminated != True): 

        while True:
            printBoard(board)
            print("\nTurn:", turn.upper(), "\n")
            playerInput = input("Enter the move in format 'P3 e5'. \nTo promote, say 'promote P3'. \nTo castle, say 'castle'. \n\n").strip()
            validity, piece, dest = inputValidate(playerInput, board, startingWhite, turn)
            if validity is not False:
                break
            else: 
                print("Invalid move. Try again!")
            
        # Standard move
        if piece is not None: 
            print("Moving piece")
            board = movePiece(piece, dest, board)

        # Pawn promotion
        elif validity in board: 
            print("Promoting pawn")
            pass

        # Castling
        elif validity == "castle": 
            print("Castling")
            board = castle(turn, board, startingWhite)



        # Make move
        
        # Analyze board state and have escape clauses for checkmate, draw, etc. 
        
        turn = "player" if turn == "bot" else "bot"

        # Print board and most recent turn i guess? 



startingWhite = True

#print(inputValidate("P1 a3", board, True, 'bot')) #true

startGame(startingWhite)
