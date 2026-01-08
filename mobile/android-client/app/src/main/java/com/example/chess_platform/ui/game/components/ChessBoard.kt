package com.example.chess_platform.ui.game.components

import androidx.compose.foundation.Canvas
import androidx.compose.foundation.background
import androidx.compose.foundation.border
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Text
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.geometry.Offset
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.example.chess_platform.domain.model.LegalMoveInfo
import com.example.chess_platform.domain.model.PlayerSide
import com.example.chess_platform.ui.theme.ChessGreen

// Board colors
private val LightSquareColor = Color(0xFFF0D9B5)
private val DarkSquareColor = Color(0xFFB58863)
private val SelectedSquareColor = Color(0xFF829769)
private val LastMoveColor = Color(0xFFCDD26A).copy(alpha = 0.7f)
private val LegalMoveIndicator = Color(0xFF000000).copy(alpha = 0.2f)
private val CheckColor = Color(0xFFE53935).copy(alpha = 0.8f)

/**
 * Chess board component
 * 
 * @param fen The FEN string representing the board position
 * @param isFlipped Whether to flip the board (black's perspective)
 * @param selectedSquare Currently selected square (e.g., "e2")
 * @param legalMoves List of legal moves from selected square
 * @param lastMove The last move made (from and to squares)
 * @param isCheck Whether the current side to move is in check
 * @param onSquareClick Callback when a square is clicked
 * @param enabled Whether the board is interactive
 */
@Composable
fun ChessBoard(
    fen: String,
    isFlipped: Boolean = false,
    selectedSquare: String? = null,
    legalMoves: List<LegalMoveInfo> = emptyList(),
    lastMove: Pair<String, String>? = null,
    isCheck: Boolean = false,
    onSquareClick: (String) -> Unit = {},
    enabled: Boolean = true,
    modifier: Modifier = Modifier
) {
    val board = remember(fen) { parseFen(fen) }
    val kingSquare = remember(fen, isCheck) {
        if (isCheck) findKingSquare(board, isWhiteTurn(fen)) else null
    }
    
    Box(
        modifier = modifier
            .aspectRatio(1f)
            .clip(RoundedCornerShape(4.dp))
            .border(2.dp, Color.DarkGray, RoundedCornerShape(4.dp))
    ) {
        Column {
            for (displayRow in 0 until 8) {
                val row = if (isFlipped) displayRow else 7 - displayRow
                Row(modifier = Modifier.weight(1f)) {
                    for (displayCol in 0 until 8) {
                        val col = if (isFlipped) 7 - displayCol else displayCol
                        val squareName = getSquareName(row, col)
                        val piece = board[row][col]
                        val isLightSquare = (row + col) % 2 == 1
                        
                        val isSelected = squareName == selectedSquare
                        val isLastMoveSquare = lastMove?.let { 
                            squareName == it.first || squareName == it.second 
                        } ?: false
                        val isKingInCheck = squareName == kingSquare
                        val legalMove = legalMoves.find { it.toSquare == squareName }
                        
                        ChessSquare(
                            piece = piece,
                            isLightSquare = isLightSquare,
                            isSelected = isSelected,
                            isLastMove = isLastMoveSquare,
                            isCheck = isKingInCheck,
                            legalMove = legalMove,
                            showCoordinates = displayCol == 0 || displayRow == 7,
                            row = row,
                            col = col,
                            isFlipped = isFlipped,
                            onClick = { if (enabled) onSquareClick(squareName) },
                            modifier = Modifier.weight(1f)
                        )
                    }
                }
            }
        }
    }
}

@Composable
private fun ChessSquare(
    piece: Char?,
    isLightSquare: Boolean,
    isSelected: Boolean,
    isLastMove: Boolean,
    isCheck: Boolean,
    legalMove: LegalMoveInfo?,
    showCoordinates: Boolean,
    row: Int,
    col: Int,
    isFlipped: Boolean,
    onClick: () -> Unit,
    modifier: Modifier = Modifier
) {
    val backgroundColor = when {
        isCheck -> CheckColor
        isSelected -> SelectedSquareColor
        isLastMove -> LastMoveColor
        isLightSquare -> LightSquareColor
        else -> DarkSquareColor
    }
    
    Box(
        modifier = modifier
            .fillMaxSize()
            .background(backgroundColor)
            .clickable(onClick = onClick),
        contentAlignment = Alignment.Center
    ) {
        // Rank coordinate (numbers on left)
        if (col == 0) {
            val displayRow = if (isFlipped) row + 1 else 8 - row
            Text(
                text = "$displayRow",
                fontSize = 10.sp,
                fontWeight = FontWeight.Bold,
                color = if (isLightSquare) DarkSquareColor else LightSquareColor,
                modifier = Modifier
                    .align(Alignment.TopStart)
                    .padding(2.dp)
            )
        }
        
        // File coordinate (letters at bottom)
        if (row == 0) {
            val displayCol = if (isFlipped) 'h' - col else 'a' + col
            Text(
                text = "$displayCol",
                fontSize = 10.sp,
                fontWeight = FontWeight.Bold,
                color = if (isLightSquare) DarkSquareColor else LightSquareColor,
                modifier = Modifier
                    .align(Alignment.BottomEnd)
                    .padding(2.dp)
            )
        }
        
        // Legal move indicator
        if (legalMove != null) {
            if (piece != null) {
                // Capture indicator - circle around the piece
                Canvas(modifier = Modifier.fillMaxSize()) {
                    drawCircle(
                        color = LegalMoveIndicator,
                        radius = size.minDimension / 2,
                        style = androidx.compose.ui.graphics.drawscope.Stroke(width = 8f)
                    )
                }
            } else {
                // Move indicator - dot in center
                Box(
                    modifier = Modifier
                        .size(12.dp)
                        .clip(CircleShape)
                        .background(LegalMoveIndicator)
                )
            }
        }
        
        // Chess piece
        piece?.let {
            Text(
                text = getPieceSymbol(it),
                fontSize = 32.sp,
                textAlign = TextAlign.Center,
                color = if (it.isUpperCase()) Color.White else Color.Black
            )
        }
    }
}

// ==================== Helper Functions ====================

/**
 * Parse FEN string to get board position
 */
private fun parseFen(fen: String): Array<Array<Char?>> {
    val board = Array(8) { arrayOfNulls<Char>(8) }
    val position = fen.split(" ").firstOrNull() ?: return board
    
    val ranks = position.split("/")
    for ((rankIndex, rank) in ranks.withIndex()) {
        var fileIndex = 0
        for (char in rank) {
            if (char.isDigit()) {
                fileIndex += char.digitToInt()
            } else {
                if (rankIndex < 8 && fileIndex < 8) {
                    board[7 - rankIndex][fileIndex] = char
                }
                fileIndex++
            }
        }
    }
    return board
}

/**
 * Check if it's white's turn from FEN
 */
private fun isWhiteTurn(fen: String): Boolean {
    val parts = fen.split(" ")
    return parts.getOrNull(1)?.lowercase() == "w"
}

/**
 * Find the king's square for check indication
 */
private fun findKingSquare(board: Array<Array<Char?>>, isWhite: Boolean): String? {
    val kingChar = if (isWhite) 'K' else 'k'
    for (row in 0 until 8) {
        for (col in 0 until 8) {
            if (board[row][col] == kingChar) {
                return getSquareName(row, col)
            }
        }
    }
    return null
}

/**
 * Convert row/col to square name (e.g., 0,0 -> "a1")
 */
private fun getSquareName(row: Int, col: Int): String {
    val file = 'a' + col
    val rank = row + 1
    return "$file$rank"
}

/**
 * Get Unicode chess piece symbol
 */
private fun getPieceSymbol(piece: Char): String {
    return when (piece) {
        'K' -> "♔"
        'Q' -> "♕"
        'R' -> "♖"
        'B' -> "♗"
        'N' -> "♘"
        'P' -> "♙"
        'k' -> "♚"
        'q' -> "♛"
        'r' -> "♜"
        'b' -> "♝"
        'n' -> "♞"
        'p' -> "♟"
        else -> ""
    }
}

/**
 * Parse square name to row/col (e.g., "e2" -> (1, 4))
 */
fun parseSquare(square: String): Pair<Int, Int>? {
    if (square.length != 2) return null
    val col = square[0] - 'a'
    val row = square[1].digitToIntOrNull()?.minus(1) ?: return null
    if (col !in 0..7 || row !in 0..7) return null
    return Pair(row, col)
}
