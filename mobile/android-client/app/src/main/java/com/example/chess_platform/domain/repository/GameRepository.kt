package com.example.chess_platform.domain.repository

import com.example.chess_platform.domain.model.*

/**
 * Repository interface for game operations
 */
interface GameRepository {
    
    /**
     * Create a new game (waiting for opponent)
     */
    suspend fun createGame(timeControl: String): Result<Game>
    
    /**
     * Create a game against computer
     */
    suspend fun createComputerGame(
        playerColor: String,
        difficulty: String,
        timeControl: String
    ): Result<Game>
    
    /**
     * Get list of games
     */
    suspend fun getGames(userId: Int? = null, limit: Int? = null): Result<List<Game>>
    
    /**
     * Get game details
     */
    suspend fun getGameDetails(gameId: Int): Result<Game>
    
    /**
     * Join a waiting game
     */
    suspend fun joinGame(gameId: Int): Result<Game>
    
    /**
     * Make a move
     */
    suspend fun makeMove(
        gameId: Int,
        fromSquare: String,
        toSquare: String,
        promotion: String? = null
    ): Result<Pair<Move, GameStatusInfo?>>
    
    /**
     * Request computer move
     */
    suspend fun makeComputerMove(gameId: Int, difficulty: String? = null): Result<Move?>
    
    /**
     * Get legal moves for a square
     */
    suspend fun getLegalMoves(gameId: Int, fromSquare: String): Result<List<LegalMoveInfo>>
    
    /**
     * Resign from game
     */
    suspend fun resignGame(gameId: Int): Result<Game>
    
    /**
     * Check for active game constraints
     */
    suspend fun checkActiveConstraints(): Result<ActiveGameConstraint?>
    
    /**
     * Get timer info
     */
    suspend fun getGameTimer(gameId: Int): Result<GameTimer>
}

/**
 * Active game constraint info
 */
data class ActiveGameConstraint(
    val hasActiveGame: Boolean,
    val activeGameId: Int?,
    val gameType: String?
)
