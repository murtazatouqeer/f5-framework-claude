# React Component Patterns

## Overview

Modern component design patterns for scalable React applications.

## Container/Presenter Pattern

### Concept

Separate data logic (Container) from UI rendering (Presenter).

### Implementation

```tsx
// UserListContainer.tsx - Handles data and logic
import { useUsers } from '../hooks/useUsers';
import { UserList } from './UserList';

export function UserListContainer() {
  const { users, isLoading, error, deleteUser } = useUsers();

  if (isLoading) return <LoadingSpinner />;
  if (error) return <ErrorMessage error={error} />;

  return <UserList users={users} onDelete={deleteUser} />;
}

// UserList.tsx - Pure presentation
interface UserListProps {
  users: User[];
  onDelete: (id: string) => void;
}

export function UserList({ users, onDelete }: UserListProps) {
  return (
    <ul>
      {users.map(user => (
        <li key={user.id}>
          {user.name}
          <button onClick={() => onDelete(user.id)}>Delete</button>
        </li>
      ))}
    </ul>
  );
}
```

## Compound Components

### Concept

Components that work together to form a cohesive unit with shared state.

### Implementation

```tsx
import { createContext, useContext, useState, ReactNode } from 'react';

// Context
interface AccordionContextType {
  activeIndex: number | null;
  setActiveIndex: (index: number | null) => void;
}

const AccordionContext = createContext<AccordionContextType | null>(null);

function useAccordion() {
  const context = useContext(AccordionContext);
  if (!context) {
    throw new Error('Accordion components must be used within Accordion');
  }
  return context;
}

// Root Component
interface AccordionProps {
  children: ReactNode;
  defaultIndex?: number;
}

function Accordion({ children, defaultIndex }: AccordionProps) {
  const [activeIndex, setActiveIndex] = useState<number | null>(
    defaultIndex ?? null
  );

  return (
    <AccordionContext.Provider value={{ activeIndex, setActiveIndex }}>
      <div className="accordion">{children}</div>
    </AccordionContext.Provider>
  );
}

// Item Component
interface AccordionItemProps {
  children: ReactNode;
  index: number;
}

function AccordionItem({ children, index }: AccordionItemProps) {
  const { activeIndex } = useAccordion();
  const isActive = activeIndex === index;

  return (
    <div className={`accordion-item ${isActive ? 'active' : ''}`}>
      {children}
    </div>
  );
}

// Header Component
interface AccordionHeaderProps {
  children: ReactNode;
  index: number;
}

function AccordionHeader({ children, index }: AccordionHeaderProps) {
  const { activeIndex, setActiveIndex } = useAccordion();
  const isActive = activeIndex === index;

  return (
    <button
      className="accordion-header"
      onClick={() => setActiveIndex(isActive ? null : index)}
      aria-expanded={isActive}
    >
      {children}
    </button>
  );
}

// Panel Component
interface AccordionPanelProps {
  children: ReactNode;
  index: number;
}

function AccordionPanel({ children, index }: AccordionPanelProps) {
  const { activeIndex } = useAccordion();

  if (activeIndex !== index) return null;

  return <div className="accordion-panel">{children}</div>;
}

// Attach sub-components
Accordion.Item = AccordionItem;
Accordion.Header = AccordionHeader;
Accordion.Panel = AccordionPanel;

export { Accordion };

// Usage
<Accordion defaultIndex={0}>
  <Accordion.Item index={0}>
    <Accordion.Header index={0}>Section 1</Accordion.Header>
    <Accordion.Panel index={0}>Content 1</Accordion.Panel>
  </Accordion.Item>
  <Accordion.Item index={1}>
    <Accordion.Header index={1}>Section 2</Accordion.Header>
    <Accordion.Panel index={1}>Content 2</Accordion.Panel>
  </Accordion.Item>
</Accordion>
```

## Render Props Pattern

### Concept

Pass a function as a prop that returns React elements, allowing component logic reuse.

### Implementation

```tsx
interface MousePosition {
  x: number;
  y: number;
}

interface MouseTrackerProps {
  render: (position: MousePosition) => ReactNode;
}

function MouseTracker({ render }: MouseTrackerProps) {
  const [position, setPosition] = useState<MousePosition>({ x: 0, y: 0 });

  useEffect(() => {
    const handleMouseMove = (event: MouseEvent) => {
      setPosition({ x: event.clientX, y: event.clientY });
    };

    window.addEventListener('mousemove', handleMouseMove);
    return () => window.removeEventListener('mousemove', handleMouseMove);
  }, []);

  return <>{render(position)}</>;
}

// Usage
<MouseTracker
  render={({ x, y }) => (
    <div>
      Mouse position: {x}, {y}
    </div>
  )}
/>
```

### Children as Function

```tsx
interface ToggleProps {
  children: (props: { on: boolean; toggle: () => void }) => ReactNode;
  initial?: boolean;
}

function Toggle({ children, initial = false }: ToggleProps) {
  const [on, setOn] = useState(initial);
  const toggle = () => setOn(prev => !prev);

  return <>{children({ on, toggle })}</>;
}

// Usage
<Toggle>
  {({ on, toggle }) => (
    <button onClick={toggle}>
      {on ? 'ON' : 'OFF'}
    </button>
  )}
</Toggle>
```

## Higher-Order Components (HOC)

### Concept

A function that takes a component and returns a new enhanced component.

### Implementation

```tsx
// withAuth HOC
function withAuth<P extends object>(
  WrappedComponent: React.ComponentType<P>
) {
  return function WithAuthComponent(props: P) {
    const { user, isLoading } = useAuth();
    const navigate = useNavigate();

    useEffect(() => {
      if (!isLoading && !user) {
        navigate('/login');
      }
    }, [user, isLoading, navigate]);

    if (isLoading) return <LoadingSpinner />;
    if (!user) return null;

    return <WrappedComponent {...props} />;
  };
}

// Usage
const ProtectedDashboard = withAuth(Dashboard);
```

### withErrorBoundary HOC

```tsx
function withErrorBoundary<P extends object>(
  WrappedComponent: React.ComponentType<P>,
  fallback: ReactNode
) {
  return function WithErrorBoundary(props: P) {
    return (
      <ErrorBoundary fallback={fallback}>
        <WrappedComponent {...props} />
      </ErrorBoundary>
    );
  };
}
```

## Polymorphic Components

### Concept

Components that can render as different HTML elements.

### Implementation

```tsx
type PolymorphicProps<E extends React.ElementType> = {
  as?: E;
  children?: ReactNode;
} & Omit<React.ComponentPropsWithoutRef<E>, 'as' | 'children'>;

function Box<E extends React.ElementType = 'div'>({
  as,
  children,
  ...props
}: PolymorphicProps<E>) {
  const Component = as || 'div';
  return <Component {...props}>{children}</Component>;
}

// Usage
<Box as="section" className="container">Content</Box>
<Box as="article">Article content</Box>
<Box as="a" href="/link">Link text</Box>
```

## Controlled vs Uncontrolled

### Controlled Component

```tsx
interface ControlledInputProps {
  value: string;
  onChange: (value: string) => void;
}

function ControlledInput({ value, onChange }: ControlledInputProps) {
  return (
    <input
      value={value}
      onChange={(e) => onChange(e.target.value)}
    />
  );
}

// Usage - parent controls state
const [value, setValue] = useState('');
<ControlledInput value={value} onChange={setValue} />
```

### Uncontrolled Component

```tsx
interface UncontrolledInputProps {
  defaultValue?: string;
  onBlur?: (value: string) => void;
}

function UncontrolledInput({ defaultValue, onBlur }: UncontrolledInputProps) {
  const inputRef = useRef<HTMLInputElement>(null);

  return (
    <input
      ref={inputRef}
      defaultValue={defaultValue}
      onBlur={() => onBlur?.(inputRef.current?.value ?? '')}
    />
  );
}
```

### Hybrid Pattern

```tsx
interface HybridInputProps {
  value?: string;
  defaultValue?: string;
  onChange?: (value: string) => void;
}

function HybridInput({ value, defaultValue, onChange }: HybridInputProps) {
  const [internalValue, setInternalValue] = useState(defaultValue ?? '');
  const isControlled = value !== undefined;
  const currentValue = isControlled ? value : internalValue;

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const newValue = e.target.value;
    if (!isControlled) {
      setInternalValue(newValue);
    }
    onChange?.(newValue);
  };

  return <input value={currentValue} onChange={handleChange} />;
}
```

## Best Practices

### Pattern Selection Guide

| Pattern | Use When |
|---------|----------|
| Container/Presenter | Clear separation of data and UI needed |
| Compound Components | Building cohesive component groups |
| Render Props | Logic reuse with flexible rendering |
| HOC | Cross-cutting concerns (auth, logging) |
| Polymorphic | Flexible element rendering |
| Controlled | Form inputs, precise state control |
| Uncontrolled | Simple forms, performance-critical |
