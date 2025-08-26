// ================================
// Globals
// ================================
const API_BASE = "http://127.0.0.1:8000/api";
let accessToken = localStorage.getItem("access");
let refreshToken = localStorage.getItem("refresh");

// ================================
// Helper Functions
// ================================

// Generic fetch with JWT auth & auto-refresh
async function apiFetch(url, options = {}) {
  if (!options.headers) options.headers = {};
  if (accessToken) {
    options.headers["Authorization"] = `Bearer ${accessToken}`;
  }

  let response = await fetch(url, options);

  // If token expired, try refreshing once
  if (response.status === 401 && refreshToken) {
    const refreshed = await refreshAccessToken();
    if (refreshed) {
      options.headers["Authorization"] = `Bearer ${accessToken}`;
      response = await fetch(url, options);
    }
  }

  return response;
}

function saveTokens(access, refresh) {
  accessToken = access;
  refreshToken = refresh;
  localStorage.setItem("access", access);
  localStorage.setItem("refresh", refresh);
}

function clearTokens() {
  accessToken = null;
  refreshToken = null;
  localStorage.removeItem("access");
  localStorage.removeItem("refresh");
}

// ================================
// Auth
// ================================
async function registerUser(username, email, password) {
  const res = await fetch(`${API_BASE}/auth/register/`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ username, email, password })
  });
  return res.json();
}

async function loginUser(username, password) {
  const res = await fetch(`${API_BASE}/auth/login/`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ username, password })
  });
  if (res.ok) {
    const data = await res.json();
    saveTokens(data.access, data.refresh);
  }
  return res.json();
}

async function refreshAccessToken() {
  if (!refreshToken) return false;
  const res = await fetch(`${API_BASE}/auth/refresh/`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ refresh: refreshToken })
  });

  if (res.ok) {
    const data = await res.json();
    saveTokens(data.access, refreshToken);
    return true;
  } else {
    clearTokens();
    return false;
  }
}

async function logoutUser() {
  await apiFetch(`${API_BASE}/auth/logout/`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ refresh: refreshToken })
  });
  clearTokens();
}

// ================================
// Games
// ================================
async function createGame() {
  const res = await apiFetch(`${API_BASE}/games/create/`, {
    method: "POST",
    headers: { "Content-Type": "application/json" }
  });
  return res.json();
}

async function joinGame(gameId) {
  const res = await apiFetch(`${API_BASE}/games/${gameId}/join/`, {
    method: "POST",
    headers: { "Content-Type": "application/json" }
  });
  return res.json();
}

async function makeMove(gameId, from, to) {
  const res = await apiFetch(`${API_BASE}/games/${gameId}/move/`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ from_square: from, to_square: to })
  });
  return res.json();
}

async function getGames() {
  const res = await apiFetch(`${API_BASE}/games/`);
  return res.json();
}

async function getGameDetail(gameId) {
  const res = await apiFetch(`${API_BASE}/games/${gameId}/`);
  return res.json();
}

// ================================
// Chessboard Rendering (Updated)
// ================================

const boardElement = document.getElementById("chessboard");

// Helper: map FEN char -> asset filename
function fenCharToAssetChar(ch) {
  if (!ch || ch.length !== 1) return null;
  const isWhite = ch === ch.toUpperCase();
  const pieceLetter = ch.toUpperCase(); // 'P','R','N','B','Q','K'
  return (isWhite ? 'w' : 'b') + pieceLetter; // e.g. 'wP' or 'bK'
}

// Render board from FEN
function renderBoardFromFen(fen, assetBase = "./assets") {
  const boardEl = document.getElementById("chessboard");
  boardEl.innerHTML = "";

  const placement = fen.split(" ")[0];
  const ranks = placement.split("/");

  for (let rankIndex = 0; rankIndex < 8; rankIndex++) {
    const rankStr = ranks[rankIndex];
    let file = 0;

    for (const ch of rankStr) {
      if (/\d/.test(ch)) {
        const empties = parseInt(ch, 10);
        for (let i = 0; i < empties; i++) {
          const sq = document.createElement("div");
          sq.className = "square " + (((rankIndex + file) % 2 === 0) ? "light" : "dark");
          boardEl.appendChild(sq);
          file++;
        }
      } else {
        const assetName = fenCharToAssetChar(ch);
        const sq = document.createElement("div");
        sq.className = "square " + (((rankIndex + file) % 2 === 0) ? "light" : "dark");

        const img = document.createElement("img");
        img.src = `${assetBase}/${assetName}.png`;
        img.alt = assetName;
        img.draggable = false;
        sq.appendChild(img);

        boardEl.appendChild(sq);
        file++;
      }
    }
  }
}

// ================================
// UI Handlers
// ================================

document.addEventListener("DOMContentLoaded", () => {
  // Example: auto-load games on page load
  loadGameList();
});

async function loadGameList() {
  const games = await getGames();
  const gameList = document.getElementById("game-list");
  gameList.innerHTML = "";

  games.forEach(game => {
    const card = document.createElement("div");
    card.className = "game-card";
    card.innerHTML = `
      <p><strong>Game #${game.id}</strong></p>
      <p>Status: ${game.status}</p>
      <p>White: ${game.white_player_username || "?"}</p>
      <p>Black: ${game.black_player_username || "?"}</p>
      <button onclick="joinGame(${game.id})">Join</button>
      <button onclick="viewGame(${game.id})">View</button>
    `;
    gameList.appendChild(card);
  });
}

async function viewGame(gameId) {
  const game = await getGameDetail(gameId);
  renderBoardFromFen(game.fen); // Updated function call
}
