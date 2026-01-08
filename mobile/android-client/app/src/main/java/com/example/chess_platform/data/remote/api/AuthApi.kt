package com.example.chess_platform.data.remote.api

import com.example.chess_platform.data.remote.dto.LoginRequest
import com.example.chess_platform.data.remote.dto.LoginResponse
import com.example.chess_platform.data.remote.dto.RegisterRequest
import com.example.chess_platform.data.remote.dto.RegisterResponse
import com.example.chess_platform.data.remote.dto.RefreshTokenRequest
import com.example.chess_platform.data.remote.dto.RefreshTokenResponse
import com.example.chess_platform.data.remote.dto.UserProfileResponse
import com.example.chess_platform.data.remote.dto.SkillLevelResponse
import retrofit2.Response
import retrofit2.http.Body
import retrofit2.http.GET
import retrofit2.http.POST

/**
 * Authentication API endpoints matching Django backend
 */
interface AuthApi {
    
    /**
     * Login with username and password
     * Endpoint: POST /api/auth/login/
     */
    @POST("auth/login/")
    suspend fun login(@Body request: LoginRequest): Response<LoginResponse>
    
    /**
     * Register a new user
     * Endpoint: POST /api/auth/register/
     */
    @POST("auth/register/")
    suspend fun register(@Body request: RegisterRequest): Response<RegisterResponse>
    
    /**
     * Refresh access token using refresh token
     * Endpoint: POST /api/auth/refresh/
     */
    @POST("auth/refresh/")
    suspend fun refreshToken(@Body request: RefreshTokenRequest): Response<RefreshTokenResponse>
    
    /**
     * Logout - invalidate tokens
     * Endpoint: POST /api/auth/logout/
     */
    @POST("auth/logout/")
    suspend fun logout(): Response<Unit>
    
    /**
     * Get current user profile
     * Endpoint: GET /api/auth/profile/
     */
    @GET("auth/profile/")
    suspend fun getProfile(): Response<UserProfileResponse>
    
    /**
     * Get available skill levels for registration
     * Endpoint: GET /api/auth/skill-levels/
     */
    @GET("auth/skill-levels/")
    suspend fun getSkillLevels(): Response<SkillLevelResponse>
}
