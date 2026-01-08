package com.example.chess_platform.data.repository

import android.util.Log
import com.example.chess_platform.data.remote.api.GameApi
import com.example.chess_platform.data.remote.dto.*
import com.example.chess_platform.domain.model.*
import com.example.chess_platform.domain.repository.ActiveGameConstraint
import com.example.chess_platform.domain.repository.GameRepository
import javax.inject.Inject

private const val TAG = "GameRepository"

/**
 * Implementation of GameRepository
 */
class GameRepositoryImpl @Inject constructor(
    private val gameApi: GameApi
) : GameRepository {

    override suspend fun createGame(timeControl: String): Result<Game> {
        return try {
            Log.d(TAG, "Creating online game with time control: $timeControl")
            val response = gameApi.createGame(CreateGameRequest(timeControl))
            if (response.isSuccessful && response.body() != null) {
                Log.d(TAG, "Game created successfully: ${response.body()!!.id}")
                Result.success(response.body()!!.toDomain())
            } else {
                val errorMsg = parseErrorMessage(response.code(), response.errorBody()?.string())
                Log.e(TAG, "Failed to create game: $errorMsg")
                Result.failure(Exception(errorMsg))
            }
        } catch (e: java.net.SocketTimeoutException) {
            Log.e(TAG, "Timeout creating game", e)
            Result.failure(Exception("Connection timed out. Is the server running?"))
        } catch (e: java.net.ConnectException) {
            Log.e(TAG, "Connection error creating game", e)
            Result.failure(Exception("Cannot connect to server. Check your connection."))
        } catch (e: Exception) {
            Log.e(TAG, "Error creating game", e)
            Result.failure(Exception("Network error: ${e.message?.take(100)}"))
        }
    }

    override suspend fun createComputerGame(
        playerColor: String,
        difficulty: String,
        timeControl: String
    ): Result<Game> {
        return try {
            val response = gameApi.createComputerGame(
                CreateComputerGameRequest(
                    playerColor = playerColor,
                    difficulty = difficulty,
                    timeControl = timeControl
                )
            )
            if (response.isSuccessful && response.body() != null) {
                Result.success(response.body()!!.toDomain())
            } else {
                val errorMsg = parseErrorMessage(response.code(), response.errorBody()?.string())
                Result.failure(Exception(errorMsg))
            }
        } catch (e: java.net.SocketTimeoutException) {
            Result.failure(Exception("Connection timed out. Is the server running?"))
        } catch (e: java.net.ConnectException) {
            Result.failure(Exception("Cannot connect to server. Check your connection."))
        } catch (e: Exception) {
            Result.failure(Exception("Network error: ${e.message?.take(100)}"))
        }
    }

    override suspend fun getGames(userId: Int?, limit: Int?): Result<List<Game>> {
        return try {
            val response = gameApi.getGames(userId, limit)
            if (response.isSuccessful && response.body() != null) {
                Result.success(response.body()!!.map { it.toDomain() })
            } else {
                Result.failure(Exception(response.errorBody()?.string() ?: "Failed to get games"))
            }
        } catch (e: Exception) {
            Result.failure(e)
        }
    }

    override suspend fun getGameDetails(gameId: Int): Result<Game> {
        return try {
            val response = gameApi.getGameDetails(gameId)
            if (response.isSuccessful && response.body() != null) {
                Result.success(response.body()!!.toDomain())
            } else {
                Result.failure(Exception(response.errorBody()?.string() ?: "Failed to get game details"))
            }
        } catch (e: Exception) {
            Result.failure(e)
        }
    }

    override suspend fun joinGame(gameId: Int): Result<Game> {
        return try {
            val response = gameApi.joinGame(gameId)
            if (response.isSuccessful && response.body() != null) {
                Result.success(response.body()!!.toDomain())
            } else {
                Result.failure(Exception(response.errorBody()?.string() ?: "Failed to join game"))
            }
        } catch (e: Exception) {
            Result.failure(e)
        }
    }

    override suspend fun makeMove(
        gameId: Int,
        fromSquare: String,
        toSquare: String,
        promotion: String?
    ): Result<Pair<Move, GameStatusInfo?>> {
        return try {
            val response = gameApi.makeMove(
                gameId,
                MakeMoveRequest(fromSquare, toSquare, promotion)
            )
            if (response.isSuccessful && response.body() != null) {
                val body = response.body()!!
                val move = body.move.toDomain()
                val status = body.gameStatus?.toDomain()
                Result.success(Pair(move, status))
            } else {
                Result.failure(Exception(response.errorBody()?.string() ?: "Failed to make move"))
            }
        } catch (e: Exception) {
            Result.failure(e)
        }
    }

    override suspend fun makeComputerMove(gameId: Int, difficulty: String?): Result<Move?> {
        return try {
            Log.d(TAG, "Requesting computer move for game $gameId, difficulty=$difficulty")
            // Always provide a request body (Retrofit @Body cannot be null)
            val request = ComputerMoveRequest(difficulty)
            val response = gameApi.makeComputerMove(gameId, request)
            Log.d(TAG, "Computer move response: code=${response.code()}, success=${response.isSuccessful}")
            if (response.isSuccessful && response.body() != null) {
                val body = response.body()!!
                val move = body.move?.toDomain()
                    ?: body.computerMove?.let { compMove ->
                        // If move is null but computerMove exists, create a Move from it
                        Move(
                            id = 0,
                            gameId = gameId,
                            moveNumber = 0,
                            playerId = null,
                            playerUsername = "Computer",
                            fromSquare = compMove.from ?: "",
                            toSquare = compMove.to ?: "",
                            notation = compMove.san,
                            fenAfterMove = body.game?.fen
                        )
                    }
                Log.d(TAG, "Computer move: ${move?.fromSquare}-${move?.toSquare}")
                Result.success(move)
            } else {
                val errorMsg = parseErrorMessage(response.code(), response.errorBody()?.string())
                Log.e(TAG, "Computer move failed: $errorMsg")
                Result.failure(Exception(errorMsg))
            }
        } catch (e: java.net.SocketTimeoutException) {
            Log.e(TAG, "Timeout for computer move", e)
            Result.failure(Exception("Computer is thinking... try again"))
        } catch (e: Exception) {
            Log.e(TAG, "Error getting computer move", e)
            Result.failure(Exception("Failed to get computer move: ${e.message?.take(50)}"))
        }
    }

    override suspend fun getLegalMoves(gameId: Int, fromSquare: String): Result<List<LegalMoveInfo>> {
        return try {
            val response = gameApi.getLegalMoves(gameId, fromSquare)
            if (response.isSuccessful && response.body() != null) {
                val moves = response.body()!!.moves.map { 
                    LegalMoveInfo(
                        toSquare = it.to,
                        isCapture = it.capture,
                        uci = it.uci
                    )
                }
                Result.success(moves)
            } else {
                Result.failure(Exception(response.errorBody()?.string() ?: "Failed to get legal moves"))
            }
        } catch (e: Exception) {
            Result.failure(e)
        }
    }

    override suspend fun resignGame(gameId: Int): Result<Game> {
        return try {
            Log.d(TAG, "Resigning from game $gameId")
            val response = gameApi.resignGame(gameId)
            Log.d(TAG, "Resign response: code=${response.code()}, success=${response.isSuccessful}")
            if (response.isSuccessful && response.body() != null) {
                val game = response.body()!!.game
                if (game != null) {
                    Log.d(TAG, "Resign successful, game status: ${game.status}")
                    Result.success(game.toDomain())
                } else {
                    // Even without game data, if request succeeded, fetch game details
                    Log.w(TAG, "Resign succeeded but no game data, fetching details")
                    getGameDetails(gameId)
                }
            } else {
                val errorMsg = parseErrorMessage(response.code(), response.errorBody()?.string())
                Log.e(TAG, "Resign failed: $errorMsg")
                Result.failure(Exception(errorMsg))
            }
        } catch (e: Exception) {
            Log.e(TAG, "Error resigning", e)
            Result.failure(Exception("Failed to resign: ${e.message?.take(50)}"))
        }
    }

    override suspend fun checkActiveConstraints(): Result<ActiveGameConstraint?> {
        return try {
            val response = gameApi.checkActiveConstraints()
            if (response.isSuccessful && response.body() != null) {
                val body = response.body()!!
                if (body.hasActiveGame) {
                    Result.success(
                        ActiveGameConstraint(
                            hasActiveGame = true,
                            activeGameId = body.activeGameId,
                            gameType = body.gameType
                        )
                    )
                } else {
                    Result.success(null)
                }
            } else {
                Result.failure(Exception(response.errorBody()?.string() ?: "Failed to check constraints"))
            }
        } catch (e: Exception) {
            Result.failure(e)
        }
    }

    override suspend fun getGameTimer(gameId: Int): Result<GameTimer> {
        return try {
            val response = gameApi.getGameTimer(gameId)
            if (response.isSuccessful && response.body() != null) {
                Result.success(response.body()!!.toDomain())
            } else {
                Result.failure(Exception(response.errorBody()?.string() ?: "Failed to get timer"))
            }
        } catch (e: Exception) {
            Result.failure(e)
        }
    }
}

// ==================== DTO to Domain Mappers ====================

private fun GameResponse.toDomain(): Game {
    // Detect if it's a computer game by checking if either player has "computer" in their username
    val isComputerGame = (whitePlayerUsername?.contains("computer", ignoreCase = true) == true) ||
                         (blackPlayerUsername?.contains("computer", ignoreCase = true) == true)
    
    // Determine player color for computer games
    val playerColor = when {
        whitePlayerUsername?.contains("computer", ignoreCase = true) == true -> PlayerSide.BLACK
        blackPlayerUsername?.contains("computer", ignoreCase = true) == true -> PlayerSide.WHITE
        else -> null
    }
    
    return Game(
        id = id,
        whitePlayer = whitePlayerUsername?.let { 
            Player(whitePlayer ?: 0, it, whitePlayerRating) 
        },
        blackPlayer = blackPlayerUsername?.let { 
            Player(blackPlayer ?: 0, it, blackPlayerRating) 
        },
        status = GameState.fromString(status),
        fen = fen,
        winnerId = winner,
        moves = moves.map { it.toDomain() },
        isComputerGame = isComputerGame,
        playerColor = playerColor
    )
}

private fun ComputerGameResponse.toDomain(): Game {
    return Game(
        id = id,
        whitePlayer = whitePlayerUsername?.let { 
            Player(whitePlayer ?: 0, it, whitePlayerRating ?: computerRating) 
        },
        blackPlayer = blackPlayerUsername?.let { 
            Player(blackPlayer ?: 0, it, blackPlayerRating ?: computerRating) 
        },
        status = GameState.fromString(status),
        fen = fen,
        winnerId = winner,
        moves = moves.map { it.toDomain() },
        isComputerGame = true,
        computerRating = computerRating,
        playerColor = playerColor?.let { PlayerSide.fromString(it) }
    )
}

private fun MoveDto.toDomain(): Move {
    return Move(
        id = id,
        gameId = game,
        moveNumber = moveNumber,
        playerId = player,
        playerUsername = playerUsername,
        fromSquare = fromSquare,
        toSquare = toSquare,
        notation = notation,
        fenAfterMove = fenAfterMove
    )
}

private fun GameStatus.toDomain(): GameStatusInfo {
    return GameStatusInfo(
        isCheckmate = isCheckmate,
        isStalemate = isStalemate,
        isCheck = isCheck,
        isGameOver = isGameOver,
        result = result
    )
}

private fun TimerResponse.toDomain(): GameTimer {
    return GameTimer(
        gameId = gameId,
        whiteTime = whiteTime,
        blackTime = blackTime,
        currentTurn = PlayerSide.fromString(currentTurn),
        gameStatus = gameStatus ?: status,
        timeControl = timeControl,
        increment = increment,
        whiteTimePressure = TimePressureLevel.fromString(timePressure?.white),
        blackTimePressure = TimePressureLevel.fromString(timePressure?.black)
    )
}

// ==================== Error Handling ====================

/**
 * Parse error response to get a user-friendly message
 * Handles HTML error pages, JSON errors, and HTTP status codes
 */
private fun parseErrorMessage(statusCode: Int, errorBody: String?): String {
    // Check for HTML response (server returned error page)
    if (errorBody?.contains("<!DOCTYPE", ignoreCase = true) == true ||
        errorBody?.contains("<html", ignoreCase = true) == true) {
        return when (statusCode) {
            404 -> "Endpoint not found. Server may be outdated."
            500 -> "Server error. Please try again later."
            401 -> "Please login again."
            403 -> "Access denied."
            else -> "Server error ($statusCode)"
        }
    }
    
    // Try to extract JSON error message
    if (errorBody != null && errorBody.isNotBlank()) {
        // Simple extraction for {"detail": "message"} or {"error": "message"}
        val detailMatch = Regex("\"(?:detail|error|message)\"\\s*:\\s*\"([^\"]+)\"").find(errorBody)
        if (detailMatch != null) {
            return detailMatch.groupValues[1]
        }
        
        // Return truncated error if it's short enough
        if (errorBody.length < 100 && !errorBody.contains("<")) {
            return errorBody
        }
    }
    
    // Default messages based on status code
    return when (statusCode) {
        400 -> "Invalid request"
        401 -> "Please login again"
        403 -> "Access denied"
        404 -> "Not found"
        500 -> "Server error"
        502 -> "Server unavailable"
        503 -> "Service temporarily unavailable"
        else -> "Request failed ($statusCode)"
    }
}
