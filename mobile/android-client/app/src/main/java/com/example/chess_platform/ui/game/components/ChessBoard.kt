package com.example.chess_platform.ui.game.components

import androidx.compose.foundation.Canvas
import androidx.compose.foundation.Image
import androidx.compose.foundation.background
import androidx.compose.foundation.border
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material3.Text
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.layout.ContentScale
import androidx.compose.ui.res.painterResource
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.example.chess_platform.R
import com.example.chess_platform.domain.model.LegalMoveInfo

// ==================== Board Theme ====================

/**
 * Board color theme - can be changed via settings
 */
data class BoardTheme(
    val lightSquare: Color,
    val darkSquare: Color,
    val selectedSquare: Color,
    val lastMoveLight: Color,
    val lastMoveDark: Color,
    val legalMoveIndicator: Color,
    val checkColor: Color,
    val borderColor: Color
)

// Default classic wood theme
val ClassicBoardTheme = BoardTheme(
    lightSquare = Color(0xFFF0D9B5),
    darkSquare = Color(0xFFB58863),
    selectedSquare = Color(0xFF829769),
    lastMoveLight = Color(0xFFCDD26A),
    lastMoveDark = Color(0xFFAAA23A),
    legalMoveIndicator = Color(0xFF000000).copy(alpha = 0.18f),
    checkColor = Color(0xFFE53935).copy(alpha = 0.7f),
    borderColor = Color(0xFF5D4037)
)

// ==================== Chess Board Composable ====================

/**
 * A clean and practical chess board component using piece images
 * 
 * @param fen FEN string representing the board position
 * @param isFlipped Whether the board is flipped (black's perspective)
 * @param selectedSquare Currently selected square (e.g., "e2")
 * @param legalMoves List of legal moves from selected square
 * @param lastMove The last move made (from and to squares)
 * @param isCheck Whether the current side to move is in check
 * @param onSquareClick Callback when a square is clicked
 * @param enabled Whether the board is interactive
 * @param theme Board color theme
 */
@Composable
fun ChessBoard(
    fen: String,
    modifier: Modifier = Modifier,
    isFlipped: Boolean = false,
    selectedSquare: String? = null,
    legalMoves: List<LegalMoveInfo> = emptyList(),
    lastMove: Pair<String, String>? = null,
    isCheck: Boolean = false,
    onSquareClick: (String) -> Unit = {},
    enabled: Boolean = true,
    theme: BoardTheme = ClassicBoardTheme
) {
    val board = remember(fen) { parseFen(fen) }
    val kingSquare = remember(fen, isCheck) {
        if (isCheck) findKingSquare(board, isWhiteTurn(fen)) else null
    }
    
    Box(
        modifier = modifier
            .aspectRatio(1f)
            .clip(RoundedCornerShape(4.dp))
            .border(3.dp, theme.borderColor, RoundedCornerShape(4.dp))
            .background(theme.borderColor)
    ) {
        Column(modifier = Modifier.padding(2.dp)) {
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
                            row = row,
                            col = col,
                            displayRow = displayRow,
                            displayCol = displayCol,
                            isFlipped = isFlipped,
                            onClick = { if (enabled) onSquareClick(squareName) },
                            theme = theme,
                            modifier = Modifier.weight(1f)
                        )
                    }
                }
            }
        }
    }
}

// ==================== Chess Square ====================

@Composable
private fun ChessSquare(
    piece: Char?,
    isLightSquare: Boolean,
    isSelected: Boolean,
    isLastMove: Boolean,
    isCheck: Boolean,
    legalMove: LegalMoveInfo?,
    row: Int,
    col: Int,
    displayRow: Int,
    displayCol: Int,
    isFlipped: Boolean,
    onClick: () -> Unit,
    theme: BoardTheme,
    modifier: Modifier = Modifier
) {
    // Determine background color based on state
    val backgroundColor = when {
        isCheck -> theme.checkColor
        isSelected -> theme.selectedSquare
        isLastMove -> if (isLightSquare) theme.lastMoveLight else theme.lastMoveDark
        isLightSquare -> theme.lightSquare
        else -> theme.darkSquare
    }
    
    Box(
        modifier = modifier
            .fillMaxSize()
            .background(backgroundColor)
            .clickable(onClick = onClick),
        contentAlignment = Alignment.Center
    ) {
        // Rank coordinate (1-8 on left edge)
        if (displayCol == 0) {
            val rankNumber = if (isFlipped) displayRow + 1 else 8 - displayRow
            Text(
                text = "$rankNumber",
                fontSize = 9.sp,
                fontWeight = FontWeight.Bold,
                color = if (isLightSquare) theme.darkSquare else theme.lightSquare,
                modifier = Modifier
                    .align(Alignment.TopStart)
                    .padding(1.dp)
            )
        }
        
        // File coordinate (a-h at bottom edge)
        if (displayRow == 7) {
            val fileChar = if (isFlipped) 'h' - displayCol else 'a' + displayCol
            Text(
                text = "$fileChar",
                fontSize = 9.sp,
                fontWeight = FontWeight.Bold,
                color = if (isLightSquare) theme.darkSquare else theme.lightSquare,
                modifier = Modifier
                    .align(Alignment.BottomEnd)
                    .padding(1.dp)
            )
        }
        
        // Legal move indicator
        if (legalMove != null) {
            if (piece != null) {
                // Capture indicator - ring around the piece
                Canvas(modifier = Modifier.fillMaxSize(0.9f)) {
                    drawCircle(
                        color = theme.legalMoveIndicator,
                        radius = size.minDimension / 2,
                        style = androidx.compose.ui.graphics.drawscope.Stroke(width = 6f)
                    )
                }
            } else {
                // Move indicator - small dot in center
                Box(
                    modifier = Modifier
                        .size(14.dp)
                        .clip(CircleShape)
                        .background(theme.legalMoveIndicator)
                )
            }
        }
        
        // Chess piece image
        piece?.let {
            val pieceResId = getPieceDrawable(it)
            if (pieceResId != 0) {
                Image(
                    painter = painterResource(id = pieceResId),
                    contentDescription = getPieceDescription(it),
                    modifier = Modifier
                        .fillMaxSize(0.85f)
                        .padding(2.dp),
                    contentScale = ContentScale.Fit
                )
            }
        }
    }
}

// ==================== Piece Image Mapping ====================

/**
 * Get drawable resource ID for a chess piece
 * Uses the piece images copied from frontend/assets
 */
private fun getPieceDrawable(piece: Char): Int {
    return when (piece) {
        'K' -> R.drawable.piece_wk  // White King
        'Q' -> R.drawable.piece_wq  // White Queen
        'R' -> R.drawable.piece_wr  // White Rook
        'B' -> R.drawable.piece_wb  // White Bishop
        'N' -> R.drawable.piece_wn  // White Knight
        'P' -> R.drawable.piece_wp  // White Pawn
        'k' -> R.drawable.piece_bk  // Black King
        'q' -> R.drawable.piece_bq  // Black Queen
        'r' -> R.drawable.piece_br  // Black Rook
        'b' -> R.drawable.piece_bb  // Black Bishop
        'n' -> R.drawable.piece_bn  // Black Knight
        'p' -> R.drawable.piece_bp  // Black Pawn
        else -> 0
    }
}

/**
 * Get accessibility description for a piece
 */
private fun getPieceDescription(piece: Char): String {
    val color = if (piece.isUpperCase()) "White" else "Black"
    val pieceName = when (piece.lowercaseChar()) {
        'k' -> "King"
        'q' -> "Queen"
        'r' -> "Rook"
        'b' -> "Bishop"
        'n' -> "Knight"
        'p' -> "Pawn"
        else -> "Piece"
    }
    return "$color $pieceName"
}

// ==================== FEN Parsing Utilities ====================

/**
 * Parse FEN string to get board position as 2D array
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
 * Check if it's white's turn from FEN string
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
 * Convert row/col indices to algebraic notation (e.g., 0,0 -> "a1")
 */
private fun getSquareName(row: Int, col: Int): String {
    val file = 'a' + col
    val rank = row + 1
    return "$file$rank"
}

/**
 * Parse algebraic square to row/col indices (e.g., "e2" -> (1, 4))
 */
fun parseSquare(square: String): Pair<Int, Int>? {
    if (square.length != 2) return null
    val col = square[0] - 'a'
    val row = square[1].digitToIntOrNull()?.minus(1) ?: return null
    if (col !in 0..7 || row !in 0..7) return null
    return Pair(row, col)
}
