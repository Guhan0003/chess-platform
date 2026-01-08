package com.example.chess_platform.ui.auth

import androidx.compose.animation.animateColorAsState
import androidx.compose.animation.core.animateFloatAsState
import androidx.compose.foundation.BorderStroke
import androidx.compose.foundation.background
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.foundation.text.KeyboardActions
import androidx.compose.foundation.text.KeyboardOptions
import androidx.compose.foundation.verticalScroll
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.*
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.focus.FocusDirection
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.platform.LocalFocusManager
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.input.ImeAction
import androidx.compose.ui.text.input.KeyboardType
import androidx.compose.ui.text.input.PasswordVisualTransformation
import androidx.compose.ui.text.input.VisualTransformation
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.unit.dp
import androidx.hilt.navigation.compose.hiltViewModel
import com.example.chess_platform.ui.components.ChessBackground
import com.example.chess_platform.ui.components.ChessCard
import com.example.chess_platform.ui.components.ChessTextField
import com.example.chess_platform.ui.components.GradientButton
import com.example.chess_platform.ui.theme.*

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun RegisterScreen(
    viewModel: RegisterViewModel = hiltViewModel(),
    onNavigateToLogin: () -> Unit,
    onRegisterSuccess: () -> Unit
) {
    val uiState by viewModel.uiState.collectAsState()
    val focusManager = LocalFocusManager.current
    
    // Navigate on successful registration
    LaunchedEffect(uiState.isRegistered) {
        if (uiState.isRegistered) {
            onRegisterSuccess()
        }
    }
    
    ChessBackground {
        Column(
            modifier = Modifier
                .fillMaxSize()
                .verticalScroll(rememberScrollState())
                .padding(24.dp),
            horizontalAlignment = Alignment.CenterHorizontally
        ) {
            Spacer(modifier = Modifier.height(32.dp))
            
            ChessCard(
                modifier = Modifier.fillMaxWidth()
            ) {
                Column(
                    modifier = Modifier
                        .fillMaxWidth()
                        .padding(24.dp),
                    horizontalAlignment = Alignment.CenterHorizontally
                ) {
                    // Logo/Title
                    Text(
                        text = "♔ Join Chess Platform",
                        style = MaterialTheme.typography.headlineMedium.copy(
                            fontWeight = FontWeight.Bold
                        ),
                        color = AccentPrimary
                    )
                    
                    Spacer(modifier = Modifier.height(8.dp))
                    
                    Text(
                        text = "Create your account and start playing",
                        style = MaterialTheme.typography.bodyMedium,
                        color = TextMuted,
                        textAlign = TextAlign.Center
                    )
                    
                    Spacer(modifier = Modifier.height(24.dp))
                    
                    // Username Field
                    ChessTextField(
                        value = uiState.username,
                        onValueChange = { viewModel.onEvent(RegisterEvent.UsernameChanged(it)) },
                        label = "Username *",
                        placeholder = "Choose a username",
                        error = uiState.usernameError,
                        leadingIcon = {
                            Icon(Icons.Default.Person, null, tint = TextMuted)
                        },
                        keyboardOptions = KeyboardOptions(
                            keyboardType = KeyboardType.Text,
                            imeAction = ImeAction.Next
                        ),
                        keyboardActions = KeyboardActions(
                            onNext = { focusManager.moveFocus(FocusDirection.Down) }
                        ),
                        modifier = Modifier.fillMaxWidth()
                    )
                    
                    Spacer(modifier = Modifier.height(12.dp))
                    
                    // Email Field
                    ChessTextField(
                        value = uiState.email,
                        onValueChange = { viewModel.onEvent(RegisterEvent.EmailChanged(it)) },
                        label = "Email *",
                        placeholder = "Enter your email",
                        error = uiState.emailError,
                        leadingIcon = {
                            Icon(Icons.Default.Email, null, tint = TextMuted)
                        },
                        keyboardOptions = KeyboardOptions(
                            keyboardType = KeyboardType.Email,
                            imeAction = ImeAction.Next
                        ),
                        keyboardActions = KeyboardActions(
                            onNext = { focusManager.moveFocus(FocusDirection.Down) }
                        ),
                        modifier = Modifier.fillMaxWidth()
                    )
                    
                    Spacer(modifier = Modifier.height(12.dp))
                    
                    // Optional Name Fields Row
                    Row(
                        modifier = Modifier.fillMaxWidth(),
                        horizontalArrangement = Arrangement.spacedBy(12.dp)
                    ) {
                        ChessTextField(
                            value = uiState.firstName,
                            onValueChange = { viewModel.onEvent(RegisterEvent.FirstNameChanged(it)) },
                            label = "First Name",
                            placeholder = "First",
                            keyboardOptions = KeyboardOptions(
                                keyboardType = KeyboardType.Text,
                                imeAction = ImeAction.Next
                            ),
                            modifier = Modifier.weight(1f)
                        )
                        
                        ChessTextField(
                            value = uiState.lastName,
                            onValueChange = { viewModel.onEvent(RegisterEvent.LastNameChanged(it)) },
                            label = "Last Name",
                            placeholder = "Last",
                            keyboardOptions = KeyboardOptions(
                                keyboardType = KeyboardType.Text,
                                imeAction = ImeAction.Next
                            ),
                            modifier = Modifier.weight(1f)
                        )
                    }
                    
                    Spacer(modifier = Modifier.height(12.dp))
                    
                    // Password Field
                    ChessTextField(
                        value = uiState.password,
                        onValueChange = { viewModel.onEvent(RegisterEvent.PasswordChanged(it)) },
                        label = "Password *",
                        placeholder = "Create a password",
                        error = uiState.passwordError,
                        visualTransformation = if (uiState.isPasswordVisible) 
                            VisualTransformation.None else PasswordVisualTransformation(),
                        trailingIcon = {
                            IconButton(onClick = { viewModel.onEvent(RegisterEvent.TogglePasswordVisibility) }) {
                                Icon(
                                    imageVector = if (uiState.isPasswordVisible) 
                                        Icons.Default.VisibilityOff else Icons.Default.Visibility,
                                    contentDescription = null,
                                    tint = TextMuted
                                )
                            }
                        },
                        keyboardOptions = KeyboardOptions(
                            keyboardType = KeyboardType.Password,
                            imeAction = ImeAction.Next
                        ),
                        modifier = Modifier.fillMaxWidth()
                    )
                    
                    // Password Strength Indicator
                    if (uiState.password.isNotEmpty()) {
                        Spacer(modifier = Modifier.height(8.dp))
                        PasswordStrengthIndicator(strength = uiState.passwordStrength)
                    }
                    
                    Spacer(modifier = Modifier.height(12.dp))
                    
                    // Confirm Password Field
                    ChessTextField(
                        value = uiState.confirmPassword,
                        onValueChange = { viewModel.onEvent(RegisterEvent.ConfirmPasswordChanged(it)) },
                        label = "Confirm Password *",
                        placeholder = "Confirm your password",
                        error = uiState.confirmPasswordError,
                        visualTransformation = if (uiState.isConfirmPasswordVisible) 
                            VisualTransformation.None else PasswordVisualTransformation(),
                        trailingIcon = {
                            IconButton(onClick = { viewModel.onEvent(RegisterEvent.ToggleConfirmPasswordVisibility) }) {
                                Icon(
                                    imageVector = if (uiState.isConfirmPasswordVisible) 
                                        Icons.Default.VisibilityOff else Icons.Default.Visibility,
                                    contentDescription = null,
                                    tint = TextMuted
                                )
                            }
                        },
                        keyboardOptions = KeyboardOptions(
                            keyboardType = KeyboardType.Password,
                            imeAction = ImeAction.Done
                        ),
                        modifier = Modifier.fillMaxWidth()
                    )
                    
                    Spacer(modifier = Modifier.height(16.dp))
                    
                    // Skill Level Selection
                    Text(
                        text = "Select Your Skill Level *",
                        style = MaterialTheme.typography.labelLarge,
                        color = TextSecondary,
                        modifier = Modifier
                            .fillMaxWidth()
                            .padding(bottom = 8.dp)
                    )
                    
                    SkillLevelSelector(
                        skillLevels = uiState.skillLevels,
                        selectedLevel = uiState.selectedSkillLevel,
                        onSelectLevel = { viewModel.onEvent(RegisterEvent.SkillLevelChanged(it)) }
                    )
                    
                    // Error Message
                    if (uiState.error != null) {
                        Spacer(modifier = Modifier.height(16.dp))
                        Card(
                            colors = CardDefaults.cardColors(
                                containerColor = Error.copy(alpha = 0.1f)
                            ),
                            modifier = Modifier.fillMaxWidth()
                        ) {
                            Text(
                                text = uiState.error!!,
                                color = Error,
                                style = MaterialTheme.typography.bodySmall,
                                modifier = Modifier.padding(12.dp),
                                textAlign = TextAlign.Center
                            )
                        }
                    }
                    
                    Spacer(modifier = Modifier.height(24.dp))
                    
                    // Register Button
                    GradientButton(
                        text = if (uiState.isLoading) "Creating Account..." else "Create Account",
                        onClick = { viewModel.onEvent(RegisterEvent.Register) },
                        enabled = !uiState.isLoading,
                        modifier = Modifier.fillMaxWidth()
                    )
                    
                    Spacer(modifier = Modifier.height(24.dp))
                    
                    // Login Link
                    Row(
                        horizontalArrangement = Arrangement.Center,
                        verticalAlignment = Alignment.CenterVertically
                    ) {
                        Text(
                            text = "Already have an account? ",
                            style = MaterialTheme.typography.bodyMedium,
                            color = TextMuted
                        )
                        TextButton(onClick = onNavigateToLogin) {
                            Text(
                                text = "Sign In",
                                style = MaterialTheme.typography.bodyMedium.copy(
                                    fontWeight = FontWeight.SemiBold
                                ),
                                color = AccentPrimary
                            )
                        }
                    }
                }
            }
            
            Spacer(modifier = Modifier.height(32.dp))
        }
    }
}

@Composable
private fun PasswordStrengthIndicator(strength: PasswordStrength) {
    val (color, text, progress) = when (strength) {
        PasswordStrength.NONE -> Triple(BorderDefault, "", 0f)
        PasswordStrength.WEAK -> Triple(Error, "Weak", 0.25f)
        PasswordStrength.FAIR -> Triple(Warning, "Fair", 0.5f)
        PasswordStrength.GOOD -> Triple(Info, "Good", 0.75f)
        PasswordStrength.STRONG -> Triple(Success, "Strong", 1f)
    }
    
    val animatedProgress by animateFloatAsState(targetValue = progress, label = "progress")
    val animatedColor by animateColorAsState(targetValue = color, label = "color")
    
    Column(modifier = Modifier.fillMaxWidth()) {
        LinearProgressIndicator(
            progress = { animatedProgress },
            modifier = Modifier
                .fillMaxWidth()
                .height(4.dp)
                .clip(RoundedCornerShape(2.dp)),
            color = animatedColor,
            trackColor = BorderDefault
        )
        
        if (text.isNotEmpty()) {
            Spacer(modifier = Modifier.height(4.dp))
            Text(
                text = text,
                style = MaterialTheme.typography.labelSmall,
                color = animatedColor
            )
        }
    }
}

@Composable
private fun SkillLevelSelector(
    skillLevels: List<com.example.chess_platform.data.remote.dto.SkillLevelItem>,
    selectedLevel: String,
    onSelectLevel: (String) -> Unit
) {
    // Default skill levels if none loaded
    val levels = skillLevels.ifEmpty {
        listOf(
            com.example.chess_platform.data.remote.dto.SkillLevelItem("beginner", "Beginner", "New to chess", 800),
            com.example.chess_platform.data.remote.dto.SkillLevelItem("intermediate", "Intermediate", "Know basics", 1200),
            com.example.chess_platform.data.remote.dto.SkillLevelItem("advanced", "Advanced", "Experienced", 1600),
            com.example.chess_platform.data.remote.dto.SkillLevelItem("expert", "Expert", "Tournament level", 2000)
        )
    }
    
    Column(
        modifier = Modifier.fillMaxWidth(),
        verticalArrangement = Arrangement.spacedBy(8.dp)
    ) {
        levels.forEach { level ->
            val isSelected = selectedLevel == level.id
            
            Card(
                modifier = Modifier
                    .fillMaxWidth()
                    .clickable { onSelectLevel(level.id) },
                colors = CardDefaults.cardColors(
                    containerColor = if (isSelected) AccentPrimary.copy(alpha = 0.15f) else BgTertiary
                ),
                border = if (isSelected) BorderStroke(1.dp, AccentPrimary) else null,
                shape = RoundedCornerShape(8.dp)
            ) {
                Row(
                    modifier = Modifier
                        .fillMaxWidth()
                        .padding(12.dp),
                    horizontalArrangement = Arrangement.SpaceBetween,
                    verticalAlignment = Alignment.CenterVertically
                ) {
                    Column(modifier = Modifier.weight(1f)) {
                        Text(
                            text = level.name,
                            style = MaterialTheme.typography.bodyLarge.copy(
                                fontWeight = FontWeight.Medium
                            ),
                            color = if (isSelected) AccentLight else TextPrimary
                        )
                        Text(
                            text = level.description,
                            style = MaterialTheme.typography.bodySmall,
                            color = TextMuted
                        )
                    }
                    
                    Column(horizontalAlignment = Alignment.End) {
                        Text(
                            text = "${level.rating}",
                            style = MaterialTheme.typography.titleMedium.copy(
                                fontWeight = FontWeight.Bold
                            ),
                            color = if (isSelected) AccentPrimary else TextSecondary
                        )
                        Text(
                            text = "Rating",
                            style = MaterialTheme.typography.labelSmall,
                            color = TextMuted
                        )
                    }
                    
                    if (isSelected) {
                        Spacer(modifier = Modifier.width(8.dp))
                        Icon(
                            imageVector = Icons.Default.CheckCircle,
                            contentDescription = null,
                            tint = AccentPrimary,
                            modifier = Modifier.size(24.dp)
                        )
                    }
                }
            }
        }
    }
}
