---
name: react-native-skills
description: React Native patterns, navigation, and best practices for cross-platform mobile
category: stacks/mobile/react-native
applies_to: react-native
allowed-tools: Read, Write, Glob, Grep, Bash
user-invocable: true
context: inject
---

# React Native Skills

Framework for building native apps using React.

## Sub-Skills

### Architecture
- [project-structure.md](architecture/project-structure.md) - Project organization
- [expo-vs-cli.md](architecture/expo-vs-cli.md) - Expo vs CLI
- [monorepo.md](architecture/monorepo.md) - Monorepo patterns

### Navigation
- [react-navigation.md](navigation/react-navigation.md) - React Navigation
- [stack-navigator.md](navigation/stack-navigator.md) - Stack navigator
- [tab-navigator.md](navigation/tab-navigator.md) - Tab navigator
- [deep-linking.md](navigation/deep-linking.md) - Deep linking

### State Management
- [redux.md](state/redux.md) - Redux patterns
- [zustand.md](state/zustand.md) - Zustand patterns
- [context.md](state/context.md) - Context API
- [react-query.md](state/react-query.md) - React Query

### Components
- [styling.md](components/styling.md) - StyleSheet patterns
- [platform-specific.md](components/platform-specific.md) - Platform.OS
- [native-modules.md](components/native-modules.md) - Native modules
- [animations.md](components/animations.md) - Reanimated

### Data
- [fetch.md](data/fetch.md) - Fetch API
- [axios.md](data/axios.md) - Axios patterns
- [async-storage.md](data/async-storage.md) - AsyncStorage
- [realm.md](data/realm.md) - Realm database

### Performance
- [flatlist.md](performance/flatlist.md) - FlatList optimization
- [images.md](performance/images.md) - Image optimization
- [hermes.md](performance/hermes.md) - Hermes engine
- [memoization.md](performance/memoization.md) - Memoization

### Testing
- [jest.md](testing/jest.md) - Jest patterns
- [detox.md](testing/detox.md) - Detox E2E
- [component-testing.md](testing/component-testing.md) - Component tests

### Build & Deploy
- [fastlane.md](deploy/fastlane.md) - Fastlane automation
- [code-push.md](deploy/code-push.md) - CodePush
- [eas.md](deploy/eas.md) - Expo EAS

## Detection
Auto-detected when project contains:
- `metro.config.js` file
- `app.json` with React Native
- `react-native` package
