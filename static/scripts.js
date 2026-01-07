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

function qs(sel, root = document) {
  return root.querySelector(sel);
}

function qsa(sel, root = document) {
  return Array.from(root.querySelectorAll(sel));
}

function setTurn(turn) {
  const turnSpan = qs(".turn-display span");
  if (turnSpan) turnSpan.textContent = turn;
  document.body.setAttribute("data-turn", turn);
}

function isPlayersTurn() {
  return document.body.getAttribute("data-turn") === "player";
}

async function postJson(url, payload) {
  const resp = await fetch(url, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload || {}),
  });
  const data = await resp.json().catch(() => ({}));
  if (!resp.ok) throw new Error(data?.status || `HTTP ${resp.status}`);
  return data;
}

function resetGame() {
  window.location.href = "/"; // reset via server
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
  const form = qs(".promotion-form");
  if (form) form.style.display = "block";
}

function hidePromotionForm() {
  promotionOpen = false;
  const form = qs(".promotion-form");
  if (form) form.style.display = "none";
}

function notifyCheckIfAny(resp) {
  if (resp && resp.in_check === true) {
    const side = resp.turn; // side to move (and in check)
    Toast.show(`${side.toUpperCase()} is in check!`, "warning", { timeout: 2200 });
  }
}

function makeMove(moveInput) {
  if (!moveInput) return;
  postJson("/make_move", { move: moveInput })
    .then((response) => {
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
    })
    .catch(() => {
      Toast.show("Error making move.", "error", { timeout: 2400 });
    });
}

function sendPromotion(choice) {
  postJson("/promote", { piece: choice })
    .then((response) => {
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
    })
    .catch(() => {
      Toast.show("Error promoting pawn.", "error", { timeout: 2400 });
    });
}

function botMove() {
  postJson("/bot_move")
    .then((response) => {
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
    })
    .catch(() => {
      Toast.show("Error with bot move.", "error", { timeout: 2400 });
    });
}

// Keep a callable function if template uses inline onclick
function castleMove() {
  if (!isPlayersTurn() || promotionOpen) return;
  makeMove("castle");
}

function clearSelection() {
  qsa(".chess-board td.selected").forEach((td) => td.classList.remove("selected"));
}

document.addEventListener("DOMContentLoaded", () => {
  hidePromotionForm();

  // Promotion form handler (if present in template)
  const promotionForm = qs(".promotion-form");
  if (promotionForm) promotionForm.addEventListener("submit", function (e) {
    e.preventDefault();
    const sel = qs("#promotion_piece");
    const choice = ((sel && sel.value) || "QUEEN").toUpperCase();
    sendPromotion(choice);
  });

  qsa(".chess-board td").forEach((cell) => cell.addEventListener("click", function () {
    // block clicks if it's not the player's turn or promotion dialog is open
    if (!isPlayersTurn() || promotionOpen) return;

    const cellIndex = parseInt(this.id.split("-")[1], 10);
    const img = qs("img", this);
    const piece = img ? img.getAttribute("alt") : null;

    // First click: select a player piece (lowercase name)
    if (!selectedPiece) {
      if (!piece || piece[0] !== piece[0].toLowerCase()) {
        // not a player piece
        return;
      }
      selectedPiece = piece;
      clearSelection();
      this.classList.add("selected");
      return;
    }

    // Clicking another player's piece switches selection
    if (piece && piece[0] === piece[0].toLowerCase()) {
      clearSelection();
      selectedPiece = piece;
      this.classList.add("selected");
      return;
    }

    // Attempt a move: "<piece> <destIndex>"
    const moveInput = `${selectedPiece} ${cellIndex}`;
    selectedPiece = null;
    clearSelection();
    makeMove(moveInput);
  }));

  qsa(".chess-board td").forEach((cell) => {
    cell.addEventListener("mouseenter", () => cell.classList.add("hover"));
    cell.addEventListener("mouseleave", () => cell.classList.remove("hover"));
  });

  // Buttons (works with or without inline onclicks)
  const btnCastle = qs("#btn-castle");
  if (btnCastle) btnCastle.addEventListener("click", castleMove);
  const btnReset = qs("#btn-reset");
  if (btnReset) btnReset.addEventListener("click", resetGame);

  qsa(".github-link").forEach((link) => {
    const url = link.getAttribute("data-url") || link.getAttribute("href") || "";
    const username = (url.split("github.com/")[1] || "").split("/")[0] || "GitHub";
    link.textContent = username;
  });
});
