---
description: Mobile development commands
argument-hint: <generate|scaffold> <type> [name]
---

# /f5-mobile - Mobile Development Assistant

Hỗ trợ phát triển mobile app theo stack đã chọn trong project.

## ARGUMENTS
The user's request is: $ARGUMENTS

## DETECT MOBILE STACK

```bash
# Auto-detect from .f5/config.json
STACK=$(jq -r '.stack.mobile // "none"' .f5/config.json 2>/dev/null)
```

## STACK-SPECIFIC COMMANDS

### Flutter (Default Cross-Platform)

| Command | Description |
|---------|-------------|
| `screen <name>` | Generate screen with state management |
| `widget <name>` | Generate reusable widget |
| `provider <name>` | Generate Riverpod provider |
| `bloc <name>` | Generate BLoC pattern |
| `repository <name>` | Generate repository |
| `model <name>` | Generate data model with freezed |
| `service <name>` | Generate service |

### React Native (Expo)

| Command | Description |
|---------|-------------|
| `screen <name>` | Generate screen component |
| `component <name>` | Generate component |
| `hook <name>` | Generate custom hook |
| `store <name>` | Generate Zustand store |
| `navigation <name>` | Setup navigation |
| `api <name>` | Generate API client |

### Android (Kotlin)

| Command | Description |
|---------|-------------|
| `activity <name>` | Generate Activity |
| `fragment <name>` | Generate Fragment |
| `viewmodel <name>` | Generate ViewModel |
| `repository <name>` | Generate Repository |
| `composable <name>` | Generate Jetpack Compose |
| `room <name>` | Generate Room entity |

### iOS (Swift)

| Command | Description |
|---------|-------------|
| `view <name>` | Generate SwiftUI View |
| `viewmodel <name>` | Generate ViewModel |
| `service <name>` | Generate Service |
| `model <name>` | Generate Codable model |
| `coordinator <name>` | Generate Coordinator |

## EXECUTION

Based on detected stack and user request:

```markdown
## Mobile: {{STACK}}

### Generated Files:
{{list of generated files}}

### Architecture:
{{architecture diagram}}

### Next Steps:
{{stack-specific recommendations}}

### Related Commands:
- /f5-test-unit     - Run unit tests
- /f5-test-it       - Run integration tests
- /f5-design ui     - Generate UI mockups
```

## EXAMPLES

```bash
# Flutter
/f5-mobile screen HomeScreen
/f5-mobile widget ProductCard
/f5-mobile provider authProvider
/f5-mobile bloc CartBloc

# React Native
/f5-mobile screen ProfileScreen
/f5-mobile component Avatar
/f5-mobile store cartStore

# Android
/f5-mobile activity MainActivity
/f5-mobile composable UserCard
/f5-mobile viewmodel UserViewModel

# iOS
/f5-mobile view ContentView
/f5-mobile viewmodel UserViewModel
/f5-mobile model User
```

## ARCHITECTURE PATTERNS

| Stack | Default Pattern |
|-------|----------------|
| Flutter | Clean Architecture + Riverpod |
| React Native | Feature-based + Zustand |
| Android | MVVM + Hilt |
| iOS | MVVM + Combine |

## BEST PRACTICES

Claude automatically applies:

### Flutter
- Separation of concerns (presentation/domain/data)
- Riverpod for state management
- Freezed for immutable models
- Go Router for navigation

### React Native
- Expo Router for navigation
- React Query for data fetching
- Zustand for state
- TypeScript strict mode

### Android
- Jetpack Compose for UI
- Kotlin Coroutines + Flow
- Hilt for DI
- Room for local storage

### iOS
- SwiftUI for UI
- Combine for reactive
- Swift Concurrency (async/await)
- CoreData for persistence

## PLATFORM-SPECIFIC

Claude handles platform differences:

```markdown
### iOS-specific:
- App Store guidelines
- iOS design guidelines
- Permission handling
- Push notifications

### Android-specific:
- Material Design
- Permission requests
- Background services
- Firebase integration
```
