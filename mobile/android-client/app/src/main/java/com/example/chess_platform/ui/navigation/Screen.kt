package com.example.chess_platform.ui.navigation

/**
 * Navigation routes for the Chess Platform app
 */
sealed class Screen(val route: String) {
    // Auth screens
    object Login : Screen("login")
    object Register : Screen("register")
    object ForgotPassword : Screen("forgot_password")
    
    // Main screens
    object Dashboard : Screen("dashboard")
    object Profile : Screen("profile")
    object Settings : Screen("settings")
    
    // Game screens
    object PlayMenu : Screen("play_menu")
    object Game : Screen("game/{gameId}") {
        fun createRoute(gameId: String) = "game/$gameId"
    }
    object GameAnalysis : Screen("game_analysis/{gameId}") {
        fun createRoute(gameId: String) = "game_analysis/$gameId"
    }
    
    // Bot/Offline game
    object PlayBot : Screen("play_bot")
    object OverTheBoard : Screen("over_the_board")
    
    // Puzzles
    object Puzzles : Screen("puzzles")
    object PuzzleGame : Screen("puzzle/{puzzleId}") {
        fun createRoute(puzzleId: String) = "puzzle/$puzzleId"
    }
    
    // Leaderboard
    object Leaderboard : Screen("leaderboard")
}
