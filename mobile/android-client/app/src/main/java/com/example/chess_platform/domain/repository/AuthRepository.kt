package com.example.chess_platform.domain.repository

import com.example.chess_platform.data.remote.dto.SkillLevelItem
import com.example.chess_platform.domain.model.User
import com.example.chess_platform.util.Resource
import kotlinx.coroutines.flow.Flow

/**
 * Authentication Repository Interface
 * Defines the contract for authentication operations
 */
interface AuthRepository {
    
    /**
     * Login with username and password
     */
    suspend fun login(username: String, password: String): Resource<User>
    
    /**
     * Register a new user
     */
    suspend fun register(
        username: String,
        email: String,
        password: String,
        passwordConfirm: String,
        skillLevel: String,
        firstName: String? = null,
        lastName: String? = null
    ): Resource<String>
    
    /**
     * Logout current user
     */
    suspend fun logout(): Resource<Unit>
    
    /**
     * Get current user profile
     */
    suspend fun getProfile(): Resource<User>
    
    /**
     * Refresh authentication token
     */
    suspend fun refreshToken(): Resource<String>
    
    /**
     * Get available skill levels for registration
     */
    suspend fun getSkillLevels(): Resource<List<SkillLevelItem>>
    
    /**
     * Flow to observe login state
     */
    val isLoggedIn: Flow<Boolean>
    
    /**
     * Flow to observe current username
     */
    val currentUsername: Flow<String?>
}
