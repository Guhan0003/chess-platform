package com.example.chess_platform.domain.model

/**
 * Domain model for a chess game
 */
data class Game(
    val id: Int,
    val whitePlayer: Player?,
    val blackPlayer: Player?,
    val status: GameState,
    val fen: String,
    val winnerId: Int?,
    val moves: List<Move>,
    val isComputerGame: Boolean = false,
    val computerRating: Int? = null,
    val playerColor: PlayerSide? = null,
    val timeControl: String? = null,
    val whiteTimeLeft: Double = 0.0,
    val blackTimeLeft: Double = 0.0
) {
    val currentTurn: PlayerSide
        get() = if (fen.contains(" w ")) PlayerSide.WHITE else PlayerSide.BLACK
    
    val isGameOver: Boolean
        get() = status == GameState.FINISHED
    
    val isMyTurn: Boolean
        get() = playerColor == currentTurn
    
    fun getPlayerByColor(color: PlayerSide): Player? {
        return if (color == PlayerSide.WHITE) whitePlayer else blackPlayer
    }
}

/**
 * Player info within a game
 */
data class Player(
    val id: Int,
    val username: String,
    val rating: Int?
)

/**
 * Domain model for a chess move
 */
data class Move(
    val id: Int,
    val gameId: Int,
    val moveNumber: Int,
    val playerId: Int?,
    val playerUsername: String?,
    val fromSquare: String,
    val toSquare: String,
    val notation: String?,
    val fenAfterMove: String?
)

/**
 * Game status
 */
enum class GameState {
    WAITING,
    ACTIVE,
    FINISHED;
    
    companion object {
        fun fromString(value: String): GameState {
            return when (value.lowercase()) {
                "waiting" -> WAITING
                "active" -> ACTIVE
                "finished" -> FINISHED
                else -> WAITING
            }
        }
    }
}

/**
 * Player side (color)
 */
enum class PlayerSide {
    WHITE,
    BLACK;
    
    companion object {
        fun fromString(value: String): PlayerSide {
            return if (value.lowercase() == "black") BLACK else WHITE
        }
    }
    
    fun opposite(): PlayerSide = if (this == WHITE) BLACK else WHITE
}

/**
 * Represents game result status
 */
data class GameStatusInfo(
    val isCheckmate: Boolean = false,
    val isStalemate: Boolean = false,
    val isCheck: Boolean = false,
    val isGameOver: Boolean = false,
    val result: String? = null
)

/**
 * Legal move information
 */
data class LegalMoveInfo(
    val toSquare: String,
    val isCapture: Boolean,
    val uci: String
)

/**
 * Timer information
 */
data class GameTimer(
    val gameId: Int,
    val whiteTime: Double,
    val blackTime: Double,
    val currentTurn: PlayerSide,
    val gameStatus: String?,
    val timeControl: String?,
    val increment: Int = 0,
    val whiteTimePressure: TimePressureLevel = TimePressureLevel.NONE,
    val blackTimePressure: TimePressureLevel = TimePressureLevel.NONE
)

enum class TimePressureLevel {
    NONE,
    LOW,
    CRITICAL;
    
    companion object {
        fun fromString(value: String?): TimePressureLevel {
            return when (value?.lowercase()) {
                "low" -> LOW
                "critical" -> CRITICAL
                else -> NONE
            }
        }
    }
}
