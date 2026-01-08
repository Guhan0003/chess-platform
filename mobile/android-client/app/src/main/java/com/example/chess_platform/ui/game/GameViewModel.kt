package com.example.chess_platform.ui.game

import androidx.lifecycle.SavedStateHandle
import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.example.chess_platform.domain.model.*
import com.example.chess_platform.domain.repository.GameRepository
import dagger.hilt.android.lifecycle.HiltViewModel
import kotlinx.coroutines.Job
import kotlinx.coroutines.delay
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.flow.update
import kotlinx.coroutines.launch
import javax.inject.Inject

@HiltViewModel
class GameViewModel @Inject constructor(
    private val gameRepository: GameRepository,
    savedStateHandle: SavedStateHandle
) : ViewModel() {
    
    private val gameId: Int = savedStateHandle.get<Int>("gameId") ?: 0
    
    private val _uiState = MutableStateFlow(GameUiState(gameId = gameId))
    val uiState: StateFlow<GameUiState> = _uiState.asStateFlow()
    
    private var timerJob: Job? = null
    
    init {
        loadGame()
    }
    
    // ==================== Game Loading ====================
    
    fun loadGame() {
        viewModelScope.launch {
            _uiState.update { it.copy(isLoading = true, error = null) }
            
            val result = gameRepository.getGameDetails(gameId)
            result.fold(
                onSuccess = { game ->
                    val playerColor = determinePlayerColor(game)
                    _uiState.update { state ->
                        state.copy(
                            isLoading = false,
                            game = game,
                            fen = game.fen,
                            moves = game.moves,
                            playerColor = playerColor,
                            isFlipped = playerColor == PlayerSide.BLACK,
                            isComputerGame = game.isComputerGame,
                            isMyTurn = game.currentTurn == playerColor,
                            whiteTime = game.whiteTimeLeft.takeIf { it > 0 } ?: 600.0,
                            blackTime = game.blackTimeLeft.takeIf { it > 0 } ?: 600.0,
                            isGameOver = game.isGameOver
                        )
                    }
                    
                    // Start timer if game is active
                    if (game.status == GameState.ACTIVE) {
                        startTimer()
                    }
                    
                    // If it's computer's turn in a bot game, request computer move
                    if (game.isComputerGame && game.currentTurn != playerColor && !game.isGameOver) {
                        requestComputerMove()
                    }
                },
                onFailure = { e ->
                    _uiState.update { 
                        it.copy(
                            isLoading = false,
                            error = e.message ?: "Failed to load game"
                        )
                    }
                }
            )
        }
    }
    
    private fun determinePlayerColor(game: Game): PlayerSide {
        // For computer games, use the stored player color
        game.playerColor?.let { return it }
        
        // Otherwise, determine based on player positions
        // This is a simplified version - in a real app you'd compare with the logged-in user
        return PlayerSide.WHITE
    }
    
    // ==================== Timer ====================
    
    private fun startTimer() {
        timerJob?.cancel()
        timerJob = viewModelScope.launch {
            while (true) {
                delay(100) // Update every 100ms for smooth countdown
                
                val state = _uiState.value
                if (state.isGameOver) break
                
                val decrement = 0.1 // 100ms
                val newWhiteTime = if (state.currentTurn == PlayerSide.WHITE) {
                    (state.whiteTime - decrement).coerceAtLeast(0.0)
                } else state.whiteTime
                
                val newBlackTime = if (state.currentTurn == PlayerSide.BLACK) {
                    (state.blackTime - decrement).coerceAtLeast(0.0)
                } else state.blackTime
                
                _uiState.update { it.copy(
                    whiteTime = newWhiteTime,
                    blackTime = newBlackTime,
                    whiteTimePressure = calculateTimePressure(newWhiteTime),
                    blackTimePressure = calculateTimePressure(newBlackTime)
                )}
                
                // Check for timeout
                if (newWhiteTime <= 0 || newBlackTime <= 0) {
                    handleTimeout()
                    break
                }
            }
        }
    }
    
    private fun calculateTimePressure(time: Double): TimePressureLevel {
        return when {
            time <= 30 -> TimePressureLevel.CRITICAL
            time <= 180 -> TimePressureLevel.LOW
            else -> TimePressureLevel.NONE
        }
    }
    
    private fun handleTimeout() {
        _uiState.update { it.copy(
            isGameOver = true,
            result = if (it.whiteTime <= 0) "0-1" else "1-0"
        )}
    }
    
    // ==================== Square Selection & Moves ====================
    
    fun onSquareClick(square: String) {
        val state = _uiState.value
        
        // Don't allow interaction if not player's turn or game is over
        if (!state.isMyTurn || state.isGameOver || state.isWaitingForComputer) return
        
        val selectedSquare = state.selectedSquare
        
        if (selectedSquare == null) {
            // First click - select a piece
            selectSquare(square)
        } else if (selectedSquare == square) {
            // Clicked same square - deselect
            deselectSquare()
        } else {
            // Check if clicking on a legal move destination
            val legalMove = state.legalMoves.find { it.toSquare == square }
            if (legalMove != null) {
                // Check for pawn promotion
                if (isPawnPromotion(selectedSquare, square, state.fen)) {
                    _uiState.update { it.copy(
                        showPromotionDialog = true,
                        promotionMove = Pair(selectedSquare, square)
                    )}
                } else {
                    makeMove(selectedSquare, square)
                }
            } else {
                // Select a different piece
                selectSquare(square)
            }
        }
    }
    
    private fun selectSquare(square: String) {
        viewModelScope.launch {
            val result = gameRepository.getLegalMoves(gameId, square)
            result.fold(
                onSuccess = { moves ->
                    if (moves.isNotEmpty()) {
                        _uiState.update { it.copy(
                            selectedSquare = square,
                            legalMoves = moves
                        )}
                    }
                },
                onFailure = { /* Ignore - probably not our piece */ }
            )
        }
    }
    
    private fun deselectSquare() {
        _uiState.update { it.copy(
            selectedSquare = null,
            legalMoves = emptyList()
        )}
    }
    
    private fun isPawnPromotion(from: String, to: String, fen: String): Boolean {
        val board = parseFenSimple(fen)
        val fromRow = from[1].digitToInt() - 1
        val toRow = to[1].digitToInt() - 1
        val fromCol = from[0] - 'a'
        
        val piece = board.getOrNull(fromRow)?.getOrNull(fromCol)
        
        return (piece == 'P' && toRow == 7) || (piece == 'p' && toRow == 0)
    }
    
    private fun parseFenSimple(fen: String): Array<Array<Char?>> {
        val board = Array(8) { arrayOfNulls<Char>(8) }
        val position = fen.split(" ").firstOrNull() ?: return board
        
        val ranks = position.split("/")
        for ((rankIndex, rank) in ranks.withIndex()) {
            var fileIndex = 0
            for (char in rank) {
                if (char.isDigit()) {
                    fileIndex += char.digitToInt()
                } else {
                    if (rankIndex < 8 && fileIndex < 8) {
                        board[7 - rankIndex][fileIndex] = char
                    }
                    fileIndex++
                }
            }
        }
        return board
    }
    
    // ==================== Making Moves ====================
    
    private fun makeMove(from: String, to: String, promotion: String? = null) {
        viewModelScope.launch {
            deselectSquare()
            
            val result = gameRepository.makeMove(gameId, from, to, promotion)
            result.fold(
                onSuccess = { (move, status) ->
                    val newFen = move.fenAfterMove ?: _uiState.value.fen
                    
                    _uiState.update { state ->
                        state.copy(
                            fen = newFen,
                            lastMove = Pair(from, to),
                            moves = state.moves + move,
                            isCheck = status?.isCheck ?: false,
                            isCheckmate = status?.isCheckmate ?: false,
                            isStalemate = status?.isStalemate ?: false,
                            isGameOver = status?.isGameOver ?: false,
                            result = status?.result,
                            isMyTurn = false
                        )
                    }
                    
                    // If computer game and game isn't over, request computer move
                    if (_uiState.value.isComputerGame && !(_uiState.value.isGameOver)) {
                        requestComputerMove()
                    }
                },
                onFailure = { e ->
                    _uiState.update { it.copy(error = e.message ?: "Failed to make move") }
                }
            )
        }
    }
    
    fun onPromotionSelected(piece: String) {
        val promotionMove = _uiState.value.promotionMove ?: return
        _uiState.update { it.copy(showPromotionDialog = false, promotionMove = null) }
        makeMove(promotionMove.first, promotionMove.second, piece)
    }
    
    fun dismissPromotionDialog() {
        _uiState.update { it.copy(showPromotionDialog = false, promotionMove = null) }
    }
    
    // ==================== Computer Move ====================
    
    private fun requestComputerMove() {
        viewModelScope.launch {
            _uiState.update { it.copy(isWaitingForComputer = true) }
            
            // Add a small delay to make it feel more natural
            delay(500)
            
            val result = gameRepository.makeComputerMove(gameId)
            result.fold(
                onSuccess = { move ->
                    if (move != null) {
                        val newFen = move.fenAfterMove ?: _uiState.value.fen
                        
                        _uiState.update { state ->
                            state.copy(
                                fen = newFen,
                                lastMove = Pair(move.fromSquare, move.toSquare),
                                moves = state.moves + move,
                                isWaitingForComputer = false,
                                isMyTurn = true
                            )
                        }
                        
                        // Reload to get updated game status
                        checkGameStatus()
                    }
                },
                onFailure = { e ->
                    _uiState.update { 
                        it.copy(
                            isWaitingForComputer = false,
                            error = e.message ?: "Computer move failed"
                        )
                    }
                }
            )
        }
    }
    
    private fun checkGameStatus() {
        viewModelScope.launch {
            val result = gameRepository.getGameDetails(gameId)
            result.fold(
                onSuccess = { game ->
                    _uiState.update { state ->
                        state.copy(
                            isGameOver = game.isGameOver,
                            game = game
                        )
                    }
                },
                onFailure = { /* Ignore */ }
            )
        }
    }
    
    // ==================== Game Actions ====================
    
    fun flipBoard() {
        _uiState.update { it.copy(isFlipped = !it.isFlipped) }
    }
    
    fun showResignDialog() {
        _uiState.update { it.copy(showResignDialog = true) }
    }
    
    fun dismissResignDialog() {
        _uiState.update { it.copy(showResignDialog = false) }
    }
    
    fun resignGame() {
        viewModelScope.launch {
            _uiState.update { it.copy(showResignDialog = false) }
            
            val result = gameRepository.resignGame(gameId)
            result.fold(
                onSuccess = { game ->
                    timerJob?.cancel()
                    _uiState.update { 
                        it.copy(
                            game = game,
                            isGameOver = true,
                            result = if (it.playerColor == PlayerSide.WHITE) "0-1" else "1-0"
                        )
                    }
                },
                onFailure = { e ->
                    _uiState.update { it.copy(error = e.message ?: "Failed to resign") }
                }
            )
        }
    }
    
    fun clearError() {
        _uiState.update { it.copy(error = null) }
    }
    
    override fun onCleared() {
        super.onCleared()
        timerJob?.cancel()
    }
}
