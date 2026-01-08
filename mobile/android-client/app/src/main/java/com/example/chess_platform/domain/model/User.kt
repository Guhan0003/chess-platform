package com.example.chess_platform.domain.model

/**
 * Domain model for User
 * Clean architecture - business logic layer
 */
data class User(
    val id: Int,
    val username: String,
    val email: String,
    val firstName: String? = null,
    val lastName: String? = null,
    val bio: String? = null,
    val country: String? = null,
    val avatar: String? = null,
    val isOnline: Boolean = false,
    val blitzRating: Int = 1200,
    val rapidRating: Int = 1200,
    val classicalRating: Int = 1200,
    val gamesPlayed: Int = 0,
    val gamesWon: Int = 0,
    val gamesLost: Int = 0,
    val gamesDrawn: Int = 0
) {
    val fullName: String
        get() = listOfNotNull(firstName, lastName).joinToString(" ").ifEmpty { username }
    
    val winRate: Double
        get() = if (gamesPlayed > 0) (gamesWon.toDouble() / gamesPlayed) * 100 else 0.0
    
    val highestRating: Int
        get() = maxOf(blitzRating, rapidRating, classicalRating)
}
