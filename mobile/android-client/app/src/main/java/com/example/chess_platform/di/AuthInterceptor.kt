package com.example.chess_platform.di

import android.util.Log
import com.example.chess_platform.data.local.TokenManager
import kotlinx.coroutines.runBlocking
import okhttp3.Interceptor
import okhttp3.Response

private const val TAG = "AuthInterceptor"

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
        
        Log.d(TAG, "Request: ${originalRequest.method} $url")
        
        // Check if endpoint is public
        val isPublicEndpoint = PUBLIC_ENDPOINTS.any { url.contains(it) }
        
        if (isPublicEndpoint) {
            Log.d(TAG, "Public endpoint, skipping auth")
            return chain.proceed(originalRequest)
        }
        
        // Get access token
        val accessToken = runBlocking {
            tokenManager.getAccessTokenSync()
        }
        
        Log.d(TAG, "Token available: ${accessToken != null}, length: ${accessToken?.length ?: 0}")
        
        return if (accessToken != null) {
            val authenticatedRequest = originalRequest.newBuilder()
                .header("Authorization", "Bearer $accessToken")
                .build()
            chain.proceed(authenticatedRequest)
        } else {
            Log.w(TAG, "No token available for authenticated request!")
            chain.proceed(originalRequest)
        }
    }
}
