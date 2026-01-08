package com.example.chess_platform.ui.auth

import com.example.chess_platform.data.remote.dto.SkillLevelItem

/**
 * UI State for Login Screen
 */
data class LoginUiState(
    val username: String = "",
    val password: String = "",
    val isLoading: Boolean = false,
    val isPasswordVisible: Boolean = false,
    val error: String? = null,
    val isLoggedIn: Boolean = false
)

/**
 * UI State for Register Screen
 */
data class RegisterUiState(
    val username: String = "",
    val email: String = "",
    val password: String = "",
    val confirmPassword: String = "",
    val firstName: String = "",
    val lastName: String = "",
    val selectedSkillLevel: String = "beginner",
    val skillLevels: List<SkillLevelItem> = emptyList(),
    val isLoading: Boolean = false,
    val isPasswordVisible: Boolean = false,
    val isConfirmPasswordVisible: Boolean = false,
    val error: String? = null,
    val isRegistered: Boolean = false,
    
    // Field validation
    val usernameError: String? = null,
    val emailError: String? = null,
    val passwordError: String? = null,
    val confirmPasswordError: String? = null,
    val passwordStrength: PasswordStrength = PasswordStrength.NONE
)

/**
 * Password strength levels matching web UI
 */
enum class PasswordStrength {
    NONE,
    WEAK,
    FAIR,
    GOOD,
    STRONG
}

/**
 * Events from Login Screen
 */
sealed class LoginEvent {
    data class UsernameChanged(val username: String) : LoginEvent()
    data class PasswordChanged(val password: String) : LoginEvent()
    object TogglePasswordVisibility : LoginEvent()
    object Login : LoginEvent()
    object ClearError : LoginEvent()
}

/**
 * Events from Register Screen
 */
sealed class RegisterEvent {
    data class UsernameChanged(val username: String) : RegisterEvent()
    data class EmailChanged(val email: String) : RegisterEvent()
    data class PasswordChanged(val password: String) : RegisterEvent()
    data class ConfirmPasswordChanged(val confirmPassword: String) : RegisterEvent()
    data class FirstNameChanged(val firstName: String) : RegisterEvent()
    data class LastNameChanged(val lastName: String) : RegisterEvent()
    data class SkillLevelChanged(val skillLevel: String) : RegisterEvent()
    object TogglePasswordVisibility : RegisterEvent()
    object ToggleConfirmPasswordVisibility : RegisterEvent()
    object Register : RegisterEvent()
    object ClearError : RegisterEvent()
    object LoadSkillLevels : RegisterEvent()
}
