# Advanced Hook Patterns

## Overview

Advanced patterns and techniques for building robust, reusable hooks.

## Compound Hook Pattern

Combine multiple related hooks into a single, cohesive API.

```tsx
interface UseFormFieldReturn {
  value: string;
  error: string | null;
  touched: boolean;
  onChange: (e: React.ChangeEvent<HTMLInputElement>) => void;
  onBlur: () => void;
  reset: () => void;
  inputProps: {
    value: string;
    onChange: (e: React.ChangeEvent<HTMLInputElement>) => void;
    onBlur: () => void;
    'aria-invalid'?: boolean;
  };
}

function useFormField(
  initialValue = '',
  validate?: (value: string) => string | null
): UseFormFieldReturn {
  const [value, setValue] = useState(initialValue);
  const [error, setError] = useState<string | null>(null);
  const [touched, setTouched] = useState(false);

  const onChange = useCallback(
    (e: React.ChangeEvent<HTMLInputElement>) => {
      const newValue = e.target.value;
      setValue(newValue);
      if (validate && touched) {
        setError(validate(newValue));
      }
    },
    [validate, touched]
  );

  const onBlur = useCallback(() => {
    setTouched(true);
    if (validate) {
      setError(validate(value));
    }
  }, [validate, value]);

  const reset = useCallback(() => {
    setValue(initialValue);
    setError(null);
    setTouched(false);
  }, [initialValue]);

  const inputProps = useMemo(
    () => ({
      value,
      onChange,
      onBlur,
      ...(error && touched ? { 'aria-invalid': true } : {}),
    }),
    [value, onChange, onBlur, error, touched]
  );

  return { value, error, touched, onChange, onBlur, reset, inputProps };
}

// Usage
function LoginForm() {
  const email = useFormField('', (v) =>
    !v.includes('@') ? 'Invalid email' : null
  );
  const password = useFormField('', (v) =>
    v.length < 8 ? 'Password too short' : null
  );

  return (
    <form>
      <input {...email.inputProps} type="email" />
      {email.touched && email.error && <span>{email.error}</span>}

      <input {...password.inputProps} type="password" />
      {password.touched && password.error && <span>{password.error}</span>}
    </form>
  );
}
```

## State Machine Hook

Implement finite state machines for complex state logic.

```tsx
type MachineConfig<S extends string, E extends string> = {
  initial: S;
  states: {
    [K in S]: {
      on?: { [key in E]?: S };
      entry?: () => void;
      exit?: () => void;
    };
  };
};

function useStateMachine<S extends string, E extends string>(
  config: MachineConfig<S, E>
) {
  const [state, setState] = useState<S>(config.initial);
  const prevState = useRef<S>(config.initial);

  const transition = useCallback(
    (event: E) => {
      const currentState = config.states[state];
      const nextState = currentState.on?.[event];

      if (nextState && nextState !== state) {
        // Exit current state
        currentState.exit?.();

        // Enter next state
        config.states[nextState].entry?.();

        prevState.current = state;
        setState(nextState);
      }
    },
    [state, config]
  );

  const can = useCallback(
    (event: E): boolean => {
      return !!config.states[state].on?.[event];
    },
    [state, config]
  );

  return {
    state,
    previousState: prevState.current,
    transition,
    can,
  };
}

// Usage
type FetchState = 'idle' | 'loading' | 'success' | 'error';
type FetchEvent = 'FETCH' | 'RESOLVE' | 'REJECT' | 'RESET';

function useFetchMachine() {
  return useStateMachine<FetchState, FetchEvent>({
    initial: 'idle',
    states: {
      idle: {
        on: { FETCH: 'loading' },
      },
      loading: {
        on: { RESOLVE: 'success', REJECT: 'error' },
        entry: () => console.log('Loading started'),
      },
      success: {
        on: { RESET: 'idle', FETCH: 'loading' },
      },
      error: {
        on: { RESET: 'idle', FETCH: 'loading' },
      },
    },
  });
}
```

## Reducer with Middleware

Add middleware support to useReducer for logging, async, etc.

```tsx
type Middleware<S, A> = (
  getState: () => S,
  dispatch: React.Dispatch<A>
) => (next: React.Dispatch<A>) => React.Dispatch<A>;

function useReducerWithMiddleware<S, A>(
  reducer: React.Reducer<S, A>,
  initialState: S,
  middlewares: Middleware<S, A>[] = []
): [S, React.Dispatch<A>] {
  const [state, originalDispatch] = useReducer(reducer, initialState);
  const stateRef = useRef(state);

  useEffect(() => {
    stateRef.current = state;
  }, [state]);

  const getState = useCallback(() => stateRef.current, []);

  const dispatch = useMemo(() => {
    let composedDispatch = originalDispatch;

    for (let i = middlewares.length - 1; i >= 0; i--) {
      composedDispatch = middlewares[i](getState, originalDispatch)(composedDispatch);
    }

    return composedDispatch;
  }, [middlewares, getState, originalDispatch]);

  return [state, dispatch];
}

// Logger middleware
const loggerMiddleware: Middleware<any, any> = (getState) => (next) => (action) => {
  console.log('Previous state:', getState());
  console.log('Action:', action);
  next(action);
  console.log('Next state:', getState());
};

// Async middleware
const asyncMiddleware: Middleware<any, any> = (getState, dispatch) => (next) => (action) => {
  if (typeof action === 'function') {
    return action(dispatch, getState);
  }
  return next(action);
};
```

## Hook Factory Pattern

Create parameterized hooks with factories.

```tsx
function createResourceHook<T>(fetcher: () => Promise<T>) {
  return function useResource() {
    const [data, setData] = useState<T | null>(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<Error | null>(null);

    useEffect(() => {
      let cancelled = false;

      async function load() {
        try {
          const result = await fetcher();
          if (!cancelled) {
            setData(result);
            setError(null);
          }
        } catch (e) {
          if (!cancelled) {
            setError(e as Error);
          }
        } finally {
          if (!cancelled) {
            setLoading(false);
          }
        }
      }

      load();

      return () => {
        cancelled = true;
      };
    }, []);

    return { data, loading, error };
  };
}

// Create specific resource hooks
const useUsers = createResourceHook(() => fetch('/api/users').then(r => r.json()));
const useProducts = createResourceHook(() => fetch('/api/products').then(r => r.json()));
const useOrders = createResourceHook(() => fetch('/api/orders').then(r => r.json()));

// Usage
function UserList() {
  const { data: users, loading, error } = useUsers();
  // ...
}
```

## Hook Composition

Build complex hooks by composing simpler ones.

```tsx
// Base hooks
function useCounter(initial = 0) {
  const [count, setCount] = useState(initial);
  const increment = useCallback(() => setCount(c => c + 1), []);
  const decrement = useCallback(() => setCount(c => c - 1), []);
  const reset = useCallback(() => setCount(initial), [initial]);
  return { count, increment, decrement, reset };
}

function useBoolean(initial = false) {
  const [value, setValue] = useState(initial);
  const setTrue = useCallback(() => setValue(true), []);
  const setFalse = useCallback(() => setValue(false), []);
  const toggle = useCallback(() => setValue(v => !v), []);
  return { value, setTrue, setFalse, toggle };
}

// Composed hook
function usePagination({ totalItems, itemsPerPage = 10 }) {
  const { count: page, increment: nextPage, decrement: prevPage, reset } = useCounter(1);
  const { value: isLoading, setTrue: startLoading, setFalse: stopLoading } = useBoolean(false);

  const totalPages = Math.ceil(totalItems / itemsPerPage);
  const hasNextPage = page < totalPages;
  const hasPrevPage = page > 1;

  const goToPage = useCallback(
    (p: number) => {
      if (p >= 1 && p <= totalPages) {
        reset();
        for (let i = 1; i < p; i++) nextPage();
      }
    },
    [totalPages, reset, nextPage]
  );

  return {
    page,
    totalPages,
    hasNextPage,
    hasPrevPage,
    nextPage: hasNextPage ? nextPage : undefined,
    prevPage: hasPrevPage ? prevPage : undefined,
    goToPage,
    isLoading,
    startLoading,
    stopLoading,
  };
}
```

## Optimistic Update Pattern

Handle optimistic updates with rollback capability.

```tsx
interface UseOptimisticReturn<T> {
  data: T;
  optimisticUpdate: (updater: (prev: T) => T, commit: () => Promise<void>) => Promise<void>;
  isPending: boolean;
}

function useOptimistic<T>(initialData: T): UseOptimisticReturn<T> {
  const [data, setData] = useState<T>(initialData);
  const [isPending, setIsPending] = useState(false);
  const rollbackRef = useRef<T>(initialData);

  const optimisticUpdate = useCallback(
    async (updater: (prev: T) => T, commit: () => Promise<void>) => {
      rollbackRef.current = data;
      setData(updater);
      setIsPending(true);

      try {
        await commit();
      } catch (error) {
        // Rollback on error
        setData(rollbackRef.current);
        throw error;
      } finally {
        setIsPending(false);
      }
    },
    [data]
  );

  return { data, optimisticUpdate, isPending };
}

// Usage
function TodoList() {
  const { data: todos, optimisticUpdate, isPending } = useOptimistic<Todo[]>([]);

  const toggleTodo = async (id: string) => {
    await optimisticUpdate(
      (prev) => prev.map(t => t.id === id ? { ...t, done: !t.done } : t),
      () => api.toggleTodo(id)
    );
  };

  return (
    <ul className={isPending ? 'opacity-50' : ''}>
      {todos.map(todo => (
        <li key={todo.id} onClick={() => toggleTodo(todo.id)}>
          {todo.text}
        </li>
      ))}
    </ul>
  );
}
```

## Subscription Pattern

Handle external subscriptions cleanly.

```tsx
function useSubscription<T>(
  subscribe: (callback: (value: T) => void) => () => void,
  getSnapshot: () => T
): T {
  const [value, setValue] = useState<T>(getSnapshot);

  useEffect(() => {
    const unsubscribe = subscribe((newValue) => {
      setValue(newValue);
    });

    // Sync in case value changed between render and effect
    setValue(getSnapshot());

    return unsubscribe;
  }, [subscribe, getSnapshot]);

  return value;
}

// Usage with WebSocket
function useWebSocket<T>(url: string) {
  const wsRef = useRef<WebSocket | null>(null);
  const [lastMessage, setLastMessage] = useState<T | null>(null);

  useEffect(() => {
    const ws = new WebSocket(url);
    wsRef.current = ws;

    ws.onmessage = (event) => {
      setLastMessage(JSON.parse(event.data));
    };

    return () => {
      ws.close();
    };
  }, [url]);

  const send = useCallback((data: unknown) => {
    wsRef.current?.send(JSON.stringify(data));
  }, []);

  return { lastMessage, send };
}
```

## Best Practices Summary

1. **Keep hooks focused** - One concern per hook
2. **Use composition** - Build complex from simple
3. **Handle cleanup** - Always unsubscribe, clear timers
4. **Memoize appropriately** - useCallback, useMemo for stability
5. **TypeScript generics** - Make hooks flexible and type-safe
6. **Return stable references** - Prevent unnecessary re-renders
7. **Document dependencies** - Clear dependency arrays
8. **Test hooks** - Use @testing-library/react-hooks
