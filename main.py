import numpy as np

PAWN, KNIGHT, BISHOP, ROOK, QUEEN, KING = range(6)

initial_positions = {
    PAWN:    0x00FF00000000FF00,
    KNIGHT:  0x4200000000000042,
    BISHOP:  0x2400000000000024,
    ROOK:    0x8100000000000081,
    QUEEN:   0x0800000000000008,
    KING:    0x1000000000000010
}

white_pieces = {piece: 0 for piece in range(6)}
black_pieces = {piece: 0 for piece in range(6)}

for piece, bitboard in initial_positions.items():
    white_pieces[piece] = bitboard
    black_pieces[piece] = bitboard << 56 

def set_bit(bitboard, position):
    return bitboard | (1 << position)

def clear_bit(bitboard, position):
    return bitboard & ~(1 << position)

def is_bit_set(bitboard, position):
    return (bitboard >> position) & 1

def print_board(white_pieces, black_pieces):
    board = np.zeros(64, dtype=str)
    board[:] = '.'

    piece_symbols = 'PNBRQKpnbrqk'
    for piece in range(6):
        for pos in range(64):
            if is_bit_set(white_pieces[piece], pos):
                board[pos] = piece_symbols[piece]
            if is_bit_set(black_pieces[piece], pos):
                board[pos] = piece_symbols[piece + 6]
    
    for rank in range(8):
        print(' '.join(board[rank*8:(rank+1)*8]))

print_board(white_pieces, black_pieces)
