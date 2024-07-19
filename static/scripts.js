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
            } else {
                alert("Invalid move!");
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
        if (!selectedPiece) {
            // Select a piece
            selectedPiece = $(this).text().trim();
            selectedCell = cellIndex;
            if (!selectedPiece) {
                selectedPiece = null;
                selectedCell = null;
            } else {
                $(this).addClass('selected');
            }
        } else {
            // Make a move
            let moveInput = selectedPiece + ' ' + cellId.split('-')[1];
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
                    } else {
                        alert("Invalid move!");
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
    });
});
