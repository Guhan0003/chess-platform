package com.example.chess_platform.data.repository

import com.example.chess_platform.data.local.TokenManager
import com.example.chess_platform.data.remote.api.AuthApi
import com.example.chess_platform.data.remote.dto.ApiErrorResponse
import com.example.chess_platform.data.remote.dto.LoginRequest
import com.example.chess_platform.data.remote.dto.RegisterRequest
import com.example.chess_platform.data.remote.dto.RefreshTokenRequest
import com.example.chess_platform.data.remote.dto.UserProfileResponse
import com.example.chess_platform.data.remote.dto.SkillLevelItem
import com.example.chess_platform.domain.model.User
import com.example.chess_platform.domain.repository.AuthRepository
import com.example.chess_platform.util.Resource
import com.squareup.moshi.Moshi
import kotlinx.coroutines.flow.Flow
import javax.inject.Inject
import javax.inject.Singleton

@Singleton
class AuthRepositoryImpl @Inject constructor(
    private val authApi: AuthApi,
    private val tokenManager: TokenManager,
    private val moshi: Moshi
) : AuthRepository {
    
    override suspend fun login(username: String, password: String): Resource<User> {
        return try {
            val response = authApi.login(LoginRequest(username, password))
            
            if (response.isSuccessful) {
                response.body()?.let { loginResponse ->
                    // Save tokens
                    tokenManager.saveTokens(loginResponse.accessToken, loginResponse.refreshToken)
                    
                    // Get user profile
                    val profileResult = getProfile()
                    if (profileResult is Resource.Success) {
                        Resource.Success(profileResult.data!!)
                    } else {
                        // Login succeeded but profile fetch failed
                        // Create minimal user from username
                        Resource.Success(User(id = 0, username = username, email = ""))
                    }
                } ?: Resource.Error("Empty response from server")
            } else {
                val errorBody = response.errorBody()?.string()
                val errorMessage = parseErrorMessage(errorBody) ?: "Login failed"
                Resource.Error(errorMessage)
            }
        } catch (e: Exception) {
            Resource.Error(e.message ?: "Network error occurred")
        }
    }
    
    override suspend fun register(
        username: String,
        email: String,
        password: String,
        passwordConfirm: String,
        skillLevel: String,
        firstName: String?,
        lastName: String?
    ): Resource<String> {
        return try {
            val response = authApi.register(
                RegisterRequest(
                    username = username,
                    email = email,
                    password = password,
                    passwordConfirm = passwordConfirm,
                    skillLevel = skillLevel,
                    firstName = firstName,
                    lastName = lastName
                )
            )
            
            if (response.isSuccessful) {
                response.body()?.let { registerResponse ->
                    Resource.Success(registerResponse.message)
                } ?: Resource.Success("Registration successful!")
            } else {
                val errorBody = response.errorBody()?.string()
                val errorMessage = parseErrorMessage(errorBody) ?: "Registration failed"
                Resource.Error(errorMessage)
            }
        } catch (e: Exception) {
            Resource.Error(e.message ?: "Network error occurred")
        }
    }
    
    override suspend fun logout(): Resource<Unit> {
        return try {
            authApi.logout()
            tokenManager.clearTokens()
            Resource.Success(Unit)
        } catch (e: Exception) {
            // Clear tokens anyway on logout
            tokenManager.clearTokens()
            Resource.Success(Unit)
        }
    }
    
    override suspend fun getProfile(): Resource<User> {
        return try {
            val response = authApi.getProfile()
            
            if (response.isSuccessful) {
                response.body()?.let { profileResponse ->
                    val user = profileResponse.toUser()
                    tokenManager.saveUserInfo(user.id, user.username)
                    Resource.Success(user)
                } ?: Resource.Error("Empty profile response")
            } else {
                Resource.Error("Failed to fetch profile")
            }
        } catch (e: Exception) {
            Resource.Error(e.message ?: "Network error occurred")
        }
    }
    
    override suspend fun refreshToken(): Resource<String> {
        return try {
            val refreshToken = tokenManager.getRefreshTokenSync()
                ?: return Resource.Error("No refresh token available")
            
            val response = authApi.refreshToken(RefreshTokenRequest(refreshToken))
            
            if (response.isSuccessful) {
                response.body()?.let { refreshResponse ->
                    tokenManager.updateAccessToken(refreshResponse.accessToken)
                    Resource.Success(refreshResponse.accessToken)
                } ?: Resource.Error("Empty refresh response")
            } else {
                // Refresh failed - clear tokens
                tokenManager.clearTokens()
                Resource.Error("Session expired. Please login again.")
            }
        } catch (e: Exception) {
            Resource.Error(e.message ?: "Failed to refresh token")
        }
    }
    
    override suspend fun getSkillLevels(): Resource<List<SkillLevelItem>> {
        return try {
            val response = authApi.getSkillLevels()
            
            if (response.isSuccessful) {
                response.body()?.let { skillLevelResponse ->
                    Resource.Success(skillLevelResponse.skillLevels)
                } ?: Resource.Success(getDefaultSkillLevels())
            } else {
                Resource.Success(getDefaultSkillLevels())
            }
        } catch (e: Exception) {
            // Return default skill levels if API fails
            Resource.Success(getDefaultSkillLevels())
        }
    }
    
    override val isLoggedIn: Flow<Boolean> = tokenManager.isLoggedIn
    
    override val currentUsername: Flow<String?> = tokenManager.username
    
    private fun parseErrorMessage(errorBody: String?): String? {
        if (errorBody.isNullOrEmpty()) return null
        
        return try {
            val adapter = moshi.adapter(ApiErrorResponse::class.java)
            val errorResponse = adapter.fromJson(errorBody)
            
            errorResponse?.let { error ->
                when {
                    error.detail != null -> error.detail
                    error.error != null -> error.error
                    error.message != null -> error.message
                    error.usernameError?.isNotEmpty() == true -> error.usernameError.first()
                    error.emailError?.isNotEmpty() == true -> error.emailError.first()
                    error.passwordError?.isNotEmpty() == true -> error.passwordError.first()
                    error.nonFieldErrors?.isNotEmpty() == true -> error.nonFieldErrors.first()
                    else -> null
                }
            }
        } catch (e: Exception) {
            null
        }
    }
    
    private fun getDefaultSkillLevels(): List<SkillLevelItem> {
        return listOf(
            SkillLevelItem("beginner", "Beginner", "New to chess or learning basics", 800),
            SkillLevelItem("intermediate", "Intermediate", "Know the rules and basic tactics", 1200),
            SkillLevelItem("advanced", "Advanced", "Experienced player with good skills", 1600),
            SkillLevelItem("expert", "Expert", "Strong player, tournament experience", 2000)
        )
    }
    
    private fun UserProfileResponse.toUser(): User {
        return User(
            id = id,
            username = username,
            email = email,
            firstName = firstName,
            lastName = lastName,
            bio = bio,
            country = country,
            avatar = avatar,
            isOnline = isOnline ?: false,
            blitzRating = blitzRating ?: 1200,
            rapidRating = rapidRating ?: 1200,
            classicalRating = classicalRating ?: 1200,
            gamesPlayed = gamesPlayed ?: 0,
            gamesWon = gamesWon ?: 0,
            gamesLost = gamesLost ?: 0,
            gamesDrawn = gamesDrawn ?: 0
        )
    }
}
