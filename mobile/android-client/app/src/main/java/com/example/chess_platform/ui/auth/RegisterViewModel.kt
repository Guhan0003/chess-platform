package com.example.chess_platform.ui.auth

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.example.chess_platform.domain.repository.AuthRepository
import com.example.chess_platform.util.Resource
import dagger.hilt.android.lifecycle.HiltViewModel
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.flow.update
import kotlinx.coroutines.launch
import javax.inject.Inject

@HiltViewModel
class RegisterViewModel @Inject constructor(
    private val authRepository: AuthRepository
) : ViewModel() {
    
    private val _uiState = MutableStateFlow(RegisterUiState())
    val uiState: StateFlow<RegisterUiState> = _uiState.asStateFlow()
    
    init {
        loadSkillLevels()
    }
    
    fun onEvent(event: RegisterEvent) {
        when (event) {
            is RegisterEvent.UsernameChanged -> {
                _uiState.update { 
                    it.copy(
                        username = event.username, 
                        usernameError = validateUsername(event.username),
                        error = null
                    ) 
                }
            }
            is RegisterEvent.EmailChanged -> {
                _uiState.update { 
                    it.copy(
                        email = event.email, 
                        emailError = validateEmail(event.email),
                        error = null
                    ) 
                }
            }
            is RegisterEvent.PasswordChanged -> {
                val strength = calculatePasswordStrength(event.password)
                _uiState.update { 
                    it.copy(
                        password = event.password, 
                        passwordError = validatePassword(event.password),
                        passwordStrength = strength,
                        confirmPasswordError = if (it.confirmPassword.isNotEmpty() && it.confirmPassword != event.password) 
                            "Passwords don't match" else null,
                        error = null
                    ) 
                }
            }
            is RegisterEvent.ConfirmPasswordChanged -> {
                _uiState.update { 
                    it.copy(
                        confirmPassword = event.confirmPassword, 
                        confirmPasswordError = if (event.confirmPassword != it.password) 
                            "Passwords don't match" else null,
                        error = null
                    ) 
                }
            }
            is RegisterEvent.FirstNameChanged -> {
                _uiState.update { it.copy(firstName = event.firstName) }
            }
            is RegisterEvent.LastNameChanged -> {
                _uiState.update { it.copy(lastName = event.lastName) }
            }
            is RegisterEvent.SkillLevelChanged -> {
                _uiState.update { it.copy(selectedSkillLevel = event.skillLevel) }
            }
            is RegisterEvent.TogglePasswordVisibility -> {
                _uiState.update { it.copy(isPasswordVisible = !it.isPasswordVisible) }
            }
            is RegisterEvent.ToggleConfirmPasswordVisibility -> {
                _uiState.update { it.copy(isConfirmPasswordVisible = !it.isConfirmPasswordVisible) }
            }
            is RegisterEvent.Register -> register()
            is RegisterEvent.ClearError -> {
                _uiState.update { it.copy(error = null) }
            }
            is RegisterEvent.LoadSkillLevels -> loadSkillLevels()
        }
    }
    
    private fun loadSkillLevels() {
        viewModelScope.launch {
            when (val result = authRepository.getSkillLevels()) {
                is Resource.Success -> {
                    result.data?.let { skillLevels ->
                        _uiState.update { it.copy(skillLevels = skillLevels) }
                    }
                }
                else -> {} // Use default skill levels from state
            }
        }
    }
    
    private fun register() {
        val currentState = _uiState.value
        
        // Validate all fields
        val usernameError = validateUsername(currentState.username)
        val emailError = validateEmail(currentState.email)
        val passwordError = validatePassword(currentState.password)
        val confirmPasswordError = if (currentState.confirmPassword != currentState.password) 
            "Passwords don't match" else null
        
        if (usernameError != null || emailError != null || passwordError != null || confirmPasswordError != null) {
            _uiState.update { 
                it.copy(
                    usernameError = usernameError,
                    emailError = emailError,
                    passwordError = passwordError,
                    confirmPasswordError = confirmPasswordError,
                    error = "Please fix the errors above"
                ) 
            }
            return
        }
        
        viewModelScope.launch {
            _uiState.update { it.copy(isLoading = true, error = null) }
            
            when (val result = authRepository.register(
                username = currentState.username,
                email = currentState.email,
                password = currentState.password,
                passwordConfirm = currentState.confirmPassword,
                skillLevel = currentState.selectedSkillLevel,
                firstName = currentState.firstName.takeIf { it.isNotBlank() },
                lastName = currentState.lastName.takeIf { it.isNotBlank() }
            )) {
                is Resource.Success -> {
                    _uiState.update { it.copy(isLoading = false, isRegistered = true) }
                }
                is Resource.Error -> {
                    _uiState.update { 
                        it.copy(
                            isLoading = false, 
                            error = result.message ?: "Registration failed"
                        ) 
                    }
                }
                is Resource.Loading -> {
                    _uiState.update { it.copy(isLoading = true) }
                }
            }
        }
    }
    
    private fun validateUsername(username: String): String? {
        return when {
            username.isBlank() -> "Username is required"
            username.length < 3 -> "Username must be at least 3 characters"
            !username.matches(Regex("^[a-zA-Z0-9_-]+$")) -> "Only letters, numbers, underscores and hyphens"
            else -> null
        }
    }
    
    private fun validateEmail(email: String): String? {
        return when {
            email.isBlank() -> "Email is required"
            !android.util.Patterns.EMAIL_ADDRESS.matcher(email).matches() -> "Invalid email format"
            else -> null
        }
    }
    
    private fun validatePassword(password: String): String? {
        return when {
            password.isBlank() -> "Password is required"
            password.length < 8 -> "Password must be at least 8 characters"
            else -> null
        }
    }
    
    private fun calculatePasswordStrength(password: String): PasswordStrength {
        if (password.isEmpty()) return PasswordStrength.NONE
        
        var score = 0
        
        // Length checks
        if (password.length >= 8) score++
        if (password.length >= 12) score++
        
        // Character variety checks
        if (password.any { it.isLowerCase() }) score++
        if (password.any { it.isUpperCase() }) score++
        if (password.any { it.isDigit() }) score++
        if (password.any { !it.isLetterOrDigit() }) score++
        
        return when {
            score <= 2 -> PasswordStrength.WEAK
            score <= 3 -> PasswordStrength.FAIR
            score <= 4 -> PasswordStrength.GOOD
            else -> PasswordStrength.STRONG
        }
    }
}
