package com.example.chess_platform.ui.navigation

import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.material3.Text
import androidx.compose.material3.TextButton
import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.collectAsState
import androidx.compose.runtime.getValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.hilt.navigation.compose.hiltViewModel
import androidx.navigation.NavHostController
import androidx.navigation.NavType
import androidx.navigation.compose.NavHost
import androidx.navigation.compose.composable
import androidx.navigation.compose.rememberNavController
import androidx.navigation.navArgument
import com.example.chess_platform.domain.repository.AuthRepository
import com.example.chess_platform.ui.auth.LoginScreen
import com.example.chess_platform.ui.auth.RegisterScreen
import com.example.chess_platform.ui.dashboard.DashboardScreen
import com.example.chess_platform.ui.game.GameScreen
import com.example.chess_platform.ui.play.PlayScreen

@Composable
fun ChessNavGraph(
    navController: NavHostController = rememberNavController(),
    authRepository: AuthRepository,
    startDestination: String = Screen.Login.route
) {
    val isLoggedIn by authRepository.isLoggedIn.collectAsState(initial = false)
    
    // Determine start destination based on login state
    LaunchedEffect(isLoggedIn) {
        if (isLoggedIn) {
            navController.navigate(Screen.Dashboard.route) {
                popUpTo(Screen.Login.route) { inclusive = true }
            }
        }
    }
    
    NavHost(
        navController = navController,
        startDestination = startDestination
    ) {
        // Auth Flow
        composable(Screen.Login.route) {
            LoginScreen(
                onNavigateToRegister = {
                    navController.navigate(Screen.Register.route)
                },
                onNavigateToForgotPassword = {
                    navController.navigate(Screen.ForgotPassword.route)
                },
                onLoginSuccess = {
                    navController.navigate(Screen.Dashboard.route) {
                        popUpTo(Screen.Login.route) { inclusive = true }
                    }
                }
            )
        }
        
        composable(Screen.Register.route) {
            RegisterScreen(
                onNavigateToLogin = {
                    navController.popBackStack()
                },
                onRegisterSuccess = {
                    // After registration, go to login
                    navController.navigate(Screen.Login.route) {
                        popUpTo(Screen.Register.route) { inclusive = true }
                    }
                }
            )
        }
        
        composable(Screen.ForgotPassword.route) {
            // TODO: Implement ForgotPasswordScreen
            ForgotPasswordPlaceholder(
                onNavigateBack = {
                    navController.popBackStack()
                }
            )
        }
        
        // Main App Flow
        composable(Screen.Dashboard.route) {
            DashboardScreen(
                onNavigateToProfile = {
                    navController.navigate(Screen.Profile.route)
                },
                onNavigateToSettings = {
                    navController.navigate(Screen.Settings.route)
                },
                onNavigateToPlayMenu = {
                    navController.navigate(Screen.PlayMenu.route)
                },
                onNavigateToPlayBot = {
                    navController.navigate(Screen.PlayBot.route)
                },
                onNavigateToOverTheBoard = {
                    navController.navigate(Screen.OverTheBoard.route)
                },
                onNavigateToPuzzles = {
                    navController.navigate(Screen.Puzzles.route)
                },
                onNavigateToLeaderboard = {
                    navController.navigate(Screen.Leaderboard.route)
                },
                onLogout = {
                    navController.navigate(Screen.Login.route) {
                        popUpTo(0) { inclusive = true }
                    }
                }
            )
        }
        
        // Play screens
        composable(Screen.PlayMenu.route) {
            PlayScreen(
                onNavigateBack = {
                    navController.popBackStack()
                },
                onNavigateToGame = { gameId ->
                    navController.navigate(Screen.Game.createRoute(gameId.toString()))
                }
            )
        }
        
        composable(Screen.PlayBot.route) {
            PlayScreen(
                onNavigateBack = {
                    navController.popBackStack()
                },
                onNavigateToGame = { gameId ->
                    navController.navigate(Screen.Game.createRoute(gameId.toString()))
                }
            )
        }
        
        // Game screen with gameId argument
        composable(
            route = Screen.Game.route,
            arguments = listOf(
                navArgument("gameId") { type = NavType.IntType }
            )
        ) {
            GameScreen(
                onNavigateBack = {
                    navController.popBackStack()
                }
            )
        }
        
        composable(Screen.OverTheBoard.route) {
            // TODO: Implement OverTheBoardScreen (local 2-player)
            PlaceholderScreen("Over the Board", onNavigateBack = { navController.popBackStack() })
        }
        
        // Profile and Settings
        composable(Screen.Profile.route) {
            // TODO: Implement ProfileScreen
            PlaceholderScreen("Profile", onNavigateBack = { navController.popBackStack() })
        }
        
        composable(Screen.Settings.route) {
            // TODO: Implement SettingsScreen
            PlaceholderScreen("Settings", onNavigateBack = { navController.popBackStack() })
        }
        
        // Puzzles
        composable(Screen.Puzzles.route) {
            // TODO: Implement PuzzlesScreen
            PlaceholderScreen("Puzzles", onNavigateBack = { navController.popBackStack() })
        }
        
        // Leaderboard
        composable(Screen.Leaderboard.route) {
            // TODO: Implement LeaderboardScreen
            PlaceholderScreen("Leaderboard", onNavigateBack = { navController.popBackStack() })
        }
    }
}

@Composable
private fun PlaceholderScreen(title: String, onNavigateBack: () -> Unit) {
    Box(
        modifier = Modifier.fillMaxSize(),
        contentAlignment = Alignment.Center
    ) {
        Column(
            horizontalAlignment = Alignment.CenterHorizontally
        ) {
            Text("$title - Coming Soon")
            TextButton(onClick = onNavigateBack) {
                Text("Go Back")
            }
        }
    }
}

@Composable
private fun ForgotPasswordPlaceholder(onNavigateBack: () -> Unit) {
    PlaceholderScreen("Forgot Password", onNavigateBack)
}
