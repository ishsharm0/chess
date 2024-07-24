let selectedPiece = null;
let selectedCell = null;

function resetGame() {
    window.location.href = "/";  // Redirect to the index route to reset the game
}

function makeMove() {
    var moveInput = $("input[name='move']").val();
    console.log(`Making move with input: ${moveInput}`);
    $.ajax({
        url: "/make_move",
        type: "POST",
        contentType: "application/json",
        data: JSON.stringify({ move: moveInput }),
        success: function(response) {
            updateBoard(response.board, response.turn);
            console.log(`Move result: ${response.status}`);
            if (response.status === 'success' || response.status === 'castle') {
                if (response.turn === 'bot') {
                    botMove();
                }
            } else if (response.status === 'promote') {
                showPromotionForm();
            } else if (response.status === 'checkmate') {
                alert(`Checkmate! Winner: ${response.winner}`);
                resetGame();
            } else if (response.status === 'stalemate') {
                alert("Stalemate! Game over.");
                resetGame();
            } else {
                alert(response.status);
            }
        },
        error: function() {
            alert("Error making move.");
        }
    });
}

function botMove() {
    $.ajax({
        url: "/bot_move",
        type: "POST",
        success: function(response) {
            updateBoard(response.board, response.turn);
            console.log(`Bot move result: ${response.status}`);
            if (response.status === 'checkmate') {
                alert(`Checkmate! Winner: ${response.winner}`);
                resetGame();
            } else if (response.status === 'stalemate') {
                alert("Stalemate! Game over.");
                resetGame();
            }
        },
        error: function() {
            alert("Error with bot move.");
        }
    });
}

function updateBoard(board, turn) {
    console.log(`Updating board. Turn: ${turn}`);
    // Update the board cells with the new board state
    var cells = document.querySelectorAll(".chess-board td");
    for (var i = 0; i < cells.length; i++) {
        let piece = board[i];
        if (piece) {
            let pieceType = piece[0].toLowerCase(); // 'p', 'r', etc.
            let colorClass = (piece[0] === piece[0].toUpperCase()) ? 'white-piece' : 'black-piece';
            cells[i].innerHTML = `<img src="/static/icons/${pieceType}.svg" class="${colorClass}" alt="${piece}" />`;
        } else {
            cells[i].innerHTML = '';
        }
    }
    $(".turn-display span").text(turn);
    $("body").attr("data-turn", turn);
}

function showPromotionForm() {
    // Show the promotion form
    $(".promotion-form").show();
}

function selectCell(row, col) {
    if (selectedCell) {
        const moveInput = `${selectedCell.row}${selectedCell.col} ${row}${col}`;
        $("input[name='move']").val(moveInput);
        makeMove();
        selectedCell = null;
    } else {
        selectedCell = { row, col };
    }
}

$(document).ready(function() {
    $(".promotion-form").hide(); // Hide the promotion form initially
    $("#move-form").on("submit", function(event) {
        event.preventDefault();
        makeMove();
    });

    $(".chess-board td").on("click", function() {
        if ($("body").attr("data-turn") !== "player") {
            return; // Do nothing if it's not the player's turn
        }
        
        let cellId = $(this).attr('id');
        let cellIndex = parseInt(cellId.split('-')[1]);
        let piece = $(this).find('img').attr('alt');

        console.log(`Clicked cell: ${cellId}, piece: ${piece}, cellIndex: ${cellIndex}`);

        if (!selectedPiece) {
            // Select a piece
            selectedPiece = piece;
            selectedCell = cellIndex;
            if (!selectedPiece) {
                selectedPiece = null;
                selectedCell = null;
            } else {
                $(".chess-board td").removeClass('selected');
                $(this).addClass('selected');
                console.log(`Selected piece: ${selectedPiece} at cell: ${selectedCell}`);
            }
        } else {
            // If clicking on another player piece, switch the selected piece
            if (piece && ((selectedPiece.toLowerCase() === selectedPiece && piece.toLowerCase() === piece) || 
                          (selectedPiece.toUpperCase() === selectedPiece && piece.toUpperCase() === piece))) {
                $(".chess-board td").removeClass('selected');
                selectedPiece = piece;
                selectedCell = cellIndex;
                $(this).addClass('selected');
                console.log(`Switched selected piece to: ${selectedPiece} at cell: ${selectedCell}`);
            } else {
                // Make a move
                let moveInput = selectedPiece + ' ' + cellIndex;
                console.log(`Move input: ${moveInput}`);
                $.ajax({
                    url: "/make_move",
                    type: "POST",
                    contentType: "application/json",
                    data: JSON.stringify({ move: moveInput }),
                    success: function(response) {
                        updateBoard(response.board, response.turn);
                        console.log(`Move result: ${response.status}`);
                        if (response.status === 'success' || response.status === 'castle') {
                            if (response.turn === 'bot') {
                                botMove();
                            }
                        } else if (response.status === 'promote') {
                            showPromotionForm();
                        } else if (response.status === 'checkmate') {
                            alert(`Checkmate! Winner: ${response.winner}`);
                            resetGame();
                        } else if (response.status === 'stalemate') {
                            alert("Stalemate! Game over.");
                            resetGame();
                        } else {
                            alert(response.status);
                        }
                        selectedPiece = null;
                        selectedCell = null;
                        $(".chess-board td").removeClass('selected');
                    },
                    error: function() {
                        alert("Error making move.");
                        selectedPiece = null;
                        selectedCell = null;
                        $(".chess-board td").removeClass('selected');
                    }
                });
            }
        }
    });

    $(".chess-board td").hover(
        function() {
            $(this).addClass('hover');
        },
        function() {
            $(this).removeClass('hover');
        }
    );
});
