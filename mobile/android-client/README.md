# Chess Platform - Android Mobile App

A Kotlin Android app built with Jetpack Compose, connecting to the Chess Platform Django backend.

## 🏗️ Architecture

```
app/src/main/java/com/example/chess_platform/
├── ChessPlatformApp.kt          # Application class (Hilt entry point)
├── MainActivity.kt               # Main activity with Navigation
├── data/
│   ├── local/
│   │   └── TokenManager.kt      # DataStore for secure token storage
│   ├── remote/
│   │   ├── api/
│   │   │   └── AuthApi.kt       # Retrofit API interfaces
│   │   └── dto/
│   │       └── AuthDto.kt       # Data Transfer Objects
│   └── repository/
│       └── AuthRepositoryImpl.kt # Repository implementations
├── di/
│   ├── AppModule.kt             # Hilt dependency injection
│   └── AuthInterceptor.kt       # OkHttp auth interceptor
├── domain/
│   ├── model/
│   │   └── User.kt              # Domain models
│   └── repository/
│       └── AuthRepository.kt    # Repository interfaces
├── ui/
│   ├── auth/
│   │   ├── AuthState.kt         # UI states and events
│   │   ├── LoginScreen.kt       # Login composable
│   │   ├── LoginViewModel.kt    # Login business logic
│   │   ├── RegisterScreen.kt    # Register composable
│   │   └── RegisterViewModel.kt # Register business logic
│   ├── components/
│   │   └── CommonComponents.kt  # Reusable UI components
│   ├── dashboard/
│   │   ├── DashboardScreen.kt   # Main dashboard
│   │   └── DashboardViewModel.kt
│   ├── navigation/
│   │   ├── ChessNavGraph.kt     # Navigation setup
│   │   └── Screen.kt            # Route definitions
│   └── theme/
│       ├── Color.kt             # Color palette (matches web UI)
│       ├── Theme.kt             # Material3 theme
│       └── Type.kt              # Typography
└── util/
    └── Resource.kt              # Generic API response wrapper
```

## 🎨 Design System

The app uses a dark chess theme matching the web UI:

| Color | Hex | Usage |
|-------|-----|-------|
| BgPrimary | `#0A0A0A` | Main background |
| BgSecondary | `#1A1A1A` | Secondary surfaces |
| AccentPrimary | `#769656` | Primary green accent |
| AccentLight | `#8FAD6B` | Light green variant |
| TextPrimary | `#F0D9B5` | Main text (cream) |
| BoardLight | `#F0D9B5` | Light squares |
| BoardDark | `#B58863` | Dark squares |

## 🔧 Setup

### Prerequisites
- Android Studio Ladybug or later
- JDK 11+
- Android SDK 24+ (target 36)

### Configuration

1. **API URL**: Update `API_BASE_URL` in `app/build.gradle.kts`:
   ```kotlin
   // For Android emulator connecting to localhost
   buildConfigField("String", "API_BASE_URL", "\"http://10.0.2.2:8000/api/\"")
   
   // For physical device (replace with your computer's IP)
   buildConfigField("String", "API_BASE_URL", "\"http://192.168.x.x:8000/api/\"")
   ```

2. **Sync Gradle**: Let Android Studio sync the project

3. **Run Backend**: Ensure Django server is running:
   ```bash
   cd chess-platform
   python manage.py runserver 0.0.0.0:8000
   ```

4. **Build & Run**: Run the app on emulator or device

## 📦 Dependencies

| Library | Purpose |
|---------|---------|
| Jetpack Compose | Modern UI toolkit |
| Material3 | Design system |
| Navigation Compose | Screen navigation |
| Retrofit + Moshi | REST API client |
| OkHttp | HTTP client with interceptors |
| Hilt | Dependency injection |
| Coroutines + Flow | Async operations |
| DataStore | Secure preferences storage |
| Coil | Image loading |
| Room | Local database (offline support) |

## 🚀 Features

### Implemented ✅
- [x] User authentication (Login/Register)
- [x] JWT token management
- [x] Dashboard with ratings display
- [x] Dark theme matching web UI
- [x] Skill level selection on registration
- [x] Password strength indicator
- [x] Form validation

### Coming Soon 🔜
- [ ] Play against bots (offline)
- [ ] Over-the-board mode (local 2P)
- [ ] Online multiplayer
- [ ] Puzzles
- [ ] Game analysis
- [ ] User profile
- [ ] Settings
- [ ] Leaderboard

## 🧪 Testing

```bash
# Run unit tests
./gradlew test

# Run instrumented tests
./gradlew connectedAndroidTest
```

## 📱 Screens

### Login Screen
- Username/password input
- Gradient button matching web design
- Link to registration
- Forgot password option

### Register Screen  
- Username, email, password fields
- Password strength meter
- Skill level selector (Beginner to Expert)
- Initial rating display

### Dashboard
- Quick play buttons (Online, Bot, OTB)
- Rating cards (Blitz, Rapid, Classical)
- Game statistics summary
- Win rate visualization

## 🔒 Security

- JWT tokens stored in encrypted DataStore
- Automatic token refresh
- Auth interceptor for protected API calls
- Public endpoints excluded from auth

## 📄 License

Part of the Chess Platform project.
