# React Hook Template

Production-ready custom hook templates for React applications.

## Basic State Hook

```tsx
// hooks/use{{HookName}}.ts
import { useState, useCallback, useMemo } from 'react';

interface Use{{HookName}}Options {
  initialValue?: string;
  validate?: (value: string) => string | null;
}

interface Use{{HookName}}Return {
  value: string;
  error: string | null;
  isValid: boolean;
  setValue: (value: string) => void;
  reset: () => void;
  validate: () => boolean;
}

export function use{{HookName}}(
  options: Use{{HookName}}Options = {}
): Use{{HookName}}Return {
  const { initialValue = '', validate: validateFn } = options;

  const [value, setValueState] = useState(initialValue);
  const [error, setError] = useState<string | null>(null);

  const setValue = useCallback((newValue: string) => {
    setValueState(newValue);
    setError(null);
  }, []);

  const reset = useCallback(() => {
    setValueState(initialValue);
    setError(null);
  }, [initialValue]);

  const validate = useCallback(() => {
    if (!validateFn) return true;
    const validationError = validateFn(value);
    setError(validationError);
    return validationError === null;
  }, [value, validateFn]);

  const isValid = error === null && value.length > 0;

  return useMemo(
    () => ({
      value,
      error,
      isValid,
      setValue,
      reset,
      validate,
    }),
    [value, error, isValid, setValue, reset, validate]
  );
}
```

## Async Data Hook

```tsx
// hooks/useAsync.ts
import { useState, useCallback, useEffect, useRef } from 'react';

type AsyncStatus = 'idle' | 'pending' | 'success' | 'error';

interface UseAsyncState<T> {
  status: AsyncStatus;
  data: T | null;
  error: Error | null;
  isIdle: boolean;
  isPending: boolean;
  isSuccess: boolean;
  isError: boolean;
}

interface UseAsyncReturn<T> extends UseAsyncState<T> {
  execute: () => Promise<T | void>;
  reset: () => void;
}

export function useAsync<T>(
  asyncFunction: () => Promise<T>,
  options: {
    immediate?: boolean;
    onSuccess?: (data: T) => void;
    onError?: (error: Error) => void;
  } = {}
): UseAsyncReturn<T> {
  const { immediate = false, onSuccess, onError } = options;

  const [state, setState] = useState<UseAsyncState<T>>({
    status: 'idle',
    data: null,
    error: null,
    isIdle: true,
    isPending: false,
    isSuccess: false,
    isError: false,
  });

  const isMountedRef = useRef(true);

  const execute = useCallback(async () => {
    setState({
      status: 'pending',
      data: null,
      error: null,
      isIdle: false,
      isPending: true,
      isSuccess: false,
      isError: false,
    });

    try {
      const data = await asyncFunction();

      if (!isMountedRef.current) return;

      setState({
        status: 'success',
        data,
        error: null,
        isIdle: false,
        isPending: false,
        isSuccess: true,
        isError: false,
      });

      onSuccess?.(data);
      return data;
    } catch (error) {
      if (!isMountedRef.current) return;

      const err = error instanceof Error ? error : new Error(String(error));

      setState({
        status: 'error',
        data: null,
        error: err,
        isIdle: false,
        isPending: false,
        isSuccess: false,
        isError: true,
      });

      onError?.(err);
    }
  }, [asyncFunction, onSuccess, onError]);

  const reset = useCallback(() => {
    setState({
      status: 'idle',
      data: null,
      error: null,
      isIdle: true,
      isPending: false,
      isSuccess: false,
      isError: false,
    });
  }, []);

  useEffect(() => {
    if (immediate) {
      execute();
    }
  }, [immediate, execute]);

  useEffect(() => {
    return () => {
      isMountedRef.current = false;
    };
  }, []);

  return { ...state, execute, reset };
}
```

## API Query Hook

```tsx
// hooks/useQuery.ts
import { useState, useEffect, useCallback, useRef } from 'react';

interface UseQueryOptions<T> {
  enabled?: boolean;
  refetchOnWindowFocus?: boolean;
  refetchInterval?: number;
  staleTime?: number;
  cacheTime?: number;
  onSuccess?: (data: T) => void;
  onError?: (error: Error) => void;
  select?: (data: any) => T;
  retry?: number | boolean;
  retryDelay?: number;
}

interface UseQueryReturn<T> {
  data: T | undefined;
  error: Error | null;
  isLoading: boolean;
  isFetching: boolean;
  isError: boolean;
  isSuccess: boolean;
  refetch: () => Promise<void>;
}

// Simple cache implementation
const cache = new Map<string, { data: any; timestamp: number }>();

export function useQuery<T>(
  queryKey: string | string[],
  queryFn: () => Promise<T>,
  options: UseQueryOptions<T> = {}
): UseQueryReturn<T> {
  const {
    enabled = true,
    refetchOnWindowFocus = true,
    refetchInterval,
    staleTime = 0,
    cacheTime = 5 * 60 * 1000, // 5 minutes
    onSuccess,
    onError,
    select,
    retry = 3,
    retryDelay = 1000,
  } = options;

  const key = Array.isArray(queryKey) ? queryKey.join('-') : queryKey;

  const [state, setState] = useState<{
    data: T | undefined;
    error: Error | null;
    isLoading: boolean;
    isFetching: boolean;
  }>(() => {
    const cached = cache.get(key);
    if (cached && Date.now() - cached.timestamp < cacheTime) {
      return {
        data: select ? select(cached.data) : cached.data,
        error: null,
        isLoading: false,
        isFetching: false,
      };
    }
    return {
      data: undefined,
      error: null,
      isLoading: true,
      isFetching: true,
    };
  });

  const retryCountRef = useRef(0);
  const abortControllerRef = useRef<AbortController | null>(null);

  const fetchData = useCallback(
    async (isInitial = false) => {
      // Check cache
      const cached = cache.get(key);
      const isStale = !cached || Date.now() - cached.timestamp > staleTime;

      if (cached && !isStale) {
        setState((prev) => ({
          ...prev,
          data: select ? select(cached.data) : cached.data,
          isLoading: false,
          isFetching: false,
        }));
        return;
      }

      // Cancel previous request
      abortControllerRef.current?.abort();
      abortControllerRef.current = new AbortController();

      setState((prev) => ({
        ...prev,
        isLoading: isInitial && !cached,
        isFetching: true,
      }));

      try {
        const data = await queryFn();
        const selectedData = select ? select(data) : data;

        cache.set(key, { data, timestamp: Date.now() });

        setState({
          data: selectedData,
          error: null,
          isLoading: false,
          isFetching: false,
        });

        onSuccess?.(selectedData);
        retryCountRef.current = 0;
      } catch (error) {
        if (error instanceof Error && error.name === 'AbortError') {
          return;
        }

        const maxRetries = typeof retry === 'boolean' ? (retry ? 3 : 0) : retry;

        if (retryCountRef.current < maxRetries) {
          retryCountRef.current++;
          setTimeout(() => fetchData(isInitial), retryDelay);
          return;
        }

        const err = error instanceof Error ? error : new Error(String(error));

        setState((prev) => ({
          ...prev,
          error: err,
          isLoading: false,
          isFetching: false,
        }));

        onError?.(err);
        retryCountRef.current = 0;
      }
    },
    [key, queryFn, select, staleTime, retry, retryDelay, onSuccess, onError]
  );

  // Initial fetch
  useEffect(() => {
    if (enabled) {
      fetchData(true);
    }

    return () => {
      abortControllerRef.current?.abort();
    };
  }, [enabled, fetchData]);

  // Refetch on window focus
  useEffect(() => {
    if (!refetchOnWindowFocus || !enabled) return;

    const handleFocus = () => {
      fetchData();
    };

    window.addEventListener('focus', handleFocus);
    return () => window.removeEventListener('focus', handleFocus);
  }, [refetchOnWindowFocus, enabled, fetchData]);

  // Refetch interval
  useEffect(() => {
    if (!refetchInterval || !enabled) return;

    const interval = setInterval(() => fetchData(), refetchInterval);
    return () => clearInterval(interval);
  }, [refetchInterval, enabled, fetchData]);

  const refetch = useCallback(() => fetchData(), [fetchData]);

  return {
    ...state,
    isError: state.error !== null,
    isSuccess: state.data !== undefined && state.error === null,
    refetch,
  };
}
```

## Mutation Hook

```tsx
// hooks/useMutation.ts
import { useState, useCallback, useRef } from 'react';

interface UseMutationOptions<TData, TVariables> {
  onSuccess?: (data: TData, variables: TVariables) => void;
  onError?: (error: Error, variables: TVariables) => void;
  onSettled?: (
    data: TData | undefined,
    error: Error | null,
    variables: TVariables
  ) => void;
}

interface UseMutationReturn<TData, TVariables> {
  data: TData | undefined;
  error: Error | null;
  isLoading: boolean;
  isError: boolean;
  isSuccess: boolean;
  mutate: (variables: TVariables) => void;
  mutateAsync: (variables: TVariables) => Promise<TData>;
  reset: () => void;
}

export function useMutation<TData, TVariables>(
  mutationFn: (variables: TVariables) => Promise<TData>,
  options: UseMutationOptions<TData, TVariables> = {}
): UseMutationReturn<TData, TVariables> {
  const { onSuccess, onError, onSettled } = options;

  const [state, setState] = useState<{
    data: TData | undefined;
    error: Error | null;
    isLoading: boolean;
  }>({
    data: undefined,
    error: null,
    isLoading: false,
  });

  const isMountedRef = useRef(true);

  const mutateAsync = useCallback(
    async (variables: TVariables): Promise<TData> => {
      setState({ data: undefined, error: null, isLoading: true });

      try {
        const data = await mutationFn(variables);

        if (!isMountedRef.current) return data;

        setState({ data, error: null, isLoading: false });
        onSuccess?.(data, variables);
        onSettled?.(data, null, variables);
        return data;
      } catch (error) {
        const err = error instanceof Error ? error : new Error(String(error));

        if (!isMountedRef.current) throw err;

        setState({ data: undefined, error: err, isLoading: false });
        onError?.(err, variables);
        onSettled?.(undefined, err, variables);
        throw err;
      }
    },
    [mutationFn, onSuccess, onError, onSettled]
  );

  const mutate = useCallback(
    (variables: TVariables) => {
      mutateAsync(variables).catch(() => {
        // Error is already handled in mutateAsync
      });
    },
    [mutateAsync]
  );

  const reset = useCallback(() => {
    setState({ data: undefined, error: null, isLoading: false });
  }, []);

  return {
    ...state,
    isError: state.error !== null,
    isSuccess: state.data !== undefined && !state.isLoading,
    mutate,
    mutateAsync,
    reset,
  };
}
```

## Pagination Hook

```tsx
// hooks/usePagination.ts
import { useState, useMemo, useCallback } from 'react';

interface UsePaginationOptions {
  totalItems: number;
  initialPage?: number;
  initialPageSize?: number;
  siblingCount?: number;
}

interface UsePaginationReturn {
  currentPage: number;
  pageSize: number;
  totalPages: number;
  startIndex: number;
  endIndex: number;
  hasPreviousPage: boolean;
  hasNextPage: boolean;
  pages: (number | 'ellipsis')[];
  setPage: (page: number) => void;
  setPageSize: (size: number) => void;
  nextPage: () => void;
  previousPage: () => void;
  firstPage: () => void;
  lastPage: () => void;
}

export function usePagination(
  options: UsePaginationOptions
): UsePaginationReturn {
  const {
    totalItems,
    initialPage = 1,
    initialPageSize = 10,
    siblingCount = 1,
  } = options;

  const [currentPage, setCurrentPage] = useState(initialPage);
  const [pageSize, setPageSizeState] = useState(initialPageSize);

  const totalPages = Math.ceil(totalItems / pageSize);

  // Ensure current page is valid
  const validCurrentPage = Math.min(Math.max(1, currentPage), totalPages || 1);

  const startIndex = (validCurrentPage - 1) * pageSize;
  const endIndex = Math.min(startIndex + pageSize - 1, totalItems - 1);

  const pages = useMemo(() => {
    const range = (start: number, end: number): number[] => {
      const length = end - start + 1;
      return Array.from({ length }, (_, i) => start + i);
    };

    const totalPageNumbers = siblingCount * 2 + 5;

    if (totalPageNumbers >= totalPages) {
      return range(1, totalPages);
    }

    const leftSiblingIndex = Math.max(validCurrentPage - siblingCount, 1);
    const rightSiblingIndex = Math.min(
      validCurrentPage + siblingCount,
      totalPages
    );

    const shouldShowLeftDots = leftSiblingIndex > 2;
    const shouldShowRightDots = rightSiblingIndex < totalPages - 1;

    if (!shouldShowLeftDots && shouldShowRightDots) {
      const leftItemCount = 3 + 2 * siblingCount;
      const leftRange = range(1, leftItemCount);
      return [...leftRange, 'ellipsis' as const, totalPages];
    }

    if (shouldShowLeftDots && !shouldShowRightDots) {
      const rightItemCount = 3 + 2 * siblingCount;
      const rightRange = range(totalPages - rightItemCount + 1, totalPages);
      return [1, 'ellipsis' as const, ...rightRange];
    }

    if (shouldShowLeftDots && shouldShowRightDots) {
      const middleRange = range(leftSiblingIndex, rightSiblingIndex);
      return [
        1,
        'ellipsis' as const,
        ...middleRange,
        'ellipsis' as const,
        totalPages,
      ];
    }

    return range(1, totalPages);
  }, [totalPages, validCurrentPage, siblingCount]);

  const setPage = useCallback(
    (page: number) => {
      const newPage = Math.min(Math.max(1, page), totalPages || 1);
      setCurrentPage(newPage);
    },
    [totalPages]
  );

  const setPageSize = useCallback(
    (size: number) => {
      setPageSizeState(size);
      setCurrentPage(1);
    },
    []
  );

  const nextPage = useCallback(() => {
    setPage(validCurrentPage + 1);
  }, [validCurrentPage, setPage]);

  const previousPage = useCallback(() => {
    setPage(validCurrentPage - 1);
  }, [validCurrentPage, setPage]);

  const firstPage = useCallback(() => {
    setPage(1);
  }, [setPage]);

  const lastPage = useCallback(() => {
    setPage(totalPages);
  }, [totalPages, setPage]);

  return {
    currentPage: validCurrentPage,
    pageSize,
    totalPages,
    startIndex,
    endIndex,
    hasPreviousPage: validCurrentPage > 1,
    hasNextPage: validCurrentPage < totalPages,
    pages,
    setPage,
    setPageSize,
    nextPage,
    previousPage,
    firstPage,
    lastPage,
  };
}
```

## Intersection Observer Hook

```tsx
// hooks/useIntersectionObserver.ts
import { useState, useEffect, useRef, type RefObject } from 'react';

interface UseIntersectionObserverOptions {
  threshold?: number | number[];
  root?: Element | null;
  rootMargin?: string;
  freezeOnceVisible?: boolean;
}

interface UseIntersectionObserverReturn {
  ref: RefObject<HTMLElement>;
  isIntersecting: boolean;
  entry: IntersectionObserverEntry | undefined;
}

export function useIntersectionObserver(
  options: UseIntersectionObserverOptions = {}
): UseIntersectionObserverReturn {
  const {
    threshold = 0,
    root = null,
    rootMargin = '0%',
    freezeOnceVisible = false,
  } = options;

  const ref = useRef<HTMLElement>(null);
  const [entry, setEntry] = useState<IntersectionObserverEntry>();

  const frozen = entry?.isIntersecting && freezeOnceVisible;

  useEffect(() => {
    const node = ref.current;

    if (!node || frozen) return;

    const observer = new IntersectionObserver(
      ([entry]) => {
        setEntry(entry);
      },
      { threshold, root, rootMargin }
    );

    observer.observe(node);

    return () => {
      observer.disconnect();
    };
  }, [threshold, root, rootMargin, frozen]);

  return {
    ref,
    isIntersecting: entry?.isIntersecting ?? false,
    entry,
  };
}

// Usage for infinite scroll
export function useInfiniteScroll(
  onLoadMore: () => void,
  hasMore: boolean,
  isLoading: boolean
) {
  const { ref, isIntersecting } = useIntersectionObserver({
    threshold: 0.1,
  });

  useEffect(() => {
    if (isIntersecting && hasMore && !isLoading) {
      onLoadMore();
    }
  }, [isIntersecting, hasMore, isLoading, onLoadMore]);

  return ref;
}
```

## Hook Testing Template

```tsx
// hooks/__tests__/use{{HookName}}.test.ts
import { renderHook, act, waitFor } from '@testing-library/react';
import { use{{HookName}} } from '../use{{HookName}}';

describe('use{{HookName}}', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  describe('initialization', () => {
    it('returns initial state', () => {
      const { result } = renderHook(() => use{{HookName}}());

      expect(result.current.value).toBe('');
      expect(result.current.error).toBeNull();
      expect(result.current.isValid).toBe(false);
    });

    it('accepts initial value', () => {
      const { result } = renderHook(() =>
        use{{HookName}}({ initialValue: 'test' })
      );

      expect(result.current.value).toBe('test');
    });
  });

  describe('state updates', () => {
    it('updates value when setValue is called', () => {
      const { result } = renderHook(() => use{{HookName}}());

      act(() => {
        result.current.setValue('new value');
      });

      expect(result.current.value).toBe('new value');
    });

    it('resets to initial value', () => {
      const { result } = renderHook(() =>
        use{{HookName}}({ initialValue: 'initial' })
      );

      act(() => {
        result.current.setValue('changed');
      });

      act(() => {
        result.current.reset();
      });

      expect(result.current.value).toBe('initial');
    });
  });

  describe('validation', () => {
    it('validates value using provided function', () => {
      const validate = jest.fn((value: string) =>
        value.length < 3 ? 'Too short' : null
      );

      const { result } = renderHook(() =>
        use{{HookName}}({ validate })
      );

      act(() => {
        result.current.setValue('ab');
      });

      act(() => {
        result.current.validate();
      });

      expect(result.current.error).toBe('Too short');
      expect(result.current.isValid).toBe(false);
    });
  });

  describe('async operations', () => {
    it('handles async state correctly', async () => {
      const { result } = renderHook(() => use{{HookName}}());

      act(() => {
        result.current.fetchData();
      });

      expect(result.current.isLoading).toBe(true);

      await waitFor(() => {
        expect(result.current.isLoading).toBe(false);
      });

      expect(result.current.data).toBeDefined();
    });
  });

  describe('memoization', () => {
    it('maintains stable function references', () => {
      const { result, rerender } = renderHook(() => use{{HookName}}());

      const { setValue: firstSetValue, reset: firstReset } = result.current;

      rerender();

      expect(result.current.setValue).toBe(firstSetValue);
      expect(result.current.reset).toBe(firstReset);
    });
  });

  describe('cleanup', () => {
    it('cancels pending operations on unmount', () => {
      const { result, unmount } = renderHook(() => use{{HookName}}());

      act(() => {
        result.current.fetchData();
      });

      unmount();

      // No error should be thrown
    });
  });
});
```
