# Compound Components Pattern

## Overview

Compound components allow building flexible, composable component APIs where child components implicitly share state with a parent component.

## Basic Pattern

```tsx
import { createContext, useContext, useState, ReactNode } from 'react';

// 1. Create Context
interface SelectContextType {
  value: string;
  onChange: (value: string) => void;
  isOpen: boolean;
  setIsOpen: (open: boolean) => void;
}

const SelectContext = createContext<SelectContextType | null>(null);

// 2. Hook to consume context
function useSelectContext() {
  const context = useContext(SelectContext);
  if (!context) {
    throw new Error('Select components must be used within Select');
  }
  return context;
}

// 3. Parent Component
interface SelectProps {
  value: string;
  onChange: (value: string) => void;
  children: ReactNode;
}

function Select({ value, onChange, children }: SelectProps) {
  const [isOpen, setIsOpen] = useState(false);

  return (
    <SelectContext.Provider value={{ value, onChange, isOpen, setIsOpen }}>
      <div className="relative">{children}</div>
    </SelectContext.Provider>
  );
}

// 4. Child Components
function SelectTrigger({ children }: { children: ReactNode }) {
  const { isOpen, setIsOpen } = useSelectContext();

  return (
    <button
      onClick={() => setIsOpen(!isOpen)}
      aria-expanded={isOpen}
      className="flex items-center justify-between w-full px-3 py-2 border rounded"
    >
      {children}
      <ChevronDownIcon className={isOpen ? 'rotate-180' : ''} />
    </button>
  );
}

function SelectValue({ placeholder }: { placeholder?: string }) {
  const { value } = useSelectContext();
  return <span>{value || placeholder}</span>;
}

function SelectContent({ children }: { children: ReactNode }) {
  const { isOpen } = useSelectContext();

  if (!isOpen) return null;

  return (
    <div className="absolute top-full left-0 w-full mt-1 bg-white border rounded shadow-lg z-10">
      {children}
    </div>
  );
}

function SelectItem({ value, children }: { value: string; children: ReactNode }) {
  const { value: selectedValue, onChange, setIsOpen } = useSelectContext();

  return (
    <button
      onClick={() => {
        onChange(value);
        setIsOpen(false);
      }}
      className={cn(
        'w-full px-3 py-2 text-left hover:bg-gray-100',
        selectedValue === value && 'bg-blue-50 text-blue-600'
      )}
    >
      {children}
    </button>
  );
}

// 5. Attach sub-components
Select.Trigger = SelectTrigger;
Select.Value = SelectValue;
Select.Content = SelectContent;
Select.Item = SelectItem;

export { Select };
```

### Usage

```tsx
<Select value={country} onChange={setCountry}>
  <Select.Trigger>
    <Select.Value placeholder="Select a country" />
  </Select.Trigger>
  <Select.Content>
    <Select.Item value="us">United States</Select.Item>
    <Select.Item value="uk">United Kingdom</Select.Item>
    <Select.Item value="jp">Japan</Select.Item>
  </Select.Content>
</Select>
```

## Menu Component

```tsx
import { createContext, useContext, useState, useRef, useEffect, ReactNode } from 'react';

interface MenuContextType {
  isOpen: boolean;
  setIsOpen: (open: boolean) => void;
  activeIndex: number;
  setActiveIndex: (index: number) => void;
}

const MenuContext = createContext<MenuContextType | null>(null);

function useMenuContext() {
  const context = useContext(MenuContext);
  if (!context) {
    throw new Error('Menu components must be used within Menu');
  }
  return context;
}

interface MenuProps {
  children: ReactNode;
}

function Menu({ children }: MenuProps) {
  const [isOpen, setIsOpen] = useState(false);
  const [activeIndex, setActiveIndex] = useState(-1);
  const menuRef = useRef<HTMLDivElement>(null);

  // Close on outside click
  useEffect(() => {
    function handleClickOutside(event: MouseEvent) {
      if (menuRef.current && !menuRef.current.contains(event.target as Node)) {
        setIsOpen(false);
      }
    }

    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  return (
    <MenuContext.Provider value={{ isOpen, setIsOpen, activeIndex, setActiveIndex }}>
      <div ref={menuRef} className="relative inline-block">
        {children}
      </div>
    </MenuContext.Provider>
  );
}

function MenuButton({ children }: { children: ReactNode }) {
  const { isOpen, setIsOpen } = useMenuContext();

  return (
    <button
      onClick={() => setIsOpen(!isOpen)}
      aria-haspopup="true"
      aria-expanded={isOpen}
      className="px-4 py-2 bg-gray-100 rounded hover:bg-gray-200"
    >
      {children}
    </button>
  );
}

function MenuList({ children }: { children: ReactNode }) {
  const { isOpen } = useMenuContext();

  if (!isOpen) return null;

  return (
    <div
      role="menu"
      className="absolute top-full right-0 mt-1 min-w-[200px] bg-white border rounded shadow-lg py-1 z-10"
    >
      {children}
    </div>
  );
}

interface MenuItemProps {
  onClick?: () => void;
  disabled?: boolean;
  children: ReactNode;
}

function MenuItem({ onClick, disabled = false, children }: MenuItemProps) {
  const { setIsOpen } = useMenuContext();

  const handleClick = () => {
    if (!disabled) {
      onClick?.();
      setIsOpen(false);
    }
  };

  return (
    <button
      role="menuitem"
      onClick={handleClick}
      disabled={disabled}
      className={cn(
        'w-full px-4 py-2 text-left hover:bg-gray-100',
        disabled && 'opacity-50 cursor-not-allowed'
      )}
    >
      {children}
    </button>
  );
}

function MenuDivider() {
  return <hr className="my-1 border-gray-200" />;
}

Menu.Button = MenuButton;
Menu.List = MenuList;
Menu.Item = MenuItem;
Menu.Divider = MenuDivider;

export { Menu };
```

### Usage

```tsx
<Menu>
  <Menu.Button>Actions</Menu.Button>
  <Menu.List>
    <Menu.Item onClick={handleEdit}>Edit</Menu.Item>
    <Menu.Item onClick={handleDuplicate}>Duplicate</Menu.Item>
    <Menu.Divider />
    <Menu.Item onClick={handleDelete}>Delete</Menu.Item>
  </Menu.List>
</Menu>
```

## Form Group Component

```tsx
interface FormGroupContextType {
  id: string;
  error?: string;
  required?: boolean;
}

const FormGroupContext = createContext<FormGroupContextType | null>(null);

function useFormGroupContext() {
  return useContext(FormGroupContext);
}

interface FormGroupProps {
  children: ReactNode;
  error?: string;
  required?: boolean;
}

function FormGroup({ children, error, required }: FormGroupProps) {
  const id = useId();

  return (
    <FormGroupContext.Provider value={{ id, error, required }}>
      <div className="space-y-1">{children}</div>
    </FormGroupContext.Provider>
  );
}

function FormLabel({ children }: { children: ReactNode }) {
  const context = useFormGroupContext();

  return (
    <label
      htmlFor={context?.id}
      className="text-sm font-medium text-gray-700"
    >
      {children}
      {context?.required && <span className="text-red-500 ml-1">*</span>}
    </label>
  );
}

function FormInput(props: React.InputHTMLAttributes<HTMLInputElement>) {
  const context = useFormGroupContext();

  return (
    <input
      id={context?.id}
      aria-invalid={!!context?.error}
      aria-describedby={context?.error ? `${context.id}-error` : undefined}
      className={cn(
        'w-full px-3 py-2 border rounded',
        context?.error ? 'border-red-500' : 'border-gray-300'
      )}
      {...props}
    />
  );
}

function FormError() {
  const context = useFormGroupContext();

  if (!context?.error) return null;

  return (
    <p
      id={`${context.id}-error`}
      className="text-sm text-red-500"
      role="alert"
    >
      {context.error}
    </p>
  );
}

FormGroup.Label = FormLabel;
FormGroup.Input = FormInput;
FormGroup.Error = FormError;

export { FormGroup };
```

### Usage

```tsx
<FormGroup error={errors.email} required>
  <FormGroup.Label>Email</FormGroup.Label>
  <FormGroup.Input
    type="email"
    value={email}
    onChange={(e) => setEmail(e.target.value)}
  />
  <FormGroup.Error />
</FormGroup>
```

## Benefits

1. **Flexibility** - Users control layout and composition
2. **Implicit State** - Children share state without prop drilling
3. **Semantic API** - Clear, readable component usage
4. **Customization** - Easy to add, remove, or reorder parts
5. **Encapsulation** - Internal state management hidden

## Best Practices

### Error Handling

```tsx
function useRequiredContext<T>(context: Context<T | null>, name: string): T {
  const value = useContext(context);
  if (value === null) {
    throw new Error(`${name} must be used within its Provider`);
  }
  return value;
}
```

### TypeScript Support

```tsx
// Ensure proper typing for compound components
interface SelectComponent extends React.FC<SelectProps> {
  Trigger: typeof SelectTrigger;
  Value: typeof SelectValue;
  Content: typeof SelectContent;
  Item: typeof SelectItem;
}

const Select: SelectComponent = Object.assign(SelectRoot, {
  Trigger: SelectTrigger,
  Value: SelectValue,
  Content: SelectContent,
  Item: SelectItem,
});
```

### Controlled vs Uncontrolled

```tsx
interface SelectProps {
  // Controlled
  value?: string;
  onChange?: (value: string) => void;
  // Uncontrolled
  defaultValue?: string;
}

function Select({ value, onChange, defaultValue, children }: SelectProps) {
  const [internalValue, setInternalValue] = useState(defaultValue ?? '');
  const isControlled = value !== undefined;

  const currentValue = isControlled ? value : internalValue;
  const handleChange = (newValue: string) => {
    if (!isControlled) {
      setInternalValue(newValue);
    }
    onChange?.(newValue);
  };

  // ...
}
```
