package com.example.chess_platform.ui.game

import androidx.compose.foundation.background
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.automirrored.filled.ArrowBack
import androidx.compose.material.icons.filled.*
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import androidx.compose.ui.window.Dialog
import androidx.hilt.navigation.compose.hiltViewModel
import com.example.chess_platform.domain.model.Move
import com.example.chess_platform.domain.model.PlayerSide
import com.example.chess_platform.domain.model.TimePressureLevel
import com.example.chess_platform.ui.game.components.ChessBoard
import com.example.chess_platform.ui.theme.ChessGreen

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun GameScreen(
    onNavigateBack: () -> Unit,
    viewModel: GameViewModel = hiltViewModel()
) {
    val uiState by viewModel.uiState.collectAsState()
    
    // Show error snackbar
    val snackbarHostState = remember { SnackbarHostState() }
    LaunchedEffect(uiState.error) {
        uiState.error?.let { error ->
            snackbarHostState.showSnackbar(error)
            viewModel.clearError()
        }
    }
    
    Scaffold(
        snackbarHost = { SnackbarHost(snackbarHostState) },
        topBar = {
            TopAppBar(
                title = { 
                    Text(
                        if (uiState.isComputerGame) "vs Computer" else "Online Game",
                        fontWeight = FontWeight.Bold
                    )
                },
                navigationIcon = {
                    IconButton(onClick = onNavigateBack) {
                        Icon(Icons.AutoMirrored.Filled.ArrowBack, contentDescription = "Back")
                    }
                },
                actions = {
                    IconButton(onClick = { viewModel.flipBoard() }) {
                        Icon(Icons.Default.SwapVert, contentDescription = "Flip Board")
                    }
                },
                colors = TopAppBarDefaults.topAppBarColors(
                    containerColor = MaterialTheme.colorScheme.background
                )
            )
        }
    ) { paddingValues ->
        if (uiState.isLoading) {
            Box(
                modifier = Modifier
                    .fillMaxSize()
                    .padding(paddingValues),
                contentAlignment = Alignment.Center
            ) {
                CircularProgressIndicator(color = ChessGreen)
            }
        } else {
            Column(
                modifier = Modifier
                    .fillMaxSize()
                    .padding(paddingValues)
                    .padding(horizontal = 16.dp)
            ) {
                // Opponent info and timer
                PlayerInfoBar(
                    name = uiState.opponentName,
                    rating = uiState.opponentRating,
                    time = uiState.opponentTime,
                    isActive = uiState.currentTurn != uiState.playerColor,
                    timePressure = if (uiState.playerColor == PlayerSide.WHITE) 
                        uiState.blackTimePressure else uiState.whiteTimePressure,
                    modifier = Modifier.fillMaxWidth()
                )
                
                Spacer(modifier = Modifier.height(8.dp))
                
                // Chess board
                Box(
                    modifier = Modifier.weight(1f),
                    contentAlignment = Alignment.Center
                ) {
                    ChessBoard(
                        fen = uiState.fen,
                        isFlipped = uiState.isFlipped,
                        selectedSquare = uiState.selectedSquare,
                        legalMoves = uiState.legalMoves,
                        lastMove = uiState.lastMove,
                        isCheck = uiState.isCheck,
                        onSquareClick = { viewModel.onSquareClick(it) },
                        enabled = uiState.isMyTurn && !uiState.isGameOver && !uiState.isWaitingForComputer,
                        modifier = Modifier.fillMaxWidth()
                    )
                    
                    // Waiting for computer indicator
                    if (uiState.isWaitingForComputer) {
                        Box(
                            modifier = Modifier
                                .fillMaxSize()
                                .background(Color.Black.copy(alpha = 0.3f)),
                            contentAlignment = Alignment.Center
                        ) {
                            CircularProgressIndicator(color = ChessGreen)
                        }
                    }
                }
                
                Spacer(modifier = Modifier.height(8.dp))
                
                // Player info and timer
                PlayerInfoBar(
                    name = uiState.playerName,
                    rating = null,
                    time = uiState.myTime,
                    isActive = uiState.currentTurn == uiState.playerColor,
                    timePressure = if (uiState.playerColor == PlayerSide.WHITE) 
                        uiState.whiteTimePressure else uiState.blackTimePressure,
                    modifier = Modifier.fillMaxWidth()
                )
                
                Spacer(modifier = Modifier.height(12.dp))
                
                // Game status or move history
                if (uiState.isGameOver) {
                    GameOverCard(
                        result = uiState.result,
                        isCheckmate = uiState.isCheckmate,
                        isStalemate = uiState.isStalemate,
                        playerColor = uiState.playerColor,
                        onNewGame = onNavigateBack
                    )
                } else {
                    // Action buttons
                    Row(
                        modifier = Modifier.fillMaxWidth(),
                        horizontalArrangement = Arrangement.spacedBy(8.dp)
                    ) {
                        OutlinedButton(
                            onClick = { viewModel.showResignDialog() },
                            modifier = Modifier.weight(1f),
                            colors = ButtonDefaults.outlinedButtonColors(
                                contentColor = MaterialTheme.colorScheme.error
                            )
                        ) {
                            Icon(Icons.Default.Flag, contentDescription = null)
                            Spacer(modifier = Modifier.width(4.dp))
                            Text("Resign")
                        }
                    }
                }
                
                Spacer(modifier = Modifier.height(12.dp))
                
                // Move history
                if (uiState.moves.isNotEmpty()) {
                    MoveHistoryCard(
                        moves = uiState.moves,
                        modifier = Modifier
                            .fillMaxWidth()
                            .heightIn(max = 120.dp)
                    )
                }
                
                Spacer(modifier = Modifier.height(8.dp))
            }
        }
    }
    
    // Resign confirmation dialog
    if (uiState.showResignDialog) {
        AlertDialog(
            onDismissRequest = { viewModel.dismissResignDialog() },
            title = { Text("Resign Game?") },
            text = { Text("Are you sure you want to resign? This will count as a loss.") },
            confirmButton = {
                TextButton(
                    onClick = { viewModel.resignGame() },
                    colors = ButtonDefaults.textButtonColors(
                        contentColor = MaterialTheme.colorScheme.error
                    )
                ) {
                    Text("Resign")
                }
            },
            dismissButton = {
                TextButton(onClick = { viewModel.dismissResignDialog() }) {
                    Text("Cancel")
                }
            }
        )
    }
    
    // Promotion dialog
    if (uiState.showPromotionDialog) {
        PromotionDialog(
            isWhite = uiState.playerColor == PlayerSide.WHITE,
            onPieceSelected = { viewModel.onPromotionSelected(it) },
            onDismiss = { viewModel.dismissPromotionDialog() }
        )
    }
}

@Composable
private fun PlayerInfoBar(
    name: String,
    rating: Int?,
    time: Double,
    isActive: Boolean,
    timePressure: TimePressureLevel,
    modifier: Modifier = Modifier
) {
    val backgroundColor = if (isActive) {
        ChessGreen.copy(alpha = 0.15f)
    } else {
        MaterialTheme.colorScheme.surfaceVariant.copy(alpha = 0.5f)
    }
    
    val timerColor = when (timePressure) {
        TimePressureLevel.CRITICAL -> Color.Red
        TimePressureLevel.LOW -> Color(0xFFFF9800)
        TimePressureLevel.NONE -> if (isActive) ChessGreen else MaterialTheme.colorScheme.onSurface
    }
    
    Row(
        modifier = modifier
            .background(backgroundColor, RoundedCornerShape(8.dp))
            .padding(12.dp),
        verticalAlignment = Alignment.CenterVertically
    ) {
        Column(modifier = Modifier.weight(1f)) {
            Text(
                text = name,
                fontWeight = FontWeight.Bold,
                fontSize = 16.sp
            )
            if (rating != null) {
                Text(
                    text = "Rating: $rating",
                    fontSize = 12.sp,
                    color = MaterialTheme.colorScheme.onSurfaceVariant
                )
            }
        }
        
        // Timer
        Text(
            text = formatTime(time),
            fontWeight = FontWeight.Bold,
            fontSize = 20.sp,
            color = timerColor
        )
    }
}

@Composable
private fun GameOverCard(
    result: String?,
    isCheckmate: Boolean,
    isStalemate: Boolean,
    playerColor: PlayerSide,
    onNewGame: () -> Unit
) {
    val (title, subtitle) = when {
        isCheckmate -> {
            val isWin = (result == "1-0" && playerColor == PlayerSide.WHITE) ||
                    (result == "0-1" && playerColor == PlayerSide.BLACK)
            if (isWin) "Checkmate!" to "You won!" else "Checkmate" to "You lost"
        }
        isStalemate -> "Stalemate" to "Draw"
        result == "1/2-1/2" -> "Draw" to "Game ended in a draw"
        else -> {
            val isWin = (result == "1-0" && playerColor == PlayerSide.WHITE) ||
                    (result == "0-1" && playerColor == PlayerSide.BLACK)
            if (isWin) "Victory!" to "Opponent resigned" else "Defeat" to "You resigned"
        }
    }
    
    Card(
        modifier = Modifier.fillMaxWidth(),
        colors = CardDefaults.cardColors(
            containerColor = ChessGreen.copy(alpha = 0.2f)
        )
    ) {
        Column(
            modifier = Modifier
                .fillMaxWidth()
                .padding(16.dp),
            horizontalAlignment = Alignment.CenterHorizontally
        ) {
            Text(
                text = title,
                fontSize = 24.sp,
                fontWeight = FontWeight.Bold,
                color = ChessGreen
            )
            Text(
                text = subtitle,
                fontSize = 14.sp,
                color = MaterialTheme.colorScheme.onSurfaceVariant
            )
            Spacer(modifier = Modifier.height(12.dp))
            Button(
                onClick = onNewGame,
                colors = ButtonDefaults.buttonColors(containerColor = ChessGreen)
            ) {
                Text("Back to Menu")
            }
        }
    }
}

@Composable
private fun MoveHistoryCard(
    moves: List<Move>,
    modifier: Modifier = Modifier
) {
    Card(
        modifier = modifier,
        colors = CardDefaults.cardColors(
            containerColor = MaterialTheme.colorScheme.surfaceVariant.copy(alpha = 0.5f)
        )
    ) {
        Column(modifier = Modifier.padding(12.dp)) {
            Text(
                text = "Moves",
                fontWeight = FontWeight.SemiBold,
                fontSize = 14.sp,
                modifier = Modifier.padding(bottom = 8.dp)
            )
            LazyColumn {
                items(moves.chunked(2)) { movePair ->
                    val moveNumber = (moves.indexOf(movePair.first()) / 2) + 1
                    Row(
                        modifier = Modifier.fillMaxWidth(),
                        horizontalArrangement = Arrangement.Start
                    ) {
                        Text(
                            text = "$moveNumber.",
                            modifier = Modifier.width(30.dp),
                            fontSize = 12.sp,
                            color = MaterialTheme.colorScheme.onSurfaceVariant
                        )
                        Text(
                            text = movePair.getOrNull(0)?.notation ?: "",
                            modifier = Modifier.width(60.dp),
                            fontSize = 12.sp
                        )
                        Text(
                            text = movePair.getOrNull(1)?.notation ?: "",
                            modifier = Modifier.width(60.dp),
                            fontSize = 12.sp
                        )
                    }
                }
            }
        }
    }
}

@Composable
private fun PromotionDialog(
    isWhite: Boolean,
    onPieceSelected: (String) -> Unit,
    onDismiss: () -> Unit
) {
    Dialog(onDismissRequest = onDismiss) {
        Card(
            modifier = Modifier.padding(16.dp),
            shape = RoundedCornerShape(16.dp)
        ) {
            Column(
                modifier = Modifier.padding(16.dp),
                horizontalAlignment = Alignment.CenterHorizontally
            ) {
                Text(
                    text = "Promote to",
                    fontWeight = FontWeight.Bold,
                    fontSize = 18.sp,
                    modifier = Modifier.padding(bottom = 16.dp)
                )
                Row(
                    horizontalArrangement = Arrangement.spacedBy(8.dp)
                ) {
                    val pieces = listOf("q" to "♛", "r" to "♜", "b" to "♝", "n" to "♞")
                    pieces.forEach { (code, symbol) ->
                        TextButton(
                            onClick = { onPieceSelected(code) },
                            modifier = Modifier.size(60.dp)
                        ) {
                            Text(
                                text = if (isWhite) symbol.uppercase() else symbol,
                                fontSize = 36.sp,
                                color = if (isWhite) Color.White else Color.Black
                            )
                        }
                    }
                }
            }
        }
    }
}

private fun formatTime(seconds: Double): String {
    val totalSeconds = seconds.toInt()
    val mins = totalSeconds / 60
    val secs = totalSeconds % 60
    val tenths = ((seconds - totalSeconds) * 10).toInt()
    
    return if (totalSeconds < 60) {
        String.format("%d.%d", secs, tenths)
    } else {
        String.format("%d:%02d", mins, secs)
    }
}
