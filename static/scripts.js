// ----------------------
// Toasts (no dependency)
// ----------------------
const Toast = (() => {
  const rootId = "toast-root";
  const icons = {
    info: "ℹ️",
    success: "✅",
    warning: "⚠️",
    error: "⛔",
    check: "♟️",
    mate: "♚",
  };

  function ensureRoot() {
    let root = document.getElementById(rootId);
    if (!root) {
      root = document.createElement("div");
      root.id = rootId;
      document.body.appendChild(root);
    }
    return root;
  }

  function show(message, type = "info", opts = {}) {
    const { timeout = 2800, persist = false } = opts;
    const root = ensureRoot();

    const toast = document.createElement("div");
    toast.className = `toast toast-${type}`;
    toast.setAttribute("role", "status");

    const icon = document.createElement("span");
    icon.className = "toast-icon";
    icon.textContent = icons[type] || icons.info;

    const text = document.createElement("div");
    text.className = "toast-text";
    text.textContent = message;

    const close = document.createElement("button");
    close.className = "toast-close";
    close.setAttribute("aria-label", "Close notification");
    close.innerHTML = "&times;";
    close.onclick = () => dismiss(toast);

    toast.appendChild(icon);
    toast.appendChild(text);
    toast.appendChild(close);

    root.appendChild(toast);

    // Enter animation
    requestAnimationFrame(() => {
      toast.classList.add("in");
    });

    if (!persist) {
      setTimeout(() => dismiss(toast), timeout);
    }
    return toast;
  }

  function dismiss(node) {
    if (!node) return;
    node.classList.remove("in");
    node.classList.add("out");
    node.addEventListener(
      "animationend",
      () => node.parentElement && node.parentElement.removeChild(node),
      { once: true }
    );
  }

  return { show, dismiss };
})();

// ----------------------
// Game UI logic
// ----------------------
let selectedPiece = null;   // piece name like 'p2' or 'N1'
let promotionOpen = false;

function resetGame() {
  window.location.href = "/"; // reset via server
}

function setTurn(turn) {
  $(".turn-display span").text(turn);
  $("body").attr("data-turn", turn);
}

function updateBoard(board, turn) {
  const cells = document.querySelectorAll(".chess-board td");
  for (let i = 0; i < cells.length; i++) {
    const piece = board[i];
    if (piece) {
      const t = piece[0].toLowerCase(); // 'p','r',...
      const colorClass = piece[0] === piece[0].toUpperCase() ? "black-piece" : "white-piece";
      cells[i].innerHTML = `<img src="/static/icons/${t}.svg" class="${colorClass}" alt="${piece}" />`;
    } else {
      cells[i].innerHTML = "";
    }
  }
  setTurn(turn);
}

function showPromotionForm() {
  promotionOpen = true;
  $(".promotion-form").show();
}

function hidePromotionForm() {
  promotionOpen = false;
  $(".promotion-form").hide();
}

function notifyCheckIfAny(resp) {
  if (resp && resp.in_check === true) {
    const side = resp.turn; // side to move (and in check)
    Toast.show(`${side.toUpperCase()} is in check!`, "warning", { timeout: 2200 });
  }
}

function makeMove(moveInput) {
  if (!moveInput) return;
  $.ajax({
    url: "/make_move",
    type: "POST",
    contentType: "application/json",
    data: JSON.stringify({ move: moveInput }),
    success: function (response) {
      updateBoard(response.board, response.turn);
      switch (response.status) {
        case "success":
        case "castle":
          notifyCheckIfAny(response);
          if (response.turn === "bot") botMove();
          break;
        case "promote":
          Toast.show("Pawn reached last rank — choose a promotion.", "info", { timeout: 2500 });
          showPromotionForm();
          break;
        case "checkmate":
          Toast.show(`Checkmate! Winner: ${response.winner}`, "mate", { timeout: 1800 });
          setTimeout(resetGame, 1400);
          break;
        case "stalemate":
          Toast.show("Stalemate — draw.", "info", { timeout: 2000 });
          setTimeout(resetGame, 1400);
          break;
        case "invalid-castle":
          Toast.show("Castling is not legal in this position.", "error", { timeout: 2600 });
          break;
        default:
          Toast.show(response.status || "Invalid move.", "error", { timeout: 2200 });
      }
    },
    error: function () {
      Toast.show("Error making move.", "error", { timeout: 2400 });
    },
  });
}

function sendPromotion(choice) {
  $.ajax({
    url: "/promote",
    type: "POST",
    contentType: "application/json",
    data: JSON.stringify({ piece: choice }),
    success: function (response) {
      updateBoard(response.board, response.turn);
      hidePromotionForm();

      if (response.status === "checkmate") {
        Toast.show(`Checkmate! Winner: ${response.winner}`, "mate", { timeout: 1800 });
        setTimeout(resetGame, 1400);
        return;
      }
      if (response.status === "stalemate") {
        Toast.show("Stalemate — draw.", "info", { timeout: 2000 });
        setTimeout(resetGame, 1400);
        return;
      }
      if (response.status === "promoted") {
        Toast.show("Pawn promoted.", "success", { timeout: 1600 });
        notifyCheckIfAny(response);
        if (response.turn === "bot") botMove();
      }
    },
    error: function () {
      Toast.show("Error promoting pawn.", "error", { timeout: 2400 });
    },
  });
}

function botMove() {
  $.ajax({
    url: "/bot_move",
    type: "POST",
    success: function (response) {
      updateBoard(response.board, response.turn);
      if (response.status === "checkmate") {
        Toast.show(`Checkmate! Winner: ${response.winner}`, "mate", { timeout: 1800 });
        setTimeout(resetGame, 1400);
      } else if (response.status === "stalemate") {
        Toast.show("Stalemate — draw.", "info", { timeout: 2000 });
        setTimeout(resetGame, 1400);
      } else if (response.status === "success") {
        notifyCheckIfAny(response);
      } else if (response.status === "error") {
        Toast.show("Bot couldn't find a valid move.", "error", { timeout: 2200 });
      }
    },
    error: function () {
      Toast.show("Error with bot move.", "error", { timeout: 2400 });
    },
  });
}

// Keep a callable function if template uses inline onclick
function castleMove() {
  if ($("body").attr("data-turn") !== "player" || promotionOpen) return;
  makeMove("castle");
}


$(document).ready(function () {
  hidePromotionForm();

  // Promotion form handler (if present in template)
  $(".promotion-form").on("submit", function (e) {
    e.preventDefault();
    const choice = ($("#promotion_piece").val() || "QUEEN").toUpperCase();
    sendPromotion(choice);
  });

  $(".chess-board td").on("click", function () {
    // block clicks if it's not the player's turn or promotion dialog is open
    if ($("body").attr("data-turn") !== "player" || promotionOpen) return;

    const cellId = $(this).attr("id");
    const cellIndex = parseInt(cellId.split("-")[1], 10);
    const img = $(this).find("img");
    const piece = img.length ? img.attr("alt") : null;

    // First click: select a player piece (lowercase name)
    if (!selectedPiece) {
      if (!piece || piece[0] !== piece[0].toLowerCase()) {
        // not a player piece
        return;
      }
      selectedPiece = piece;
      $(".chess-board td").removeClass("selected");
      $(this).addClass("selected");
      return;
    }

    // Clicking another player's piece switches selection
    if (piece && piece[0] === piece[0].toLowerCase()) {
      $(".chess-board td").removeClass("selected");
      selectedPiece = piece;
      $(this).addClass("selected");
      return;
    }

    // Attempt a move: "<piece> <destIndex>"
    const moveInput = `${selectedPiece} ${cellIndex}`;
    selectedPiece = null;
    $(".chess-board td").removeClass("selected");
    makeMove(moveInput);
  });

  $(".chess-board td").hover(
    function () { $(this).addClass("hover"); },
    function () { $(this).removeClass("hover"); }
  );

  // Buttons (works with or without inline onclicks)
  $("#btn-castle").on("click", castleMove);
  $("#btn-reset").on("click", resetGame);

  $(".github-link").each(function () {
    const link = $(this);
    const url = link.data("url");

    // GitHub blocks CORS for HTML, so use GitHub's public API to get user info instead
    // Extract username from URL
    const username = url.split("github.com/")[1].split("/")[0];

    fetch(`https://api.github.com/users/${username}`)
      .then(response => response.json())
      .then(data => {
        if (data && data.name) {
          link.text(data.name);
        } else if (data && data.login) {
          link.text(data.login);
        } else {
          link.text(username);
        }
      })
      .catch(() => {
        link.text(username);
      });
  });
});
