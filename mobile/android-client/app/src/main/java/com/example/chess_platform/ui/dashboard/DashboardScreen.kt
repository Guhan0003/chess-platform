package com.example.chess_platform.ui.dashboard

import androidx.compose.foundation.background
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.LazyRow
import androidx.compose.foundation.lazy.items
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.*
import androidx.compose.material.icons.outlined.*
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.Brush
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.vector.ImageVector
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.hilt.navigation.compose.hiltViewModel
import com.example.chess_platform.ui.components.ChessBackground
import com.example.chess_platform.ui.components.ChessCard
import com.example.chess_platform.ui.components.GradientButton
import com.example.chess_platform.ui.theme.*

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun DashboardScreen(
    viewModel: DashboardViewModel = hiltViewModel(),
    onNavigateToProfile: () -> Unit,
    onNavigateToSettings: () -> Unit,
    onNavigateToPlayMenu: () -> Unit,
    onNavigateToPlayBot: () -> Unit,
    onNavigateToOverTheBoard: () -> Unit,
    onNavigateToPuzzles: () -> Unit,
    onNavigateToLeaderboard: () -> Unit,
    onLogout: () -> Unit
) {
    val uiState by viewModel.uiState.collectAsState()
    
    ChessBackground {
        Scaffold(
            containerColor = Color.Transparent,
            topBar = {
                DashboardTopBar(
                    username = uiState.username,
                    onProfileClick = onNavigateToProfile,
                    onSettingsClick = onNavigateToSettings,
                    onLogoutClick = {
                        viewModel.logout()
                        onLogout()
                    }
                )
            }
        ) { paddingValues ->
            LazyColumn(
                modifier = Modifier
                    .fillMaxSize()
                    .padding(paddingValues)
                    .padding(horizontal = 16.dp),
                verticalArrangement = Arrangement.spacedBy(16.dp)
            ) {
                item { Spacer(modifier = Modifier.height(8.dp)) }
                
                // Quick Play Section
                item {
                    QuickPlaySection(
                        onPlayOnline = onNavigateToPlayMenu,
                        onPlayBot = onNavigateToPlayBot,
                        onOverTheBoard = onNavigateToOverTheBoard
                    )
                }
                
                // Rating Cards
                item {
                    RatingSection(
                        blitzRating = uiState.blitzRating,
                        rapidRating = uiState.rapidRating,
                        classicalRating = uiState.classicalRating
                    )
                }
                
                // Quick Actions
                item {
                    QuickActionsSection(
                        onPuzzlesClick = onNavigateToPuzzles,
                        onLeaderboardClick = onNavigateToLeaderboard
                    )
                }
                
                // Stats Summary
                item {
                    StatsSummaryCard(
                        gamesPlayed = uiState.gamesPlayed,
                        wins = uiState.gamesWon,
                        losses = uiState.gamesLost,
                        draws = uiState.gamesDrawn
                    )
                }
                
                item { Spacer(modifier = Modifier.height(16.dp)) }
            }
        }
    }
}

@OptIn(ExperimentalMaterial3Api::class)
@Composable
private fun DashboardTopBar(
    username: String,
    onProfileClick: () -> Unit,
    onSettingsClick: () -> Unit,
    onLogoutClick: () -> Unit
) {
    var showMenu by remember { mutableStateOf(false) }
    
    TopAppBar(
        title = {
            Row(verticalAlignment = Alignment.CenterVertically) {
                Text(
                    text = "♔",
                    style = MaterialTheme.typography.headlineSmall
                )
                Spacer(modifier = Modifier.width(8.dp))
                Column {
                    Text(
                        text = "Chess Platform",
                        style = MaterialTheme.typography.titleMedium.copy(
                            fontWeight = FontWeight.Bold
                        ),
                        color = TextPrimary
                    )
                    Text(
                        text = "Welcome, $username",
                        style = MaterialTheme.typography.bodySmall,
                        color = TextMuted
                    )
                }
            }
        },
        actions = {
            IconButton(onClick = { showMenu = true }) {
                Icon(
                    imageVector = Icons.Default.MoreVert,
                    contentDescription = "Menu",
                    tint = TextPrimary
                )
            }
            
            DropdownMenu(
                expanded = showMenu,
                onDismissRequest = { showMenu = false },
                containerColor = BgCard
            ) {
                DropdownMenuItem(
                    text = { Text("Profile", color = TextPrimary) },
                    onClick = {
                        showMenu = false
                        onProfileClick()
                    },
                    leadingIcon = {
                        Icon(Icons.Default.Person, null, tint = TextMuted)
                    }
                )
                DropdownMenuItem(
                    text = { Text("Settings", color = TextPrimary) },
                    onClick = {
                        showMenu = false
                        onSettingsClick()
                    },
                    leadingIcon = {
                        Icon(Icons.Default.Settings, null, tint = TextMuted)
                    }
                )
                HorizontalDivider(color = BorderDefault)
                DropdownMenuItem(
                    text = { Text("Logout", color = Error) },
                    onClick = {
                        showMenu = false
                        onLogoutClick()
                    },
                    leadingIcon = {
                        Icon(Icons.Default.Logout, null, tint = Error)
                    }
                )
            }
        },
        colors = TopAppBarDefaults.topAppBarColors(
            containerColor = Color.Transparent
        )
    )
}

@Composable
private fun QuickPlaySection(
    onPlayOnline: () -> Unit,
    onPlayBot: () -> Unit,
    onOverTheBoard: () -> Unit
) {
    ChessCard {
        Column(
            modifier = Modifier
                .fillMaxWidth()
                .padding(16.dp)
        ) {
            Text(
                text = "Play Chess",
                style = MaterialTheme.typography.titleLarge.copy(
                    fontWeight = FontWeight.Bold
                ),
                color = TextPrimary
            )
            
            Spacer(modifier = Modifier.height(16.dp))
            
            // Main Play Button
            GradientButton(
                text = "▶  Play Online",
                onClick = onPlayOnline,
                modifier = Modifier.fillMaxWidth()
            )
            
            Spacer(modifier = Modifier.height(12.dp))
            
            // Secondary Options
            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.spacedBy(12.dp)
            ) {
                PlayOptionCard(
                    icon = Icons.Default.SmartToy,
                    title = "Play Bot",
                    subtitle = "Practice offline",
                    onClick = onPlayBot,
                    modifier = Modifier.weight(1f)
                )
                
                PlayOptionCard(
                    icon = Icons.Default.People,
                    title = "Over Board",
                    subtitle = "Local 2P",
                    onClick = onOverTheBoard,
                    modifier = Modifier.weight(1f)
                )
            }
        }
    }
}

@Composable
private fun PlayOptionCard(
    icon: ImageVector,
    title: String,
    subtitle: String,
    onClick: () -> Unit,
    modifier: Modifier = Modifier
) {
    Card(
        modifier = modifier.clickable(onClick = onClick),
        colors = CardDefaults.cardColors(
            containerColor = BgTertiary
        ),
        shape = RoundedCornerShape(12.dp)
    ) {
        Column(
            modifier = Modifier
                .fillMaxWidth()
                .padding(16.dp),
            horizontalAlignment = Alignment.CenterHorizontally
        ) {
            Icon(
                imageVector = icon,
                contentDescription = null,
                tint = AccentPrimary,
                modifier = Modifier.size(32.dp)
            )
            Spacer(modifier = Modifier.height(8.dp))
            Text(
                text = title,
                style = MaterialTheme.typography.bodyMedium.copy(
                    fontWeight = FontWeight.Medium
                ),
                color = TextPrimary
            )
            Text(
                text = subtitle,
                style = MaterialTheme.typography.labelSmall,
                color = TextMuted
            )
        }
    }
}

@Composable
private fun RatingSection(
    blitzRating: Int,
    rapidRating: Int,
    classicalRating: Int
) {
    Row(
        modifier = Modifier.fillMaxWidth(),
        horizontalArrangement = Arrangement.spacedBy(12.dp)
    ) {
        RatingCard(
            title = "Blitz",
            rating = blitzRating,
            icon = "⚡",
            modifier = Modifier.weight(1f)
        )
        RatingCard(
            title = "Rapid",
            rating = rapidRating,
            icon = "🕐",
            modifier = Modifier.weight(1f)
        )
        RatingCard(
            title = "Classical",
            rating = classicalRating,
            icon = "♟️",
            modifier = Modifier.weight(1f)
        )
    }
}

@Composable
private fun RatingCard(
    title: String,
    rating: Int,
    icon: String,
    modifier: Modifier = Modifier
) {
    Card(
        modifier = modifier,
        colors = CardDefaults.cardColors(
            containerColor = BgCard
        ),
        shape = RoundedCornerShape(12.dp)
    ) {
        Column(
            modifier = Modifier
                .fillMaxWidth()
                .padding(12.dp),
            horizontalAlignment = Alignment.CenterHorizontally
        ) {
            Text(
                text = icon,
                style = MaterialTheme.typography.titleLarge
            )
            Spacer(modifier = Modifier.height(4.dp))
            Text(
                text = rating.toString(),
                style = MaterialTheme.typography.titleLarge.copy(
                    fontWeight = FontWeight.Bold
                ),
                color = AccentLight
            )
            Text(
                text = title,
                style = MaterialTheme.typography.labelSmall,
                color = TextMuted
            )
        }
    }
}

@Composable
private fun QuickActionsSection(
    onPuzzlesClick: () -> Unit,
    onLeaderboardClick: () -> Unit
) {
    Row(
        modifier = Modifier.fillMaxWidth(),
        horizontalArrangement = Arrangement.spacedBy(12.dp)
    ) {
        QuickActionCard(
            icon = Icons.Default.Extension,
            title = "Puzzles",
            color = Warning,
            onClick = onPuzzlesClick,
            modifier = Modifier.weight(1f)
        )
        QuickActionCard(
            icon = Icons.Default.Leaderboard,
            title = "Leaderboard",
            color = Info,
            onClick = onLeaderboardClick,
            modifier = Modifier.weight(1f)
        )
    }
}

@Composable
private fun QuickActionCard(
    icon: ImageVector,
    title: String,
    color: Color,
    onClick: () -> Unit,
    modifier: Modifier = Modifier
) {
    Card(
        modifier = modifier.clickable(onClick = onClick),
        colors = CardDefaults.cardColors(
            containerColor = color.copy(alpha = 0.1f)
        ),
        shape = RoundedCornerShape(12.dp)
    ) {
        Row(
            modifier = Modifier
                .fillMaxWidth()
                .padding(16.dp),
            verticalAlignment = Alignment.CenterVertically,
            horizontalArrangement = Arrangement.Center
        ) {
            Icon(
                imageVector = icon,
                contentDescription = null,
                tint = color,
                modifier = Modifier.size(24.dp)
            )
            Spacer(modifier = Modifier.width(8.dp))
            Text(
                text = title,
                style = MaterialTheme.typography.bodyMedium.copy(
                    fontWeight = FontWeight.Medium
                ),
                color = color
            )
        }
    }
}

@Composable
private fun StatsSummaryCard(
    gamesPlayed: Int,
    wins: Int,
    losses: Int,
    draws: Int
) {
    ChessCard {
        Column(
            modifier = Modifier
                .fillMaxWidth()
                .padding(16.dp)
        ) {
            Text(
                text = "Your Stats",
                style = MaterialTheme.typography.titleMedium.copy(
                    fontWeight = FontWeight.Bold
                ),
                color = TextPrimary
            )
            
            Spacer(modifier = Modifier.height(16.dp))
            
            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.SpaceEvenly
            ) {
                StatItem(label = "Played", value = gamesPlayed.toString(), color = TextPrimary)
                StatItem(label = "Wins", value = wins.toString(), color = Success)
                StatItem(label = "Losses", value = losses.toString(), color = Error)
                StatItem(label = "Draws", value = draws.toString(), color = TextMuted)
            }
            
            // Win rate bar
            if (gamesPlayed > 0) {
                Spacer(modifier = Modifier.height(16.dp))
                
                val winRate = wins.toFloat() / gamesPlayed
                val drawRate = draws.toFloat() / gamesPlayed
                
                Row(
                    modifier = Modifier
                        .fillMaxWidth()
                        .height(8.dp)
                        .clip(RoundedCornerShape(4.dp))
                ) {
                    Box(
                        modifier = Modifier
                            .weight(if (winRate > 0) winRate else 0.001f)
                            .fillMaxHeight()
                            .background(Success)
                    )
                    Box(
                        modifier = Modifier
                            .weight(if (drawRate > 0) drawRate else 0.001f)
                            .fillMaxHeight()
                            .background(TextMuted)
                    )
                    Box(
                        modifier = Modifier
                            .weight(if (1 - winRate - drawRate > 0) 1 - winRate - drawRate else 0.001f)
                            .fillMaxHeight()
                            .background(Error)
                    )
                }
                
                Spacer(modifier = Modifier.height(8.dp))
                
                Text(
                    text = "Win Rate: ${String.format("%.1f", winRate * 100)}%",
                    style = MaterialTheme.typography.labelMedium,
                    color = TextMuted
                )
            }
        }
    }
}

@Composable
private fun StatItem(
    label: String,
    value: String,
    color: Color
) {
    Column(horizontalAlignment = Alignment.CenterHorizontally) {
        Text(
            text = value,
            style = MaterialTheme.typography.headlineSmall.copy(
                fontWeight = FontWeight.Bold
            ),
            color = color
        )
        Text(
            text = label,
            style = MaterialTheme.typography.labelSmall,
            color = TextMuted
        )
    }
}
