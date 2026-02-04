---
name: rn-component
description: React Native component template with variants and accessibility
applies_to: react-native
variables:
  - name: componentName
    description: Name of the component (e.g., Button, Card)
  - name: hasVariants
    description: Include variant props
  - name: hasForwardRef
    description: Include forwardRef for input components
---

# React Native Component Template

## Basic Component

```typescript
// src/components/{{componentName}}.tsx
import { View, Text, StyleSheet, ViewStyle, TextStyle } from 'react-native';

interface {{componentName}}Props {
  title: string;
  subtitle?: string;
  style?: ViewStyle;
}

export function {{componentName}}({ title, subtitle, style }: {{componentName}}Props) {
  return (
    <View style={[styles.container, style]}>
      <Text style={styles.title}>{title}</Text>
      {subtitle && <Text style={styles.subtitle}>{subtitle}</Text>}
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    padding: 16,
    backgroundColor: '#fff',
    borderRadius: 12,
  },
  title: {
    fontSize: 16,
    fontWeight: '600',
    color: '#000',
  },
  subtitle: {
    fontSize: 14,
    color: '#666',
    marginTop: 4,
  },
});
```

## Pressable Component

```typescript
// src/components/{{componentName}}.tsx
import { Pressable, Text, StyleSheet, ViewStyle, PressableProps } from 'react-native';
import { Ionicons } from '@expo/vector-icons';

interface {{componentName}}Props extends Omit<PressableProps, 'style'> {
  title: string;
  icon?: keyof typeof Ionicons.glyphMap;
  variant?: 'primary' | 'secondary' | 'outline';
  size?: 'sm' | 'md' | 'lg';
  loading?: boolean;
  style?: ViewStyle;
}

export function {{componentName}}({
  title,
  icon,
  variant = 'primary',
  size = 'md',
  loading = false,
  disabled,
  style,
  ...pressableProps
}: {{componentName}}Props) {
  return (
    <Pressable
      style={({ pressed }) => [
        styles.base,
        styles[variant],
        styles[`size_${size}`],
        pressed && styles.pressed,
        disabled && styles.disabled,
        style,
      ]}
      disabled={disabled || loading}
      accessibilityRole="button"
      accessibilityState={{ disabled: disabled || loading }}
      {...pressableProps}
    >
      {loading ? (
        <ActivityIndicator color={variant === 'primary' ? '#fff' : '#007AFF'} />
      ) : (
        <>
          {icon && (
            <Ionicons
              name={icon}
              size={size === 'sm' ? 16 : size === 'lg' ? 24 : 20}
              color={variant === 'primary' ? '#fff' : '#007AFF'}
              style={styles.icon}
            />
          )}
          <Text style={[styles.text, styles[`text_${variant}`], styles[`text_${size}`]]}>
            {title}
          </Text>
        </>
      )}
    </Pressable>
  );
}

const styles = StyleSheet.create({
  base: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    borderRadius: 12,
  },
  primary: {
    backgroundColor: '#007AFF',
  },
  secondary: {
    backgroundColor: '#E5E5EA',
  },
  outline: {
    backgroundColor: 'transparent',
    borderWidth: 1,
    borderColor: '#007AFF',
  },
  size_sm: {
    paddingVertical: 8,
    paddingHorizontal: 16,
  },
  size_md: {
    paddingVertical: 12,
    paddingHorizontal: 24,
  },
  size_lg: {
    paddingVertical: 16,
    paddingHorizontal: 32,
  },
  pressed: {
    opacity: 0.8,
  },
  disabled: {
    opacity: 0.5,
  },
  icon: {
    marginRight: 8,
  },
  text: {
    fontWeight: '600',
  },
  text_primary: {
    color: '#fff',
  },
  text_secondary: {
    color: '#000',
  },
  text_outline: {
    color: '#007AFF',
  },
  text_sm: {
    fontSize: 14,
  },
  text_md: {
    fontSize: 16,
  },
  text_lg: {
    fontSize: 18,
  },
});
```

## Input Component with forwardRef

```typescript
// src/components/{{componentName}}.tsx
import { forwardRef } from 'react';
import {
  View,
  TextInput,
  Text,
  StyleSheet,
  TextInputProps,
  ViewStyle,
} from 'react-native';
import { Ionicons } from '@expo/vector-icons';

interface {{componentName}}Props extends TextInputProps {
  label?: string;
  error?: string;
  leftIcon?: keyof typeof Ionicons.glyphMap;
  rightIcon?: keyof typeof Ionicons.glyphMap;
  onRightIconPress?: () => void;
  containerStyle?: ViewStyle;
}

export const {{componentName}} = forwardRef<TextInput, {{componentName}}Props>(
  function {{componentName}}(
    {
      label,
      error,
      leftIcon,
      rightIcon,
      onRightIconPress,
      containerStyle,
      style,
      ...inputProps
    },
    ref
  ) {
    return (
      <View style={containerStyle}>
        {label && <Text style={styles.label}>{label}</Text>}
        <View style={[styles.inputContainer, error && styles.inputError]}>
          {leftIcon && (
            <Ionicons
              name={leftIcon}
              size={20}
              color="#666"
              style={styles.leftIcon}
            />
          )}
          <TextInput
            ref={ref}
            style={[styles.input, style]}
            placeholderTextColor="#999"
            accessibilityLabel={label}
            accessibilityHint={error}
            {...inputProps}
          />
          {rightIcon && (
            <Pressable onPress={onRightIconPress} style={styles.rightIcon}>
              <Ionicons name={rightIcon} size={20} color="#666" />
            </Pressable>
          )}
        </View>
        {error && <Text style={styles.error}>{error}</Text>}
      </View>
    );
  }
);

const styles = StyleSheet.create({
  label: {
    fontSize: 14,
    fontWeight: '500',
    color: '#000',
    marginBottom: 8,
  },
  inputContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#F2F2F7',
    borderRadius: 12,
    borderWidth: 1,
    borderColor: 'transparent',
  },
  inputError: {
    borderColor: '#FF3B30',
  },
  input: {
    flex: 1,
    paddingVertical: 14,
    paddingHorizontal: 16,
    fontSize: 16,
    color: '#000',
  },
  leftIcon: {
    marginLeft: 16,
  },
  rightIcon: {
    padding: 12,
  },
  error: {
    fontSize: 12,
    color: '#FF3B30',
    marginTop: 4,
  },
});
```

## Card Component

```typescript
// src/components/{{componentName}}.tsx
import { View, Text, Pressable, StyleSheet, ViewStyle } from 'react-native';
import { Image } from 'expo-image';

interface {{componentName}}Props {
  title: string;
  subtitle?: string;
  imageUrl?: string;
  onPress?: () => void;
  children?: React.ReactNode;
  style?: ViewStyle;
}

export function {{componentName}}({
  title,
  subtitle,
  imageUrl,
  onPress,
  children,
  style,
}: {{componentName}}Props) {
  const Container = onPress ? Pressable : View;

  return (
    <Container
      style={({ pressed }) => [
        styles.container,
        pressed && styles.pressed,
        style,
      ]}
      onPress={onPress}
      accessibilityRole={onPress ? 'button' : undefined}
    >
      {imageUrl && (
        <Image
          source={{ uri: imageUrl }}
          style={styles.image}
          contentFit="cover"
        />
      )}
      <View style={styles.content}>
        <Text style={styles.title} numberOfLines={2}>
          {title}
        </Text>
        {subtitle && (
          <Text style={styles.subtitle} numberOfLines={1}>
            {subtitle}
          </Text>
        )}
        {children}
      </View>
    </Container>
  );
}

const styles = StyleSheet.create({
  container: {
    backgroundColor: '#fff',
    borderRadius: 16,
    overflow: 'hidden',
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 8,
    elevation: 4,
  },
  pressed: {
    opacity: 0.9,
    transform: [{ scale: 0.98 }],
  },
  image: {
    width: '100%',
    height: 180,
  },
  content: {
    padding: 16,
  },
  title: {
    fontSize: 18,
    fontWeight: '600',
    color: '#000',
  },
  subtitle: {
    fontSize: 14,
    color: '#666',
    marginTop: 4,
  },
});
```

## List Item Component

```typescript
// src/components/{{componentName}}.tsx
import { View, Text, Pressable, StyleSheet } from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { Image } from 'expo-image';

interface {{componentName}}Props {
  title: string;
  subtitle?: string;
  leftIcon?: keyof typeof Ionicons.glyphMap;
  imageUrl?: string;
  rightText?: string;
  showChevron?: boolean;
  onPress?: () => void;
}

export function {{componentName}}({
  title,
  subtitle,
  leftIcon,
  imageUrl,
  rightText,
  showChevron = true,
  onPress,
}: {{componentName}}Props) {
  return (
    <Pressable
      style={({ pressed }) => [styles.container, pressed && styles.pressed]}
      onPress={onPress}
      disabled={!onPress}
      accessibilityRole="button"
    >
      {leftIcon && (
        <View style={styles.iconContainer}>
          <Ionicons name={leftIcon} size={24} color="#007AFF" />
        </View>
      )}
      {imageUrl && (
        <Image source={{ uri: imageUrl }} style={styles.image} />
      )}
      <View style={styles.content}>
        <Text style={styles.title}>{title}</Text>
        {subtitle && <Text style={styles.subtitle}>{subtitle}</Text>}
      </View>
      {rightText && <Text style={styles.rightText}>{rightText}</Text>}
      {showChevron && onPress && (
        <Ionicons name="chevron-forward" size={20} color="#C7C7CC" />
      )}
    </Pressable>
  );
}

const styles = StyleSheet.create({
  container: {
    flexDirection: 'row',
    alignItems: 'center',
    padding: 16,
    backgroundColor: '#fff',
    borderBottomWidth: 1,
    borderBottomColor: '#E5E5EA',
  },
  pressed: {
    backgroundColor: '#F2F2F7',
  },
  iconContainer: {
    width: 36,
    height: 36,
    borderRadius: 8,
    backgroundColor: '#E5E5EA',
    alignItems: 'center',
    justifyContent: 'center',
    marginRight: 12,
  },
  image: {
    width: 48,
    height: 48,
    borderRadius: 8,
    marginRight: 12,
  },
  content: {
    flex: 1,
  },
  title: {
    fontSize: 16,
    color: '#000',
  },
  subtitle: {
    fontSize: 14,
    color: '#666',
    marginTop: 2,
  },
  rightText: {
    fontSize: 16,
    color: '#666',
    marginRight: 8,
  },
});
```

## Usage

1. Replace `{{componentName}}` with component name
2. Adjust props interface as needed
3. Add to component exports in index file
4. Use throughout the app
