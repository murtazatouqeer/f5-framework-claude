---
name: rn-platform-specific
description: Platform-specific code patterns for iOS and Android
applies_to: react-native
---

# Platform-Specific Code in React Native

## Platform Detection

### Using Platform Module

```typescript
import { Platform } from 'react-native';

// Check platform
if (Platform.OS === 'ios') {
  // iOS specific code
}

if (Platform.OS === 'android') {
  // Android specific code
}

// Platform version
const isIOS15OrAbove = Platform.OS === 'ios' && parseInt(Platform.Version, 10) >= 15;
const isAndroid12OrAbove = Platform.OS === 'android' && Platform.Version >= 31;
```

### Platform.select()

```typescript
import { Platform, StyleSheet } from 'react-native';

const styles = StyleSheet.create({
  container: {
    ...Platform.select({
      ios: {
        shadowColor: '#000',
        shadowOffset: { width: 0, height: 2 },
        shadowOpacity: 0.1,
        shadowRadius: 4,
      },
      android: {
        elevation: 4,
      },
      default: {
        // Web or other platforms
        boxShadow: '0 2px 4px rgba(0,0,0,0.1)',
      },
    }),
  },
});

// For values
const hitSlop = Platform.select({
  ios: { top: 10, bottom: 10, left: 10, right: 10 },
  android: { top: 20, bottom: 20, left: 20, right: 20 },
});
```

## Platform-Specific Files

### File Extensions

```
Button.tsx          # Shared implementation
Button.ios.tsx      # iOS specific
Button.android.tsx  # Android specific
Button.native.tsx   # iOS + Android (not web)
Button.web.tsx      # Web specific
```

```typescript
// Button.ios.tsx
export function Button(props: ButtonProps) {
  return <IOSButton {...props} />;
}

// Button.android.tsx
export function Button(props: ButtonProps) {
  return <AndroidButton {...props} />;
}

// Usage - React Native auto-selects correct file
import { Button } from './Button';
```

## Platform-Specific Styling

### Shadows

```typescript
import { Platform, StyleSheet } from 'react-native';

const styles = StyleSheet.create({
  card: {
    backgroundColor: '#fff',
    borderRadius: 8,
    // iOS shadow
    ...Platform.select({
      ios: {
        shadowColor: '#000',
        shadowOffset: { width: 0, height: 2 },
        shadowOpacity: 0.1,
        shadowRadius: 8,
      },
      android: {
        elevation: 4,
      },
    }),
  },
});

// Reusable shadow utility
export const shadow = (level: 1 | 2 | 3 | 4 | 5) => {
  const elevationMap = { 1: 2, 2: 4, 3: 6, 4: 8, 5: 12 };
  const shadowOpacityMap = { 1: 0.05, 2: 0.1, 3: 0.15, 4: 0.2, 5: 0.25 };

  return Platform.select({
    ios: {
      shadowColor: '#000',
      shadowOffset: { width: 0, height: level },
      shadowOpacity: shadowOpacityMap[level],
      shadowRadius: level * 2,
    },
    android: {
      elevation: elevationMap[level],
    },
    default: {},
  });
};
```

### Safe Area Handling

```typescript
import { Platform, StatusBar } from 'react-native';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import Constants from 'expo-constants';

// Get status bar height
const statusBarHeight = Platform.select({
  ios: Constants.statusBarHeight,
  android: StatusBar.currentHeight ?? 0,
  default: 0,
});

// Using safe area insets
function Header() {
  const insets = useSafeAreaInsets();

  return (
    <View style={[styles.header, { paddingTop: insets.top }]}>
      {/* Header content */}
    </View>
  );
}
```

### Font Weights

```typescript
// Font weights work differently on Android
const styles = StyleSheet.create({
  boldText: {
    ...Platform.select({
      ios: {
        fontWeight: '700',
      },
      android: {
        fontFamily: 'sans-serif-medium',
        fontWeight: 'bold',
      },
    }),
  },
});
```

## Platform-Specific Components

### Pressable with Platform Feedback

```typescript
import { Pressable, Platform, StyleSheet } from 'react-native';

function PlatformButton({ onPress, children, ...props }: PressableProps) {
  return (
    <Pressable
      onPress={onPress}
      style={({ pressed }) => [
        styles.button,
        Platform.OS === 'ios' && pressed && styles.iosPressed,
      ]}
      android_ripple={
        Platform.OS === 'android'
          ? { color: 'rgba(0, 0, 0, 0.1)', borderless: false }
          : undefined
      }
      {...props}
    >
      {children}
    </Pressable>
  );
}

const styles = StyleSheet.create({
  button: {
    padding: 12,
    backgroundColor: '#007AFF',
    borderRadius: 8,
  },
  iosPressed: {
    opacity: 0.7,
  },
});
```

### Platform Action Sheet

```typescript
import { Platform, ActionSheetIOS, Alert } from 'react-native';

function showActionSheet(options: string[], onSelect: (index: number) => void) {
  if (Platform.OS === 'ios') {
    ActionSheetIOS.showActionSheetWithOptions(
      {
        options: [...options, 'Cancel'],
        cancelButtonIndex: options.length,
        destructiveButtonIndex: options.findIndex(o => o.includes('Delete')),
      },
      (buttonIndex) => {
        if (buttonIndex !== options.length) {
          onSelect(buttonIndex);
        }
      }
    );
  } else {
    // Android - use Alert or custom modal
    Alert.alert(
      'Select Option',
      undefined,
      [
        ...options.map((option, index) => ({
          text: option,
          onPress: () => onSelect(index),
        })),
        { text: 'Cancel', style: 'cancel' },
      ]
    );
  }
}
```

### Platform Date Picker

```typescript
import { Platform } from 'react-native';
import DateTimePicker from '@react-native-community/datetimepicker';

function DatePicker({ value, onChange }: DatePickerProps) {
  const [show, setShow] = useState(Platform.OS === 'ios');

  const handleChange = (event: any, selectedDate?: Date) => {
    // Android closes picker on selection
    if (Platform.OS === 'android') {
      setShow(false);
    }
    if (selectedDate) {
      onChange(selectedDate);
    }
  };

  return (
    <>
      {Platform.OS === 'android' && (
        <Button title="Select Date" onPress={() => setShow(true)} />
      )}

      {show && (
        <DateTimePicker
          value={value}
          mode="date"
          display={Platform.OS === 'ios' ? 'spinner' : 'default'}
          onChange={handleChange}
        />
      )}
    </>
  );
}
```

## Platform-Specific Native Modules

### Haptics

```typescript
import { Platform } from 'react-native';
import * as Haptics from 'expo-haptics';

async function triggerHaptic(type: 'light' | 'medium' | 'heavy' | 'success' | 'error') {
  if (Platform.OS === 'web') return;

  try {
    switch (type) {
      case 'light':
        await Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Light);
        break;
      case 'medium':
        await Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Medium);
        break;
      case 'heavy':
        await Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Heavy);
        break;
      case 'success':
        await Haptics.notificationAsync(Haptics.NotificationFeedbackType.Success);
        break;
      case 'error':
        await Haptics.notificationAsync(Haptics.NotificationFeedbackType.Error);
        break;
    }
  } catch {
    // Haptics not available
  }
}
```

### Biometric Authentication

```typescript
import { Platform } from 'react-native';
import * as LocalAuthentication from 'expo-local-authentication';

async function authenticateWithBiometrics(): Promise<boolean> {
  const hasHardware = await LocalAuthentication.hasHardwareAsync();
  if (!hasHardware) return false;

  const isEnrolled = await LocalAuthentication.isEnrolledAsync();
  if (!isEnrolled) return false;

  const result = await LocalAuthentication.authenticateAsync({
    promptMessage: Platform.select({
      ios: 'Authenticate with Face ID or Touch ID',
      android: 'Authenticate with fingerprint',
      default: 'Authenticate',
    }),
    cancelLabel: 'Cancel',
    disableDeviceFallback: false,
  });

  return result.success;
}
```

## Platform-Specific Permissions

```typescript
import { Platform, PermissionsAndroid } from 'react-native';
import * as ImagePicker from 'expo-image-picker';

async function requestCameraPermission(): Promise<boolean> {
  if (Platform.OS === 'android') {
    const granted = await PermissionsAndroid.request(
      PermissionsAndroid.PERMISSIONS.CAMERA,
      {
        title: 'Camera Permission',
        message: 'App needs camera access to take photos',
        buttonNeutral: 'Ask Later',
        buttonNegative: 'Cancel',
        buttonPositive: 'OK',
      }
    );
    return granted === PermissionsAndroid.RESULTS.GRANTED;
  }

  // iOS - use Expo's permissions
  const { status } = await ImagePicker.requestCameraPermissionsAsync();
  return status === 'granted';
}
```

## Best Practices

1. **Minimize Platform-Specific Code**: Share as much code as possible
2. **Use Platform.select()**: For inline platform differences
3. **Use File Extensions**: For larger platform-specific implementations
4. **Test on Both Platforms**: Behavior can differ significantly
5. **Handle Web**: Consider web support with default case
6. **Document Differences**: Note platform-specific behavior in comments
