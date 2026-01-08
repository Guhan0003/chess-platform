package com.example.chess_platform.ui.dashboard

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.example.chess_platform.domain.repository.AuthRepository
import com.example.chess_platform.util.Resource
import dagger.hilt.android.lifecycle.HiltViewModel
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.flow.first
import kotlinx.coroutines.flow.update
import kotlinx.coroutines.launch
import javax.inject.Inject

data class DashboardUiState(
    val username: String = "Player",
    val blitzRating: Int = 1200,
    val rapidRating: Int = 1200,
    val classicalRating: Int = 1200,
    val gamesPlayed: Int = 0,
    val gamesWon: Int = 0,
    val gamesLost: Int = 0,
    val gamesDrawn: Int = 0,
    val isLoading: Boolean = false,
    val error: String? = null
)

@HiltViewModel
class DashboardViewModel @Inject constructor(
    private val authRepository: AuthRepository
) : ViewModel() {
    
    private val _uiState = MutableStateFlow(DashboardUiState())
    val uiState: StateFlow<DashboardUiState> = _uiState.asStateFlow()
    
    init {
        loadUserData()
    }
    
    private fun loadUserData() {
        viewModelScope.launch {
            _uiState.update { it.copy(isLoading = true) }
            
            // Get username from stored data
            val username = authRepository.currentUsername.first() ?: "Player"
            _uiState.update { it.copy(username = username) }
            
            // Fetch profile from API
            when (val result = authRepository.getProfile()) {
                is Resource.Success -> {
                    result.data?.let { user ->
                        _uiState.update { state ->
                            state.copy(
                                isLoading = false,
                                username = user.username,
                                blitzRating = user.blitzRating,
                                rapidRating = user.rapidRating,
                                classicalRating = user.classicalRating,
                                gamesPlayed = user.gamesPlayed,
                                gamesWon = user.gamesWon,
                                gamesLost = user.gamesLost,
                                gamesDrawn = user.gamesDrawn
                            )
                        }
                    }
                }
                is Resource.Error -> {
                    _uiState.update { 
                        it.copy(
                            isLoading = false,
                            error = result.message
                        )
                    }
                }
                is Resource.Loading -> {
                    _uiState.update { it.copy(isLoading = true) }
                }
            }
        }
    }
    
    fun logout() {
        viewModelScope.launch {
            authRepository.logout()
        }
    }
    
    fun refresh() {
        loadUserData()
    }
}
