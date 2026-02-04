# Redux Toolkit

## Overview

The official, opinionated Redux toolkit for efficient Redux development.

## Store Configuration

```tsx
// store/index.ts
import { configureStore } from '@reduxjs/toolkit';
import { useDispatch, useSelector, TypedUseSelectorHook } from 'react-redux';
import userReducer from './slices/userSlice';
import cartReducer from './slices/cartSlice';
import { api } from './api';

export const store = configureStore({
  reducer: {
    user: userReducer,
    cart: cartReducer,
    [api.reducerPath]: api.reducer,
  },
  middleware: (getDefaultMiddleware) =>
    getDefaultMiddleware().concat(api.middleware),
});

// Types
export type RootState = ReturnType<typeof store.getState>;
export type AppDispatch = typeof store.dispatch;

// Typed hooks
export const useAppDispatch = () => useDispatch<AppDispatch>();
export const useAppSelector: TypedUseSelectorHook<RootState> = useSelector;
```

## Creating Slices

```tsx
// store/slices/userSlice.ts
import { createSlice, PayloadAction, createAsyncThunk } from '@reduxjs/toolkit';

interface User {
  id: string;
  name: string;
  email: string;
}

interface UserState {
  currentUser: User | null;
  isLoading: boolean;
  error: string | null;
}

const initialState: UserState = {
  currentUser: null,
  isLoading: false,
  error: null,
};

// Async thunk
export const fetchUser = createAsyncThunk(
  'user/fetchUser',
  async (userId: string, { rejectWithValue }) => {
    try {
      const response = await fetch(`/api/users/${userId}`);
      if (!response.ok) throw new Error('Failed to fetch user');
      return await response.json();
    } catch (error) {
      return rejectWithValue((error as Error).message);
    }
  }
);

export const loginUser = createAsyncThunk(
  'user/login',
  async (
    credentials: { email: string; password: string },
    { rejectWithValue }
  ) => {
    try {
      const response = await fetch('/api/auth/login', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(credentials),
      });
      if (!response.ok) throw new Error('Login failed');
      return await response.json();
    } catch (error) {
      return rejectWithValue((error as Error).message);
    }
  }
);

const userSlice = createSlice({
  name: 'user',
  initialState,
  reducers: {
    setUser: (state, action: PayloadAction<User>) => {
      state.currentUser = action.payload;
    },
    clearUser: (state) => {
      state.currentUser = null;
    },
    updateUserProfile: (state, action: PayloadAction<Partial<User>>) => {
      if (state.currentUser) {
        state.currentUser = { ...state.currentUser, ...action.payload };
      }
    },
  },
  extraReducers: (builder) => {
    builder
      // fetchUser
      .addCase(fetchUser.pending, (state) => {
        state.isLoading = true;
        state.error = null;
      })
      .addCase(fetchUser.fulfilled, (state, action) => {
        state.isLoading = false;
        state.currentUser = action.payload;
      })
      .addCase(fetchUser.rejected, (state, action) => {
        state.isLoading = false;
        state.error = action.payload as string;
      })
      // loginUser
      .addCase(loginUser.pending, (state) => {
        state.isLoading = true;
        state.error = null;
      })
      .addCase(loginUser.fulfilled, (state, action) => {
        state.isLoading = false;
        state.currentUser = action.payload.user;
      })
      .addCase(loginUser.rejected, (state, action) => {
        state.isLoading = false;
        state.error = action.payload as string;
      });
  },
});

export const { setUser, clearUser, updateUserProfile } = userSlice.actions;
export default userSlice.reducer;
```

## Cart Slice with Immer

```tsx
// store/slices/cartSlice.ts
import { createSlice, PayloadAction } from '@reduxjs/toolkit';

interface CartItem {
  id: string;
  name: string;
  price: number;
  quantity: number;
}

interface CartState {
  items: CartItem[];
  total: number;
}

const initialState: CartState = {
  items: [],
  total: 0,
};

const calculateTotal = (items: CartItem[]): number =>
  items.reduce((sum, item) => sum + item.price * item.quantity, 0);

const cartSlice = createSlice({
  name: 'cart',
  initialState,
  reducers: {
    addItem: (state, action: PayloadAction<Omit<CartItem, 'quantity'>>) => {
      const existingItem = state.items.find(
        (item) => item.id === action.payload.id
      );
      if (existingItem) {
        existingItem.quantity += 1;
      } else {
        state.items.push({ ...action.payload, quantity: 1 });
      }
      state.total = calculateTotal(state.items);
    },
    removeItem: (state, action: PayloadAction<string>) => {
      state.items = state.items.filter((item) => item.id !== action.payload);
      state.total = calculateTotal(state.items);
    },
    updateQuantity: (
      state,
      action: PayloadAction<{ id: string; quantity: number }>
    ) => {
      const item = state.items.find((item) => item.id === action.payload.id);
      if (item) {
        item.quantity = action.payload.quantity;
        state.total = calculateTotal(state.items);
      }
    },
    clearCart: (state) => {
      state.items = [];
      state.total = 0;
    },
  },
});

export const { addItem, removeItem, updateQuantity, clearCart } =
  cartSlice.actions;
export default cartSlice.reducer;
```

## RTK Query

```tsx
// store/api/index.ts
import { createApi, fetchBaseQuery } from '@reduxjs/toolkit/query/react';

interface Product {
  id: string;
  name: string;
  price: number;
  description: string;
}

export const api = createApi({
  reducerPath: 'api',
  baseQuery: fetchBaseQuery({
    baseUrl: '/api',
    prepareHeaders: (headers, { getState }) => {
      const token = (getState() as RootState).user.token;
      if (token) {
        headers.set('authorization', `Bearer ${token}`);
      }
      return headers;
    },
  }),
  tagTypes: ['Product', 'User'],
  endpoints: (builder) => ({
    // Queries
    getProducts: builder.query<Product[], void>({
      query: () => '/products',
      providesTags: (result) =>
        result
          ? [
              ...result.map(({ id }) => ({ type: 'Product' as const, id })),
              { type: 'Product', id: 'LIST' },
            ]
          : [{ type: 'Product', id: 'LIST' }],
    }),
    getProduct: builder.query<Product, string>({
      query: (id) => `/products/${id}`,
      providesTags: (result, error, id) => [{ type: 'Product', id }],
    }),

    // Mutations
    createProduct: builder.mutation<Product, Omit<Product, 'id'>>({
      query: (body) => ({
        url: '/products',
        method: 'POST',
        body,
      }),
      invalidatesTags: [{ type: 'Product', id: 'LIST' }],
    }),
    updateProduct: builder.mutation<Product, Partial<Product> & { id: string }>({
      query: ({ id, ...body }) => ({
        url: `/products/${id}`,
        method: 'PATCH',
        body,
      }),
      invalidatesTags: (result, error, { id }) => [{ type: 'Product', id }],
    }),
    deleteProduct: builder.mutation<void, string>({
      query: (id) => ({
        url: `/products/${id}`,
        method: 'DELETE',
      }),
      invalidatesTags: (result, error, id) => [{ type: 'Product', id }],
    }),
  }),
});

export const {
  useGetProductsQuery,
  useGetProductQuery,
  useCreateProductMutation,
  useUpdateProductMutation,
  useDeleteProductMutation,
} = api;
```

## Usage in Components

```tsx
// components/ProductList.tsx
import { useAppSelector, useAppDispatch } from '../store';
import { addItem } from '../store/slices/cartSlice';
import { useGetProductsQuery } from '../store/api';

function ProductList() {
  const dispatch = useAppDispatch();
  const { data: products, isLoading, error, refetch } = useGetProductsQuery();
  const cartItems = useAppSelector((state) => state.cart.items);

  if (isLoading) return <Spinner />;
  if (error) return <Error onRetry={refetch} />;

  return (
    <div className="grid grid-cols-3 gap-4">
      {products?.map((product) => {
        const inCart = cartItems.some((item) => item.id === product.id);
        return (
          <ProductCard
            key={product.id}
            product={product}
            inCart={inCart}
            onAddToCart={() =>
              dispatch(
                addItem({
                  id: product.id,
                  name: product.name,
                  price: product.price,
                })
              )
            }
          />
        );
      })}
    </div>
  );
}
```

## Selectors

```tsx
// store/selectors.ts
import { createSelector } from '@reduxjs/toolkit';
import { RootState } from './index';

// Basic selector
export const selectCartItems = (state: RootState) => state.cart.items;
export const selectCartTotal = (state: RootState) => state.cart.total;
export const selectCurrentUser = (state: RootState) => state.user.currentUser;

// Memoized selector
export const selectCartItemCount = createSelector(
  [selectCartItems],
  (items) => items.reduce((sum, item) => sum + item.quantity, 0)
);

// Parameterized selector
export const selectCartItemById = createSelector(
  [selectCartItems, (state: RootState, id: string) => id],
  (items, id) => items.find((item) => item.id === id)
);

// Usage
function CartSummary() {
  const itemCount = useAppSelector(selectCartItemCount);
  const total = useAppSelector(selectCartTotal);

  return (
    <div>
      <span>{itemCount} items</span>
      <span>${total}</span>
    </div>
  );
}
```

## Provider Setup

```tsx
// main.tsx
import { Provider } from 'react-redux';
import { store } from './store';

function App() {
  return (
    <Provider store={store}>
      <Router>
        <Routes />
      </Router>
    </Provider>
  );
}
```

## Best Practices

1. **Use RTK Query for API** - Automatic caching and invalidation
2. **Create typed hooks** - useAppDispatch, useAppSelector
3. **Use createSelector** - Memoize derived state
4. **Normalize state** - Use entity adapters for collections
5. **Keep slices focused** - One slice per domain
6. **Leverage Immer** - Write "mutating" logic safely
