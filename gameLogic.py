from colorama import Style, init, Fore
import os

clearLogs = True
init(autoreset=True)

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

def detectCheckmate(board, turn, botWhite, gameStates):
    # Invert turn to check if the opponent is in checkmate
    enemy_turn = 'bot' if turn == 'player' else 'player'
    allMoves = getAllTeamMoves(enemy_turn, board, turn == 'bot', gameStates)

    # Check if any move leads to a position where the enemy king is not in check
    for moves in allMoves:
        for move in moves:
            if isKingSafe(move, enemy_turn):
                return False  # Not checkmate if at least one move leads out of check
    return True

def detectStalemate(board, turn, botWhite, gameStates):
    if len(getAllTeamMoves(turn, board, botWhite, gameStates)) == 0: 
        return True
    else: return False

def isKingSafe(board, turn, position=None):
    casePiece = 'K' if turn == 'bot' else 'k'
    if position is None:
        kingPosition = findPiece(casePiece, board)
    else:
        kingPosition = position

    if kingPosition == -1:
        return False

    enemy = 'player' if turn == 'bot' else 'bot'
    
    # Directions for knight moves
    knightMoves = [15, 17, -15, -17, 10, 6, -10, -6]
    # Directions for rook/queen (horizontal and vertical)
    directions = [1, -1, 8, -8]
    # Directions for bishop/queen (diagonals)
    diagonals = [9, -9, 7, -7]

    # Check pawn attacks
    pawnAttacks = [-9, -7] if turn == 'bot' else [9, 7]
    for attack in pawnAttacks:
        pos = kingPosition + attack
        if isOnBoard(pos) and isEnemyPiece(board, pos, 'p', enemy):
            return False

    # Check horizontal and vertical threats (from rooks and queens)
    for direction in directions:
        step = direction
        pos = kingPosition + step
        while isOnBoard(pos) and not crossesBorder(kingPosition, pos):
            if board[pos]:
                if board[pos][0].lower() in ['r', 'q'] and isEnemyPiece(board, pos, board[pos][0], enemy):
                    return False
                break  # A piece blocks further checking in this direction
            pos += step

    # Check diagonal threats (from bishops and queens)
    for direction in diagonals:
        step = direction
        pos = kingPosition + step
        while isOnBoard(pos) and not crossesBorder(kingPosition, pos):
            if board[pos]:
                if board[pos][0].lower() in ['b', 'q'] and isEnemyPiece(board, pos, board[pos][0], enemy):
                    return False
                break  # A piece blocks further checking in this direction
            pos += step

    # Check knight attacks
    for move in knightMoves:
        pos = kingPosition + move
        if isOnBoard(pos) and isEnemyPiece(board, pos, 'n', enemy):
            return False

    # Check if the enemy king is directly next to this king
    for move in [-1, 1, -8, 8, -9, -7, 9, 7]:
        pos = kingPosition + move
        if isOnBoard(pos) and not crossesBorder(kingPosition, pos) and isEnemyPiece(board, pos, 'k', enemy):
            return False

    return True

def crossesBorder(origin, destination):
    # Special handling for knight crossing board logic
    if abs(origin % 8 - destination % 8) > 2:
        return True
    return abs(origin // 8 - destination // 8) > 2 or (origin % 8 == 0 or destination % 8 == 7)

def isOnBoard(position):
    return 0 <= position < 64

def isEnemyPiece(board, position, pieceType, enemy):
    piece = board[position]
    if piece and piece[0].lower() == pieceType:
        return (piece.islower() if enemy == 'player' else piece.isupper())
    return False

def getPieceMoves(piece, originalBoard, botWhite, gameStates): # Returns an array of all possible game tuples for a piece 
    # Checks if piece is there
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
        
            # If valid move, move it to the new board
            if moveValidate(piece, destIndex, turn, originalBoard, botWhite, gameStates):                
                testBoard = list(originalBoard)
                testBoard[destIndex] = piece 
                testBoard[currIndex] = None  
                possibleMoves.append(tuple(testBoard))  

    return tuple(possibleMoves)

def getAllTeamMoves(team, board, botWhite, gameStates): #Returns an array of arrays for a given team
    teamMoves = []
    if team == 'player': 
        for piece in board: 
            if piece is not None and piece[0].islower(): 
                teamMoves.append(getPieceMoves(piece, board, botWhite, gameStates))
    if team == 'bot': 
        for piece in board: 
            if piece is not None and piece[0].isupper(): 
                teamMoves.append(getPieceMoves(piece, board, botWhite, gameStates))
    return tuple(teamMoves)

def findPiece(piece, board):
    try:
        return board.index(piece)
    except ValueError:
        return -1  # Return -1 or another indicator that the piece is not found


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

def movePiece(piece, destIndex, board, gameStates, turn): # Returns a tuple with updated board
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
            if currIndex // 8 == 6:
                board = promotePawn(piece, board)
        elif piece[0] == 'P': 
            if currIndex // 8 == 1:
                board = promotePawn(piece, board)
        if piece[0].lower() == 'p': 
            if (colDiff == 1 or colDiff == -1) and rowDiff == (1 if piece.islower() else -1):
                    
                    if gameStates[-2]: #Checking previous game state  
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

def moveValidate(piece, dest, turn, board, botWhite, gameStates):

    validTurn = (piece[0].islower() and turn == 'player') or (piece[0].isupper() and turn == 'bot')
    
    if not validTurn:
        return False 

    if isinstance(dest, str):
        destIndex = findSquare(dest)
    else:
        destIndex = dest  # Assuming dest is already an index if not a string

    currIndex = findPiece(piece, board)
    if currIndex == -1 or destIndex is False:
        return False  # Early exit if no valid current or destination index

    colDiff = (destIndex % 8) - (currIndex % 8)
    rowDiff = (destIndex // 8) - (currIndex // 8)

    # Check if the destination square is not blocked by a friendly piece
    if board[destIndex] is not None and ((turn == 'bot' and board[destIndex][0].isupper()) or (turn == 'player' and board[destIndex][0].islower())):
        return False

    #Move validity checking
    match piece[0].lower():
        case "r":
            if colDiff != 0 and rowDiff != 0:
                return False  # Rooks move in straight lines, not diagonally

            if colDiff == 0:  # Vertical movement
                step = 1 if rowDiff > 0 else -1
                for i in range(1, abs(rowDiff)):
                    if board[currIndex + i * 8 * step] is not None:
                        return False  # There is a piece in the way
            elif rowDiff == 0:  # Horizontal movement
                step = 1 if colDiff > 0 else -1
                for i in range(1, abs(colDiff)):
                    if board[currIndex + i * step] is not None:
                        return False  # There is a piece in the way 
            
        case "n":
            if abs(colDiff) == 2: 
                if abs(rowDiff) == 1: 
                    pass
                else: return False
            elif abs(colDiff) == 1: 
                if abs(rowDiff) == 2: 
                    pass
                else: return False
            else: 
                return False
            
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
                step = 1 if rowDiff > 0 else -1
                for i in range(1, abs(rowDiff)):
                    if board[currIndex + i * 8 * step] is not None:
                        return False  # There is a piece in the way
            elif rowDiff == 0:  # Horizontal movement
                step = 1 if colDiff > 0 else -1
                for i in range(1, abs(colDiff)):
                    if board[currIndex + i * step] is not None:
                        return False  # There is a piece in the way 

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
            
            # Is king safe on destIndex? Pass 
            if isKingSafe(movePiece(piece, destIndex, board, gameStates, turn), turn):
                pass
            else:
                return False

            # Within king's range? 
            if abs(rowDiff) <= 1 and abs(colDiff) <= 1:
                if board[destIndex] is None: 
                    return True
                elif turn == 'bot' and board[destIndex][0].islower(): 
                    return True
                elif turn == 'player' and board[destIndex][0].isupper(): 
                    return True
                else: return False

            # Castling
            if botWhite:
                if turn == 'bot' and 'K' in board and 'R2' in board:
                    if findPiece('K', board) == 60 and findPiece('R2', board) == 63:
                        if board[61] is None and board[62] is None:
                            return True
            else:
                if turn == 'bot' and 'K' in board and 'R1' in board:  # Use 'R1' here if that's intended for non-botWhite side
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
            if (colDiff == 1 or colDiff == -1) and rowDiff == (1 if piece.islower() else -1) and board[destIndex] is None:
                if len(gameStates) > 2:  # Need at least two game states to check the last move
                    lastBoard = gameStates[-2]
                    lastMovedIndex = destIndex + (8 if turn == 'player' else -8)

                    # Check if the last moved index is on the board
                    if 0 <= lastMovedIndex < 64:
                        lastMovedPiece = lastBoard[lastMovedIndex]

                        if lastMovedPiece is not None:
                            if lastMovedPiece[0].lower() == 'p' and abs(findPiece(lastMovedPiece, lastBoard) - findPiece(lastMovedPiece, board)) == 16:
                                # Ensure that the pawn moved two squares in the previous move
                                if (lastMovedPiece.islower() and findPiece(lastMovedPiece, board) == lastMovedIndex - 16) or \
                                (lastMovedPiece.isupper() and findPiece(lastMovedPiece, board) == lastMovedIndex + 16):
                                    return True
            return False

    if turn == 'bot':
            return True if board[destIndex] is None or (board[destIndex][0].islower()) else False
    elif turn == 'player':
        return True if board[destIndex] is None or (board[destIndex][0].isupper()) else False

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
    if botWhite:
        if turn == 'bot':
            kingPos = findPiece('K', board)
            rookPos = findPiece('R2', board) if 'R2' in board else -1
            critical_positions = [60, 61, 62] if kingPos == 60 and rookPos == 63 else []
        else:
            kingPos = findPiece('k', board)
            rookPos = findPiece('r2', board) if 'r2' in board else -1
            critical_positions = [4, 5, 6] if kingPos == 4 and rookPos == 7 else []
    else:
        if turn == 'bot':
            kingPos = findPiece('K', board)
            rookPos = findPiece('R1', board) if 'R1' in board else -1
            critical_positions = [59, 58, 57] if kingPos == 59 and rookPos == 56 else []
        else:
            kingPos = findPiece('k', board)
            rookPos = findPiece('r1', board) if 'r1' in board else -1
            critical_positions = [3, 2, 1] if kingPos == 3 and rookPos == 0 else []

    if not critical_positions:  # If initial position check fails
        return False

    if not isKingSafe(board, turn):  # Check if king is currently in check
        return False

    # Check if any of the critical squares are under attack
    for pos in critical_positions:
        if not isKingSafe(board, turn, pos):  # Assume this function can check safety for specific positions
            return False

    return True

def printBoard(board):
    if clearLogs:
        os.system('cls' if os.name == 'nt' else 'clear')

    for i in range(8):
        rowText = ""

        for j in range(8):
            square = board[i * 8 + j]
            if square:
                color = ""
                if square.isupper():  # bot's pieces
                    match square[0]:
                        case 'K':
                            color = Fore.RED + Style.BRIGHT
                        case 'Q':
                            color = Fore.RED
                        case 'B':
                            color = Fore.MAGENTA
                        case 'N':
                            color = Fore.LIGHTMAGENTA_EX + Style.BRIGHT
                        case 'R':
                            color = Fore.LIGHTYELLOW_EX + Style.BRIGHT
                        case 'P':
                            color = Fore.YELLOW
                else:  # player's pieces
                    match square[0]:
                        case 'k':
                            color = Fore.GREEN + Style.BRIGHT
                        case 'q':
                            color = Fore.GREEN
                        case 'b':
                            color = Fore.CYAN
                        case 'n':
                            color = Fore.LIGHTCYAN_EX + Style.BRIGHT
                        case 'r':
                            color = Fore.LIGHTBLUE_EX + Style.BRIGHT
                        case 'p':
                            color = Fore.BLUE
                    #color = Fore.GREEN if 'k' == square[0] else Fore.CYAN

                # Use color based on piece type
                pieceDisplay = color + square.rjust(3) + Style.RESET_ALL
            else:
                pieceDisplay = '·'.rjust(3)

            rowText += pieceDisplay + " "
        print(rowText)

def inputValidate(inputString, board, botWhite, turn, gameStates):
    print("Validating input")
    inputParts = inputString.strip().split()  # Ensure input is properly split

    # Normal move
    if len(inputParts) == 2 and inputParts[0] in board and findSquare(inputParts[1].lower()):
        piece = inputParts[0]
        dest = inputParts[1]
        destIndex = findSquare(dest)

        if destIndex is not False:
            print(f"Command parsed as move: {piece} to {dest} (index {destIndex})")
            if moveValidate(piece, destIndex, turn, board, botWhite, gameStates):
                print("destIndex", destIndex)
                return (True, piece, destIndex)
            else:
                print("Move validation failed.")
                return (False, None, None)
        else:
            print("Destination square is invalid.")
            return (False, None, None)

    # Castle            
    elif inputString.lower() == "castle":
        if castleValidate(botWhite, turn, board):
            return ("castle", None, None)
        else:
            #print("Reached bad")
            return (False, None, None)
    
    print("Input does not match any valid command format.")
    return (False, None, None)