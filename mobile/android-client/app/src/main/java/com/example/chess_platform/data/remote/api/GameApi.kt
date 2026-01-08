package com.example.chess_platform.data.remote.api

import com.example.chess_platform.data.remote.dto.*
import retrofit2.Response
import retrofit2.http.*

/**
 * Game API interface for chess game operations
 */
interface GameApi {

    // ==================== GAME CREATION ====================

    /**
     * Create a new game (waiting for opponent)
     */
    @POST("api/games/create/")
    suspend fun createGame(
        @Body request: CreateGameRequest
    ): Response<GameResponse>

    /**
     * Create a game against computer
     */
    @POST("api/games/create-computer/")
    suspend fun createComputerGame(
        @Body request: CreateComputerGameRequest
    ): Response<ComputerGameResponse>

    // ==================== GAME LISTING ====================

    /**
     * Get list of games (with optional filters)
     */
    @GET("api/games/")
    suspend fun getGames(
        @Query("user_id") userId: Int? = null,
        @Query("limit") limit: Int? = null
    ): Response<List<GameResponse>>

    /**
     * Get game details
     */
    @GET("api/games/{id}/")
    suspend fun getGameDetails(
        @Path("id") gameId: Int
    ): Response<GameResponse>

    // ==================== GAME ACTIONS ====================

    /**
     * Join a waiting game as black player
     */
    @POST("api/games/{id}/join/")
    suspend fun joinGame(
        @Path("id") gameId: Int
    ): Response<GameResponse>

    /**
     * Make a move in a game
     */
    @POST("api/games/{id}/move/")
    suspend fun makeMove(
        @Path("id") gameId: Int,
        @Body request: MakeMoveRequest
    ): Response<MoveResponse>

    /**
     * Request computer to make a move
     */
    @POST("api/games/{id}/computer-move/")
    suspend fun makeComputerMove(
        @Path("id") gameId: Int,
        @Body request: ComputerMoveRequest
    ): Response<ComputerMoveResponse>

    /**
     * Get legal moves for a square
     */
    @GET("api/games/{id}/legal-moves/")
    suspend fun getLegalMoves(
        @Path("id") gameId: Int,
        @Query("from_square") fromSquare: String
    ): Response<LegalMovesResponse>

    // ==================== GAME CONTROL ====================

    /**
     * Resign from a game
     */
    @POST("api/games/{id}/resign/")
    suspend fun resignGame(
        @Path("id") gameId: Int
    ): Response<ResignResponse>

    /**
     * Check for active game constraints
     */
    @GET("api/games/active-constraints/")
    suspend fun checkActiveConstraints(): Response<ActiveConstraintsResponse>

    // ==================== TIMER ====================

    /**
     * Get game timer status
     */
    @GET("api/games/{id}/timer/")
    suspend fun getGameTimer(
        @Path("id") gameId: Int
    ): Response<TimerResponse>

    /**
     * Get professional timer status
     */
    @GET("api/games/{id}/professional-timer/")
    suspend fun getProfessionalTimer(
        @Path("id") gameId: Int
    ): Response<TimerResponse>
}
