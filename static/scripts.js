let selectedPiece = null;
let selectedCell = null;

function resetGame() {
    window.location.href = "/";  // Redirect to the index route to reset the game
}

function makeMove() {
    var moveInput = $("input[name='move']").val();
    $.ajax({
        url: "/make_move",
        type: "POST",
        contentType: "application/json",
        data: JSON.stringify({ move: moveInput }),
        success: function(response) {
            updateBoard(response.board, response.turn);
            if (response.status === 'success' || response.status === 'castle') {
                if (response.turn === 'bot') {
                    botMove();
                }
            } else if (response.status === 'promote') {
                showPromotionForm();
            } else if (response.status === 'checkmate') {
                alert("Checkmate! Game over.");
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
            if (response.status === 'checkmate') {
                alert("Checkmate! Game over.");
                resetGame();
            } else if (response.status === 'stalemate') {
                alert("Stalemate! Game over.");
                resetGame();
            } else if (response.status !== 'success') {
                alert("Error with bot move.");
            }
        },
        error: function() {
            alert("Error with bot move.");
        }
    });
}


function updateBoard(board, turn) {
    // Update the board cells with the new board state
    var cells = document.querySelectorAll(".chess-board td");
    for (var i = 0; i < cells.length; i++) {
        cells[i].innerText = board[i] ? board[i] : ' ';
    }
    $(".turn-display span").text(turn);  // Update the turn display
}

function showPromotionForm() {
    // Show the promotion form
    $(".promotion-form").show();
}

$(document).ready(function() {
    $(".promotion-form").hide(); // Hide the promotion form initially
    $("#move-form").on("submit", function(event) {
        event.preventDefault();
        makeMove();
    });

    $(".chess-board td").on("click", function() {
        let cellId = $(this).attr('id');
        let cellIndex = parseInt(cellId.split('-')[1]);
        let piece = $(this).text().trim();

        if (!selectedPiece) {
            // Select a piece
            selectedPiece = piece;
            selectedCell = cellIndex;
            if (!selectedPiece) {
                selectedPiece = null;
                selectedCell = null;
            } else {
                $(this).addClass('selected');
            }
        } else {
            // If clicking on another player piece, switch the selected piece
            if (piece && ((selectedPiece.toLowerCase() === selectedPiece && piece.toLowerCase() === piece) || 
                          (selectedPiece.toUpperCase() === selectedPiece && piece.toUpperCase() === piece))) {
                $(".chess-board td").removeClass('selected');
                selectedPiece = piece;
                selectedCell = cellIndex;
                $(this).addClass('selected');
            } else {
                // Make a move
                let moveInput = selectedPiece + ' ' + cellIndex;
                $.ajax({
                    url: "/make_move",
                    type: "POST",
                    contentType: "application/json",
                    data: JSON.stringify({ move: moveInput }),
                    success: function(response) {
                        updateBoard(response.board, response.turn);
                        if (response.status === 'success' || response.status === 'castle') {
                            if (response.turn === 'bot') {
                                botMove();
                            }
                        } else if (response.status === 'promote') {
                            showPromotionForm();
                        } else if (response.status === 'checkmate') {
                            alert("Checkmate! Game over.");
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
});
