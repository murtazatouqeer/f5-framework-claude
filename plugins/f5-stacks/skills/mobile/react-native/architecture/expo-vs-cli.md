---
name: rn-expo-vs-cli
description: Comparison and guidance for Expo vs React Native CLI
applies_to: react-native
---

# Expo vs React Native CLI

## Quick Decision Guide

| Factor | Choose Expo | Choose CLI |
|--------|-------------|-----------|
| Team Experience | New to mobile | Experienced native devs |
| Native Modules | Using Expo SDK | Need custom native code |
| Build Process | Simple OTA updates | Full native control |
| Timeline | Fast MVP | Long-term complex app |
| Platform | Both iOS/Android | Heavy platform-specific |

## Expo (Recommended for Most Projects)

### Expo Managed Workflow

```bash
# Create new project
npx create-expo-app my-app -t expo-template-blank-typescript

# Start development
npx expo start

# Build for production
eas build --platform all
```

### Expo Advantages

1. **Zero Native Setup**: No Xcode/Android Studio required for development
2. **OTA Updates**: Push JavaScript updates without app store review
3. **Expo SDK**: Pre-built native modules (camera, location, etc.)
4. **EAS Build**: Cloud builds for iOS/Android
5. **Expo Router**: File-based routing
6. **Dev Tools**: Built-in debugging, hot reload

### Expo SDK Modules

```typescript
// Common Expo modules
import * as Camera from 'expo-camera';
import * as ImagePicker from 'expo-image-picker';
import * as Location from 'expo-location';
import * as Notifications from 'expo-notifications';
import * as SecureStore from 'expo-secure-store';
import * as FileSystem from 'expo-file-system';
import * as Haptics from 'expo-haptics';
import * as LocalAuthentication from 'expo-local-authentication';
import Constants from 'expo-constants';
```

### Expo Configuration (app.json)

```json
{
  "expo": {
    "name": "My App",
    "slug": "my-app",
    "version": "1.0.0",
    "scheme": "myapp",
    "ios": {
      "supportsTablet": true,
      "bundleIdentifier": "com.company.myapp",
      "infoPlist": {
        "NSCameraUsageDescription": "Camera access for photos"
      }
    },
    "android": {
      "package": "com.company.myapp",
      "permissions": ["CAMERA", "ACCESS_FINE_LOCATION"]
    },
    "plugins": [
      "expo-router",
      [
        "expo-camera",
        { "cameraPermission": "Allow camera access" }
      ]
    ]
  }
}
```

### EAS Build Configuration (eas.json)

```json
{
  "cli": {
    "version": ">= 5.0.0"
  },
  "build": {
    "development": {
      "developmentClient": true,
      "distribution": "internal"
    },
    "preview": {
      "distribution": "internal",
      "ios": {
        "simulator": true
      }
    },
    "production": {
      "autoIncrement": true
    }
  },
  "submit": {
    "production": {}
  }
}
```

## React Native CLI

### When to Use CLI

1. **Custom Native Modules**: Need to write native code (Objective-C/Swift/Java/Kotlin)
2. **Specific Libraries**: Library doesn't support Expo
3. **Full Control**: Need complete native project access
4. **Existing Native App**: Adding RN to native app

### CLI Project Setup

```bash
# Create new project
npx react-native@latest init MyApp --template react-native-template-typescript

# iOS setup
cd ios && pod install && cd ..

# Start Metro
npx react-native start

# Run on device/simulator
npx react-native run-ios
npx react-native run-android
```

### CLI Project Structure

```
MyApp/
├── android/                    # Native Android project
│   ├── app/
│   │   ├── src/main/
│   │   │   ├── java/com/myapp/
│   │   │   ├── res/
│   │   │   └── AndroidManifest.xml
│   │   └── build.gradle
│   └── build.gradle
├── ios/                        # Native iOS project
│   ├── MyApp/
│   │   ├── AppDelegate.mm
│   │   ├── Info.plist
│   │   └── Images.xcassets/
│   ├── Podfile
│   └── MyApp.xcworkspace
├── src/                        # JavaScript/TypeScript code
├── App.tsx
├── index.js
├── metro.config.js
├── babel.config.js
└── package.json
```

### Native Module Example (iOS)

```swift
// ios/MyModule.swift
import Foundation

@objc(MyModule)
class MyModule: NSObject {

  @objc
  func doSomething(_ value: String, resolver: @escaping RCTPromiseResolveBlock, rejecter: @escaping RCTPromiseRejectBlock) {
    // Native implementation
    resolver("Result: \(value)")
  }

  @objc
  static func requiresMainQueueSetup() -> Bool {
    return false
  }
}
```

```typescript
// src/native/MyModule.ts
import { NativeModules } from 'react-native';

const { MyModule } = NativeModules;

export function doSomething(value: string): Promise<string> {
  return MyModule.doSomething(value);
}
```

## Expo Development Build (Hybrid Approach)

Best of both worlds - Expo tooling with custom native code.

### Setup Development Build

```bash
# Install dev client
npx expo install expo-dev-client

# Create development build
eas build --profile development --platform ios
```

### Custom Native Module with Expo

```bash
# Create native module
npx create-expo-module my-native-module

# Structure
my-native-module/
├── android/
│   └── src/main/java/.../MyNativeModule.kt
├── ios/
│   └── MyNativeModule.swift
├── src/
│   └── index.ts
└── expo-module.config.json
```

### expo-module.config.json

```json
{
  "platforms": ["ios", "android"],
  "ios": {
    "modules": ["MyNativeModule"]
  },
  "android": {
    "modules": ["MyNativeModule"]
  }
}
```

## Migration Paths

### Expo to CLI (Ejecting)

```bash
# Not recommended - use Development Build instead
# If absolutely necessary:
npx expo prebuild

# This generates android/ and ios/ folders
```

### CLI to Expo

```bash
# Add Expo SDK
npx install-expo-modules@latest

# Update metro.config.js
const { getDefaultConfig } = require('expo/metro-config');
const config = getDefaultConfig(__dirname);
module.exports = config;
```

## Feature Comparison

| Feature | Expo Managed | Expo Dev Build | CLI |
|---------|--------------|----------------|-----|
| Hot Reload | ✅ | ✅ | ✅ |
| OTA Updates | ✅ | ✅ | ❌ |
| Cloud Builds | ✅ | ✅ | ❌ |
| Custom Native | ❌ | ✅ | ✅ |
| Expo SDK | ✅ | ✅ | ⚠️ |
| Web Support | ✅ | ✅ | ⚠️ |
| Setup Time | Minutes | Hours | Hours |

## Recommendation

1. **Start with Expo Managed** for 90% of projects
2. **Use Development Build** when custom native code needed
3. **Use CLI only** for brownfield apps or extreme edge cases

```bash
# Recommended: Expo with router
npx create-expo-app my-app --template tabs

# Development build when needed
npx expo install expo-dev-client
eas build --profile development
```
