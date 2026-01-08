package com.example.chess_platform

import android.app.Application
import dagger.hilt.android.HiltAndroidApp

/**
 * Chess Platform Application class
 * Entry point for Hilt dependency injection
 */
@HiltAndroidApp
class ChessPlatformApp : Application() {
    
    override fun onCreate() {
        super.onCreate()
        // Initialize any app-wide components here
    }
}
