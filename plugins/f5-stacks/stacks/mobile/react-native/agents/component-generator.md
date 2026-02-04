---
name: rn-component-generator
description: Generate reusable React Native components with TypeScript and accessibility
triggers:
  - "rn component"
  - "react native component"
  - "create component"
  - "generate component"
applies_to: react-native
---

# React Native Component Generator

## Purpose

Generate production-ready React Native components with:
- TypeScript props interface
- forwardRef support when needed
- Accessibility props
- Variant and size support
- StyleSheet optimization
- Platform-specific handling

## Input Requirements

```yaml
required:
  - component_name: string    # e.g., "Button", "Card", "Input"
  - category: ui | form | layout | feedback

optional:
  - variants: string[]        # e.g., ["primary", "secondary", "outline"]
  - sizes: string[]           # e.g., ["sm", "md", "lg"]
  - has_icon: boolean
  - has_loading: boolean
  - is_pressable: boolean
  - platform_specific: boolean
```

## Generation Templates

### UI Component Template

```typescript
// src/components/ui/{{ComponentName}}.tsx
import { forwardRef, type ReactNode } from 'react';
import {
  View,
  Text,
  Pressable,
  StyleSheet,
  ActivityIndicator,
  type ViewStyle,
  type TextStyle,
  type PressableProps,
} from 'react-native';

type Variant = 'primary' | 'secondary' | 'outline' | 'ghost';
type Size = 'sm' | 'md' | 'lg';

interface {{ComponentName}}Props extends Omit<PressableProps, 'style'> {
  /** Component variant */
  variant?: Variant;
  /** Component size */
  size?: Size;
  /** Display text */
  title?: string;
  /** Left icon element */
  leftIcon?: ReactNode;
  /** Right icon element */
  rightIcon?: ReactNode;
  /** Loading state */
  isLoading?: boolean;
  /** Full width mode */
  fullWidth?: boolean;
  /** Custom container style */
  style?: ViewStyle;
  /** Custom text style */
  textStyle?: TextStyle;
  /** Children content */
  children?: ReactNode;
  /** Test ID for testing */
  testID?: string;
}

export const {{ComponentName}} = forwardRef<View, {{ComponentName}}Props>(
  (
    {
      variant = 'primary',
      size = 'md',
      title,
      leftIcon,
      rightIcon,
      isLoading = false,
      fullWidth = false,
      disabled,
      style,
      textStyle,
      children,
      testID,
      ...props
    },
    ref
  ) => {
    const isDisabled = disabled || isLoading;

    return (
      <Pressable
        ref={ref}
        disabled={isDisabled}
        style={({ pressed }) => [
          styles.base,
          styles[variant],
          styles[`${size}Container`],
          fullWidth && styles.fullWidth,
          pressed && styles.pressed,
          isDisabled && styles.disabled,
          style,
        ]}
        accessibilityRole="button"
        accessibilityState={{ disabled: isDisabled }}
        testID={testID}
        {...props}
      >
        {isLoading ? (
          <ActivityIndicator
            size="small"
            color={variant === 'primary' ? '#fff' : '#007AFF'}
          />
        ) : (
          <>
            {leftIcon && <View style={styles.iconLeft}>{leftIcon}</View>}
            {title ? (
              <Text
                style={[
                  styles.text,
                  styles[`${variant}Text`],
                  styles[`${size}Text`],
                  textStyle,
                ]}
              >
                {title}
              </Text>
            ) : (
              children
            )}
            {rightIcon && <View style={styles.iconRight}>{rightIcon}</View>}
          </>
        )}
      </Pressable>
    );
  }
);

{{ComponentName}}.displayName = '{{ComponentName}}';

const styles = StyleSheet.create({
  base: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    borderRadius: 8,
  },
  fullWidth: {
    width: '100%',
  },
  pressed: {
    opacity: 0.8,
  },
  disabled: {
    opacity: 0.5,
  },

  // Variants
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
  ghost: {
    backgroundColor: 'transparent',
  },

  // Sizes
  smContainer: {
    paddingHorizontal: 12,
    paddingVertical: 6,
    minHeight: 32,
  },
  mdContainer: {
    paddingHorizontal: 16,
    paddingVertical: 10,
    minHeight: 44,
  },
  lgContainer: {
    paddingHorizontal: 24,
    paddingVertical: 14,
    minHeight: 52,
  },

  // Text
  text: {
    fontWeight: '600',
  },
  primaryText: {
    color: '#fff',
  },
  secondaryText: {
    color: '#000',
  },
  outlineText: {
    color: '#007AFF',
  },
  ghostText: {
    color: '#007AFF',
  },
  smText: {
    fontSize: 14,
  },
  mdText: {
    fontSize: 16,
  },
  lgText: {
    fontSize: 18,
  },

  // Icons
  iconLeft: {
    marginRight: 8,
  },
  iconRight: {
    marginLeft: 8,
  },
});
```

### Card Component Template

```typescript
// src/components/ui/Card.tsx
import { type ReactNode } from 'react';
import {
  View,
  Pressable,
  StyleSheet,
  type ViewStyle,
  type PressableProps,
} from 'react-native';

interface CardProps extends Omit<PressableProps, 'style'> {
  /** Card content */
  children: ReactNode;
  /** Custom style */
  style?: ViewStyle;
  /** Padding size */
  padding?: 'none' | 'sm' | 'md' | 'lg';
  /** Shadow elevation */
  elevation?: 'none' | 'sm' | 'md' | 'lg';
  /** Make card pressable */
  pressable?: boolean;
  /** Test ID */
  testID?: string;
}

export function Card({
  children,
  style,
  padding = 'md',
  elevation = 'sm',
  pressable = false,
  testID,
  ...props
}: CardProps) {
  const content = (
    <View
      style={[
        styles.base,
        styles[`padding${padding.charAt(0).toUpperCase() + padding.slice(1)}`],
        styles[`elevation${elevation.charAt(0).toUpperCase() + elevation.slice(1)}`],
        style,
      ]}
      testID={testID}
    >
      {children}
    </View>
  );

  if (pressable) {
    return (
      <Pressable
        style={({ pressed }) => [pressed && styles.pressed]}
        {...props}
      >
        {content}
      </Pressable>
    );
  }

  return content;
}

const styles = StyleSheet.create({
  base: {
    backgroundColor: '#fff',
    borderRadius: 12,
    overflow: 'hidden',
  },
  pressed: {
    opacity: 0.9,
  },

  // Padding
  paddingNone: {
    padding: 0,
  },
  paddingSm: {
    padding: 8,
  },
  paddingMd: {
    padding: 16,
  },
  paddingLg: {
    padding: 24,
  },

  // Elevation
  elevationNone: {
    shadowOpacity: 0,
    elevation: 0,
  },
  elevationSm: {
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 1 },
    shadowOpacity: 0.1,
    shadowRadius: 2,
    elevation: 2,
  },
  elevationMd: {
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.15,
    shadowRadius: 4,
    elevation: 4,
  },
  elevationLg: {
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.2,
    shadowRadius: 8,
    elevation: 8,
  },
});
```

### Input Component Template

```typescript
// src/components/ui/Input.tsx
import { forwardRef, useState } from 'react';
import {
  View,
  Text,
  TextInput,
  StyleSheet,
  type TextInputProps,
  type ViewStyle,
} from 'react-native';

interface InputProps extends TextInputProps {
  /** Input label */
  label?: string;
  /** Error message */
  error?: string;
  /** Helper text */
  helperText?: string;
  /** Left icon */
  leftIcon?: React.ReactNode;
  /** Right icon */
  rightIcon?: React.ReactNode;
  /** Container style */
  containerStyle?: ViewStyle;
  /** Full width */
  fullWidth?: boolean;
}

export const Input = forwardRef<TextInput, InputProps>(
  (
    {
      label,
      error,
      helperText,
      leftIcon,
      rightIcon,
      containerStyle,
      fullWidth = true,
      style,
      ...props
    },
    ref
  ) => {
    const [isFocused, setIsFocused] = useState(false);
    const hasError = !!error;

    return (
      <View style={[styles.container, fullWidth && styles.fullWidth, containerStyle]}>
        {label && <Text style={styles.label}>{label}</Text>}

        <View
          style={[
            styles.inputContainer,
            isFocused && styles.inputFocused,
            hasError && styles.inputError,
          ]}
        >
          {leftIcon && <View style={styles.iconLeft}>{leftIcon}</View>}

          <TextInput
            ref={ref}
            style={[styles.input, style]}
            placeholderTextColor="#999"
            onFocus={(e) => {
              setIsFocused(true);
              props.onFocus?.(e);
            }}
            onBlur={(e) => {
              setIsFocused(false);
              props.onBlur?.(e);
            }}
            {...props}
          />

          {rightIcon && <View style={styles.iconRight}>{rightIcon}</View>}
        </View>

        {(error || helperText) && (
          <Text style={[styles.helperText, hasError && styles.errorText]}>
            {error || helperText}
          </Text>
        )}
      </View>
    );
  }
);

Input.displayName = 'Input';

const styles = StyleSheet.create({
  container: {
    marginBottom: 16,
  },
  fullWidth: {
    width: '100%',
  },
  label: {
    fontSize: 14,
    fontWeight: '500',
    color: '#333',
    marginBottom: 6,
  },
  inputContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#f5f5f5',
    borderRadius: 8,
    borderWidth: 1,
    borderColor: '#e0e0e0',
    paddingHorizontal: 12,
  },
  inputFocused: {
    borderColor: '#007AFF',
    backgroundColor: '#fff',
  },
  inputError: {
    borderColor: '#ff3b30',
  },
  input: {
    flex: 1,
    height: 44,
    fontSize: 16,
    color: '#000',
  },
  iconLeft: {
    marginRight: 8,
  },
  iconRight: {
    marginLeft: 8,
  },
  helperText: {
    fontSize: 12,
    color: '#666',
    marginTop: 4,
  },
  errorText: {
    color: '#ff3b30',
  },
});
```

## Output Files

```
src/components/
├── ui/
│   ├── {{ComponentName}}.tsx
│   └── __tests__/
│       └── {{ComponentName}}.test.tsx
└── index.ts  # Export barrel
```

## Best Practices

1. **TypeScript**: Strong prop types with JSDoc comments
2. **forwardRef**: Use when component wraps focusable elements
3. **Accessibility**: Always include accessibilityRole and accessibilityState
4. **Composition**: Support children prop for flexible content
5. **Variants**: Use discriminated unions for variant props
6. **Testing**: Include testID prop for test automation
