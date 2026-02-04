---
name: vue-vueuse
description: VueUse utility library patterns
applies_to: vue
---

# VueUse Library

## Overview

VueUse is a collection of essential Vue Composition utilities.
It provides 200+ composables for common tasks.

## Installation

```bash
npm install @vueuse/core
```

## Common Utilities

### State

```typescript
import {
  useStorage,
  useLocalStorage,
  useSessionStorage,
  useRefHistory,
  useDebouncedRef,
  useThrottledRef,
} from '@vueuse/core';

// Reactive localStorage
const state = useLocalStorage('my-key', { count: 0 });
state.value.count++;

// With serializer
const data = useStorage('key', null, undefined, {
  serializer: {
    read: (v) => v ? JSON.parse(v) : null,
    write: (v) => JSON.stringify(v),
  },
});

// History tracking with undo/redo
const counter = ref(0);
const { history, undo, redo, canUndo, canRedo } = useRefHistory(counter);

// Debounced ref
const search = useDebouncedRef('', 500);

// Throttled ref
const scrollY = useThrottledRef(0, 100);
```

### Elements

```typescript
import {
  useElementSize,
  useElementVisibility,
  useIntersectionObserver,
  useMutationObserver,
  useResizeObserver,
  useScroll,
  useScrollLock,
} from '@vueuse/core';

const el = ref<HTMLElement | null>(null);

// Element size
const { width, height } = useElementSize(el);

// Visibility in viewport
const isVisible = useElementVisibility(el);

// Intersection observer
const { stop } = useIntersectionObserver(
  el,
  ([{ isIntersecting }]) => {
    console.log('Intersecting:', isIntersecting);
  },
  { threshold: 0.5 }
);

// Resize observer
useResizeObserver(el, (entries) => {
  const entry = entries[0];
  console.log('Size:', entry.contentRect);
});

// Scroll position
const { x, y, isScrolling, arrivedState } = useScroll(el);

// Lock scroll
const isLocked = useScrollLock(document.body);
```

### Browser

```typescript
import {
  useClipboard,
  usePermission,
  useShare,
  useFullscreen,
  useTitle,
  useFavicon,
  usePreferredDark,
  usePreferredLanguages,
  useMediaQuery,
  useBreakpoints,
  breakpointsTailwind,
} from '@vueuse/core';

// Clipboard
const { copy, copied, isSupported } = useClipboard();
await copy('Hello!');

// Share API
const { share, isSupported: shareSupported } = useShare();
await share({ title: 'Hello', url: location.href });

// Fullscreen
const { isFullscreen, enter, exit, toggle } = useFullscreen();

// Document title
const title = useTitle('My App');
title.value = 'New Title';

// Favicon
const icon = useFavicon();
icon.value = '/new-icon.png';

// Media queries
const isDark = usePreferredDark();
const isMobile = useMediaQuery('(max-width: 768px)');

// Breakpoints
const breakpoints = useBreakpoints(breakpointsTailwind);
const smAndLarger = breakpoints.greaterOrEqual('sm');
const mdAndSmaller = breakpoints.smallerOrEqual('md');
```

### Sensors

```typescript
import {
  useMouse,
  useMousePressed,
  useKeyModifier,
  useKeyPressed,
  useMagicKeys,
  useDeviceOrientation,
  useDeviceMotion,
  useGeolocation,
  useIdle,
  useNetwork,
  useOnline,
  useBattery,
} from '@vueuse/core';

// Mouse position
const { x, y, sourceType } = useMouse();

// Mouse pressed state
const { pressed } = useMousePressed();

// Keyboard
const ctrl = useKeyModifier('Control');
const { pressed: spacePressed } = useKeyPressed('Space');

// Magic keys (combinations)
const { current, ctrl_s, shift_ctrl_a } = useMagicKeys();

// Geolocation
const { coords, locatedAt, error } = useGeolocation();

// Network status
const { isOnline, offlineAt, downlink, type } = useNetwork();

// Idle detection
const { idle, lastActive } = useIdle(5 * 60 * 1000); // 5 minutes

// Battery
const { charging, level, chargingTime } = useBattery();
```

### Network

```typescript
import {
  useFetch,
  useEventSource,
  useWebSocket,
} from '@vueuse/core';

// Fetch with reactive URL
const url = ref('/api/users');
const { data, error, isFetching, execute } = useFetch(url, {
  immediate: false,
  refetch: true,
}).json();

// With options
const { data: postData } = useFetch('/api/posts')
  .post({ title: 'Hello' })
  .json();

// Server-Sent Events
const { data: sseData, status, close } = useEventSource('/events');

// WebSocket
const { status: wsStatus, data: wsData, send, close: wsClose } = useWebSocket(
  'wss://example.com/socket',
  {
    autoReconnect: true,
    heartbeat: {
      message: 'ping',
      interval: 1000,
    },
  }
);
```

### Animation

```typescript
import {
  useTransition,
  useInterval,
  useTimeout,
  useTimestamp,
  useRafFn,
  useNow,
} from '@vueuse/core';

// Smooth transitions
const source = ref(0);
const output = useTransition(source, {
  duration: 1000,
  transition: [0.75, 0, 0.25, 1], // Easing
});
source.value = 100; // Will animate

// Interval
const { counter, pause, resume } = useInterval(1000, {
  controls: true,
});

// Timeout
const { ready, start, stop } = useTimeout(3000, {
  controls: true,
});

// Request Animation Frame
const { pause: pauseRaf, resume: resumeRaf } = useRafFn(() => {
  // Animation frame callback
});

// Current timestamp
const { timestamp } = useTimestamp({ controls: true });
const now = useNow();
```

### Utilities

```typescript
import {
  watchDebounced,
  watchThrottled,
  watchOnce,
  watchPausable,
  whenever,
  until,
  useCycleList,
  useToggle,
  computedAsync,
  computedWithControl,
} from '@vueuse/core';

// Debounced watch
watchDebounced(
  source,
  () => {
    console.log('Debounced');
  },
  { debounce: 500 }
);

// Throttled watch
watchThrottled(source, callback, { throttle: 500 });

// Watch once
watchOnce(source, callback);

// Pausable watch
const { pause, resume } = watchPausable(source, callback);

// Whenever (watch for truthy)
whenever(isReady, () => {
  console.log('Ready!');
});

// Until (promise-based)
await until(isReady).toBe(true);
await until(count).toMatch((v) => v > 5);

// Cycle through list
const { state, next, prev } = useCycleList(['A', 'B', 'C']);

// Async computed
const userInfo = computedAsync(async () => {
  return await fetchUserInfo(userId.value);
}, null);
```

### Component Utilities

```typescript
import {
  useVModel,
  useVModels,
  useFocusTrap,
  useActiveElement,
  templateRef,
  unrefElement,
} from '@vueuse/core';

// v-model helper
const props = defineProps<{ modelValue: string }>();
const emit = defineEmits<{ (e: 'update:modelValue', v: string): void }>();

const value = useVModel(props, 'modelValue', emit);
// Now use value.value directly

// Multiple v-models
const props2 = defineProps<{ firstName: string; lastName: string }>();
const { firstName, lastName } = useVModels(props2);

// Focus trap for modals
const target = ref<HTMLElement | null>(null);
useFocusTrap(target);

// Active element tracking
const activeElement = useActiveElement();
```

## Best Practices

1. **Import only what you need** - Tree-shakeable
2. **Check `isSupported`** - Browser API availability
3. **Use with controls** - For pause/resume capabilities
4. **Combine composables** - Build complex features
5. **Handle errors** - Network composables may fail
