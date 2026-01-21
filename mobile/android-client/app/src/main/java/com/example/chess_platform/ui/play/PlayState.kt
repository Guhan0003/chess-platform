package com.example.chess_platform.ui.play

import com.example.chess_platform.data.remote.dto.BotDifficulty
import com.example.chess_platform.data.remote.dto.PlayerColor
import com.example.chess_platform.data.remote.dto.TimeControlOption
import com.example.chess_platform.domain.model.Game

/**
 * UI State for Play screens
 */
data class PlayUiState(
    val isLoading: Boolean = false,
    val error: String? = null,
    val createdGame: Game? = null,
    
    // Game configuration - default to 10 min Rapid
    val selectedTimeControl: TimeControlOption = TimeControlOption.RAPID_10,
    val selectedDifficulty: BotDifficulty = BotDifficulty.MEDIUM,
    val selectedColor: PlayerColor = PlayerColor.WHITE,
    
    // Navigation flags
    val navigateToGame: Int? = null
)

/**
 * Game mode selection
 */
enum class GameMode {
    ONLINE,      // Play against human online
    BOT,         // Play against computer
    OTB          // Over-the-board (local 2-player)
}
