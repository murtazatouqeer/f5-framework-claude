---
name: rn-core-components
description: React Native core components and their usage
applies_to: react-native
---

# React Native Core Components

## View Components

### View

Basic container component, similar to `div` in web.

```typescript
import { View, StyleSheet } from 'react-native';

function Container({ children }: { children: React.ReactNode }) {
  return <View style={styles.container}>{children}</View>;
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    padding: 16,
    backgroundColor: '#fff',
  },
});
```

### SafeAreaView

Respects device safe areas (notches, home indicators).

```typescript
import { SafeAreaView, StyleSheet } from 'react-native';
// Or from expo
import { SafeAreaView } from 'react-native-safe-area-context';

function Screen({ children }: { children: React.ReactNode }) {
  return (
    <SafeAreaView style={styles.container} edges={['top', 'bottom']}>
      {children}
    </SafeAreaView>
  );
}
```

### ScrollView

Scrollable container for content.

```typescript
import { ScrollView, RefreshControl } from 'react-native';

function ScrollableContent() {
  const [refreshing, setRefreshing] = useState(false);

  const onRefresh = useCallback(async () => {
    setRefreshing(true);
    await fetchData();
    setRefreshing(false);
  }, []);

  return (
    <ScrollView
      contentContainerStyle={styles.content}
      showsVerticalScrollIndicator={false}
      keyboardShouldPersistTaps="handled"
      refreshControl={
        <RefreshControl refreshing={refreshing} onRefresh={onRefresh} />
      }
    >
      {/* Content */}
    </ScrollView>
  );
}
```

### KeyboardAvoidingView

Adjusts layout when keyboard is shown.

```typescript
import { KeyboardAvoidingView, Platform } from 'react-native';

function FormScreen() {
  return (
    <KeyboardAvoidingView
      style={styles.container}
      behavior={Platform.OS === 'ios' ? 'padding' : 'height'}
      keyboardVerticalOffset={Platform.OS === 'ios' ? 64 : 0}
    >
      {/* Form content */}
    </KeyboardAvoidingView>
  );
}
```

## Text Components

### Text

Display text content.

```typescript
import { Text, StyleSheet } from 'react-native';

function Typography() {
  return (
    <>
      <Text style={styles.heading}>Heading</Text>
      <Text style={styles.body}>Body text with{' '}
        <Text style={styles.bold}>bold</Text> and{' '}
        <Text style={styles.link} onPress={handlePress}>link</Text>
      </Text>
      <Text numberOfLines={2} ellipsizeMode="tail">
        Long text that will be truncated...
      </Text>
    </>
  );
}

const styles = StyleSheet.create({
  heading: {
    fontSize: 24,
    fontWeight: '700',
    color: '#000',
    marginBottom: 8,
  },
  body: {
    fontSize: 16,
    lineHeight: 24,
    color: '#333',
  },
  bold: {
    fontWeight: '600',
  },
  link: {
    color: '#007AFF',
    textDecorationLine: 'underline',
  },
});
```

### TextInput

User text input.

```typescript
import { TextInput, StyleSheet } from 'react-native';

function Input() {
  const [value, setValue] = useState('');

  return (
    <TextInput
      style={styles.input}
      value={value}
      onChangeText={setValue}
      placeholder="Enter text..."
      placeholderTextColor="#999"
      autoCapitalize="none"
      autoCorrect={false}
      keyboardType="email-address"
      returnKeyType="done"
      onSubmitEditing={handleSubmit}
      secureTextEntry={false} // true for password
      multiline={false}
      maxLength={100}
    />
  );
}

const styles = StyleSheet.create({
  input: {
    height: 48,
    borderWidth: 1,
    borderColor: '#e0e0e0',
    borderRadius: 8,
    paddingHorizontal: 16,
    fontSize: 16,
    backgroundColor: '#fff',
  },
});
```

## Touchable Components

### Pressable (Recommended)

Modern touchable component with more control.

```typescript
import { Pressable, Text, StyleSheet } from 'react-native';

function Button({ title, onPress, disabled }: ButtonProps) {
  return (
    <Pressable
      style={({ pressed }) => [
        styles.button,
        pressed && styles.pressed,
        disabled && styles.disabled,
      ]}
      onPress={onPress}
      disabled={disabled}
      android_ripple={{ color: 'rgba(0,0,0,0.1)' }}
    >
      <Text style={styles.text}>{title}</Text>
    </Pressable>
  );
}

const styles = StyleSheet.create({
  button: {
    backgroundColor: '#007AFF',
    paddingVertical: 12,
    paddingHorizontal: 24,
    borderRadius: 8,
    alignItems: 'center',
  },
  pressed: {
    opacity: 0.8,
  },
  disabled: {
    opacity: 0.5,
  },
  text: {
    color: '#fff',
    fontSize: 16,
    fontWeight: '600',
  },
});
```

### TouchableOpacity

Fades on press.

```typescript
import { TouchableOpacity } from 'react-native';

<TouchableOpacity
  activeOpacity={0.7}
  onPress={handlePress}
  onLongPress={handleLongPress}
>
  {/* Content */}
</TouchableOpacity>
```

## Image Components

### Image

Display local or remote images.

```typescript
import { Image, StyleSheet } from 'react-native';

function Avatar({ uri, size = 48 }: { uri: string; size?: number }) {
  return (
    <Image
      source={{ uri }}
      style={[styles.avatar, { width: size, height: size }]}
      resizeMode="cover"
      onError={(e) => console.log('Image error:', e.nativeEvent.error)}
      defaultSource={require('@/assets/placeholder.png')}
    />
  );
}

// Local image
<Image source={require('@/assets/logo.png')} />

const styles = StyleSheet.create({
  avatar: {
    borderRadius: 24,
    backgroundColor: '#e0e0e0',
  },
});
```

### expo-image (Recommended)

Better performance with caching.

```typescript
import { Image } from 'expo-image';

function OptimizedImage({ uri }: { uri: string }) {
  return (
    <Image
      source={uri}
      style={styles.image}
      contentFit="cover"
      placeholder={blurhash}
      transition={200}
      cachePolicy="memory-disk"
    />
  );
}
```

## List Components

### FlatList

Performant list for large data sets.

```typescript
import { FlatList } from 'react-native';

function ItemList({ data }: { data: Item[] }) {
  const renderItem = useCallback(
    ({ item }: { item: Item }) => <ItemCard item={item} />,
    []
  );

  return (
    <FlatList
      data={data}
      renderItem={renderItem}
      keyExtractor={(item) => item.id}
      ItemSeparatorComponent={() => <View style={styles.separator} />}
      ListHeaderComponent={<ListHeader />}
      ListFooterComponent={<ListFooter />}
      ListEmptyComponent={<EmptyState />}
      onEndReached={handleLoadMore}
      onEndReachedThreshold={0.5}
      refreshing={refreshing}
      onRefresh={handleRefresh}
      showsVerticalScrollIndicator={false}
      initialNumToRender={10}
      maxToRenderPerBatch={10}
      windowSize={5}
    />
  );
}
```

### FlashList (Recommended)

From Shopify, better performance than FlatList.

```typescript
import { FlashList } from '@shopify/flash-list';

function FastList({ data }: { data: Item[] }) {
  return (
    <FlashList
      data={data}
      renderItem={({ item }) => <ItemCard item={item} />}
      keyExtractor={(item) => item.id}
      estimatedItemSize={100} // Required for performance
      onEndReached={handleLoadMore}
      onEndReachedThreshold={0.5}
    />
  );
}
```

### SectionList

Grouped list with section headers.

```typescript
import { SectionList } from 'react-native';

const sections = [
  { title: 'A', data: ['Apple', 'Avocado'] },
  { title: 'B', data: ['Banana', 'Blueberry'] },
];

function GroupedList() {
  return (
    <SectionList
      sections={sections}
      renderItem={({ item }) => <Text>{item}</Text>}
      renderSectionHeader={({ section }) => (
        <Text style={styles.header}>{section.title}</Text>
      )}
      keyExtractor={(item, index) => item + index}
      stickySectionHeadersEnabled
    />
  );
}
```

## Modal Component

```typescript
import { Modal, View, Pressable, Text } from 'react-native';

function BottomSheet({ visible, onClose, children }: BottomSheetProps) {
  return (
    <Modal
      visible={visible}
      transparent
      animationType="slide"
      onRequestClose={onClose}
    >
      <Pressable style={styles.backdrop} onPress={onClose}>
        <View style={styles.content} onStartShouldSetResponder={() => true}>
          {children}
        </View>
      </Pressable>
    </Modal>
  );
}

const styles = StyleSheet.create({
  backdrop: {
    flex: 1,
    backgroundColor: 'rgba(0,0,0,0.5)',
    justifyContent: 'flex-end',
  },
  content: {
    backgroundColor: '#fff',
    borderTopLeftRadius: 20,
    borderTopRightRadius: 20,
    padding: 20,
    maxHeight: '80%',
  },
});
```

## Activity Indicator

```typescript
import { ActivityIndicator, View } from 'react-native';

function LoadingSpinner({ size = 'large' }: { size?: 'small' | 'large' }) {
  return (
    <View style={styles.container}>
      <ActivityIndicator size={size} color="#007AFF" />
    </View>
  );
}
```

## Switch Component

```typescript
import { Switch, View, Text } from 'react-native';

function Toggle({ value, onValueChange, label }: ToggleProps) {
  return (
    <View style={styles.row}>
      <Text>{label}</Text>
      <Switch
        value={value}
        onValueChange={onValueChange}
        trackColor={{ false: '#e0e0e0', true: '#81b0ff' }}
        thumbColor={value ? '#007AFF' : '#f4f3f4'}
        ios_backgroundColor="#e0e0e0"
      />
    </View>
  );
}
```

## Best Practices

1. **Use Pressable** over TouchableOpacity for new projects
2. **Use FlashList** for lists with 50+ items
3. **Use expo-image** for better image caching
4. **Memoize** list renderItem with useCallback
5. **Avoid inline styles** - use StyleSheet.create
6. **Test accessibility** with screen readers
