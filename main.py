
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
    pass

def findIndex(square): # Translates from a chess square like e5 to an index
    try: 
        colIndex = ord(square[0]) - ord('a')
        rowIndex = int(square[1]) - 1
        index = (7 - rowIndex) * 8 + colIndex
        return index
    except: 
        return False

def findPiece(piece, board): # Returns the index of a piece like P5

    # Check if pieces are in board 
    
    return board.index(piece)

def movePiece(piece, dest, board): # Returns board with piece moved
    currLoc = findPiece(piece, board)
    destLoc = findIndex(dest)
    board = list(board)

    board[currLoc] = None
    board[destLoc] = piece

    return tuple(board)

def castleValidate(startingWhite, turn, board): 
    # Check if pieces are in board

    if startingWhite: 
        if turn == 'player' and ('k') in board and ('r2') in board:
                if findPiece('k', board) == 4 and findPiece('r2', board) == 7: 
                    return True
        elif turn == 'bot' and ('K') in board and ('R2') in board: 
            if findPiece('K', board) == 60 and findPiece('R2', board) == 63: 
                return True
    else:
        if turn == 'player' and ('k') in board and ('r2') in board:
            if findPiece('k', board) == 3 and findPiece('r1', board) == 0: 
                return True            
        elif turn == 'bot' and ('K') in board and ('R2') in board: 
            if findPiece('K', board) == 59 and findPiece('R1', board) == 56: 
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
        destIndex = findIndex(dest)
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

def inputValidate(input, board, startingWhite, turn):
    # Regular moves
    if input.split(" ")[0] in board and findIndex(input.split(" ")[1]) is not False: 
        piece = input.split(" ")[0]
        dest = findIndex(input.split(" ")[1])

        if moveValidate(piece, dest, turn, board):
            return (True, piece, dest)
        else: 
            return (False, None, None)
        
    # Castling
    elif input.lower() == "castle": 
        print("Castle")
        if castleValidate(startingWhite, turn, board):
            return ("castle", None, None)
        else: 
            return (False, None, None)
        
    # Pawn promotion
    elif input.lower().split(" ")[0] == "promote" and int(input.lower().split(" ")[1][1]) in [1,2,3,4,5,6,7,8]:
        piece = input.split(" ")[1]

        if pawnPromotionValidate(piece, turn, board):
            return (piece, None, None)
        else: 
            return (False, None, None)
    
    return (False, None, None)    

def startGame(startingWhite): 
    board = newBoard(startingWhite)

    turn = "bot" if startingWhite else "player"

    # Starts game loop
    terminated = False    
    while (terminated != True): 

        while True: 
            print("Turn: ", turn)
            playerInput = input("Enter the move in format 'P3 e5'. \nTo promote, say 'promote P3'. \nTo castle, say 'castle'. \n\n").strip()
            validity, piece, dest = inputValidate(playerInput, board, startingWhite, turn)
            if validity is not False:
                break
            else: 
                print("Invalid move. Try again!")
            
            
        if piece is not None: 
            print("Moving piece")
            movePiece(piece, dest, board)
        elif validity in board: 
            print("Promoting pawn")
            # execute promote pawn 
            pass
        elif validity == "castle": 
            print("Castling")
            # execute castle mover castle
            pass



        # Make move
        
        # Analyze board state and have escape clauses for checkmate, draw, etc. 
        
        turn = "player" if turn == "bot" else "bot"

        # Print board and most recent turn i guess? 



startingWhite = True

#print(inputValidate("P1 a3", board, True, 'bot')) #true

startGame(startingWhite)