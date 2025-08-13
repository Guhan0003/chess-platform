document.addEventListener("DOMContentLoaded", function () {
    const gamesList = document.getElementById("gamesList");
    const createGameBtn = document.getElementById("createGameBtn");

    // Load games on page load
    fetchGames();

    // Event: Create new game
    createGameBtn.addEventListener("click", function () {
        fetch("/create/", {
            method: "POST",
            headers: {
                "X-CSRFToken": getCSRFToken(),
                "Content-Type": "application/json"
            }
        })
        .then(res => res.json())
        .then(() => fetchGames())
        .catch(err => console.error("Error creating game:", err));
    });

    // Fetch available games
    function fetchGames() {
        fetch("/games/")
            .then(res => res.json())
            .then(data => {
                gamesList.innerHTML = ""; // Clear old list

                if (data.length === 0) {
                    gamesList.innerHTML = "<li>No games available.</li>";
                    return;
                }

                data.forEach(game => {
                    const li = document.createElement("li");
                    li.innerHTML = `
                        Game #${game.id} - Status: ${game.status}
                        <button data-id="${game.id}" class="join-btn">Join Game</button>
                    `;
                    gamesList.appendChild(li);
                });

                // Attach join event
                document.querySelectorAll(".join-btn").forEach(btn => {
                    btn.addEventListener("click", function () {
                        const gameId = this.getAttribute("data-id");
                        joinGame(gameId);
                    });
                });
            })
            .catch(err => console.error("Error fetching games:", err));
    }

    // Join a game
    function joinGame(gameId) {
        fetch(`/${gameId}/join/`, {
            method: "POST",
            headers: {
                "X-CSRFToken": getCSRFToken(),
                "Content-Type": "application/json"
            }
        })
        .then(res => res.json())
        .then(() => fetchGames())
        .catch(err => console.error("Error joining game:", err));
    }

    // Get CSRF token from cookies
    function getCSRFToken() {
        const name = "csrftoken=";
        const decoded = decodeURIComponent(document.cookie);
        const cookies = decoded.split(";");
        for (let cookie of cookies) {
            cookie = cookie.trim();
            if (cookie.startsWith(name)) {
                return cookie.substring(name.length, cookie.length);
            }
        }
        return "";
    }
});
