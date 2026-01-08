package com.example.chess_platform.di

import com.example.chess_platform.data.local.TokenManager
import kotlinx.coroutines.runBlocking
import okhttp3.Interceptor
import okhttp3.Response

/**
 * OkHttp Interceptor for adding authentication headers
 * Automatically adds Bearer token to authenticated requests
 */
class AuthInterceptor(
    private val tokenManager: TokenManager
) : Interceptor {
    
    companion object {
        // Endpoints that don't require authentication
        private val PUBLIC_ENDPOINTS = listOf(
            "auth/login",
            "auth/register",
            "auth/refresh",
            "auth/skill-levels",
            "auth/forgot-password"
        )
    }
    
    override fun intercept(chain: Interceptor.Chain): Response {
        val originalRequest = chain.request()
        val url = originalRequest.url.toString()
        
        // Check if endpoint is public
        val isPublicEndpoint = PUBLIC_ENDPOINTS.any { url.contains(it) }
        
        if (isPublicEndpoint) {
            return chain.proceed(originalRequest)
        }
        
        // Get access token
        val accessToken = runBlocking {
            tokenManager.getAccessTokenSync()
        }
        
        return if (accessToken != null) {
            val authenticatedRequest = originalRequest.newBuilder()
                .header("Authorization", "Bearer $accessToken")
                .build()
            chain.proceed(authenticatedRequest)
        } else {
            chain.proceed(originalRequest)
        }
    }
}
