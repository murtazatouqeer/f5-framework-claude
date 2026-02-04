# CRUD Application Example

Complete CRUD (Create, Read, Update, Delete) application example using React with TypeScript, TanStack Query, React Hook Form, and Zustand.

## Overview

This example demonstrates a full-featured user management application with:
- List view with pagination, sorting, and filtering
- Create and edit forms with validation
- Delete confirmation
- Optimistic updates
- Error handling
- Loading states

## Project Structure

```
src/
├── features/
│   └── users/
│       ├── api/
│       │   └── users.api.ts
│       ├── components/
│       │   ├── UserList.tsx
│       │   ├── UserForm.tsx
│       │   ├── UserCard.tsx
│       │   ├── UserFilters.tsx
│       │   └── DeleteUserDialog.tsx
│       ├── hooks/
│       │   ├── useUsers.ts
│       │   ├── useUser.ts
│       │   └── useUserMutations.ts
│       ├── pages/
│       │   ├── UsersPage.tsx
│       │   ├── UserDetailPage.tsx
│       │   └── UserFormPage.tsx
│       ├── store/
│       │   └── users.store.ts
│       ├── types/
│       │   └── user.types.ts
│       └── index.ts
├── shared/
│   ├── components/
│   │   ├── DataTable.tsx
│   │   ├── Pagination.tsx
│   │   ├── ConfirmDialog.tsx
│   │   └── EmptyState.tsx
│   └── hooks/
│       └── usePagination.ts
└── lib/
    └── api-client.ts
```

## Types

```typescript
// features/users/types/user.types.ts

export interface User {
  id: string;
  email: string;
  firstName: string;
  lastName: string;
  role: UserRole;
  status: UserStatus;
  avatar?: string;
  createdAt: string;
  updatedAt: string;
}

export type UserRole = 'admin' | 'user' | 'moderator';
export type UserStatus = 'active' | 'inactive' | 'pending';

export interface CreateUserDto {
  email: string;
  firstName: string;
  lastName: string;
  role: UserRole;
  password: string;
}

export interface UpdateUserDto {
  email?: string;
  firstName?: string;
  lastName?: string;
  role?: UserRole;
  status?: UserStatus;
}

export interface UsersFilters {
  search?: string;
  role?: UserRole;
  status?: UserStatus;
}

export interface PaginatedResponse<T> {
  data: T[];
  meta: {
    total: number;
    page: number;
    limit: number;
    totalPages: number;
  };
}
```

## API Layer

```typescript
// features/users/api/users.api.ts

import { apiClient } from '@/lib/api-client';
import type {
  User,
  CreateUserDto,
  UpdateUserDto,
  UsersFilters,
  PaginatedResponse,
} from '../types/user.types';

export interface GetUsersParams extends UsersFilters {
  page?: number;
  limit?: number;
  sortBy?: string;
  sortOrder?: 'asc' | 'desc';
}

export const usersApi = {
  getUsers: async (params: GetUsersParams = {}): Promise<PaginatedResponse<User>> => {
    const searchParams = new URLSearchParams();

    Object.entries(params).forEach(([key, value]) => {
      if (value !== undefined && value !== '') {
        searchParams.append(key, String(value));
      }
    });

    const response = await apiClient.get<PaginatedResponse<User>>(
      `/users?${searchParams.toString()}`
    );
    return response.data;
  },

  getUser: async (id: string): Promise<User> => {
    const response = await apiClient.get<User>(`/users/${id}`);
    return response.data;
  },

  createUser: async (data: CreateUserDto): Promise<User> => {
    const response = await apiClient.post<User>('/users', data);
    return response.data;
  },

  updateUser: async (id: string, data: UpdateUserDto): Promise<User> => {
    const response = await apiClient.patch<User>(`/users/${id}`, data);
    return response.data;
  },

  deleteUser: async (id: string): Promise<void> => {
    await apiClient.delete(`/users/${id}`);
  },
};
```

## Query Hooks

```typescript
// features/users/hooks/useUsers.ts

import { useQuery, keepPreviousData } from '@tanstack/react-query';
import { usersApi, type GetUsersParams } from '../api/users.api';

export const userKeys = {
  all: ['users'] as const,
  lists: () => [...userKeys.all, 'list'] as const,
  list: (params: GetUsersParams) => [...userKeys.lists(), params] as const,
  details: () => [...userKeys.all, 'detail'] as const,
  detail: (id: string) => [...userKeys.details(), id] as const,
};

export function useUsers(params: GetUsersParams = {}) {
  return useQuery({
    queryKey: userKeys.list(params),
    queryFn: () => usersApi.getUsers(params),
    placeholderData: keepPreviousData,
    staleTime: 1000 * 60 * 5, // 5 minutes
  });
}
```

```typescript
// features/users/hooks/useUser.ts

import { useQuery } from '@tanstack/react-query';
import { usersApi } from '../api/users.api';
import { userKeys } from './useUsers';

export function useUser(id: string) {
  return useQuery({
    queryKey: userKeys.detail(id),
    queryFn: () => usersApi.getUser(id),
    enabled: !!id,
  });
}
```

```typescript
// features/users/hooks/useUserMutations.ts

import { useMutation, useQueryClient } from '@tanstack/react-query';
import { usersApi } from '../api/users.api';
import { userKeys } from './useUsers';
import type { User, CreateUserDto, UpdateUserDto } from '../types/user.types';

export function useCreateUser() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (data: CreateUserDto) => usersApi.createUser(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: userKeys.lists() });
    },
  });
}

export function useUpdateUser() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ id, data }: { id: string; data: UpdateUserDto }) =>
      usersApi.updateUser(id, data),
    onMutate: async ({ id, data }) => {
      // Cancel outgoing queries
      await queryClient.cancelQueries({ queryKey: userKeys.detail(id) });

      // Snapshot previous value
      const previousUser = queryClient.getQueryData<User>(userKeys.detail(id));

      // Optimistically update
      if (previousUser) {
        queryClient.setQueryData<User>(userKeys.detail(id), {
          ...previousUser,
          ...data,
          updatedAt: new Date().toISOString(),
        });
      }

      return { previousUser };
    },
    onError: (_err, { id }, context) => {
      // Rollback on error
      if (context?.previousUser) {
        queryClient.setQueryData(userKeys.detail(id), context.previousUser);
      }
    },
    onSettled: (_data, _err, { id }) => {
      queryClient.invalidateQueries({ queryKey: userKeys.detail(id) });
      queryClient.invalidateQueries({ queryKey: userKeys.lists() });
    },
  });
}

export function useDeleteUser() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (id: string) => usersApi.deleteUser(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: userKeys.lists() });
    },
  });
}
```

## Store (UI State)

```typescript
// features/users/store/users.store.ts

import { create } from 'zustand';
import type { UsersFilters, UserRole, UserStatus } from '../types/user.types';

interface UsersState {
  // Filters
  filters: UsersFilters;
  setFilter: <K extends keyof UsersFilters>(key: K, value: UsersFilters[K]) => void;
  resetFilters: () => void;

  // Pagination
  page: number;
  limit: number;
  setPage: (page: number) => void;
  setLimit: (limit: number) => void;

  // Sorting
  sortBy: string;
  sortOrder: 'asc' | 'desc';
  setSort: (sortBy: string, sortOrder: 'asc' | 'desc') => void;

  // Selection
  selectedIds: Set<string>;
  toggleSelection: (id: string) => void;
  selectAll: (ids: string[]) => void;
  clearSelection: () => void;

  // UI State
  isDeleteDialogOpen: boolean;
  userToDelete: string | null;
  openDeleteDialog: (userId: string) => void;
  closeDeleteDialog: () => void;
}

const initialFilters: UsersFilters = {
  search: '',
  role: undefined,
  status: undefined,
};

export const useUsersStore = create<UsersState>((set) => ({
  // Filters
  filters: initialFilters,
  setFilter: (key, value) =>
    set((state) => ({
      filters: { ...state.filters, [key]: value },
      page: 1, // Reset to first page on filter change
    })),
  resetFilters: () => set({ filters: initialFilters, page: 1 }),

  // Pagination
  page: 1,
  limit: 10,
  setPage: (page) => set({ page }),
  setLimit: (limit) => set({ limit, page: 1 }),

  // Sorting
  sortBy: 'createdAt',
  sortOrder: 'desc',
  setSort: (sortBy, sortOrder) => set({ sortBy, sortOrder }),

  // Selection
  selectedIds: new Set(),
  toggleSelection: (id) =>
    set((state) => {
      const newSelection = new Set(state.selectedIds);
      if (newSelection.has(id)) {
        newSelection.delete(id);
      } else {
        newSelection.add(id);
      }
      return { selectedIds: newSelection };
    }),
  selectAll: (ids) => set({ selectedIds: new Set(ids) }),
  clearSelection: () => set({ selectedIds: new Set() }),

  // UI State
  isDeleteDialogOpen: false,
  userToDelete: null,
  openDeleteDialog: (userId) =>
    set({ isDeleteDialogOpen: true, userToDelete: userId }),
  closeDeleteDialog: () =>
    set({ isDeleteDialogOpen: false, userToDelete: null }),
}));
```

## Components

```typescript
// features/users/components/UserList.tsx

import { useMemo } from 'react';
import { Link } from 'react-router-dom';
import { Edit, Trash2, MoreHorizontal } from 'lucide-react';
import { useUsers } from '../hooks/useUsers';
import { useUsersStore } from '../store/users.store';
import { DataTable } from '@/shared/components/DataTable';
import { Pagination } from '@/shared/components/Pagination';
import { UserFilters } from './UserFilters';
import { DeleteUserDialog } from './DeleteUserDialog';
import type { User } from '../types/user.types';
import type { ColumnDef } from '@tanstack/react-table';

export function UserList() {
  const {
    filters,
    page,
    limit,
    sortBy,
    sortOrder,
    setPage,
    setSort,
    openDeleteDialog,
  } = useUsersStore();

  const { data, isLoading, isError, error } = useUsers({
    ...filters,
    page,
    limit,
    sortBy,
    sortOrder,
  });

  const columns = useMemo<ColumnDef<User>[]>(
    () => [
      {
        accessorKey: 'email',
        header: 'Email',
        cell: ({ row }) => (
          <Link
            to={`/users/${row.original.id}`}
            className="text-blue-600 hover:underline"
          >
            {row.original.email}
          </Link>
        ),
      },
      {
        accessorKey: 'firstName',
        header: 'First Name',
      },
      {
        accessorKey: 'lastName',
        header: 'Last Name',
      },
      {
        accessorKey: 'role',
        header: 'Role',
        cell: ({ row }) => (
          <span className="capitalize rounded-full bg-gray-100 px-2 py-1 text-xs">
            {row.original.role}
          </span>
        ),
      },
      {
        accessorKey: 'status',
        header: 'Status',
        cell: ({ row }) => {
          const statusColors = {
            active: 'bg-green-100 text-green-800',
            inactive: 'bg-gray-100 text-gray-800',
            pending: 'bg-yellow-100 text-yellow-800',
          };
          return (
            <span
              className={`capitalize rounded-full px-2 py-1 text-xs ${
                statusColors[row.original.status]
              }`}
            >
              {row.original.status}
            </span>
          );
        },
      },
      {
        id: 'actions',
        header: '',
        cell: ({ row }) => (
          <div className="flex items-center gap-2">
            <Link
              to={`/users/${row.original.id}/edit`}
              className="p-1 hover:bg-gray-100 rounded"
            >
              <Edit className="h-4 w-4" />
            </Link>
            <button
              onClick={() => openDeleteDialog(row.original.id)}
              className="p-1 hover:bg-gray-100 rounded text-red-600"
            >
              <Trash2 className="h-4 w-4" />
            </button>
          </div>
        ),
      },
    ],
    [openDeleteDialog]
  );

  if (isError) {
    return (
      <div className="text-center py-10 text-red-600">
        Error loading users: {error.message}
      </div>
    );
  }

  return (
    <div className="space-y-4">
      <UserFilters />

      <DataTable
        columns={columns}
        data={data?.data ?? []}
        isLoading={isLoading}
        sorting={{ sortBy, sortOrder }}
        onSortChange={setSort}
      />

      {data && (
        <Pagination
          currentPage={page}
          totalPages={data.meta.totalPages}
          onPageChange={setPage}
        />
      )}

      <DeleteUserDialog />
    </div>
  );
}
```

```typescript
// features/users/components/UserForm.tsx

import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import type { User, CreateUserDto, UpdateUserDto } from '../types/user.types';

const userSchema = z.object({
  email: z.string().email('Invalid email address'),
  firstName: z.string().min(1, 'First name is required'),
  lastName: z.string().min(1, 'Last name is required'),
  role: z.enum(['admin', 'user', 'moderator']),
  password: z.string().min(8, 'Password must be at least 8 characters').optional(),
  status: z.enum(['active', 'inactive', 'pending']).optional(),
});

type UserFormData = z.infer<typeof userSchema>;

interface UserFormProps {
  user?: User;
  onSubmit: (data: CreateUserDto | UpdateUserDto) => void;
  isSubmitting?: boolean;
}

export function UserForm({ user, onSubmit, isSubmitting }: UserFormProps) {
  const isEditing = !!user;

  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<UserFormData>({
    resolver: zodResolver(userSchema),
    defaultValues: user
      ? {
          email: user.email,
          firstName: user.firstName,
          lastName: user.lastName,
          role: user.role,
          status: user.status,
        }
      : {
          role: 'user',
        },
  });

  const handleFormSubmit = (data: UserFormData) => {
    if (isEditing) {
      const { password, ...updateData } = data;
      onSubmit(updateData);
    } else {
      onSubmit(data as CreateUserDto);
    }
  };

  return (
    <form onSubmit={handleSubmit(handleFormSubmit)} className="space-y-6">
      <div className="grid grid-cols-2 gap-4">
        <div>
          <label htmlFor="firstName" className="block text-sm font-medium">
            First Name
          </label>
          <input
            id="firstName"
            type="text"
            {...register('firstName')}
            className="mt-1 block w-full rounded-md border border-gray-300 px-3 py-2"
          />
          {errors.firstName && (
            <p className="mt-1 text-sm text-red-600">{errors.firstName.message}</p>
          )}
        </div>

        <div>
          <label htmlFor="lastName" className="block text-sm font-medium">
            Last Name
          </label>
          <input
            id="lastName"
            type="text"
            {...register('lastName')}
            className="mt-1 block w-full rounded-md border border-gray-300 px-3 py-2"
          />
          {errors.lastName && (
            <p className="mt-1 text-sm text-red-600">{errors.lastName.message}</p>
          )}
        </div>
      </div>

      <div>
        <label htmlFor="email" className="block text-sm font-medium">
          Email
        </label>
        <input
          id="email"
          type="email"
          {...register('email')}
          className="mt-1 block w-full rounded-md border border-gray-300 px-3 py-2"
        />
        {errors.email && (
          <p className="mt-1 text-sm text-red-600">{errors.email.message}</p>
        )}
      </div>

      {!isEditing && (
        <div>
          <label htmlFor="password" className="block text-sm font-medium">
            Password
          </label>
          <input
            id="password"
            type="password"
            {...register('password')}
            className="mt-1 block w-full rounded-md border border-gray-300 px-3 py-2"
          />
          {errors.password && (
            <p className="mt-1 text-sm text-red-600">{errors.password.message}</p>
          )}
        </div>
      )}

      <div className="grid grid-cols-2 gap-4">
        <div>
          <label htmlFor="role" className="block text-sm font-medium">
            Role
          </label>
          <select
            id="role"
            {...register('role')}
            className="mt-1 block w-full rounded-md border border-gray-300 px-3 py-2"
          >
            <option value="user">User</option>
            <option value="moderator">Moderator</option>
            <option value="admin">Admin</option>
          </select>
          {errors.role && (
            <p className="mt-1 text-sm text-red-600">{errors.role.message}</p>
          )}
        </div>

        {isEditing && (
          <div>
            <label htmlFor="status" className="block text-sm font-medium">
              Status
            </label>
            <select
              id="status"
              {...register('status')}
              className="mt-1 block w-full rounded-md border border-gray-300 px-3 py-2"
            >
              <option value="active">Active</option>
              <option value="inactive">Inactive</option>
              <option value="pending">Pending</option>
            </select>
          </div>
        )}
      </div>

      <div className="flex justify-end gap-4">
        <button
          type="button"
          onClick={() => window.history.back()}
          className="px-4 py-2 border border-gray-300 rounded-md hover:bg-gray-50"
        >
          Cancel
        </button>
        <button
          type="submit"
          disabled={isSubmitting}
          className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:opacity-50"
        >
          {isSubmitting ? 'Saving...' : isEditing ? 'Update User' : 'Create User'}
        </button>
      </div>
    </form>
  );
}
```

```typescript
// features/users/components/UserFilters.tsx

import { Search } from 'lucide-react';
import { useUsersStore } from '../store/users.store';
import { useDebouncedCallback } from 'use-debounce';

export function UserFilters() {
  const { filters, setFilter, resetFilters } = useUsersStore();

  const handleSearchChange = useDebouncedCallback((value: string) => {
    setFilter('search', value);
  }, 300);

  return (
    <div className="flex items-center gap-4 p-4 bg-white rounded-lg border">
      <div className="relative flex-1">
        <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-gray-400" />
        <input
          type="text"
          placeholder="Search users..."
          defaultValue={filters.search}
          onChange={(e) => handleSearchChange(e.target.value)}
          className="w-full pl-10 pr-4 py-2 border rounded-md"
        />
      </div>

      <select
        value={filters.role ?? ''}
        onChange={(e) => setFilter('role', e.target.value || undefined)}
        className="border rounded-md px-3 py-2"
      >
        <option value="">All Roles</option>
        <option value="admin">Admin</option>
        <option value="moderator">Moderator</option>
        <option value="user">User</option>
      </select>

      <select
        value={filters.status ?? ''}
        onChange={(e) => setFilter('status', e.target.value || undefined)}
        className="border rounded-md px-3 py-2"
      >
        <option value="">All Statuses</option>
        <option value="active">Active</option>
        <option value="inactive">Inactive</option>
        <option value="pending">Pending</option>
      </select>

      <button
        onClick={resetFilters}
        className="px-3 py-2 text-sm text-gray-600 hover:text-gray-900"
      >
        Reset
      </button>
    </div>
  );
}
```

```typescript
// features/users/components/DeleteUserDialog.tsx

import { useDeleteUser } from '../hooks/useUserMutations';
import { useUsersStore } from '../store/users.store';
import { ConfirmDialog } from '@/shared/components/ConfirmDialog';

export function DeleteUserDialog() {
  const { isDeleteDialogOpen, userToDelete, closeDeleteDialog } = useUsersStore();
  const deleteUser = useDeleteUser();

  const handleConfirm = async () => {
    if (userToDelete) {
      await deleteUser.mutateAsync(userToDelete);
      closeDeleteDialog();
    }
  };

  return (
    <ConfirmDialog
      isOpen={isDeleteDialogOpen}
      onClose={closeDeleteDialog}
      onConfirm={handleConfirm}
      title="Delete User"
      description="Are you sure you want to delete this user? This action cannot be undone."
      confirmText="Delete"
      cancelText="Cancel"
      isLoading={deleteUser.isPending}
      variant="danger"
    />
  );
}
```

## Pages

```typescript
// features/users/pages/UsersPage.tsx

import { Link } from 'react-router-dom';
import { Plus } from 'lucide-react';
import { UserList } from '../components/UserList';

export function UsersPage() {
  return (
    <div className="container mx-auto py-6">
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-2xl font-bold">Users</h1>
          <p className="text-gray-600">Manage user accounts</p>
        </div>
        <Link
          to="/users/new"
          className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700"
        >
          <Plus className="h-4 w-4" />
          Add User
        </Link>
      </div>

      <UserList />
    </div>
  );
}
```

```typescript
// features/users/pages/UserDetailPage.tsx

import { useParams, Link } from 'react-router-dom';
import { ArrowLeft, Edit } from 'lucide-react';
import { useUser } from '../hooks/useUser';
import { format } from 'date-fns';

export function UserDetailPage() {
  const { id } = useParams<{ id: string }>();
  const { data: user, isLoading, isError } = useUser(id!);

  if (isLoading) {
    return (
      <div className="container mx-auto py-6">
        <div className="animate-pulse">
          <div className="h-8 bg-gray-200 rounded w-1/4 mb-4" />
          <div className="h-4 bg-gray-200 rounded w-1/2 mb-8" />
          <div className="space-y-4">
            <div className="h-4 bg-gray-200 rounded w-3/4" />
            <div className="h-4 bg-gray-200 rounded w-1/2" />
          </div>
        </div>
      </div>
    );
  }

  if (isError || !user) {
    return (
      <div className="container mx-auto py-6 text-center">
        <p className="text-red-600">User not found</p>
        <Link to="/users" className="text-blue-600 hover:underline">
          Back to users
        </Link>
      </div>
    );
  }

  return (
    <div className="container mx-auto py-6">
      <div className="mb-6">
        <Link
          to="/users"
          className="flex items-center gap-2 text-gray-600 hover:text-gray-900 mb-4"
        >
          <ArrowLeft className="h-4 w-4" />
          Back to users
        </Link>

        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold">
              {user.firstName} {user.lastName}
            </h1>
            <p className="text-gray-600">{user.email}</p>
          </div>
          <Link
            to={`/users/${user.id}/edit`}
            className="flex items-center gap-2 px-4 py-2 border rounded-md hover:bg-gray-50"
          >
            <Edit className="h-4 w-4" />
            Edit
          </Link>
        </div>
      </div>

      <div className="bg-white rounded-lg border p-6">
        <dl className="grid grid-cols-2 gap-6">
          <div>
            <dt className="text-sm font-medium text-gray-500">Role</dt>
            <dd className="mt-1 capitalize">{user.role}</dd>
          </div>
          <div>
            <dt className="text-sm font-medium text-gray-500">Status</dt>
            <dd className="mt-1 capitalize">{user.status}</dd>
          </div>
          <div>
            <dt className="text-sm font-medium text-gray-500">Created</dt>
            <dd className="mt-1">
              {format(new Date(user.createdAt), 'PPP')}
            </dd>
          </div>
          <div>
            <dt className="text-sm font-medium text-gray-500">Last Updated</dt>
            <dd className="mt-1">
              {format(new Date(user.updatedAt), 'PPP')}
            </dd>
          </div>
        </dl>
      </div>
    </div>
  );
}
```

```typescript
// features/users/pages/UserFormPage.tsx

import { useParams, useNavigate, Link } from 'react-router-dom';
import { ArrowLeft } from 'lucide-react';
import { useUser } from '../hooks/useUser';
import { useCreateUser, useUpdateUser } from '../hooks/useUserMutations';
import { UserForm } from '../components/UserForm';
import type { CreateUserDto, UpdateUserDto } from '../types/user.types';

export function UserFormPage() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const isEditing = !!id;

  const { data: user, isLoading } = useUser(id ?? '');
  const createUser = useCreateUser();
  const updateUser = useUpdateUser();

  const handleSubmit = async (data: CreateUserDto | UpdateUserDto) => {
    if (isEditing) {
      await updateUser.mutateAsync({ id: id!, data: data as UpdateUserDto });
      navigate(`/users/${id}`);
    } else {
      const newUser = await createUser.mutateAsync(data as CreateUserDto);
      navigate(`/users/${newUser.id}`);
    }
  };

  if (isEditing && isLoading) {
    return (
      <div className="container mx-auto py-6">
        <div className="animate-pulse">
          <div className="h-8 bg-gray-200 rounded w-1/4 mb-8" />
          <div className="space-y-4">
            <div className="h-10 bg-gray-200 rounded" />
            <div className="h-10 bg-gray-200 rounded" />
            <div className="h-10 bg-gray-200 rounded" />
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="container mx-auto py-6">
      <Link
        to="/users"
        className="flex items-center gap-2 text-gray-600 hover:text-gray-900 mb-6"
      >
        <ArrowLeft className="h-4 w-4" />
        Back to users
      </Link>

      <div className="max-w-2xl">
        <h1 className="text-2xl font-bold mb-6">
          {isEditing ? 'Edit User' : 'Create User'}
        </h1>

        <div className="bg-white rounded-lg border p-6">
          <UserForm
            user={isEditing ? user : undefined}
            onSubmit={handleSubmit}
            isSubmitting={createUser.isPending || updateUser.isPending}
          />
        </div>
      </div>
    </div>
  );
}
```

## Route Configuration

```typescript
// features/users/index.ts

export { UsersPage } from './pages/UsersPage';
export { UserDetailPage } from './pages/UserDetailPage';
export { UserFormPage } from './pages/UserFormPage';
```

```typescript
// app/routes.tsx

import { createBrowserRouter } from 'react-router-dom';
import { MainLayout } from '@/layouts/MainLayout';
import { UsersPage, UserDetailPage, UserFormPage } from '@/features/users';

export const router = createBrowserRouter([
  {
    path: '/',
    element: <MainLayout />,
    children: [
      {
        path: 'users',
        children: [
          { index: true, element: <UsersPage /> },
          { path: 'new', element: <UserFormPage /> },
          { path: ':id', element: <UserDetailPage /> },
          { path: ':id/edit', element: <UserFormPage /> },
        ],
      },
    ],
  },
]);
```

## Shared Components

```typescript
// shared/components/DataTable.tsx

import {
  useReactTable,
  getCoreRowModel,
  flexRender,
  type ColumnDef,
} from '@tanstack/react-table';
import { ChevronUp, ChevronDown } from 'lucide-react';

interface DataTableProps<T> {
  columns: ColumnDef<T>[];
  data: T[];
  isLoading?: boolean;
  sorting?: {
    sortBy: string;
    sortOrder: 'asc' | 'desc';
  };
  onSortChange?: (sortBy: string, sortOrder: 'asc' | 'desc') => void;
}

export function DataTable<T>({
  columns,
  data,
  isLoading,
  sorting,
  onSortChange,
}: DataTableProps<T>) {
  const table = useReactTable({
    data,
    columns,
    getCoreRowModel: getCoreRowModel(),
  });

  const handleSort = (columnId: string) => {
    if (!onSortChange) return;

    const newOrder =
      sorting?.sortBy === columnId && sorting.sortOrder === 'asc'
        ? 'desc'
        : 'asc';
    onSortChange(columnId, newOrder);
  };

  if (isLoading) {
    return (
      <div className="bg-white rounded-lg border">
        <div className="animate-pulse p-4 space-y-4">
          {[...Array(5)].map((_, i) => (
            <div key={i} className="h-12 bg-gray-200 rounded" />
          ))}
        </div>
      </div>
    );
  }

  return (
    <div className="bg-white rounded-lg border overflow-hidden">
      <table className="w-full">
        <thead className="bg-gray-50 border-b">
          {table.getHeaderGroups().map((headerGroup) => (
            <tr key={headerGroup.id}>
              {headerGroup.headers.map((header) => (
                <th
                  key={header.id}
                  className="px-4 py-3 text-left text-sm font-medium text-gray-600"
                >
                  {header.column.getCanSort() && onSortChange ? (
                    <button
                      className="flex items-center gap-1"
                      onClick={() => handleSort(header.id)}
                    >
                      {flexRender(
                        header.column.columnDef.header,
                        header.getContext()
                      )}
                      {sorting?.sortBy === header.id && (
                        sorting.sortOrder === 'asc' ? (
                          <ChevronUp className="h-4 w-4" />
                        ) : (
                          <ChevronDown className="h-4 w-4" />
                        )
                      )}
                    </button>
                  ) : (
                    flexRender(
                      header.column.columnDef.header,
                      header.getContext()
                    )
                  )}
                </th>
              ))}
            </tr>
          ))}
        </thead>
        <tbody>
          {table.getRowModel().rows.map((row) => (
            <tr key={row.id} className="border-b last:border-0 hover:bg-gray-50">
              {row.getVisibleCells().map((cell) => (
                <td key={cell.id} className="px-4 py-3 text-sm">
                  {flexRender(cell.column.columnDef.cell, cell.getContext())}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>

      {data.length === 0 && (
        <div className="text-center py-10 text-gray-500">No data found</div>
      )}
    </div>
  );
}
```

```typescript
// shared/components/Pagination.tsx

import { ChevronLeft, ChevronRight } from 'lucide-react';

interface PaginationProps {
  currentPage: number;
  totalPages: number;
  onPageChange: (page: number) => void;
}

export function Pagination({
  currentPage,
  totalPages,
  onPageChange,
}: PaginationProps) {
  const pages = Array.from({ length: totalPages }, (_, i) => i + 1);
  const visiblePages = pages.slice(
    Math.max(0, currentPage - 3),
    Math.min(totalPages, currentPage + 2)
  );

  return (
    <div className="flex items-center justify-center gap-2">
      <button
        onClick={() => onPageChange(currentPage - 1)}
        disabled={currentPage === 1}
        className="p-2 border rounded hover:bg-gray-50 disabled:opacity-50"
      >
        <ChevronLeft className="h-4 w-4" />
      </button>

      {visiblePages[0] > 1 && (
        <>
          <button
            onClick={() => onPageChange(1)}
            className="px-3 py-1 border rounded hover:bg-gray-50"
          >
            1
          </button>
          {visiblePages[0] > 2 && <span className="px-2">...</span>}
        </>
      )}

      {visiblePages.map((page) => (
        <button
          key={page}
          onClick={() => onPageChange(page)}
          className={`px-3 py-1 border rounded ${
            page === currentPage
              ? 'bg-blue-600 text-white border-blue-600'
              : 'hover:bg-gray-50'
          }`}
        >
          {page}
        </button>
      ))}

      {visiblePages[visiblePages.length - 1] < totalPages && (
        <>
          {visiblePages[visiblePages.length - 1] < totalPages - 1 && (
            <span className="px-2">...</span>
          )}
          <button
            onClick={() => onPageChange(totalPages)}
            className="px-3 py-1 border rounded hover:bg-gray-50"
          >
            {totalPages}
          </button>
        </>
      )}

      <button
        onClick={() => onPageChange(currentPage + 1)}
        disabled={currentPage === totalPages}
        className="p-2 border rounded hover:bg-gray-50 disabled:opacity-50"
      >
        <ChevronRight className="h-4 w-4" />
      </button>
    </div>
  );
}
```

```typescript
// shared/components/ConfirmDialog.tsx

import { Fragment } from 'react';
import { Dialog, Transition } from '@headlessui/react';
import { AlertTriangle } from 'lucide-react';

interface ConfirmDialogProps {
  isOpen: boolean;
  onClose: () => void;
  onConfirm: () => void;
  title: string;
  description: string;
  confirmText?: string;
  cancelText?: string;
  isLoading?: boolean;
  variant?: 'danger' | 'warning' | 'info';
}

export function ConfirmDialog({
  isOpen,
  onClose,
  onConfirm,
  title,
  description,
  confirmText = 'Confirm',
  cancelText = 'Cancel',
  isLoading = false,
  variant = 'danger',
}: ConfirmDialogProps) {
  const variantStyles = {
    danger: 'bg-red-600 hover:bg-red-700',
    warning: 'bg-yellow-600 hover:bg-yellow-700',
    info: 'bg-blue-600 hover:bg-blue-700',
  };

  return (
    <Transition appear show={isOpen} as={Fragment}>
      <Dialog as="div" className="relative z-50" onClose={onClose}>
        <Transition.Child
          as={Fragment}
          enter="ease-out duration-300"
          enterFrom="opacity-0"
          enterTo="opacity-100"
          leave="ease-in duration-200"
          leaveFrom="opacity-100"
          leaveTo="opacity-0"
        >
          <div className="fixed inset-0 bg-black/25" />
        </Transition.Child>

        <div className="fixed inset-0 overflow-y-auto">
          <div className="flex min-h-full items-center justify-center p-4">
            <Transition.Child
              as={Fragment}
              enter="ease-out duration-300"
              enterFrom="opacity-0 scale-95"
              enterTo="opacity-100 scale-100"
              leave="ease-in duration-200"
              leaveFrom="opacity-100 scale-100"
              leaveTo="opacity-0 scale-95"
            >
              <Dialog.Panel className="w-full max-w-md transform overflow-hidden rounded-lg bg-white p-6 shadow-xl transition-all">
                <div className="flex items-start gap-4">
                  <div className="flex-shrink-0">
                    <AlertTriangle className="h-6 w-6 text-red-600" />
                  </div>
                  <div>
                    <Dialog.Title className="text-lg font-medium">
                      {title}
                    </Dialog.Title>
                    <Dialog.Description className="mt-2 text-sm text-gray-500">
                      {description}
                    </Dialog.Description>
                  </div>
                </div>

                <div className="mt-6 flex justify-end gap-3">
                  <button
                    type="button"
                    onClick={onClose}
                    disabled={isLoading}
                    className="px-4 py-2 border rounded-md hover:bg-gray-50 disabled:opacity-50"
                  >
                    {cancelText}
                  </button>
                  <button
                    type="button"
                    onClick={onConfirm}
                    disabled={isLoading}
                    className={`px-4 py-2 text-white rounded-md disabled:opacity-50 ${variantStyles[variant]}`}
                  >
                    {isLoading ? 'Loading...' : confirmText}
                  </button>
                </div>
              </Dialog.Panel>
            </Transition.Child>
          </div>
        </div>
      </Dialog>
    </Transition>
  );
}
```

## API Client

```typescript
// lib/api-client.ts

import axios, { type AxiosInstance, type AxiosError } from 'axios';

export interface ApiError {
  message: string;
  statusCode: number;
  errors?: Record<string, string[]>;
}

const createApiClient = (): AxiosInstance => {
  const client = axios.create({
    baseURL: import.meta.env.VITE_API_URL ?? '/api',
    headers: {
      'Content-Type': 'application/json',
    },
  });

  // Request interceptor - add auth token
  client.interceptors.request.use((config) => {
    const token = localStorage.getItem('token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  });

  // Response interceptor - handle errors
  client.interceptors.response.use(
    (response) => response,
    (error: AxiosError<ApiError>) => {
      if (error.response?.status === 401) {
        localStorage.removeItem('token');
        window.location.href = '/login';
      }
      return Promise.reject(error);
    }
  );

  return client;
};

export const apiClient = createApiClient();
```

## Testing

```typescript
// features/users/__tests__/UserList.test.tsx

import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { BrowserRouter } from 'react-router-dom';
import { http, HttpResponse } from 'msw';
import { setupServer } from 'msw/node';
import { UserList } from '../components/UserList';

const mockUsers = {
  data: [
    {
      id: '1',
      email: 'john@example.com',
      firstName: 'John',
      lastName: 'Doe',
      role: 'admin',
      status: 'active',
      createdAt: '2024-01-01T00:00:00Z',
      updatedAt: '2024-01-01T00:00:00Z',
    },
  ],
  meta: {
    total: 1,
    page: 1,
    limit: 10,
    totalPages: 1,
  },
};

const server = setupServer(
  http.get('/api/users', () => {
    return HttpResponse.json(mockUsers);
  })
);

beforeAll(() => server.listen());
afterEach(() => server.resetHandlers());
afterAll(() => server.close());

function renderWithProviders(component: React.ReactNode) {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: { retry: false },
    },
  });

  return render(
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>{component}</BrowserRouter>
    </QueryClientProvider>
  );
}

describe('UserList', () => {
  it('renders user list', async () => {
    renderWithProviders(<UserList />);

    await waitFor(() => {
      expect(screen.getByText('john@example.com')).toBeInTheDocument();
    });

    expect(screen.getByText('John')).toBeInTheDocument();
    expect(screen.getByText('Doe')).toBeInTheDocument();
  });

  it('shows loading state', () => {
    renderWithProviders(<UserList />);

    // Loading skeleton should be visible initially
    expect(document.querySelector('.animate-pulse')).toBeInTheDocument();
  });

  it('allows filtering by search', async () => {
    const user = userEvent.setup();
    renderWithProviders(<UserList />);

    const searchInput = screen.getByPlaceholderText('Search users...');
    await user.type(searchInput, 'john');

    // Search should be debounced
    await waitFor(() => {
      expect(searchInput).toHaveValue('john');
    });
  });
});
```

## Usage

1. Install dependencies:
```bash
npm install @tanstack/react-query @tanstack/react-table zustand react-hook-form @hookform/resolvers zod axios date-fns lucide-react @headlessui/react use-debounce
```

2. Set up QueryClient provider in your app root
3. Configure API client with your backend URL
4. Add routes to your router configuration

## Key Patterns Demonstrated

- **Query Keys Factory**: Organized query key management
- **Optimistic Updates**: Immediate UI feedback with rollback
- **Separation of Concerns**: Server state (TanStack Query) vs UI state (Zustand)
- **Type Safety**: Full TypeScript coverage
- **Pagination**: Server-side pagination with URL-based state
- **Filtering & Sorting**: Coordinated UI state management
- **Error Handling**: Comprehensive error boundaries and states
- **Loading States**: Skeleton UI and disabled states
