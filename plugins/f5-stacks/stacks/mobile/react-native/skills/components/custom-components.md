---
name: rn-custom-components
description: Building custom reusable components in React Native
applies_to: react-native
---

# Custom Components in React Native

## Component Design Principles

1. **Single Responsibility**: Each component does one thing well
2. **Composition**: Build complex UIs from simple components
3. **Props over State**: Prefer controlled components
4. **TypeScript First**: Strong typing for all props
5. **Accessibility**: Include a11y props by default

## Basic Component Pattern

```typescript
// src/components/ui/Button.tsx
import { forwardRef } from 'react';
import {
  Pressable,
  Text,
  ActivityIndicator,
  StyleSheet,
  type PressableProps,
  type ViewStyle,
  type TextStyle,
} from 'react-native';

type Variant = 'primary' | 'secondary' | 'outline' | 'ghost' | 'destructive';
type Size = 'sm' | 'md' | 'lg';

interface ButtonProps extends Omit<PressableProps, 'style'> {
  /** Button text */
  title: string;
  /** Visual variant */
  variant?: Variant;
  /** Size preset */
  size?: Size;
  /** Loading state */
  isLoading?: boolean;
  /** Full width */
  fullWidth?: boolean;
  /** Left icon */
  leftIcon?: React.ReactNode;
  /** Right icon */
  rightIcon?: React.ReactNode;
  /** Container style override */
  style?: ViewStyle;
  /** Text style override */
  textStyle?: TextStyle;
}

export const Button = forwardRef<typeof Pressable, ButtonProps>(
  (
    {
      title,
      variant = 'primary',
      size = 'md',
      isLoading = false,
      fullWidth = false,
      leftIcon,
      rightIcon,
      disabled,
      style,
      textStyle,
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
          variantStyles[variant].container,
          sizeStyles[size].container,
          fullWidth && styles.fullWidth,
          pressed && styles.pressed,
          isDisabled && styles.disabled,
          style,
        ]}
        accessibilityRole="button"
        accessibilityState={{ disabled: isDisabled }}
        {...props}
      >
        {isLoading ? (
          <ActivityIndicator
            size="small"
            color={variantStyles[variant].loadingColor}
          />
        ) : (
          <>
            {leftIcon}
            <Text
              style={[
                styles.text,
                variantStyles[variant].text,
                sizeStyles[size].text,
                leftIcon && styles.textWithLeftIcon,
                rightIcon && styles.textWithRightIcon,
                textStyle,
              ]}
            >
              {title}
            </Text>
            {rightIcon}
          </>
        )}
      </Pressable>
    );
  }
);

Button.displayName = 'Button';

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
    transform: [{ scale: 0.98 }],
  },
  disabled: {
    opacity: 0.5,
  },
  text: {
    fontWeight: '600',
  },
  textWithLeftIcon: {
    marginLeft: 8,
  },
  textWithRightIcon: {
    marginRight: 8,
  },
});

const variantStyles = {
  primary: {
    container: { backgroundColor: '#007AFF' },
    text: { color: '#fff' },
    loadingColor: '#fff',
  },
  secondary: {
    container: { backgroundColor: '#E5E5EA' },
    text: { color: '#000' },
    loadingColor: '#000',
  },
  outline: {
    container: { backgroundColor: 'transparent', borderWidth: 1, borderColor: '#007AFF' },
    text: { color: '#007AFF' },
    loadingColor: '#007AFF',
  },
  ghost: {
    container: { backgroundColor: 'transparent' },
    text: { color: '#007AFF' },
    loadingColor: '#007AFF',
  },
  destructive: {
    container: { backgroundColor: '#FF3B30' },
    text: { color: '#fff' },
    loadingColor: '#fff',
  },
};

const sizeStyles = {
  sm: {
    container: { paddingVertical: 8, paddingHorizontal: 12, minHeight: 36 },
    text: { fontSize: 14 },
  },
  md: {
    container: { paddingVertical: 12, paddingHorizontal: 16, minHeight: 44 },
    text: { fontSize: 16 },
  },
  lg: {
    container: { paddingVertical: 16, paddingHorizontal: 24, minHeight: 52 },
    text: { fontSize: 18 },
  },
};
```

## Card Component

```typescript
// src/components/ui/Card.tsx
import { View, StyleSheet, type ViewStyle } from 'react-native';

interface CardProps {
  children: React.ReactNode;
  style?: ViewStyle;
  padding?: 'none' | 'sm' | 'md' | 'lg';
  elevation?: 'none' | 'sm' | 'md' | 'lg';
}

export function Card({
  children,
  style,
  padding = 'md',
  elevation = 'sm',
}: CardProps) {
  return (
    <View
      style={[
        styles.base,
        paddingStyles[padding],
        elevationStyles[elevation],
        style,
      ]}
    >
      {children}
    </View>
  );
}

const styles = StyleSheet.create({
  base: {
    backgroundColor: '#fff',
    borderRadius: 12,
    overflow: 'hidden',
  },
});

const paddingStyles = StyleSheet.create({
  none: { padding: 0 },
  sm: { padding: 8 },
  md: { padding: 16 },
  lg: { padding: 24 },
});

const elevationStyles = StyleSheet.create({
  none: {},
  sm: {
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 1 },
    shadowOpacity: 0.1,
    shadowRadius: 2,
    elevation: 2,
  },
  md: {
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.15,
    shadowRadius: 4,
    elevation: 4,
  },
  lg: {
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.2,
    shadowRadius: 8,
    elevation: 8,
  },
});
```

## Avatar Component

```typescript
// src/components/ui/Avatar.tsx
import { View, Text, StyleSheet } from 'react-native';
import { Image } from 'expo-image';

type Size = 'xs' | 'sm' | 'md' | 'lg' | 'xl';

interface AvatarProps {
  source?: string;
  name?: string;
  size?: Size;
  style?: ViewStyle;
}

const SIZES: Record<Size, number> = {
  xs: 24,
  sm: 32,
  md: 40,
  lg: 56,
  xl: 80,
};

export function Avatar({ source, name, size = 'md', style }: AvatarProps) {
  const dimension = SIZES[size];
  const initials = name
    ?.split(' ')
    .map((n) => n[0])
    .join('')
    .toUpperCase()
    .slice(0, 2);

  if (source) {
    return (
      <Image
        source={source}
        style={[
          styles.image,
          { width: dimension, height: dimension, borderRadius: dimension / 2 },
          style,
        ]}
        contentFit="cover"
        transition={200}
      />
    );
  }

  return (
    <View
      style={[
        styles.placeholder,
        { width: dimension, height: dimension, borderRadius: dimension / 2 },
        style,
      ]}
    >
      <Text style={[styles.initials, { fontSize: dimension * 0.4 }]}>
        {initials || '?'}
      </Text>
    </View>
  );
}

const styles = StyleSheet.create({
  image: {
    backgroundColor: '#e0e0e0',
  },
  placeholder: {
    backgroundColor: '#007AFF',
    alignItems: 'center',
    justifyContent: 'center',
  },
  initials: {
    color: '#fff',
    fontWeight: '600',
  },
});
```

## Badge Component

```typescript
// src/components/ui/Badge.tsx
import { View, Text, StyleSheet } from 'react-native';

type Variant = 'default' | 'success' | 'warning' | 'error' | 'info';

interface BadgeProps {
  label: string;
  variant?: Variant;
}

export function Badge({ label, variant = 'default' }: BadgeProps) {
  return (
    <View style={[styles.container, variantStyles[variant].container]}>
      <Text style={[styles.text, variantStyles[variant].text]}>{label}</Text>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    paddingHorizontal: 8,
    paddingVertical: 4,
    borderRadius: 12,
  },
  text: {
    fontSize: 12,
    fontWeight: '500',
  },
});

const variantStyles = {
  default: {
    container: { backgroundColor: '#E5E5EA' },
    text: { color: '#000' },
  },
  success: {
    container: { backgroundColor: '#D1FAE5' },
    text: { color: '#065F46' },
  },
  warning: {
    container: { backgroundColor: '#FEF3C7' },
    text: { color: '#92400E' },
  },
  error: {
    container: { backgroundColor: '#FEE2E2' },
    text: { color: '#991B1B' },
  },
  info: {
    container: { backgroundColor: '#DBEAFE' },
    text: { color: '#1E40AF' },
  },
};
```

## Empty State Component

```typescript
// src/components/ui/EmptyState.tsx
import { View, Text, StyleSheet } from 'react-native';
import { Button } from './Button';

interface EmptyStateProps {
  icon?: React.ReactNode;
  title: string;
  description?: string;
  actionLabel?: string;
  onAction?: () => void;
  testID?: string;
}

export function EmptyState({
  icon,
  title,
  description,
  actionLabel,
  onAction,
  testID,
}: EmptyStateProps) {
  return (
    <View style={styles.container} testID={testID}>
      {icon && <View style={styles.iconContainer}>{icon}</View>}
      <Text style={styles.title}>{title}</Text>
      {description && <Text style={styles.description}>{description}</Text>}
      {actionLabel && onAction && (
        <Button
          title={actionLabel}
          onPress={onAction}
          variant="primary"
          style={styles.button}
        />
      )}
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    alignItems: 'center',
    justifyContent: 'center',
    padding: 32,
  },
  iconContainer: {
    marginBottom: 16,
  },
  title: {
    fontSize: 18,
    fontWeight: '600',
    color: '#000',
    textAlign: 'center',
    marginBottom: 8,
  },
  description: {
    fontSize: 14,
    color: '#666',
    textAlign: 'center',
    marginBottom: 24,
  },
  button: {
    minWidth: 120,
  },
});
```

## Skeleton Component

```typescript
// src/components/ui/Skeleton.tsx
import { useEffect } from 'react';
import { View, StyleSheet, type ViewStyle } from 'react-native';
import Animated, {
  useAnimatedStyle,
  useSharedValue,
  withRepeat,
  withTiming,
} from 'react-native-reanimated';

interface SkeletonProps {
  width?: number | string;
  height?: number;
  borderRadius?: number;
  style?: ViewStyle;
}

export function Skeleton({
  width = '100%',
  height = 20,
  borderRadius = 4,
  style,
}: SkeletonProps) {
  const opacity = useSharedValue(0.3);

  useEffect(() => {
    opacity.value = withRepeat(
      withTiming(0.7, { duration: 1000 }),
      -1,
      true
    );
  }, [opacity]);

  const animatedStyle = useAnimatedStyle(() => ({
    opacity: opacity.value,
  }));

  return (
    <Animated.View
      style={[
        styles.skeleton,
        { width, height, borderRadius },
        animatedStyle,
        style,
      ]}
    />
  );
}

const styles = StyleSheet.create({
  skeleton: {
    backgroundColor: '#E0E0E0',
  },
});

// Skeleton variants
export function SkeletonText({ lines = 3 }: { lines?: number }) {
  return (
    <View style={skeletonStyles.textContainer}>
      {Array.from({ length: lines }).map((_, i) => (
        <Skeleton
          key={i}
          height={16}
          width={i === lines - 1 ? '60%' : '100%'}
          style={skeletonStyles.line}
        />
      ))}
    </View>
  );
}

export function SkeletonCard() {
  return (
    <View style={skeletonStyles.card}>
      <Skeleton height={150} borderRadius={8} />
      <View style={skeletonStyles.cardContent}>
        <Skeleton height={20} width="80%" />
        <Skeleton height={16} width="40%" style={skeletonStyles.line} />
      </View>
    </View>
  );
}

const skeletonStyles = StyleSheet.create({
  textContainer: {
    gap: 8,
  },
  line: {
    marginTop: 8,
  },
  card: {
    backgroundColor: '#fff',
    borderRadius: 12,
    overflow: 'hidden',
  },
  cardContent: {
    padding: 16,
  },
});
```

## Compound Component Pattern

```typescript
// src/components/ui/List.tsx
import { View, Text, Pressable, StyleSheet, type ViewStyle } from 'react-native';
import { createContext, useContext } from 'react';

// Context for compound components
const ListContext = createContext<{ variant: 'default' | 'inset' }>({
  variant: 'default',
});

// Root component
interface ListProps {
  children: React.ReactNode;
  variant?: 'default' | 'inset';
  style?: ViewStyle;
}

function ListRoot({ children, variant = 'default', style }: ListProps) {
  return (
    <ListContext.Provider value={{ variant }}>
      <View style={[styles.list, variant === 'inset' && styles.inset, style]}>
        {children}
      </View>
    </ListContext.Provider>
  );
}

// Item component
interface ListItemProps {
  title: string;
  subtitle?: string;
  leftIcon?: React.ReactNode;
  rightIcon?: React.ReactNode;
  onPress?: () => void;
}

function ListItem({
  title,
  subtitle,
  leftIcon,
  rightIcon,
  onPress,
}: ListItemProps) {
  const { variant } = useContext(ListContext);
  const content = (
    <>
      {leftIcon && <View style={styles.leftIcon}>{leftIcon}</View>}
      <View style={styles.textContainer}>
        <Text style={styles.title}>{title}</Text>
        {subtitle && <Text style={styles.subtitle}>{subtitle}</Text>}
      </View>
      {rightIcon && <View style={styles.rightIcon}>{rightIcon}</View>}
    </>
  );

  if (onPress) {
    return (
      <Pressable
        style={({ pressed }) => [styles.item, pressed && styles.pressed]}
        onPress={onPress}
      >
        {content}
      </Pressable>
    );
  }

  return <View style={styles.item}>{content}</View>;
}

// Separator component
function ListSeparator() {
  const { variant } = useContext(ListContext);
  return (
    <View
      style={[
        styles.separator,
        variant === 'inset' && styles.separatorInset,
      ]}
    />
  );
}

// Export as compound component
export const List = Object.assign(ListRoot, {
  Item: ListItem,
  Separator: ListSeparator,
});

// Usage:
// <List variant="inset">
//   <List.Item title="Settings" onPress={...} />
//   <List.Separator />
//   <List.Item title="Profile" onPress={...} />
// </List>

const styles = StyleSheet.create({
  list: {
    backgroundColor: '#fff',
  },
  inset: {
    marginHorizontal: 16,
    borderRadius: 10,
    overflow: 'hidden',
  },
  item: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingVertical: 12,
    paddingHorizontal: 16,
    minHeight: 44,
  },
  pressed: {
    backgroundColor: '#f0f0f0',
  },
  leftIcon: {
    marginRight: 12,
  },
  rightIcon: {
    marginLeft: 12,
  },
  textContainer: {
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
  separator: {
    height: StyleSheet.hairlineWidth,
    backgroundColor: '#E0E0E0',
  },
  separatorInset: {
    marginLeft: 16,
  },
});
```
