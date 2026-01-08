package com.example.chess_platform

import android.os.Bundle
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.activity.enableEdgeToEdge
import androidx.compose.runtime.collectAsState
import androidx.compose.runtime.getValue
import androidx.navigation.compose.rememberNavController
import com.example.chess_platform.domain.repository.AuthRepository
import com.example.chess_platform.ui.navigation.ChessNavGraph
import com.example.chess_platform.ui.navigation.Screen
import com.example.chess_platform.ui.theme.ChessplatformTheme
import dagger.hilt.android.AndroidEntryPoint
import javax.inject.Inject

@AndroidEntryPoint
class MainActivity : ComponentActivity() {
    
    @Inject
    lateinit var authRepository: AuthRepository
    
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        enableEdgeToEdge()
        setContent {
            ChessplatformTheme {
                val navController = rememberNavController()
                val isLoggedIn by authRepository.isLoggedIn.collectAsState(initial = false)
                
                ChessNavGraph(
                    navController = navController,
                    authRepository = authRepository,
                    startDestination = if (isLoggedIn) Screen.Dashboard.route else Screen.Login.route
                )
            }
        }
    }
}