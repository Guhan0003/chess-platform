package com.example.chess_platform.ui.game

import com.example.chess_platform.domain.model.*

/**
 * UI State for the active game screen
 */
data class GameUiState(
    val isLoading: Boolean = true,
    val error: String? = null,
    
    // Game data
    val game: Game? = null,
    val gameId: Int = 0,
    
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
    val isGameOver: Boolean = false,
    val result: String? = null,
    
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
    
    // Move history
    val moves: List<Move> = emptyList(),
    
    // Dialogs
    val showResignDialog: Boolean = false,
    val showPromotionDialog: Boolean = false,
    val promotionMove: Pair<String, String>? = null
) {
    val currentTurn: PlayerSide
        get() = if (fen.contains(" w ")) PlayerSide.WHITE else PlayerSide.BLACK
    
    val opponentName: String
        get() {
            return if (playerColor == PlayerSide.WHITE) {
                game?.blackPlayer?.username ?: "Opponent"
            } else {
                game?.whitePlayer?.username ?: "Opponent"
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
    
    val opponentRating: Int?
        get() {
            return if (playerColor == PlayerSide.WHITE) {
                game?.blackPlayer?.rating
            } else {
                game?.whitePlayer?.rating
            }
        }
    
    val myTime: Double
        get() = if (playerColor == PlayerSide.WHITE) whiteTime else blackTime
    
    val opponentTime: Double
        get() = if (playerColor == PlayerSide.WHITE) blackTime else whiteTime
}
