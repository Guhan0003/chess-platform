package com.example.chess_platform.ui.theme

import android.app.Activity
import android.os.Build
import androidx.compose.foundation.isSystemInDarkTheme
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.darkColorScheme
import androidx.compose.material3.dynamicDarkColorScheme
import androidx.compose.material3.dynamicLightColorScheme
import androidx.compose.material3.lightColorScheme
import androidx.compose.runtime.Composable
import androidx.compose.runtime.SideEffect
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.toArgb
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.platform.LocalView
import androidx.core.view.WindowCompat

// Chess Platform Dark Theme (Primary theme - matching web UI)
private val ChessDarkColorScheme = darkColorScheme(
    primary = AccentPrimary,
    onPrimary = TextInverse,
    primaryContainer = AccentDark,
    onPrimaryContainer = TextPrimary,
    
    secondary = AccentSecondary,
    onSecondary = TextInverse,
    secondaryContainer = AccentDark,
    onSecondaryContainer = TextPrimary,
    
    tertiary = AccentLight,
    onTertiary = TextInverse,
    tertiaryContainer = AccentSecondary,
    onTertiaryContainer = TextPrimary,
    
    background = BgPrimary,
    onBackground = TextPrimary,
    
    surface = BgSecondary,
    onSurface = TextPrimary,
    surfaceVariant = BgTertiary,
    onSurfaceVariant = TextSecondary,
    
    error = Error,
    onError = Color.White,
    errorContainer = Color(0xFF93000A),
    onErrorContainer = Color(0xFFFFDAD6),
    
    outline = BorderDefault,
    outlineVariant = BorderLight,
    
    inverseSurface = BoardLight,
    inverseOnSurface = BgPrimary,
    inversePrimary = AccentDark,
    
    scrim = Color.Black.copy(alpha = 0.7f)
)

// Optional Light Theme (for future use)
private val ChessLightColorScheme = lightColorScheme(
    primary = AccentPrimary,
    onPrimary = Color.White,
    primaryContainer = AccentLight,
    onPrimaryContainer = AccentDark,
    
    secondary = AccentSecondary,
    onSecondary = Color.White,
    
    background = Color(0xFFFFFBFE),
    onBackground = BgPrimary,
    
    surface = Color(0xFFFFFBFE),
    onSurface = BgPrimary,
    
    error = Error,
    onError = Color.White
)

@Composable
fun ChessplatformTheme(
    darkTheme: Boolean = true,  // Default to dark theme for chess platform
    dynamicColor: Boolean = false,  // Disabled to maintain consistent branding
    content: @Composable () -> Unit
) {
    val colorScheme = when {
        dynamicColor && Build.VERSION.SDK_INT >= Build.VERSION_CODES.S -> {
            val context = LocalContext.current
            if (darkTheme) dynamicDarkColorScheme(context) else dynamicLightColorScheme(context)
        }
        darkTheme -> ChessDarkColorScheme
        else -> ChessLightColorScheme
    }
    
    // Update system bars to match theme
    val view = LocalView.current
    if (!view.isInEditMode) {
        SideEffect {
            val window = (view.context as Activity).window
            window.statusBarColor = BgPrimary.toArgb()
            window.navigationBarColor = BgPrimary.toArgb()
            WindowCompat.getInsetsController(window, view).isAppearanceLightStatusBars = !darkTheme
        }
    }

    MaterialTheme(
        colorScheme = colorScheme,
        typography = Typography,
        content = content
    )
}