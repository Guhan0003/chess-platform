package com.example.chess_platform.ui.game

import com.example.chess_platform.domain.model.*

/**
 * User's role in the game
 */
enum class GameRole {
    PLAYER,      // Active player in the game
    SPECTATOR,   // Watching a live game
    REPLAY       // Viewing a finished game / replay
}

/**
 * UI State for the active game screen
 */
data class GameUiState(
    val isLoading: Boolean = true,
    val error: String? = null,
    
    // Game data
    val game: Game? = null,
    val gameId: Int = 0,
    
    // User role - determines what actions are visible
    val role: GameRole = GameRole.PLAYER,
    val currentUserId: Int? = null,
    
    // Board state
    val fen: String = "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1",
    val isFlipped: Boolean = false,
    val selectedSquare: String? = null,
    val legalMoves: List<LegalMoveInfo> = emptyList(),
    val lastMove: Pair<String, String>? = null,
    
    // Game status
    val isCheck: Boolean = false,
    val isCheckmate: Boolean = false,
    val isStalemate: Boolean = false,
    val isDraw: Boolean = false,
    val isTimeout: Boolean = false,
    val isResigned: Boolean = false,
    val isGameOver: Boolean = false,
    val result: String? = null,
    val winnerName: String? = null,
    
    // Player info
    val playerColor: PlayerSide = PlayerSide.WHITE,
    val isMyTurn: Boolean = true,
    val isComputerGame: Boolean = false,
    val isWaitingForComputer: Boolean = false,
    
    // Timer (in seconds)
    val whiteTime: Double = 600.0,
    val blackTime: Double = 600.0,
    val whiteTimePressure: TimePressureLevel = TimePressureLevel.NONE,
    val blackTimePressure: TimePressureLevel = TimePressureLevel.NONE,
    val increment: Int = 0,
    
    // Move history
    val moves: List<Move> = emptyList(),
    
    // Dialogs
    val showResignDialog: Boolean = false,
    val showDrawOfferDialog: Boolean = false,
    val showDrawReceivedDialog: Boolean = false,
    val showPromotionDialog: Boolean = false,
    val showGameResultDialog: Boolean = false,
    val promotionMove: Pair<String, String>? = null,
    
    // Draw offer state
    val drawOfferPending: Boolean = false,
    val drawOfferSentByMe: Boolean = false
) {
    // ==================== Computed Properties ====================
    
    val currentTurn: PlayerSide
        get() = if (fen.contains(" w ")) PlayerSide.WHITE else PlayerSide.BLACK
    
    /** Whether the user is a player (not spectator/replay) */
    val isPlayer: Boolean
        get() = role == GameRole.PLAYER
    
    /** Whether user is watching (spectator or replay) */
    val isWatching: Boolean
        get() = role == GameRole.SPECTATOR || role == GameRole.REPLAY
    
    /** Whether game controls (resign, draw) should be visible */
    val showGameControls: Boolean
        get() = isPlayer && !isGameOver
    
    /** Whether the board is interactive for making moves */
    val canInteract: Boolean
        get() = isPlayer && isMyTurn && !isGameOver && !isWaitingForComputer
    
    // ==================== Player Names ====================
    
    val whiteName: String
        get() = game?.whitePlayer?.username ?: if (isComputerGame && playerColor == PlayerSide.BLACK) "Computer" else "White"
    
    val blackName: String
        get() = game?.blackPlayer?.username ?: if (isComputerGame && playerColor == PlayerSide.WHITE) "Computer" else "Black"
    
    val opponentName: String
        get() {
            return if (playerColor == PlayerSide.WHITE) {
                if (isComputerGame) "Computer" else game?.blackPlayer?.username ?: "Opponent"
            } else {
                if (isComputerGame) "Computer" else game?.whitePlayer?.username ?: "Opponent"
            }
        }
    
    val playerName: String
        get() {
            return if (playerColor == PlayerSide.WHITE) {
                game?.whitePlayer?.username ?: "You"
            } else {
                game?.blackPlayer?.username ?: "You"
            }
        }
    
    // ==================== Ratings ====================
    
    val whiteRating: Int?
        get() = if (isComputerGame && playerColor == PlayerSide.BLACK) {
            game?.computerRating
        } else {
            game?.whitePlayer?.rating
        }
    
    val blackRating: Int?
        get() = if (isComputerGame && playerColor == PlayerSide.WHITE) {
            game?.computerRating
        } else {
            game?.blackPlayer?.rating
        }
    
    val opponentRating: Int?
        get() {
            return if (playerColor == PlayerSide.WHITE) blackRating else whiteRating
        }
    
    val myRating: Int?
        get() = if (playerColor == PlayerSide.WHITE) whiteRating else blackRating
    
    // ==================== Timer ====================
    
    val myTime: Double
        get() = if (playerColor == PlayerSide.WHITE) whiteTime else blackTime
    
    val opponentTime: Double
        get() = if (playerColor == PlayerSide.WHITE) blackTime else whiteTime
    
    // ==================== Game Result ====================
    
    val gameResultTitle: String
        get() = when {
            isCheckmate -> if (didIWin) "Checkmate!" else "Checkmate"
            isStalemate -> "Stalemate"
            isDraw -> "Draw"
            isResigned -> if (didIWin) "Opponent Resigned" else "Resigned"
            isTimeout -> if (didIWin) "Opponent Timeout" else "Timeout"
            else -> "Game Over"
        }
    
    val gameResultSubtitle: String
        get() = when {
            didIWin -> "You won!"
            didILose -> "You lost"
            isDraw || isStalemate -> "Game drawn"
            else -> result ?: ""
        }
    
    val didIWin: Boolean
        get() = when {
            result == "1-0" && playerColor == PlayerSide.WHITE -> true
            result == "0-1" && playerColor == PlayerSide.BLACK -> true
            else -> false
        }
    
    val didILose: Boolean
        get() = when {
            result == "1-0" && playerColor == PlayerSide.BLACK -> true
            result == "0-1" && playerColor == PlayerSide.WHITE -> true
            else -> false
        }
}
