import os


def newBoard(botWhite): # True -> Bot is white
    if botWhite: 
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

def movePiece(piece, destIndex, board, gameStates, turn):
    try:
        currIndex = findPiece(piece, board)
        if currIndex == -1:
            return board

        board = list(board)

        board[destIndex] = piece
        board[currIndex] = None
        
        colDiff = (destIndex % 8) - (currIndex % 8)  # Positive if dest is to the right
        rowDiff = (destIndex // 8) - (currIndex // 8)  # Positive if dest is below
        
        if piece[0] == 'p': 
            if currIndex // 8 == 7:
                board = promotePawn(piece, board)
        elif piece[0] == 'P': 
            if currIndex // 8 == 1:
                board = promotePawn(piece, board)
        if (colDiff == 1 or colDiff == -1) and rowDiff == (1 if piece.islower() else -1):
                
                if gameStates: #Checking previous game state  
                    lastBoard = gameStates[-2]

                    lastMovedPiece = lastBoard[destIndex + 8] if turn == 'player' else lastBoard[destIndex - 8]
                    if lastMovedPiece == board[currIndex + 1] or lastMovedPiece == board[currIndex - 1]:
                        print("")
                        if lastMovedPiece[0].lower() == 'p' and lastMovedPiece[0].lower() == 'p' and abs(findPiece(lastMovedPiece, lastBoard) - findPiece(lastMovedPiece, board)) == 16:
                            
                            # Communicate en passant to startGame
                            return enPassant(destIndex, turn, board)
                            
        return tuple(board)
    

    except Exception as e:
        print(f"Error moving piece: {e}")
        return board

def castle(turn, board, botWhite): 
    board = list(board)
    if botWhite: 
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
    while True:
        playerInput = input("Enter the name of the piece you would like to switch for ('QUEEN', 'KNIGHT', 'BISHOP', 'ROOK'). If you don't want to promote, enter 'NO': \n\n").strip().upper()
        if playerInput in ("QUEEN", "KNIGHT", "BISHOP", "ROOK"):
            break
        elif playerInput == "NO":
            return(board)
        else:
            print("Invalid piece. Try again!")

    # Determine the new piece abbreviation
    if playerInput == "QUEEN":
        name = "q"
    elif playerInput == "KNIGHT":
        name = "n"
    elif playerInput == "BISHOP":
        name = "b"
    elif playerInput == "ROOK":
        name = "r"

    # Detects and names new pieces 
    count = 1
    for existingPiece in board:
        if existingPiece and existingPiece[0].lower() == name:
            existingCount = int(existingPiece[1:]) if len(existingPiece) > 1 and existingPiece[1:].isdigit() else 1
            count = max(count, existingCount + 1)

    newPiece = name + str(count)
    newPiece = newPiece.upper() if piece.isupper() else newPiece.lower()

    # Update board
    board = list(board)
    pawnIndex = findPiece(piece, board)
    if pawnIndex != -1:
        board[pawnIndex] = newPiece

    return tuple(board)

def enPassant(destIndex, turn, board):
    board = list(board)
    if turn == 'bot':
        opponentIndex = destIndex + 8 
    else: 
        opponentIndex = destIndex - 8
    print(opponentIndex)
    
    board[opponentIndex] = None  # Remove the opponent's pawn
    return tuple(board)

def castleValidate(botWhite, turn, board): 
    # Check if pieces are in board

    if botWhite: 
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

def moveValidate(piece, dest, turn, board, gameStates=False):
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
            if botWhite: 
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
                 
            elif turn == "bot":
                if rowDiff == -1 and colDiff == 0 and board[destIndex] is None:
                    return True
                elif rowDiff == -2 and colDiff == 0 and currIndex // 8 == 6 and board[destIndex] is None and board[currIndex - 8] is None:
                    return True  
                elif rowDiff == -1 and (colDiff == 1 or colDiff == -1) and board[destIndex] is not None and board[destIndex][0].islower():
                    return True

            # En passant     
            if (colDiff == 1 or colDiff == -1) and rowDiff == (1 if piece.islower() else -1):
                
                if gameStates: #Checking previous game state  
                    lastBoard = gameStates[-2]

                    lastMovedPiece = lastBoard[destIndex + 8] if turn == 'player' else lastBoard[destIndex - 8]
                    if lastMovedPiece == board[currIndex + 1] or lastMovedPiece == board[currIndex - 1]:
                        print("")
                        if lastMovedPiece[0].lower() == 'p' and lastMovedPiece[0].lower() == 'p' and abs(findPiece(lastMovedPiece, lastBoard) - findPiece(lastMovedPiece, board)) == 16:
                            
                            # Communicate en passant to startGame
                            
                            return True
            return False

    if turn == 'bot':
            return True if board[destIndex] is None or (board[destIndex][0].islower()) else False
    elif turn == 'player':
        return True if board[destIndex] is None or (board[destIndex][0].isupper()) else False

def inputValidate(inputString, board, botWhite, turn, gameStates):
    inputParts = inputString.strip().split()  # Ensure input is properly split

    if len(inputParts) == 2 and inputParts[0] in board:
        piece = inputParts[0]
        dest = inputParts[1]
        destIndex = findSquare(dest)

        if destIndex is not False:
            print(f"Command parsed as move: {piece} to {dest} (index {destIndex})")
            if moveValidate(piece, destIndex, turn, board, gameStates):
                return (True, piece, destIndex)
            else:
                print("Move validation failed.")
        else:
            print("Destination square is invalid.")
    elif inputString.lower() == "castle":
        if castleValidate(botWhite, turn, board):
            return ("castle", None, None)
        else:
            return (False, None, None)
    
    print("Input does not match any valid command format.")
    return (False, None, None) 

def startGame(botWhite): 
    board = newBoard(botWhite)

    turn = "bot" if botWhite else "player"

    # Starts game loop
    terminated = False    
    gameStates = []
    while (terminated != True): 

        while True:
            printBoard(board)
            print("\nTurn:", turn.upper(), "\n")
            playerInput = input("Enter the move in format 'P3 e5'. \nTo castle, say 'castle'. \n\n").strip()
            validity, piece, dest = inputValidate(playerInput, board, botWhite, turn, gameStates)
            if validity is not False:
                break
            else: 
                print("Invalid move. Try again!")
            
        # Standard move
        if piece is not None: 
            print("Moving piece")
            board = movePiece(piece, dest, board, gameStates, turn)


        # Castling
        elif validity == "castle": 
            print("Castling")
            board = castle(turn, board, botWhite)

        
        # Detect checkmate and draw

        gameStates.append(board)

        turn = "player" if turn == "bot" else "bot"


def getAllMoves(piece, originalBoard): # Returns an array of all possible game tuples for a piece 
    possibleMoves = []

    if piece is not None: 
        pass
    else: 
        return possibleMoves
    
    currIndex = findPiece(piece, originalBoard)  
    if currIndex == -1:
        return possibleMoves  

    turn = 'player' if piece[0].islower() else 'bot'

    # Check every position on the board 
    for destIndex in range(64):
        if currIndex != destIndex:  
            
            if moveValidate(piece, destIndex, turn, originalBoard):
                
                testBoard = list(originalBoard)
                testBoard[destIndex] = piece  # Place the piece at the destination index
                testBoard[currIndex] = None  # Remove the piece from its original position


                possibleMoves.append(tuple(testBoard))  

    return possibleMoves

def getAllTeamMoves(team, board): #Returns an array of arrays for a given team
    teamMoves = []
    if team == 'player': 
        for piece in board: 
            if piece is not None and piece[0].islower(): 
                teamMoves.append(getAllMoves(piece, board))
    if team == 'bot': 
        for piece in board: 
            if piece is not None and piece[0].islower(): 
                teamMoves.append(getAllMoves(piece, board))
    return teamMoves



botWhite = True

startGame(botWhite)