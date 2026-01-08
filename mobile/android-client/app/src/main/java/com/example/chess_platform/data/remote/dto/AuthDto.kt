package com.example.chess_platform.data.remote.dto

import com.squareup.moshi.Json
import com.squareup.moshi.JsonClass

// ================================
// Authentication Request/Response DTOs
// Matching Django Backend API
// ================================

/**
 * Login Request
 */
@JsonClass(generateAdapter = true)
data class LoginRequest(
    @Json(name = "username") val username: String,
    @Json(name = "password") val password: String
)

/**
 * Login Response - JWT tokens
 */
@JsonClass(generateAdapter = true)
data class LoginResponse(
    @Json(name = "access") val accessToken: String,
    @Json(name = "refresh") val refreshToken: String
)

/**
 * Register Request
 */
@JsonClass(generateAdapter = true)
data class RegisterRequest(
    @Json(name = "username") val username: String,
    @Json(name = "email") val email: String,
    @Json(name = "password") val password: String,
    @Json(name = "password_confirm") val passwordConfirm: String,
    @Json(name = "skill_level") val skillLevel: String,
    @Json(name = "first_name") val firstName: String? = null,
    @Json(name = "last_name") val lastName: String? = null
)

/**
 * Register Response
 */
@JsonClass(generateAdapter = true)
data class RegisterResponse(
    @Json(name = "message") val message: String
)

/**
 * Refresh Token Request
 */
@JsonClass(generateAdapter = true)
data class RefreshTokenRequest(
    @Json(name = "refresh") val refreshToken: String
)

/**
 * Refresh Token Response
 */
@JsonClass(generateAdapter = true)
data class RefreshTokenResponse(
    @Json(name = "access") val accessToken: String
)

/**
 * User Profile Response
 */
@JsonClass(generateAdapter = true)
data class UserProfileResponse(
    @Json(name = "id") val id: Int,
    @Json(name = "username") val username: String,
    @Json(name = "email") val email: String,
    @Json(name = "first_name") val firstName: String?,
    @Json(name = "last_name") val lastName: String?,
    @Json(name = "date_joined") val dateJoined: String?,
    
    // Chess-specific profile data
    @Json(name = "bio") val bio: String?,
    @Json(name = "country") val country: String?,
    @Json(name = "avatar") val avatar: String?,
    @Json(name = "is_online") val isOnline: Boolean?,
    @Json(name = "last_activity") val lastActivity: String?,
    @Json(name = "preferred_time_control") val preferredTimeControl: String?,
    @Json(name = "profile_public") val profilePublic: Boolean?,
    @Json(name = "show_rating") val showRating: Boolean?,
    
    // Rating data
    @Json(name = "blitz_rating") val blitzRating: Int?,
    @Json(name = "rapid_rating") val rapidRating: Int?,
    @Json(name = "classical_rating") val classicalRating: Int?,
    @Json(name = "blitz_peak") val blitzPeak: Int?,
    @Json(name = "rapid_peak") val rapidPeak: Int?,
    @Json(name = "classical_peak") val classicalPeak: Int?,
    
    // Game statistics
    @Json(name = "games_played") val gamesPlayed: Int?,
    @Json(name = "games_won") val gamesWon: Int?,
    @Json(name = "games_lost") val gamesLost: Int?,
    @Json(name = "games_drawn") val gamesDrawn: Int?,
    @Json(name = "win_rate") val winRate: Double?
)

/**
 * Skill Level Item
 */
@JsonClass(generateAdapter = true)
data class SkillLevelItem(
    @Json(name = "id") val id: String,
    @Json(name = "name") val name: String,
    @Json(name = "description") val description: String,
    @Json(name = "rating") val rating: Int
)

/**
 * Skill Levels Response
 */
@JsonClass(generateAdapter = true)
data class SkillLevelResponse(
    @Json(name = "skill_levels") val skillLevels: List<SkillLevelItem>
)

/**
 * API Error Response
 */
@JsonClass(generateAdapter = true)
data class ApiErrorResponse(
    @Json(name = "detail") val detail: String? = null,
    @Json(name = "error") val error: String? = null,
    @Json(name = "message") val message: String? = null,
    @Json(name = "username") val usernameError: List<String>? = null,
    @Json(name = "email") val emailError: List<String>? = null,
    @Json(name = "password") val passwordError: List<String>? = null,
    @Json(name = "non_field_errors") val nonFieldErrors: List<String>? = null
)
