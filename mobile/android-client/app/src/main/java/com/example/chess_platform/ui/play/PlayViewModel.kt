package com.example.chess_platform.ui.play

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.example.chess_platform.data.remote.dto.BotDifficulty
import com.example.chess_platform.data.remote.dto.PlayerColor
import com.example.chess_platform.data.remote.dto.TimeControlOption
import com.example.chess_platform.domain.repository.GameRepository
import dagger.hilt.android.lifecycle.HiltViewModel
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.flow.update
import kotlinx.coroutines.launch
import javax.inject.Inject

@HiltViewModel
class PlayViewModel @Inject constructor(
    private val gameRepository: GameRepository
) : ViewModel() {
    
    private val _uiState = MutableStateFlow(PlayUiState())
    val uiState: StateFlow<PlayUiState> = _uiState.asStateFlow()
    
    // ==================== Configuration Updates ====================
    
    fun selectTimeControl(timeControl: TimeControlOption) {
        _uiState.update { it.copy(selectedTimeControl = timeControl) }
    }
    
    fun selectDifficulty(difficulty: BotDifficulty) {
        _uiState.update { it.copy(selectedDifficulty = difficulty) }
    }
    
    fun selectColor(color: PlayerColor) {
        _uiState.update { it.copy(selectedColor = color) }
    }
    
    // ==================== Game Creation ====================
    
    /**
     * Create an online game (waiting for opponent)
     */
    fun createOnlineGame() {
        viewModelScope.launch {
            _uiState.update { it.copy(isLoading = true, error = null) }
            
            val result = gameRepository.createGame(
                timeControl = _uiState.value.selectedTimeControl.value
            )
            
            result.fold(
                onSuccess = { game ->
                    _uiState.update { 
                        it.copy(
                            isLoading = false,
                            createdGame = game,
                            navigateToGame = game.id
                        )
                    }
                },
                onFailure = { e ->
                    _uiState.update { 
                        it.copy(
                            isLoading = false,
                            error = e.message ?: "Failed to create game"
                        )
                    }
                }
            )
        }
    }
    
    /**
     * Create a game against computer
     */
    fun createBotGame() {
        viewModelScope.launch {
            _uiState.update { it.copy(isLoading = true, error = null) }
            
            // Handle random color selection
            val selectedColor = _uiState.value.selectedColor
            val playerColor = if (selectedColor == PlayerColor.RANDOM) {
                if (Math.random() < 0.5) PlayerColor.WHITE else PlayerColor.BLACK
            } else {
                selectedColor
            }
            
            val result = gameRepository.createComputerGame(
                playerColor = playerColor.value,
                difficulty = _uiState.value.selectedDifficulty.value,
                timeControl = _uiState.value.selectedTimeControl.value
            )
            
            result.fold(
                onSuccess = { game ->
                    _uiState.update { 
                        it.copy(
                            isLoading = false,
                            createdGame = game,
                            navigateToGame = game.id
                        )
                    }
                },
                onFailure = { e ->
                    _uiState.update { 
                        it.copy(
                            isLoading = false,
                            error = e.message ?: "Failed to create bot game"
                        )
                    }
                }
            )
        }
    }
    
    /**
     * Clear navigation flag after navigating
     */
    fun onNavigatedToGame() {
        _uiState.update { it.copy(navigateToGame = null) }
    }
    
    /**
     * Clear error message
     */
    fun clearError() {
        _uiState.update { it.copy(error = null) }
    }
}
