package com.example.chess_platform.ui.game

import androidx.compose.foundation.Image
import androidx.compose.foundation.background
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.foundation.lazy.rememberLazyListState
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.automirrored.filled.ArrowBack
import androidx.compose.material.icons.filled.*
import androidx.compose.material.icons.outlined.*
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.res.painterResource
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.text.style.TextOverflow
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import androidx.compose.ui.window.Dialog
import androidx.hilt.navigation.compose.hiltViewModel
import com.example.chess_platform.R
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
    
    // Snackbar for errors
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
            GameTopBar(
                isComputerGame = uiState.isComputerGame,
                isWatching = uiState.isWatching,
                onBack = onNavigateBack,
                onFlipBoard = { viewModel.flipBoard() }
            )
        },
        containerColor = MaterialTheme.colorScheme.background
    ) { paddingValues ->
        if (uiState.isLoading) {
            LoadingState(modifier = Modifier.padding(paddingValues))
        } else {
            GameContent(
                uiState = uiState,
                onSquareClick = viewModel::onSquareClick,
                onResign = { viewModel.showResignDialog() },
                onOfferDraw = { viewModel.showDrawOfferDialog() },
                onNavigateBack = onNavigateBack,
                modifier = Modifier.padding(paddingValues)
            )
        }
    }
    
    // ==================== Dialogs ====================
    
    // Resign confirmation
    if (uiState.showResignDialog) {
        ResignDialog(
            onConfirm = { viewModel.resignGame() },
            onDismiss = { viewModel.dismissResignDialog() }
        )
    }
    
    // Draw offer (sending)
    if (uiState.showDrawOfferDialog) {
        DrawOfferDialog(
            onConfirm = { viewModel.offerDraw() },
            onDismiss = { viewModel.dismissDrawOfferDialog() }
        )
    }
    
    // Draw received (opponent offered)
    if (uiState.showDrawReceivedDialog) {
        DrawReceivedDialog(
            opponentName = uiState.opponentName,
            onAccept = { viewModel.acceptDraw() },
            onDecline = { viewModel.declineDraw() }
        )
    }
    
    // Pawn promotion
    if (uiState.showPromotionDialog) {
        PromotionDialog(
            isWhite = uiState.playerColor == PlayerSide.WHITE,
            onPieceSelected = { viewModel.onPromotionSelected(it) },
            onDismiss = { viewModel.dismissPromotionDialog() }
        )
    }
    
    // Game result
    if (uiState.showGameResultDialog && uiState.isGameOver) {
        GameResultDialog(
            title = uiState.gameResultTitle,
            subtitle = uiState.gameResultSubtitle,
            didWin = uiState.didIWin,
            isDraw = uiState.isDraw || uiState.isStalemate,
            onRematch = { viewModel.requestRematch() },
            onAnalyze = { /* TODO: Navigate to analysis */ },
            onClose = onNavigateBack
        )
    }
}

// ==================== Top Bar ====================

@OptIn(ExperimentalMaterial3Api::class)
@Composable
private fun GameTopBar(
    isComputerGame: Boolean,
    isWatching: Boolean,
    onBack: () -> Unit,
    onFlipBoard: () -> Unit
) {
    val title = when {
        isWatching -> "Watching Game"
        isComputerGame -> "vs Computer"
        else -> "Online Game"
    }
    
    TopAppBar(
        title = { 
            Text(title, fontWeight = FontWeight.Bold, fontSize = 18.sp)
        },
        navigationIcon = {
            IconButton(onClick = onBack) {
                Icon(Icons.AutoMirrored.Filled.ArrowBack, contentDescription = "Back")
            }
        },
        actions = {
            IconButton(onClick = onFlipBoard) {
                Icon(Icons.Default.SwapVert, contentDescription = "Flip Board")
            }
        },
        colors = TopAppBarDefaults.topAppBarColors(
            containerColor = MaterialTheme.colorScheme.surface
        )
    )
}

// ==================== Loading State ====================

@Composable
private fun LoadingState(modifier: Modifier = Modifier) {
    Box(
        modifier = modifier.fillMaxSize(),
        contentAlignment = Alignment.Center
    ) {
        Column(horizontalAlignment = Alignment.CenterHorizontally) {
            CircularProgressIndicator(color = ChessGreen)
            Spacer(modifier = Modifier.height(16.dp))
            Text("Loading game...", color = MaterialTheme.colorScheme.onSurfaceVariant)
        }
    }
}

// ==================== Main Game Content ====================

@Composable
private fun GameContent(
    uiState: GameUiState,
    onSquareClick: (String) -> Unit,
    onResign: () -> Unit,
    onOfferDraw: () -> Unit,
    onNavigateBack: () -> Unit,
    modifier: Modifier = Modifier
) {
    Column(
        modifier = modifier
            .fillMaxSize()
            .padding(horizontal = 12.dp, vertical = 8.dp)
    ) {
        // Opponent player card (top)
        PlayerCard(
            name = uiState.opponentName,
            rating = uiState.opponentRating,
            time = uiState.opponentTime,
            isActive = uiState.currentTurn != uiState.playerColor && !uiState.isGameOver,
            timePressure = if (uiState.playerColor == PlayerSide.WHITE) 
                uiState.blackTimePressure else uiState.whiteTimePressure,
            isComputer = uiState.isComputerGame,
            isThinking = uiState.isWaitingForComputer,
            isTop = true
        )
        
        Spacer(modifier = Modifier.height(8.dp))
        
        // Chess Board
        Box(
            modifier = Modifier
                .weight(1f)
                .fillMaxWidth(),
            contentAlignment = Alignment.Center
        ) {
            ChessBoard(
                fen = uiState.fen,
                isFlipped = uiState.isFlipped,
                selectedSquare = uiState.selectedSquare,
                legalMoves = uiState.legalMoves,
                lastMove = uiState.lastMove,
                isCheck = uiState.isCheck,
                onSquareClick = onSquareClick,
                enabled = uiState.canInteract,
                modifier = Modifier.fillMaxWidth()
            )
        }
        
        Spacer(modifier = Modifier.height(8.dp))
        
        // Player card (bottom - you)
        PlayerCard(
            name = uiState.playerName,
            rating = uiState.myRating,
            time = uiState.myTime,
            isActive = uiState.isMyTurn && !uiState.isGameOver,
            timePressure = if (uiState.playerColor == PlayerSide.WHITE) 
                uiState.whiteTimePressure else uiState.blackTimePressure,
            isComputer = false,
            isThinking = false,
            isTop = false
        )
        
        Spacer(modifier = Modifier.height(12.dp))
        
        // Game status or controls
        if (uiState.isGameOver) {
            // Game Over card
            GameOverCard(
                title = uiState.gameResultTitle,
                subtitle = uiState.gameResultSubtitle,
                didWin = uiState.didIWin,
                onBackToMenu = onNavigateBack
            )
        } else if (uiState.showGameControls) {
            // Action buttons - ONLY for players, not spectators
            GameControls(
                onResign = onResign,
                onOfferDraw = onOfferDraw,
                drawPending = uiState.drawOfferPending,
                isComputerGame = uiState.isComputerGame
            )
        }
        
        // Move history (compact)
        if (uiState.moves.isNotEmpty()) {
            Spacer(modifier = Modifier.height(8.dp))
            MoveHistory(
                moves = uiState.moves,
                modifier = Modifier
                    .fillMaxWidth()
                    .heightIn(max = 80.dp)
            )
        }
    }
}

// ==================== Player Card ====================

@Composable
private fun PlayerCard(
    name: String,
    rating: Int?,
    time: Double,
    isActive: Boolean,
    timePressure: TimePressureLevel,
    isComputer: Boolean,
    isThinking: Boolean = false,
    isTop: Boolean
) {
    val backgroundColor = if (isActive) {
        ChessGreen.copy(alpha = 0.12f)
    } else {
        MaterialTheme.colorScheme.surfaceVariant.copy(alpha = 0.4f)
    }
    
    Surface(
        modifier = Modifier.fillMaxWidth(),
        shape = RoundedCornerShape(12.dp),
        color = backgroundColor,
        border = if (isActive) ButtonDefaults.outlinedButtonBorder(enabled = true) else null
    ) {
        Row(
            modifier = Modifier.padding(horizontal = 12.dp, vertical = 10.dp),
            verticalAlignment = Alignment.CenterVertically
        ) {
            // Avatar/Icon
            Box(
                modifier = Modifier
                    .size(40.dp)
                    .clip(CircleShape)
                    .background(
                        if (isComputer) Color(0xFF6B7FD7) 
                        else MaterialTheme.colorScheme.primary.copy(alpha = 0.2f)
                    ),
                contentAlignment = Alignment.Center
            ) {
                if (isComputer) {
                    Icon(
                        Icons.Default.SmartToy,
                        contentDescription = null,
                        tint = Color.White,
                        modifier = Modifier.size(24.dp)
                    )
                } else {
                    Text(
                        text = name.firstOrNull()?.uppercase() ?: "?",
                        fontWeight = FontWeight.Bold,
                        color = MaterialTheme.colorScheme.primary
                    )
                }
            }
            
            Spacer(modifier = Modifier.width(12.dp))
            
            // Name and rating (with thinking indicator)
            Column(modifier = Modifier.weight(1f)) {
                Row(verticalAlignment = Alignment.CenterVertically) {
                    Text(
                        text = name,
                        fontWeight = FontWeight.SemiBold,
                        fontSize = 15.sp,
                        maxLines = 1,
                        overflow = TextOverflow.Ellipsis,
                        modifier = Modifier.weight(1f, fill = false)
                    )
                    // Subtle thinking indicator - just 3 animated dots
                    if (isThinking) {
                        Spacer(modifier = Modifier.width(6.dp))
                        Text(
                            text = "...",
                            fontSize = 14.sp,
                            fontWeight = FontWeight.Bold,
                            color = ChessGreen
                        )
                    }
                }
                if (rating != null) {
                    Text(
                        text = "Rating: $rating",
                        fontSize = 12.sp,
                        color = MaterialTheme.colorScheme.onSurfaceVariant
                    )
                }
            }
            
            // Timer
            TimerDisplay(
                time = time,
                isActive = isActive,
                timePressure = timePressure
            )
        }
    }
}

// ==================== Timer Display ====================

@Composable
private fun TimerDisplay(
    time: Double,
    isActive: Boolean,
    timePressure: TimePressureLevel
) {
    val timerColor = when (timePressure) {
        TimePressureLevel.CRITICAL -> Color(0xFFE53935)
        TimePressureLevel.LOW -> Color(0xFFFF9800)
        TimePressureLevel.NONE -> if (isActive) ChessGreen else MaterialTheme.colorScheme.onSurface
    }
    
    val bgColor = when (timePressure) {
        TimePressureLevel.CRITICAL -> Color(0xFFE53935).copy(alpha = 0.15f)
        TimePressureLevel.LOW -> Color(0xFFFF9800).copy(alpha = 0.15f)
        TimePressureLevel.NONE -> if (isActive) ChessGreen.copy(alpha = 0.15f) else Color.Transparent
    }
    
    Surface(
        shape = RoundedCornerShape(8.dp),
        color = bgColor
    ) {
        Text(
            text = formatTime(time),
            fontWeight = FontWeight.Bold,
            fontSize = 18.sp,
            color = timerColor,
            modifier = Modifier.padding(horizontal = 12.dp, vertical = 6.dp)
        )
    }
}

// ==================== Game Controls (Players Only) ====================

@Composable
private fun GameControls(
    onResign: () -> Unit,
    onOfferDraw: () -> Unit,
    drawPending: Boolean,
    isComputerGame: Boolean
) {
    Row(
        modifier = Modifier.fillMaxWidth(),
        horizontalArrangement = Arrangement.spacedBy(8.dp)
    ) {
        // Draw button - not available against computer
        if (!isComputerGame) {
            OutlinedButton(
                onClick = onOfferDraw,
                enabled = !drawPending,
                modifier = Modifier.weight(1f),
                colors = ButtonDefaults.outlinedButtonColors(
                    contentColor = MaterialTheme.colorScheme.primary
                )
            ) {
                Icon(Icons.Outlined.Handshake, contentDescription = null, modifier = Modifier.size(18.dp))
                Spacer(modifier = Modifier.width(6.dp))
                Text(if (drawPending) "Draw Offered" else "Draw")
            }
        }
        
        // Resign button
        OutlinedButton(
            onClick = onResign,
            modifier = Modifier.weight(1f),
            colors = ButtonDefaults.outlinedButtonColors(
                contentColor = MaterialTheme.colorScheme.error
            )
        ) {
            Icon(Icons.Default.Flag, contentDescription = null, modifier = Modifier.size(18.dp))
            Spacer(modifier = Modifier.width(6.dp))
            Text("Resign")
        }
    }
}

// ==================== Game Over Card ====================

@Composable
private fun GameOverCard(
    title: String,
    subtitle: String,
    didWin: Boolean,
    onBackToMenu: () -> Unit
) {
    val bgColor = when {
        didWin -> ChessGreen.copy(alpha = 0.15f)
        subtitle.contains("draw", ignoreCase = true) -> Color(0xFFFF9800).copy(alpha = 0.15f)
        else -> Color(0xFFE53935).copy(alpha = 0.15f)
    }
    
    val accentColor = when {
        didWin -> ChessGreen
        subtitle.contains("draw", ignoreCase = true) -> Color(0xFFFF9800)
        else -> Color(0xFFE53935)
    }
    
    Surface(
        modifier = Modifier.fillMaxWidth(),
        shape = RoundedCornerShape(16.dp),
        color = bgColor
    ) {
        Column(
            modifier = Modifier.padding(16.dp),
            horizontalAlignment = Alignment.CenterHorizontally
        ) {
            Text(
                text = title,
                fontSize = 22.sp,
                fontWeight = FontWeight.Bold,
                color = accentColor
            )
            Text(
                text = subtitle,
                fontSize = 14.sp,
                color = MaterialTheme.colorScheme.onSurfaceVariant
            )
            Spacer(modifier = Modifier.height(12.dp))
            Button(
                onClick = onBackToMenu,
                colors = ButtonDefaults.buttonColors(containerColor = accentColor)
            ) {
                Text("Back to Menu")
            }
        }
    }
}

// ==================== Move History ====================

@Composable
private fun MoveHistory(
    moves: List<Move>,
    modifier: Modifier = Modifier
) {
    val listState = rememberLazyListState()
    
    // Auto-scroll to latest move
    LaunchedEffect(moves.size) {
        if (moves.isNotEmpty()) {
            listState.animateScrollToItem(moves.size - 1)
        }
    }
    
    Surface(
        modifier = modifier,
        shape = RoundedCornerShape(8.dp),
        color = MaterialTheme.colorScheme.surfaceVariant.copy(alpha = 0.4f)
    ) {
        Column(modifier = Modifier.padding(8.dp)) {
            Text(
                text = "Moves",
                fontWeight = FontWeight.SemiBold,
                fontSize = 12.sp,
                color = MaterialTheme.colorScheme.onSurfaceVariant
            )
            Spacer(modifier = Modifier.height(4.dp))
            LazyColumn(state = listState) {
                items(moves.chunked(2)) { movePair ->
                    val moveNumber = (moves.indexOf(movePair.first()) / 2) + 1
                    Row(modifier = Modifier.fillMaxWidth()) {
                        Text(
                            text = "$moveNumber.",
                            modifier = Modifier.width(28.dp),
                            fontSize = 11.sp,
                            color = MaterialTheme.colorScheme.onSurfaceVariant
                        )
                        Text(
                            text = movePair.getOrNull(0)?.notation ?: "",
                            modifier = Modifier.width(56.dp),
                            fontSize = 11.sp
                        )
                        Text(
                            text = movePair.getOrNull(1)?.notation ?: "",
                            modifier = Modifier.width(56.dp),
                            fontSize = 11.sp
                        )
                    }
                }
            }
        }
    }
}

// ==================== Dialogs ====================

@Composable
private fun ResignDialog(
    onConfirm: () -> Unit,
    onDismiss: () -> Unit
) {
    AlertDialog(
        onDismissRequest = onDismiss,
        icon = { Icon(Icons.Default.Flag, contentDescription = null, tint = MaterialTheme.colorScheme.error) },
        title = { Text("Resign Game?") },
        text = { Text("Are you sure you want to resign? This will count as a loss.") },
        confirmButton = {
            TextButton(
                onClick = onConfirm,
                colors = ButtonDefaults.textButtonColors(contentColor = MaterialTheme.colorScheme.error)
            ) { Text("Resign") }
        },
        dismissButton = {
            TextButton(onClick = onDismiss) { Text("Cancel") }
        }
    )
}

@Composable
private fun DrawOfferDialog(
    onConfirm: () -> Unit,
    onDismiss: () -> Unit
) {
    AlertDialog(
        onDismissRequest = onDismiss,
        icon = { Icon(Icons.Outlined.Handshake, contentDescription = null, tint = ChessGreen) },
        title = { Text("Offer Draw?") },
        text = { Text("Your opponent can accept or decline this offer.") },
        confirmButton = {
            TextButton(
                onClick = onConfirm,
                colors = ButtonDefaults.textButtonColors(contentColor = ChessGreen)
            ) { Text("Offer Draw") }
        },
        dismissButton = {
            TextButton(onClick = onDismiss) { Text("Cancel") }
        }
    )
}

@Composable
private fun DrawReceivedDialog(
    opponentName: String,
    onAccept: () -> Unit,
    onDecline: () -> Unit
) {
    AlertDialog(
        onDismissRequest = onDecline,
        icon = { Icon(Icons.Outlined.Handshake, contentDescription = null, tint = Color(0xFFFF9800)) },
        title = { Text("Draw Offered") },
        text = { Text("$opponentName is offering a draw. Do you accept?") },
        confirmButton = {
            TextButton(
                onClick = onAccept,
                colors = ButtonDefaults.textButtonColors(contentColor = ChessGreen)
            ) { Text("Accept") }
        },
        dismissButton = {
            TextButton(
                onClick = onDecline,
                colors = ButtonDefaults.textButtonColors(contentColor = MaterialTheme.colorScheme.error)
            ) { Text("Decline") }
        }
    )
}

@Composable
private fun PromotionDialog(
    isWhite: Boolean,
    onPieceSelected: (String) -> Unit,
    onDismiss: () -> Unit
) {
    Dialog(onDismissRequest = onDismiss) {
        Surface(
            shape = RoundedCornerShape(16.dp),
            color = MaterialTheme.colorScheme.surface
        ) {
            Column(
                modifier = Modifier.padding(20.dp),
                horizontalAlignment = Alignment.CenterHorizontally
            ) {
                Text(
                    text = "Promote Pawn",
                    fontWeight = FontWeight.Bold,
                    fontSize = 18.sp
                )
                Spacer(modifier = Modifier.height(16.dp))
                Row(
                    horizontalArrangement = Arrangement.spacedBy(8.dp)
                ) {
                    val pieces = if (isWhite) {
                        listOf("q" to R.drawable.piece_wq, "r" to R.drawable.piece_wr, 
                               "b" to R.drawable.piece_wb, "n" to R.drawable.piece_wn)
                    } else {
                        listOf("q" to R.drawable.piece_bq, "r" to R.drawable.piece_br,
                               "b" to R.drawable.piece_bb, "n" to R.drawable.piece_bn)
                    }
                    
                    pieces.forEach { (code, resId) ->
                        IconButton(
                            onClick = { onPieceSelected(code) },
                            modifier = Modifier
                                .size(56.dp)
                                .background(
                                    MaterialTheme.colorScheme.surfaceVariant,
                                    RoundedCornerShape(8.dp)
                                )
                        ) {
                            Image(
                                painter = painterResource(id = resId),
                                contentDescription = code,
                                modifier = Modifier.size(44.dp)
                            )
                        }
                    }
                }
            }
        }
    }
}

@Composable
private fun GameResultDialog(
    title: String,
    subtitle: String,
    didWin: Boolean,
    isDraw: Boolean,
    onRematch: () -> Unit,
    onAnalyze: () -> Unit,
    onClose: () -> Unit
) {
    val accentColor = when {
        didWin -> ChessGreen
        isDraw -> Color(0xFFFF9800)
        else -> Color(0xFFE53935)
    }
    
    Dialog(onDismissRequest = onClose) {
        Surface(
            shape = RoundedCornerShape(24.dp),
            color = MaterialTheme.colorScheme.surface
        ) {
            Column(
                modifier = Modifier.padding(24.dp),
                horizontalAlignment = Alignment.CenterHorizontally
            ) {
                // Icon
                val icon = when {
                    didWin -> Icons.Default.EmojiEvents
                    isDraw -> Icons.Outlined.Handshake
                    else -> Icons.Default.SentimentDissatisfied
                }
                Icon(
                    icon,
                    contentDescription = null,
                    tint = accentColor,
                    modifier = Modifier.size(56.dp)
                )
                
                Spacer(modifier = Modifier.height(16.dp))
                
                Text(
                    text = title,
                    fontSize = 24.sp,
                    fontWeight = FontWeight.Bold,
                    color = accentColor
                )
                Text(
                    text = subtitle,
                    fontSize = 14.sp,
                    color = MaterialTheme.colorScheme.onSurfaceVariant
                )
                
                Spacer(modifier = Modifier.height(24.dp))
                
                // Buttons
                Row(
                    modifier = Modifier.fillMaxWidth(),
                    horizontalArrangement = Arrangement.spacedBy(8.dp)
                ) {
                    OutlinedButton(
                        onClick = onClose,
                        modifier = Modifier.weight(1f)
                    ) {
                        Text("Close")
                    }
                    Button(
                        onClick = onRematch,
                        modifier = Modifier.weight(1f),
                        colors = ButtonDefaults.buttonColors(containerColor = accentColor)
                    ) {
                        Text("Rematch")
                    }
                }
            }
        }
    }
}

// ==================== Utility Functions ====================

private fun formatTime(seconds: Double): String {
    val totalSeconds = seconds.toInt().coerceAtLeast(0)
    val mins = totalSeconds / 60
    val secs = totalSeconds % 60
    val tenths = ((seconds - totalSeconds.toDouble()) * 10).toInt().coerceAtLeast(0)
    
    return if (totalSeconds < 60) {
        String.format("%d.%d", secs, tenths)
    } else {
        String.format("%d:%02d", mins, secs)
    }
}
