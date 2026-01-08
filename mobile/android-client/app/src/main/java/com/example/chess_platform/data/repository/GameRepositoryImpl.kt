package com.example.chess_platform.data.repository

import com.example.chess_platform.data.remote.api.GameApi
import com.example.chess_platform.data.remote.dto.*
import com.example.chess_platform.domain.model.*
import com.example.chess_platform.domain.repository.ActiveGameConstraint
import com.example.chess_platform.domain.repository.GameRepository
import javax.inject.Inject

/**
 * Implementation of GameRepository
 */
class GameRepositoryImpl @Inject constructor(
    private val gameApi: GameApi
) : GameRepository {

    override suspend fun createGame(timeControl: String): Result<Game> {
        return try {
            val response = gameApi.createGame(CreateGameRequest(timeControl))
            if (response.isSuccessful && response.body() != null) {
                Result.success(response.body()!!.toDomain())
            } else {
                Result.failure(Exception(response.errorBody()?.string() ?: "Failed to create game"))
            }
        } catch (e: Exception) {
            Result.failure(e)
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
                Result.failure(Exception(response.errorBody()?.string() ?: "Failed to create computer game"))
            }
        } catch (e: Exception) {
            Result.failure(e)
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
            val request = difficulty?.let { ComputerMoveRequest(it) }
            val response = gameApi.makeComputerMove(gameId, request)
            if (response.isSuccessful && response.body() != null) {
                val move = response.body()!!.move?.toDomain()
                Result.success(move)
            } else {
                Result.failure(Exception(response.errorBody()?.string() ?: "Failed to get computer move"))
            }
        } catch (e: Exception) {
            Result.failure(e)
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
            val response = gameApi.resignGame(gameId)
            if (response.isSuccessful && response.body() != null) {
                val game = response.body()!!.game
                if (game != null) {
                    Result.success(game.toDomain())
                } else {
                    Result.failure(Exception("Game data not returned"))
                }
            } else {
                Result.failure(Exception(response.errorBody()?.string() ?: "Failed to resign"))
            }
        } catch (e: Exception) {
            Result.failure(e)
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
        isComputerGame = false
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
