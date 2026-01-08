package com.example.chess_platform.ui.play

import androidx.compose.foundation.background
import androidx.compose.foundation.border
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.foundation.verticalScroll
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.automirrored.filled.ArrowBack
import androidx.compose.material.icons.filled.*
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.vector.ImageVector
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import androidx.hilt.navigation.compose.hiltViewModel
import com.example.chess_platform.data.remote.dto.BotDifficulty
import com.example.chess_platform.data.remote.dto.PlayerColor
import com.example.chess_platform.data.remote.dto.TimeControlOption
import com.example.chess_platform.ui.theme.ChessGreen

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun PlayScreen(
    onNavigateBack: () -> Unit,
    onNavigateToGame: (Int) -> Unit,
    viewModel: PlayViewModel = hiltViewModel()
) {
    val uiState by viewModel.uiState.collectAsState()
    
    // Handle navigation to game
    LaunchedEffect(uiState.navigateToGame) {
        uiState.navigateToGame?.let { gameId ->
            onNavigateToGame(gameId)
            viewModel.onNavigatedToGame()
        }
    }
    
    // Show error snackbar
    val snackbarHostState = remember { SnackbarHostState() }
    LaunchedEffect(uiState.error) {
        uiState.error?.let { error ->
            snackbarHostState.showSnackbar(error)
            viewModel.clearError()
        }
    }
    
    var selectedMode by remember { mutableStateOf(GameMode.BOT) }
    
    Scaffold(
        snackbarHost = { SnackbarHost(snackbarHostState) },
        topBar = {
            TopAppBar(
                title = { Text("Play Chess", fontWeight = FontWeight.Bold) },
                navigationIcon = {
                    IconButton(onClick = onNavigateBack) {
                        Icon(Icons.AutoMirrored.Filled.ArrowBack, contentDescription = "Back")
                    }
                },
                colors = TopAppBarDefaults.topAppBarColors(
                    containerColor = MaterialTheme.colorScheme.background
                )
            )
        }
    ) { paddingValues ->
        Column(
            modifier = Modifier
                .fillMaxSize()
                .padding(paddingValues)
                .verticalScroll(rememberScrollState())
                .padding(16.dp)
        ) {
            // Game Mode Selection
            Text(
                text = "Select Game Mode",
                style = MaterialTheme.typography.titleMedium,
                fontWeight = FontWeight.SemiBold,
                modifier = Modifier.padding(bottom = 12.dp)
            )
            
            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.spacedBy(12.dp)
            ) {
                GameModeCard(
                    title = "Online",
                    icon = Icons.Default.Public,
                    isSelected = selectedMode == GameMode.ONLINE,
                    onClick = { selectedMode = GameMode.ONLINE },
                    modifier = Modifier.weight(1f)
                )
                GameModeCard(
                    title = "Bot",
                    icon = Icons.Default.SmartToy,
                    isSelected = selectedMode == GameMode.BOT,
                    onClick = { selectedMode = GameMode.BOT },
                    modifier = Modifier.weight(1f)
                )
                GameModeCard(
                    title = "OTB",
                    icon = Icons.Default.People,
                    isSelected = selectedMode == GameMode.OTB,
                    onClick = { selectedMode = GameMode.OTB },
                    modifier = Modifier.weight(1f)
                )
            }
            
            Spacer(modifier = Modifier.height(24.dp))
            
            // Time Control Selection
            Text(
                text = "Time Control",
                style = MaterialTheme.typography.titleMedium,
                fontWeight = FontWeight.SemiBold,
                modifier = Modifier.padding(bottom = 12.dp)
            )
            
            Column(verticalArrangement = Arrangement.spacedBy(8.dp)) {
                TimeControlOption.entries.forEach { timeControl ->
                    TimeControlRow(
                        timeControl = timeControl,
                        isSelected = uiState.selectedTimeControl == timeControl,
                        onClick = { viewModel.selectTimeControl(timeControl) }
                    )
                }
            }
            
            // Bot-specific options
            if (selectedMode == GameMode.BOT) {
                Spacer(modifier = Modifier.height(24.dp))
                
                // Difficulty Selection
                Text(
                    text = "Bot Difficulty",
                    style = MaterialTheme.typography.titleMedium,
                    fontWeight = FontWeight.SemiBold,
                    modifier = Modifier.padding(bottom = 12.dp)
                )
                
                Column(verticalArrangement = Arrangement.spacedBy(8.dp)) {
                    BotDifficulty.entries.forEach { difficulty ->
                        DifficultyRow(
                            difficulty = difficulty,
                            isSelected = uiState.selectedDifficulty == difficulty,
                            onClick = { viewModel.selectDifficulty(difficulty) }
                        )
                    }
                }
                
                Spacer(modifier = Modifier.height(24.dp))
                
                // Color Selection
                Text(
                    text = "Play As",
                    style = MaterialTheme.typography.titleMedium,
                    fontWeight = FontWeight.SemiBold,
                    modifier = Modifier.padding(bottom = 12.dp)
                )
                
                Row(
                    modifier = Modifier.fillMaxWidth(),
                    horizontalArrangement = Arrangement.spacedBy(12.dp)
                ) {
                    PlayerColor.entries.forEach { color ->
                        ColorSelectionCard(
                            color = color,
                            isSelected = uiState.selectedColor == color,
                            onClick = { viewModel.selectColor(color) },
                            modifier = Modifier.weight(1f)
                        )
                    }
                }
            }
            
            Spacer(modifier = Modifier.height(32.dp))
            
            // Start Game Button
            Button(
                onClick = {
                    when (selectedMode) {
                        GameMode.ONLINE -> viewModel.createOnlineGame()
                        GameMode.BOT -> viewModel.createBotGame()
                        GameMode.OTB -> {
                            // TODO: Navigate to OTB game
                        }
                    }
                },
                modifier = Modifier
                    .fillMaxWidth()
                    .height(56.dp),
                enabled = !uiState.isLoading,
                colors = ButtonDefaults.buttonColors(
                    containerColor = ChessGreen
                ),
                shape = RoundedCornerShape(12.dp)
            ) {
                if (uiState.isLoading) {
                    CircularProgressIndicator(
                        color = Color.White,
                        modifier = Modifier.size(24.dp)
                    )
                } else {
                    Icon(
                        Icons.Default.PlayArrow,
                        contentDescription = null,
                        modifier = Modifier.size(24.dp)
                    )
                    Spacer(modifier = Modifier.width(8.dp))
                    Text(
                        text = when (selectedMode) {
                            GameMode.ONLINE -> "Find Opponent"
                            GameMode.BOT -> "Start Game"
                            GameMode.OTB -> "Start Local Game"
                        },
                        fontSize = 18.sp,
                        fontWeight = FontWeight.Bold
                    )
                }
            }
        }
    }
}

@Composable
private fun GameModeCard(
    title: String,
    icon: ImageVector,
    isSelected: Boolean,
    onClick: () -> Unit,
    modifier: Modifier = Modifier
) {
    val backgroundColor = if (isSelected) {
        ChessGreen.copy(alpha = 0.2f)
    } else {
        MaterialTheme.colorScheme.surfaceVariant
    }
    val borderColor = if (isSelected) ChessGreen else Color.Transparent
    
    Column(
        modifier = modifier
            .clip(RoundedCornerShape(12.dp))
            .border(2.dp, borderColor, RoundedCornerShape(12.dp))
            .background(backgroundColor)
            .clickable(onClick = onClick)
            .padding(16.dp),
        horizontalAlignment = Alignment.CenterHorizontally
    ) {
        Icon(
            icon,
            contentDescription = title,
            modifier = Modifier.size(32.dp),
            tint = if (isSelected) ChessGreen else MaterialTheme.colorScheme.onSurfaceVariant
        )
        Spacer(modifier = Modifier.height(8.dp))
        Text(
            text = title,
            fontWeight = if (isSelected) FontWeight.Bold else FontWeight.Medium,
            color = if (isSelected) ChessGreen else MaterialTheme.colorScheme.onSurfaceVariant
        )
    }
}

@Composable
private fun TimeControlRow(
    timeControl: TimeControlOption,
    isSelected: Boolean,
    onClick: () -> Unit
) {
    val backgroundColor = if (isSelected) {
        ChessGreen.copy(alpha = 0.15f)
    } else {
        MaterialTheme.colorScheme.surfaceVariant.copy(alpha = 0.5f)
    }
    val borderColor = if (isSelected) ChessGreen else Color.Transparent
    
    Row(
        modifier = Modifier
            .fillMaxWidth()
            .clip(RoundedCornerShape(8.dp))
            .border(1.5.dp, borderColor, RoundedCornerShape(8.dp))
            .background(backgroundColor)
            .clickable(onClick = onClick)
            .padding(horizontal = 16.dp, vertical = 12.dp),
        verticalAlignment = Alignment.CenterVertically
    ) {
        RadioButton(
            selected = isSelected,
            onClick = onClick,
            colors = RadioButtonDefaults.colors(
                selectedColor = ChessGreen
            )
        )
        Spacer(modifier = Modifier.width(12.dp))
        Column {
            Text(
                text = timeControl.displayName,
                fontWeight = FontWeight.Medium
            )
        }
    }
}

@Composable
private fun DifficultyRow(
    difficulty: BotDifficulty,
    isSelected: Boolean,
    onClick: () -> Unit
) {
    val backgroundColor = if (isSelected) {
        ChessGreen.copy(alpha = 0.15f)
    } else {
        MaterialTheme.colorScheme.surfaceVariant.copy(alpha = 0.5f)
    }
    val borderColor = if (isSelected) ChessGreen else Color.Transparent
    
    Row(
        modifier = Modifier
            .fillMaxWidth()
            .clip(RoundedCornerShape(8.dp))
            .border(1.5.dp, borderColor, RoundedCornerShape(8.dp))
            .background(backgroundColor)
            .clickable(onClick = onClick)
            .padding(horizontal = 16.dp, vertical = 12.dp),
        verticalAlignment = Alignment.CenterVertically
    ) {
        RadioButton(
            selected = isSelected,
            onClick = onClick,
            colors = RadioButtonDefaults.colors(
                selectedColor = ChessGreen
            )
        )
        Spacer(modifier = Modifier.width(12.dp))
        Column(modifier = Modifier.weight(1f)) {
            Text(
                text = difficulty.displayName,
                fontWeight = FontWeight.Medium
            )
        }
        Text(
            text = "~${difficulty.rating}",
            color = MaterialTheme.colorScheme.onSurfaceVariant,
            fontSize = 14.sp
        )
    }
}

@Composable
private fun ColorSelectionCard(
    color: PlayerColor,
    isSelected: Boolean,
    onClick: () -> Unit,
    modifier: Modifier = Modifier
) {
    val backgroundColor = if (isSelected) {
        ChessGreen.copy(alpha = 0.2f)
    } else {
        MaterialTheme.colorScheme.surfaceVariant
    }
    val borderColor = if (isSelected) ChessGreen else Color.Transparent
    
    val pieceColor = when (color) {
        PlayerColor.WHITE -> Color.White
        PlayerColor.BLACK -> Color.DarkGray
        PlayerColor.RANDOM -> ChessGreen
    }
    
    val icon = when (color) {
        PlayerColor.WHITE -> "♔"
        PlayerColor.BLACK -> "♚"
        PlayerColor.RANDOM -> "?"
    }
    
    Column(
        modifier = modifier
            .clip(RoundedCornerShape(12.dp))
            .border(2.dp, borderColor, RoundedCornerShape(12.dp))
            .background(backgroundColor)
            .clickable(onClick = onClick)
            .padding(16.dp),
        horizontalAlignment = Alignment.CenterHorizontally
    ) {
        Text(
            text = icon,
            fontSize = 36.sp,
            color = pieceColor,
            textAlign = TextAlign.Center
        )
        Spacer(modifier = Modifier.height(8.dp))
        Text(
            text = color.displayName,
            fontWeight = if (isSelected) FontWeight.Bold else FontWeight.Medium,
            color = if (isSelected) ChessGreen else MaterialTheme.colorScheme.onSurfaceVariant
        )
    }
}
