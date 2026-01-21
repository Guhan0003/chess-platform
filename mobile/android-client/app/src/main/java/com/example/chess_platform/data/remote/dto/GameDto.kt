package com.example.chess_platform.data.remote.dto

import com.squareup.moshi.Json
import com.squareup.moshi.JsonClass

// ==================== GAME CREATION REQUESTS ====================

@JsonClass(generateAdapter = true)
data class CreateGameRequest(
    @Json(name = "time_control") val timeControl: String = "rapid" // bullet, blitz, rapid, classical, unlimited
)

@JsonClass(generateAdapter = true)
data class CreateComputerGameRequest(
    @Json(name = "player_color") val playerColor: String = "white", // white or black
    @Json(name = "difficulty") val difficulty: String = "1200", // 400, 800, 1200, 1600, 2000, 2400 or easy, medium, hard, expert
    @Json(name = "time_control") val timeControl: String = "rapid"
)

// ==================== GAME RESPONSES ====================

@JsonClass(generateAdapter = true)
data class GameResponse(
    @Json(name = "id") val id: Int,
    @Json(name = "white_player") val whitePlayer: Int?,
    @Json(name = "white_player_username") val whitePlayerUsername: String?,
    @Json(name = "white_player_rating") val whitePlayerRating: Int?,
    @Json(name = "black_player") val blackPlayer: Int?,
    @Json(name = "black_player_username") val blackPlayerUsername: String?,
    @Json(name = "black_player_rating") val blackPlayerRating: Int?,
    @Json(name = "status") val status: String, // waiting, active, finished
    @Json(name = "fen") val fen: String,
    @Json(name = "winner") val winner: Int?,
    @Json(name = "created_at") val createdAt: String,
    @Json(name = "updated_at") val updatedAt: String,
    @Json(name = "moves") val moves: List<MoveDto> = emptyList()
)

@JsonClass(generateAdapter = true)
data class ComputerGameResponse(
    @Json(name = "id") val id: Int,
    @Json(name = "white_player") val whitePlayer: Int?,
    @Json(name = "white_player_username") val whitePlayerUsername: String?,
    @Json(name = "white_player_rating") val whitePlayerRating: Int?,
    @Json(name = "black_player") val blackPlayer: Int?,
    @Json(name = "black_player_username") val blackPlayerUsername: String?,
    @Json(name = "black_player_rating") val blackPlayerRating: Int?,
    @Json(name = "status") val status: String,
    @Json(name = "fen") val fen: String,
    @Json(name = "winner") val winner: Int?,
    @Json(name = "created_at") val createdAt: String,
    @Json(name = "updated_at") val updatedAt: String,
    @Json(name = "moves") val moves: List<MoveDto> = emptyList(),
    @Json(name = "difficulty") val difficulty: String?,
    @Json(name = "computer_rating") val computerRating: Int?,
    @Json(name = "player_color") val playerColor: String?,
    @Json(name = "is_computer_game") val isComputerGame: Boolean = true,
    @Json(name = "computer_personality") val computerPersonality: String?
)

@JsonClass(generateAdapter = true)
data class MoveDto(
    @Json(name = "id") val id: Int,
    @Json(name = "game") val game: Int,
    @Json(name = "move_number") val moveNumber: Int,
    @Json(name = "player") val player: Int?,
    @Json(name = "player_username") val playerUsername: String?,
    @Json(name = "from_square") val fromSquare: String,
    @Json(name = "to_square") val toSquare: String,
    @Json(name = "notation") val notation: String?,
    @Json(name = "fen_after_move") val fenAfterMove: String?,
    @Json(name = "created_at") val createdAt: String?
)

// ==================== MOVE REQUESTS/RESPONSES ====================

@JsonClass(generateAdapter = true)
data class MakeMoveRequest(
    @Json(name = "from_square") val fromSquare: String,
    @Json(name = "to_square") val toSquare: String,
    @Json(name = "promotion") val promotion: String? = null // q, r, b, n
)

@JsonClass(generateAdapter = true)
data class MoveResponse(
    @Json(name = "move") val move: MoveDto,
    @Json(name = "game") val game: GameResponse,
    @Json(name = "game_status") val gameStatus: GameStatus?
)

@JsonClass(generateAdapter = true)
data class GameStatus(
    @Json(name = "is_checkmate") val isCheckmate: Boolean = false,
    @Json(name = "is_stalemate") val isStalemate: Boolean = false,
    @Json(name = "is_check") val isCheck: Boolean = false,
    @Json(name = "is_game_over") val isGameOver: Boolean = false,
    @Json(name = "result") val result: String? = null // 1-0, 0-1, 1/2-1/2
)

@JsonClass(generateAdapter = true)
data class ComputerMoveRequest(
    @Json(name = "difficulty") val difficulty: String? = null
)

@JsonClass(generateAdapter = true)
data class ComputerMoveResponse(
    @Json(name = "move") val move: MoveDto?,
    @Json(name = "game") val game: GameResponse?,
    @Json(name = "game_status") val gameStatus: GameStatus?,
    @Json(name = "computer_move") val computerMove: ComputerMoveInfo?
)

@JsonClass(generateAdapter = true)
data class ComputerMoveInfo(
    @Json(name = "from") val from: String?,
    @Json(name = "to") val to: String?,
    @Json(name = "san") val san: String?,
    @Json(name = "uci") val uci: String?
)

// ==================== LEGAL MOVES ====================

@JsonClass(generateAdapter = true)
data class LegalMovesResponse(
    @Json(name = "from_square") val fromSquare: String,
    @Json(name = "moves") val moves: List<LegalMove>,
    @Json(name = "count") val count: Int
)

@JsonClass(generateAdapter = true)
data class LegalMove(
    @Json(name = "to") val to: String,
    @Json(name = "capture") val capture: Boolean = false,
    @Json(name = "uci") val uci: String
)

// ==================== GAME CONTROL ====================

@JsonClass(generateAdapter = true)
data class ResignResponse(
    @Json(name = "success") val success: Boolean = true,
    @Json(name = "message") val message: String?,
    @Json(name = "game") val game: GameResponse?
)

@JsonClass(generateAdapter = true)
data class ActiveConstraintsResponse(
    @Json(name = "has_active_game") val hasActiveGame: Boolean = false,
    @Json(name = "active_game_id") val activeGameId: Int? = null,
    @Json(name = "game_type") val gameType: String? = null
)

// ==================== TIMER ====================

@JsonClass(generateAdapter = true)
data class TimerResponse(
    @Json(name = "game_id") val gameId: Int,
    @Json(name = "white_time") val whiteTime: Double,
    @Json(name = "black_time") val blackTime: Double,
    @Json(name = "white_rating") val whiteRating: Int?,
    @Json(name = "black_rating") val blackRating: Int?,
    @Json(name = "current_turn") val currentTurn: String, // white or black
    @Json(name = "game_status") val gameStatus: String?,
    @Json(name = "status") val status: String?,
    @Json(name = "time_control") val timeControl: String?,
    @Json(name = "increment") val increment: Int = 0,
    @Json(name = "time_pressure") val timePressure: TimePressure?
)

@JsonClass(generateAdapter = true)
data class TimePressure(
    @Json(name = "white") val white: String?, // none, low, critical
    @Json(name = "black") val black: String?
)

// ==================== TIME CONTROL OPTIONS ====================

/**
 * Professional time control options for chess games
 * Categories: Bullet (<3min), Blitz (3-10min), Rapid (10-30min), Classical (>30min)
 */
enum class TimeControlOption(
    val value: String, 
    val displayName: String, 
    val initialTime: Int,
    val increment: Int = 0,
    val category: TimeControlCategory = TimeControlCategory.RAPID
) {
    // Ultra-Bullet & Bullet (30 sec - 2 min)
    BULLET_30S("bullet_30s", "⚡ 30 sec", 30, 0, TimeControlCategory.BULLET),
    BULLET_1("bullet_1", "⚡ 1 min", 60, 0, TimeControlCategory.BULLET),
    BULLET_1_1("bullet_1_1", "⚡ 1|1", 60, 1, TimeControlCategory.BULLET),
    BULLET_2("bullet_2", "⚡ 2 min", 120, 0, TimeControlCategory.BULLET),
    BULLET_2_1("bullet_2_1", "⚡ 2|1", 120, 1, TimeControlCategory.BULLET),
    
    // Blitz (3-10 minutes)
    BLITZ_3("blitz_3", "🔥 3 min", 180, 0, TimeControlCategory.BLITZ),
    BLITZ_3_2("blitz_3_2", "🔥 3|2", 180, 2, TimeControlCategory.BLITZ),
    BLITZ_5("blitz_5", "🔥 5 min", 300, 0, TimeControlCategory.BLITZ),
    BLITZ_5_3("blitz_5_3", "🔥 5|3", 300, 3, TimeControlCategory.BLITZ),
    BLITZ_5_5("blitz_5_5", "🔥 5|5", 300, 5, TimeControlCategory.BLITZ),
    
    // Rapid (10-30 minutes)
    RAPID_10("rapid_10", "🏃 10 min", 600, 0, TimeControlCategory.RAPID),
    RAPID_10_5("rapid_10_5", "🏃 10|5", 600, 5, TimeControlCategory.RAPID),
    RAPID_15("rapid_15", "🏃 15 min", 900, 0, TimeControlCategory.RAPID),
    RAPID_15_10("rapid_15_10", "🏃 15|10", 900, 10, TimeControlCategory.RAPID),
    
    // Classical (30+ minutes)
    CLASSICAL_30("classical_30", "♔ 30 min", 1800, 0, TimeControlCategory.CLASSICAL),
    CLASSICAL_30_20("classical_30_20", "♔ 30|20", 1800, 20, TimeControlCategory.CLASSICAL),
    CLASSICAL_60("classical_60", "♔ 60 min", 3600, 0, TimeControlCategory.CLASSICAL),
    CLASSICAL_90_30("classical_90_30", "♔ 90|30", 5400, 30, TimeControlCategory.CLASSICAL),
    
    // Unlimited
    UNLIMITED("unlimited", "∞ Unlimited", 0, 0, TimeControlCategory.UNLIMITED);
    
    companion object {
        fun fromValue(value: String): TimeControlOption {
            return entries.find { it.value == value } ?: RAPID_10
        }
        
        fun getByCategory(category: TimeControlCategory): List<TimeControlOption> {
            return entries.filter { it.category == category }
        }
    }
}

enum class TimeControlCategory(val displayName: String, val icon: String) {
    BULLET("Bullet", "⚡"),
    BLITZ("Blitz", "🔥"),
    RAPID("Rapid", "🏃"),
    CLASSICAL("Classical", "♔"),
    UNLIMITED("Unlimited", "∞")
}

enum class BotDifficulty(val value: String, val displayName: String, val rating: Int) {
    BEGINNER("400", "Beginner", 400),
    EASY("800", "Easy", 800),
    MEDIUM("1200", "Medium", 1200),
    HARD("1600", "Hard", 1600),
    EXPERT("2000", "Expert", 2000),
    MASTER("2400", "Master", 2400)
}

enum class PlayerColor(val value: String, val displayName: String) {
    WHITE("white", "White"),
    BLACK("black", "Black"),
    RANDOM("random", "Random")
}
