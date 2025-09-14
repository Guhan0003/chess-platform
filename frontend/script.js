// ================================
// Globals & API Configuration
// ================================
const API_BASE = "http://127.0.0.1:8000/api";
let accessToken = localStorage.getItem("access");
let refreshToken = localStorage.getItem("refresh");
let activeGameId = null; // track current game globally

// ================================
// DOM Element References
// ================================
let elements = {};

// ================================
// Authentication & Token Helpers
// ================================
function saveTokens(access, refresh) {
  accessToken = access;
  refreshToken = refresh;
  localStorage.setItem("access", access);
  localStorage.setItem("refresh", refresh);
  updateAuthUI();
}

function clearTokens() {
  accessToken = null;
  refreshToken = null;
  localStorage.removeItem("access");
  localStorage.removeItem("refresh");
  updateAuthUI();
}

function updateAuthUI() {
  if (elements.authStatus) {
    elements.authStatus.textContent = accessToken ? "Signed in" : "Signed out";
  }
}

// Generic fetch with JWT auth & auto-refresh
async function apiFetch(url, options = {}) {
  options.headers = options.headers || {};
  if (accessToken) {
    options.headers["Authorization"] = `Bearer ${accessToken}`;
  }

  let response = await fetch(url, options);

  if (response.status === 401 && refreshToken) {
    const refreshed = await refreshAccessToken();
    if (refreshed) {
      options.headers["Authorization"] = `Bearer ${accessToken}`;
      response = await fetch(url, options);
    }
  }

  return response;
}

// ================================
// API Functions
// ================================
async function registerUser(username, email, password) {
  const res = await fetch(`${API_BASE}/auth/register/`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ username, email, password }),
  });
  return { ok: res.ok, data: await res.json() };
}

async function loginUser(username, password) {
  const res = await fetch(`${API_BASE}/auth/login/`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ username, password }),
  });
  const data = await res.json();
  if (res.ok) {
    saveTokens(data.access, data.refresh);
  }
  return { ok: res.ok, data };
}

async function refreshAccessToken() {
  if (!refreshToken) return false;
  const res = await fetch(`${API_BASE}/auth/refresh/`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ refresh: refreshToken }),
  });
  if (res.ok) {
    const data = await res.json();
    saveTokens(data.access, refreshToken);
    return true;
  }
  clearTokens();
  return false;
}

async function logoutUser() {
  if (refreshToken) {
    await apiFetch(`${API_BASE}/auth/logout/`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ refresh: refreshToken }),
    });
  }
  clearTokens();
  alert("You have been logged out.");
}

async function createGame() {
  const res = await apiFetch(`${API_BASE}/games/create/`, { method: "POST" });
  return { ok: res.ok, data: await res.json() };
}

async function joinGame(gameId) {
  const res = await apiFetch(`${API_BASE}/games/${gameId}/join/`, { method: "POST" });
  return { ok: res.ok, data: await res.json() };
}
// Add this debug version to your script.js or replace the makeMove function

async function makeMove(gameId, from, to, promotion = null) {
  console.log("=== MAKING MOVE ===");
  console.log("Game ID:", gameId);
  console.log("From:", from, "To:", to);
  console.log("Promotion:", promotion);
  console.log("Access Token:", accessToken ? "Present" : "Missing");

  if (!gameId) {
    console.error("No active game selected.");
    alert("No active game selected. Please create or join a game first!");
    return { ok: false, data: { detail: "No active game selected" } };
  }

  const payload = { from_square: from, to_square: to };
  if (promotion) payload.promotion = promotion;
  
  console.log("Payload:", JSON.stringify(payload));
  
  const url = `${API_BASE}/games/${gameId}/move/`;
  console.log("URL:", url);

  try {
    const headers = {
      "Content-Type": "application/json",
    };
    
    if (accessToken) {
      headers["Authorization"] = `Bearer ${accessToken}`;
    }
    
    console.log("Headers:", headers);
    
    const res = await fetch(url, {
      method: "POST",
      headers: headers,
      body: JSON.stringify(payload),
    });

    console.log("Response status:", res.status);
    console.log("Response headers:", res.headers);
    
    const data = await res.json();
    console.log("Response data:", data);

    if (!res.ok) {
      console.error("Move failed:", data);
      return { ok: false, data };
    }

    console.log("Move successful!");
    return { ok: true, data };
  } catch (err) {
    console.error("Network/move error:", err);
    return { ok: false, data: { detail: "Network error: " + err.message } };
  }
}

// Also add this debug function to test moves manually
function testMove() {
  console.log("Testing move e2 to e4...");
  makeMove(activeGameId, "e2", "e4").then(result => {
    console.log("Test move result:", result);
  });
}

// Add this to window for manual testing in console
window.testMove = testMove;
window.debugMakeMove = makeMove;
async function getGames() {
  const res = await apiFetch(`${API_BASE}/games/`);
  return { ok: res.ok, data: await res.json() };
}

async function getGameDetail(gameId) {
  const res = await apiFetch(`${API_BASE}/games/${gameId}/`);
  return { ok: res.ok, data: await res.json() };
}

// Computer game functions  
async function createComputerGame(playerColor = 'white', difficulty = 'medium') {
  const res = await apiFetch(`${API_BASE}/games/create-computer/`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ player_color: playerColor, difficulty: difficulty })
  });
  return { ok: res.ok, data: await res.json() };
}

async function makeComputerMove(gameId, difficulty = 'medium') {
  const res = await apiFetch(`${API_BASE}/games/${gameId}/computer-move/`, {
    method: "POST", 
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ difficulty: difficulty })
  });
  return { ok: res.ok, data: await res.json() };
}

// ================================
// Chessboard Rendering
// ================================
function fenCharToAssetChar(ch) {
  const mapping = {
    p: "bP", r: "bR", n: "bN", b: "bB", q: "bQ", k: "bK",
    P: "wP", R: "wR", N: "wN", B: "wB", Q: "wQ", K: "wK",
  };
  return mapping[ch] || "";
}

function renderBoardFromFen(fen, assetBase = "./assets") {
  if (!elements.chessboard) return;
  elements.chessboard.innerHTML = "";

  const placement = fen.split(" ")[0];
  const ranks = placement.split("/");

  for (let rankIndex = 0; rankIndex < 8; rankIndex++) {
    const rankStr = ranks[rankIndex];
    let fileIndex = 0;
    for (const char of rankStr) {
      if (/\d/.test(char)) {
        const emptySquares = parseInt(char, 10);
        for (let i = 0; i < emptySquares; i++) {
          const square = document.createElement("div");
          const isLight = (rankIndex + fileIndex) % 2 === 0;
          square.className = `square ${isLight ? 'light' : 'dark'}`;
          square.dataset.coord = String.fromCharCode(97 + fileIndex) + (8 - rankIndex);
          elements.chessboard.appendChild(square);
          fileIndex++;
        }
      } else {
        const square = document.createElement("div");
        const isLight = (rankIndex + fileIndex) % 2 === 0;
        square.className = `square ${isLight ? 'light' : 'dark'}`;
        square.dataset.coord = String.fromCharCode(97 + fileIndex) + (8 - rankIndex);

        const assetName = fenCharToAssetChar(char);
        if (assetName) {
          const img = document.createElement("img");
          img.src = `${assetBase}/${assetName}.png`;
          img.alt = assetName;
          img.draggable = false;
          square.appendChild(img);
        }
        elements.chessboard.appendChild(square);
        fileIndex++;
      }
    }
  }

  // Enable click-to-move after rendering
  enableClickToMove();
}

// ================================
// Click-to-Move Support
// ================================
let selectedSquare = null;

function enableClickToMove() {
  if (!elements.chessboard) return;

  const squares = elements.chessboard.querySelectorAll(".square");
  squares.forEach(square => {
    square.addEventListener("click", async () => {
      const coord = square.dataset.coord;

      if (!activeGameId) {
        alert("No active game selected.");
        return;
      }

      if (!selectedSquare) {
        // First click: select source
        selectedSquare = coord;
        square.classList.add("selected");
      } else {
        // Second click: make move
        const from = selectedSquare;
        const to = coord;

        // Remove selection highlight
        const prevSquare = [...squares].find(sq => sq.dataset.coord === from);
        prevSquare?.classList.remove("selected");
        selectedSquare = null;

        // (optional) quick promotion prompt if pawn moves to last rank
        let promotion = null;
        const fromRank = parseInt(from[1], 10);
        const toRank = parseInt(to[1], 10);
        if (fromRank === 7 && toRank === 8) {
          // white pawn promotion
          promotion = prompt("Promote to (q/r/b/n)? Leave empty for queen.", "q") || "q";
        }
        if (fromRank === 2 && toRank === 1) {
          // black pawn promotion
          promotion = prompt("Promote to (q/r/b/n)? Leave empty for queen.", "q") || "q";
        }

        const { ok, data } = await makeMove(activeGameId, from, to, promotion);
        if (ok) {
          // refresh full game (ensures FEN, move list, turn)
          await updateGameDetails(activeGameId);
        } else {
          alert(`Invalid move: ${JSON.stringify(data)}`);
        }
      }
    });
  });
}

// ================================
// UI Update Functions
// ================================
async function updateGamesList() {
  if (!elements.gamesList) return;
  elements.gamesList.innerHTML = "Loading...";
  const { ok, data } = await getGames();
  if (!ok) {
    elements.gamesList.innerHTML = "Failed to load games. Are you logged in?";
    return;
  }

  elements.gamesList.innerHTML = "";
  if (data.length === 0) {
    elements.gamesList.innerHTML = "No available games.";
    return;
  }

  data.forEach(game => {
    const item = document.createElement("div");
    item.className = "game-item";
    item.innerHTML = `
      <div class="game-meta">
        <span class="players">#${game.id}: ${game.white_player_username || '...'} vs ${game.black_player_username || '...'}</span>
        <span class="status">${game.status}</span>
      </div>
      <div class="row">
        <button class="view-game-btn" data-game-id="${game.id}">View</button>
      </div>
    `;
    elements.gamesList.appendChild(item);
  });
}

// kept (as requested) but now delegates to makeMove()
async function sendMove(from, to, promotion = null) {
  if (!activeGameId) {
    alert("No active game selected.");
    return;
  }

  const result = await makeMove(activeGameId, from, to, promotion);
  if (!result.ok) {
    alert("Invalid move: " + JSON.stringify(result.data));
    return;
  }
  await updateGameDetails(activeGameId);
}

async function updateGameDetails(gameId) {
  const { ok, data: game } = await getGameDetail(gameId);
  if (!ok) {
    alert("Could not fetch game details.");
    return;
  }

  if (elements.detailsOutput) {
    elements.detailsOutput.textContent = JSON.stringify(game, null, 2);
  }

  if (elements.currentGameId) elements.currentGameId.textContent = game.id;
  activeGameId = game.id; // track current active game

  if (elements.currentGameStatus) elements.currentGameStatus.textContent = game.status;
  if (elements.currentTurn) elements.currentTurn.textContent = game.fen.split(" ")[1] === 'w' ? 'White' : 'Black';

  if (elements.moveList) {
    elements.moveList.innerHTML = "";
    game.moves.forEach(move => {
      const li = document.createElement("li");
      li.textContent = `${move.move_number}. ${move.notation}`;
      elements.moveList.appendChild(li);
    });
  }

  const assetBase = elements.chessboard.dataset.assetBase || "./assets";
  renderBoardFromFen(game.fen, assetBase);
}

// ================================
// Event Listeners Setup
// ================================
function initializeEventListeners() {
  elements.loginForm?.addEventListener("submit", async (e) => {
    e.preventDefault();
    const username = elements.loginForm.elements.username.value;
    const password = elements.loginForm.elements.password.value;
    const { ok, data } = await loginUser(username, password);
    if (ok) {
      alert("Login successful!");
      await updateGamesList();
    } else {
      alert(`Login failed: ${JSON.stringify(data)}`);
    }
  });

  elements.registerForm?.addEventListener("submit", async (e) => {
    e.preventDefault();
    const username = elements.registerForm.elements.username.value;
    const email = elements.registerForm.elements.email.value;
    const password = elements.registerForm.elements.password.value;
    const { ok, data } = await registerUser(username, email, password);
    if (ok) {
      alert("Registration successful! Please log in.");
    } else {
      alert(`Registration failed: ${JSON.stringify(data)}`);
    }
  });

  elements.btnLogout?.addEventListener("click", logoutUser);

  elements.btnRefresh?.addEventListener("click", async () => {
    const success = await refreshAccessToken();
    alert(success ? "Token refreshed." : "Failed to refresh token.");
  });

  elements.btnCreate?.addEventListener("click", async () => {
    const { ok, data } = await createGame();
    if (ok) {
      alert(`Game #${data.id} created!`);
      await updateGamesList();
      await updateGameDetails(data.id); // auto-open created game
    } else {
      alert(`Failed to create game: ${JSON.stringify(data)}`);
    }
  });

  elements.joinForm?.addEventListener("submit", async (e) => {
    e.preventDefault();
    const gameId = elements.joinForm.elements.gameId.value;
    const { ok, data } = await joinGame(gameId);
    if (ok) {
      alert(`Successfully joined game #${data.id}`);
      await updateGamesList();
      await updateGameDetails(data.id); // open joined game
    } else {
      alert(`Failed to join game: ${JSON.stringify(data)}`);
    }
  });

  elements.moveForm?.addEventListener("submit", async (e) => {
    e.preventDefault();
    const gameId = elements.moveForm.elements.gameId.value;
    const from = elements.moveForm.elements.from.value;
    const to = elements.moveForm.elements.to.value;
    const promotion = elements.moveForm.elements.promotion.value || null;

    const { ok, data } = await makeMove(gameId || activeGameId, from, to, promotion);
    if (ok) {
      alert("Move successful!");
      await updateGameDetails(gameId || activeGameId);
    } else {
      alert(`Invalid move: ${JSON.stringify(data)}`);
    }
  });

  elements.detailsForm?.addEventListener("submit", async (e) => {
    e.preventDefault();
    const gameId = elements.detailsForm.elements.gameId.value;
    if (gameId) {
      await updateGameDetails(gameId);
    }
  });

  elements.gamesList?.addEventListener("click", (e) => {
    if (e.target.classList.contains("view-game-btn")) {
      const gameId = e.target.dataset.gameId;
      updateGameDetails(gameId); // set activeGameId as well
    }
  });

  // Computer game event listeners
  elements.btnCreateComputer?.addEventListener("click", async () => {
    const difficulty = elements.computerDifficulty?.value || 'medium';
    const playerColor = elements.playerColor?.value || 'white';
    
    const { ok, data } = await createComputerGame(playerColor, difficulty);
    if (ok) {
      alert(`Computer game #${data.id} created! Difficulty: ${difficulty}, You play as: ${playerColor}`);
      await updateGamesList();
      await updateGameDetails(data.id);
    } else {
      alert(`Failed to create computer game: ${JSON.stringify(data)}`);
    }
  });

  elements.btnComputerMove?.addEventListener("click", async () => {
    if (!activeGameId) {
      alert("No active game selected.");
      return;
    }
    
    const difficulty = elements.computerDifficulty?.value || 'medium';
    
    const { ok, data } = await makeComputerMove(activeGameId, difficulty);
    if (ok) {
      alert("Computer made its move!");
      await updateGameDetails(activeGameId);
    } else {
      alert(`Computer move failed: ${JSON.stringify(data)}`);
    }
  });
}

// ================================
// Initial Page Load
// ================================
document.addEventListener("DOMContentLoaded", () => {
  elements = {
    authStatus: document.getElementById("auth-status"),
    loginForm: document.getElementById("loginForm"),
    registerForm: document.getElementById("registerForm"),
    btnLogout: document.getElementById("btn-logout"),
    btnRefresh: document.getElementById("btn-refresh"),
    btnCreate: document.getElementById("btn-create"),
    btnCreateComputer: document.getElementById("btn-create-computer"),
    btnComputerMove: document.getElementById("btn-computer-move"),
    computerDifficulty: document.getElementById("computer-difficulty"),
    playerColor: document.getElementById("player-color"),
    joinForm: document.getElementById("joinForm"),
    moveForm: document.getElementById("moveForm"),
    detailsForm: document.getElementById("detailsForm"),
    gamesList: document.getElementById("games-list"),
    detailsOutput: document.getElementById("details-output"),
    chessboard: document.getElementById("chessboard"),
    currentGameId: document.getElementById("current-game-id"),
    currentGameStatus: document.getElementById("current-game-status"),
    currentTurn: document.getElementById("current-turn"),
    moveList: document.getElementById("move-list"),
  };

  initializeEventListeners();
  updateAuthUI();

  // Render a default board on load
  const startFen = "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1";
  const assetBase = elements.chessboard?.dataset.assetBase || "./assets";
  renderBoardFromFen(startFen, assetBase);

  // Load available games (requires login)
  updateGamesList();
});