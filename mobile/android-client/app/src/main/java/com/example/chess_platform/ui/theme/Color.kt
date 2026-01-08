package com.example.chess_platform.ui.theme

import androidx.compose.ui.graphics.Color

// ================================
// Chess Platform Color System
// Matching Web UI Dark Chess Theme
// ================================

// Background Colors
val BgPrimary = Color(0xFF0A0A0A)
val BgSecondary = Color(0xFF1A1A1A)
val BgTertiary = Color(0xFF2A2A2A)
val BgCard = Color(0xFF1E1E1E)
val BgHover = Color(0xFF2E2E2E)

// Chess Green Accents
val AccentPrimary = Color(0xFF769656)
val AccentSecondary = Color(0xFF5D7A42)
val AccentDark = Color(0xFF4A5F35)
val AccentLight = Color(0xFF8FAD6B)

// Alias for convenience
val ChessGreen = AccentPrimary

// Chess Board Colors
val BoardLight = Color(0xFFF0D9B5)
val BoardDark = Color(0xFFB58863)

// Text Colors
val TextPrimary = Color(0xFFF0D9B5)
val TextSecondary = Color(0xFFD4C5A6)
val TextMuted = Color(0xFF9A8F7E)
val TextInverse = Color(0xFF2A2A2A)

// Status Colors
val Success = Color(0xFF22C55E)
val Error = Color(0xFFEF4444)
val Warning = Color(0xFFF59E0B)
val Info = Color(0xFF3B82F6)

// Border Colors
val BorderDefault = Color(0xFF3A3A3A)
val BorderLight = Color(0x1AF0D9B5)  // 10% opacity
val BorderFocus = AccentPrimary

// Gradients (for reference - implement via Brush in Compose)
val GradientAccentStart = AccentPrimary
val GradientAccentEnd = AccentLight

// Legacy colors (keeping for compatibility)
val Purple80 = AccentLight
val PurpleGrey80 = TextSecondary
val Pink80 = BoardLight

val Purple40 = AccentPrimary
val PurpleGrey40 = TextMuted
val Pink40 = BoardDark