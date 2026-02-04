# React Component Template

Production-ready component templates for React applications with TypeScript.

## Basic Component Template

```tsx
// components/{{ComponentName}}/{{ComponentName}}.tsx
import { memo, type FC, type ReactNode } from 'react';
import { cn } from '@/lib/utils';
import styles from './{{ComponentName}}.module.css';

export interface {{ComponentName}}Props {
  /** Primary content */
  children?: ReactNode;
  /** Additional CSS classes */
  className?: string;
  /** Component variant */
  variant?: 'default' | 'primary' | 'secondary' | 'outline';
  /** Size variant */
  size?: 'sm' | 'md' | 'lg';
  /** Disabled state */
  disabled?: boolean;
  /** Test identifier */
  testId?: string;
}

/**
 * {{ComponentName}} component
 *
 * @description Brief description of what this component does
 *
 * @example
 * ```tsx
 * <{{ComponentName}} variant="primary" size="md">
 *   Content here
 * </{{ComponentName}}>
 * ```
 */
export const {{ComponentName}}: FC<{{ComponentName}}Props> = memo(({
  children,
  className,
  variant = 'default',
  size = 'md',
  disabled = false,
  testId = '{{component-name}}',
}) => {
  return (
    <div
      className={cn(
        styles.root,
        styles[`variant-${variant}`],
        styles[`size-${size}`],
        disabled && styles.disabled,
        className
      )}
      data-testid={testId}
      aria-disabled={disabled}
    >
      {children}
    </div>
  );
});

{{ComponentName}}.displayName = '{{ComponentName}}';
```

## Component with Forwarded Ref

```tsx
// components/Button/Button.tsx
import { forwardRef, type ComponentPropsWithRef, type ReactNode } from 'react';
import { cn } from '@/lib/utils';
import { Spinner } from '@/components/Spinner';

const variantStyles = {
  primary: 'bg-primary text-primary-foreground hover:bg-primary/90',
  secondary: 'bg-secondary text-secondary-foreground hover:bg-secondary/80',
  outline: 'border border-input bg-background hover:bg-accent hover:text-accent-foreground',
  ghost: 'hover:bg-accent hover:text-accent-foreground',
  destructive: 'bg-destructive text-destructive-foreground hover:bg-destructive/90',
  link: 'text-primary underline-offset-4 hover:underline',
} as const;

const sizeStyles = {
  sm: 'h-9 px-3 text-sm',
  md: 'h-10 px-4 py-2',
  lg: 'h-11 px-8 text-lg',
  icon: 'h-10 w-10',
} as const;

export interface ButtonProps extends ComponentPropsWithRef<'button'> {
  /** Visual variant */
  variant?: keyof typeof variantStyles;
  /** Size variant */
  size?: keyof typeof sizeStyles;
  /** Loading state */
  isLoading?: boolean;
  /** Icon before text */
  leftIcon?: ReactNode;
  /** Icon after text */
  rightIcon?: ReactNode;
  /** Full width button */
  fullWidth?: boolean;
}

export const Button = forwardRef<HTMLButtonElement, ButtonProps>(
  (
    {
      children,
      className,
      variant = 'primary',
      size = 'md',
      isLoading = false,
      leftIcon,
      rightIcon,
      fullWidth = false,
      disabled,
      type = 'button',
      ...props
    },
    ref
  ) => {
    const isDisabled = disabled || isLoading;

    return (
      <button
        ref={ref}
        type={type}
        className={cn(
          'inline-flex items-center justify-center gap-2',
          'rounded-md font-medium transition-colors',
          'focus-visible:outline-none focus-visible:ring-2',
          'focus-visible:ring-ring focus-visible:ring-offset-2',
          'disabled:pointer-events-none disabled:opacity-50',
          variantStyles[variant],
          sizeStyles[size],
          fullWidth && 'w-full',
          className
        )}
        disabled={isDisabled}
        aria-busy={isLoading}
        {...props}
      >
        {isLoading ? (
          <Spinner className="h-4 w-4" />
        ) : leftIcon ? (
          <span className="shrink-0">{leftIcon}</span>
        ) : null}
        {children}
        {rightIcon && !isLoading && (
          <span className="shrink-0">{rightIcon}</span>
        )}
      </button>
    );
  }
);

Button.displayName = 'Button';
```

## Input Component

```tsx
// components/Input/Input.tsx
import { forwardRef, type ComponentPropsWithRef, type ReactNode } from 'react';
import { cn } from '@/lib/utils';

export interface InputProps extends Omit<ComponentPropsWithRef<'input'>, 'size'> {
  /** Label text */
  label?: string;
  /** Helper text below input */
  helperText?: string;
  /** Error message */
  error?: string;
  /** Size variant */
  size?: 'sm' | 'md' | 'lg';
  /** Left addon/icon */
  leftAddon?: ReactNode;
  /** Right addon/icon */
  rightAddon?: ReactNode;
  /** Full width input */
  fullWidth?: boolean;
}

const sizeStyles = {
  sm: 'h-8 text-sm px-2',
  md: 'h-10 px-3',
  lg: 'h-12 text-lg px-4',
};

export const Input = forwardRef<HTMLInputElement, InputProps>(
  (
    {
      label,
      helperText,
      error,
      size = 'md',
      leftAddon,
      rightAddon,
      fullWidth = false,
      className,
      id,
      disabled,
      ...props
    },
    ref
  ) => {
    const inputId = id || `input-${Math.random().toString(36).slice(2, 9)}`;
    const hasError = Boolean(error);

    return (
      <div className={cn('flex flex-col gap-1.5', fullWidth && 'w-full')}>
        {label && (
          <label
            htmlFor={inputId}
            className={cn(
              'text-sm font-medium text-foreground',
              disabled && 'opacity-50'
            )}
          >
            {label}
          </label>
        )}

        <div className="relative flex items-center">
          {leftAddon && (
            <div className="absolute left-3 flex items-center text-muted-foreground">
              {leftAddon}
            </div>
          )}

          <input
            ref={ref}
            id={inputId}
            disabled={disabled}
            aria-invalid={hasError}
            aria-describedby={
              hasError ? `${inputId}-error` : helperText ? `${inputId}-helper` : undefined
            }
            className={cn(
              'w-full rounded-md border bg-background',
              'transition-colors placeholder:text-muted-foreground',
              'focus-visible:outline-none focus-visible:ring-2',
              'focus-visible:ring-ring focus-visible:ring-offset-2',
              'disabled:cursor-not-allowed disabled:opacity-50',
              sizeStyles[size],
              leftAddon && 'pl-10',
              rightAddon && 'pr-10',
              hasError
                ? 'border-destructive focus-visible:ring-destructive'
                : 'border-input',
              className
            )}
            {...props}
          />

          {rightAddon && (
            <div className="absolute right-3 flex items-center text-muted-foreground">
              {rightAddon}
            </div>
          )}
        </div>

        {(error || helperText) && (
          <p
            id={error ? `${inputId}-error` : `${inputId}-helper`}
            className={cn(
              'text-sm',
              error ? 'text-destructive' : 'text-muted-foreground'
            )}
          >
            {error || helperText}
          </p>
        )}
      </div>
    );
  }
);

Input.displayName = 'Input';
```

## Card Component

```tsx
// components/Card/Card.tsx
import { forwardRef, type ComponentPropsWithRef, type ReactNode } from 'react';
import { cn } from '@/lib/utils';

export interface CardProps extends ComponentPropsWithRef<'div'> {
  /** Card variant */
  variant?: 'default' | 'outline' | 'elevated';
  /** Padding size */
  padding?: 'none' | 'sm' | 'md' | 'lg';
  /** Interactive card */
  interactive?: boolean;
}

const variantStyles = {
  default: 'bg-card text-card-foreground',
  outline: 'border bg-transparent',
  elevated: 'bg-card text-card-foreground shadow-lg',
};

const paddingStyles = {
  none: '',
  sm: 'p-4',
  md: 'p-6',
  lg: 'p-8',
};

export const Card = forwardRef<HTMLDivElement, CardProps>(
  (
    {
      children,
      className,
      variant = 'default',
      padding = 'md',
      interactive = false,
      ...props
    },
    ref
  ) => {
    return (
      <div
        ref={ref}
        className={cn(
          'rounded-lg border shadow-sm',
          variantStyles[variant],
          paddingStyles[padding],
          interactive && 'cursor-pointer transition-shadow hover:shadow-md',
          className
        )}
        {...props}
      >
        {children}
      </div>
    );
  }
);

Card.displayName = 'Card';

// Sub-components
export interface CardHeaderProps extends ComponentPropsWithRef<'div'> {}

export const CardHeader = forwardRef<HTMLDivElement, CardHeaderProps>(
  ({ className, ...props }, ref) => (
    <div
      ref={ref}
      className={cn('flex flex-col space-y-1.5 pb-4', className)}
      {...props}
    />
  )
);

CardHeader.displayName = 'CardHeader';

export interface CardTitleProps extends ComponentPropsWithRef<'h3'> {}

export const CardTitle = forwardRef<HTMLHeadingElement, CardTitleProps>(
  ({ className, ...props }, ref) => (
    <h3
      ref={ref}
      className={cn('text-2xl font-semibold leading-none tracking-tight', className)}
      {...props}
    />
  )
);

CardTitle.displayName = 'CardTitle';

export interface CardDescriptionProps extends ComponentPropsWithRef<'p'> {}

export const CardDescription = forwardRef<HTMLParagraphElement, CardDescriptionProps>(
  ({ className, ...props }, ref) => (
    <p
      ref={ref}
      className={cn('text-sm text-muted-foreground', className)}
      {...props}
    />
  )
);

CardDescription.displayName = 'CardDescription';

export interface CardContentProps extends ComponentPropsWithRef<'div'> {}

export const CardContent = forwardRef<HTMLDivElement, CardContentProps>(
  ({ className, ...props }, ref) => (
    <div ref={ref} className={cn('', className)} {...props} />
  )
);

CardContent.displayName = 'CardContent';

export interface CardFooterProps extends ComponentPropsWithRef<'div'> {}

export const CardFooter = forwardRef<HTMLDivElement, CardFooterProps>(
  ({ className, ...props }, ref) => (
    <div
      ref={ref}
      className={cn('flex items-center pt-4', className)}
      {...props}
    />
  )
);

CardFooter.displayName = 'CardFooter';
```

## Modal Component

```tsx
// components/Modal/Modal.tsx
import {
  useRef,
  useEffect,
  useCallback,
  type FC,
  type ReactNode,
  type MouseEvent,
} from 'react';
import { createPortal } from 'react-dom';
import { cn } from '@/lib/utils';
import { X } from 'lucide-react';

export interface ModalProps {
  /** Whether the modal is open */
  isOpen: boolean;
  /** Callback when modal should close */
  onClose: () => void;
  /** Modal title */
  title?: string;
  /** Modal description */
  description?: string;
  /** Modal content */
  children: ReactNode;
  /** Modal size */
  size?: 'sm' | 'md' | 'lg' | 'xl' | 'full';
  /** Whether to close on overlay click */
  closeOnOverlayClick?: boolean;
  /** Whether to close on escape key */
  closeOnEscape?: boolean;
  /** Whether to show close button */
  showCloseButton?: boolean;
  /** Custom class for modal content */
  className?: string;
}

const sizeStyles = {
  sm: 'max-w-sm',
  md: 'max-w-md',
  lg: 'max-w-lg',
  xl: 'max-w-xl',
  full: 'max-w-full mx-4',
};

export const Modal: FC<ModalProps> = ({
  isOpen,
  onClose,
  title,
  description,
  children,
  size = 'md',
  closeOnOverlayClick = true,
  closeOnEscape = true,
  showCloseButton = true,
  className,
}) => {
  const modalRef = useRef<HTMLDivElement>(null);
  const previousActiveElement = useRef<Element | null>(null);

  // Handle escape key
  useEffect(() => {
    if (!isOpen || !closeOnEscape) return;

    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape') {
        onClose();
      }
    };

    document.addEventListener('keydown', handleKeyDown);
    return () => document.removeEventListener('keydown', handleKeyDown);
  }, [isOpen, closeOnEscape, onClose]);

  // Focus management
  useEffect(() => {
    if (isOpen) {
      previousActiveElement.current = document.activeElement;
      modalRef.current?.focus();
    } else {
      (previousActiveElement.current as HTMLElement)?.focus();
    }
  }, [isOpen]);

  // Lock body scroll
  useEffect(() => {
    if (isOpen) {
      document.body.style.overflow = 'hidden';
    } else {
      document.body.style.overflow = '';
    }
    return () => {
      document.body.style.overflow = '';
    };
  }, [isOpen]);

  const handleOverlayClick = useCallback(
    (e: MouseEvent<HTMLDivElement>) => {
      if (closeOnOverlayClick && e.target === e.currentTarget) {
        onClose();
      }
    },
    [closeOnOverlayClick, onClose]
  );

  if (!isOpen) return null;

  return createPortal(
    <div
      className="fixed inset-0 z-50 flex items-center justify-center"
      role="presentation"
    >
      {/* Overlay */}
      <div
        className="fixed inset-0 bg-black/50 backdrop-blur-sm animate-in fade-in"
        onClick={handleOverlayClick}
        aria-hidden="true"
      />

      {/* Modal */}
      <div
        ref={modalRef}
        role="dialog"
        aria-modal="true"
        aria-labelledby={title ? 'modal-title' : undefined}
        aria-describedby={description ? 'modal-description' : undefined}
        tabIndex={-1}
        className={cn(
          'relative z-50 w-full rounded-lg bg-background p-6 shadow-lg',
          'animate-in fade-in-0 zoom-in-95',
          'focus:outline-none',
          sizeStyles[size],
          className
        )}
      >
        {/* Close button */}
        {showCloseButton && (
          <button
            onClick={onClose}
            className={cn(
              'absolute right-4 top-4 rounded-sm opacity-70',
              'ring-offset-background transition-opacity hover:opacity-100',
              'focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2'
            )}
            aria-label="Close modal"
          >
            <X className="h-4 w-4" />
          </button>
        )}

        {/* Header */}
        {(title || description) && (
          <div className="mb-4">
            {title && (
              <h2
                id="modal-title"
                className="text-lg font-semibold leading-none"
              >
                {title}
              </h2>
            )}
            {description && (
              <p
                id="modal-description"
                className="mt-2 text-sm text-muted-foreground"
              >
                {description}
              </p>
            )}
          </div>
        )}

        {/* Content */}
        {children}
      </div>
    </div>,
    document.body
  );
};

// Modal Footer for actions
export interface ModalFooterProps {
  children: ReactNode;
  className?: string;
}

export const ModalFooter: FC<ModalFooterProps> = ({ children, className }) => (
  <div className={cn('mt-6 flex justify-end gap-3', className)}>{children}</div>
);
```

## Component Test Template

```tsx
// components/{{ComponentName}}/__tests__/{{ComponentName}}.test.tsx
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { {{ComponentName}} } from '../{{ComponentName}}';

describe('{{ComponentName}}', () => {
  const defaultProps = {
    // Default props for testing
  };

  it('renders with default props', () => {
    render(<{{ComponentName}} {...defaultProps}>Content</{{ComponentName}}>);

    expect(screen.getByTestId('{{component-name}}')).toBeInTheDocument();
    expect(screen.getByText('Content')).toBeInTheDocument();
  });

  it('applies custom className', () => {
    render(
      <{{ComponentName}} {...defaultProps} className="custom-class">
        Content
      </{{ComponentName}}>
    );

    expect(screen.getByTestId('{{component-name}}')).toHaveClass('custom-class');
  });

  it('handles variant prop', () => {
    render(
      <{{ComponentName}} {...defaultProps} variant="primary">
        Content
      </{{ComponentName}}>
    );

    expect(screen.getByTestId('{{component-name}}')).toHaveClass('variant-primary');
  });

  it('handles disabled state', () => {
    render(
      <{{ComponentName}} {...defaultProps} disabled>
        Content
      </{{ComponentName}}>
    );

    expect(screen.getByTestId('{{component-name}}')).toHaveAttribute('aria-disabled', 'true');
  });

  it('is accessible', async () => {
    const { container } = render(
      <{{ComponentName}} {...defaultProps}>Content</{{ComponentName}}>
    );

    // Run axe accessibility checks
    // const results = await axe(container);
    // expect(results).toHaveNoViolations();
  });

  describe('interactions', () => {
    it('handles click events', async () => {
      const handleClick = jest.fn();
      const user = userEvent.setup();

      render(
        <{{ComponentName}} {...defaultProps} onClick={handleClick}>
          Click me
        </{{ComponentName}}>
      );

      await user.click(screen.getByText('Click me'));
      expect(handleClick).toHaveBeenCalledTimes(1);
    });

    it('handles keyboard navigation', async () => {
      const user = userEvent.setup();

      render(
        <{{ComponentName}} {...defaultProps} tabIndex={0}>
          Focusable
        </{{ComponentName}}>
      );

      await user.tab();
      expect(screen.getByText('Focusable')).toHaveFocus();
    });
  });

  describe('edge cases', () => {
    it('handles empty children', () => {
      render(<{{ComponentName}} {...defaultProps} />);
      expect(screen.getByTestId('{{component-name}}')).toBeEmptyDOMElement();
    });

    it('handles null children', () => {
      render(<{{ComponentName}} {...defaultProps}>{null}</{{ComponentName}}>);
      expect(screen.getByTestId('{{component-name}}')).toBeEmptyDOMElement();
    });
  });
});
```

## Storybook Template

```tsx
// components/{{ComponentName}}/{{ComponentName}}.stories.tsx
import type { Meta, StoryObj } from '@storybook/react';
import { {{ComponentName}} } from './{{ComponentName}}';

const meta: Meta<typeof {{ComponentName}}> = {
  title: 'Components/{{ComponentName}}',
  component: {{ComponentName}},
  tags: ['autodocs'],
  argTypes: {
    variant: {
      control: 'select',
      options: ['default', 'primary', 'secondary', 'outline'],
      description: 'Visual variant of the component',
    },
    size: {
      control: 'select',
      options: ['sm', 'md', 'lg'],
      description: 'Size variant',
    },
    disabled: {
      control: 'boolean',
      description: 'Disabled state',
    },
  },
  parameters: {
    layout: 'centered',
  },
};

export default meta;
type Story = StoryObj<typeof {{ComponentName}}>;

export const Default: Story = {
  args: {
    children: 'Default {{ComponentName}}',
  },
};

export const Primary: Story = {
  args: {
    children: 'Primary {{ComponentName}}',
    variant: 'primary',
  },
};

export const Secondary: Story = {
  args: {
    children: 'Secondary {{ComponentName}}',
    variant: 'secondary',
  },
};

export const AllSizes: Story = {
  render: () => (
    <div className="flex flex-col gap-4">
      <{{ComponentName}} size="sm">Small</{{ComponentName}}>
      <{{ComponentName}} size="md">Medium</{{ComponentName}}>
      <{{ComponentName}} size="lg">Large</{{ComponentName}}>
    </div>
  ),
};

export const Disabled: Story = {
  args: {
    children: 'Disabled {{ComponentName}}',
    disabled: true,
  },
};
```

## CSS Module Template

```css
/* components/{{ComponentName}}/{{ComponentName}}.module.css */
.root {
  /* Base styles */
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: var(--radius);
  transition: all 150ms ease;
}

/* Variants */
.variant-default {
  background-color: var(--background);
  color: var(--foreground);
  border: 1px solid var(--border);
}

.variant-primary {
  background-color: var(--primary);
  color: var(--primary-foreground);
}

.variant-secondary {
  background-color: var(--secondary);
  color: var(--secondary-foreground);
}

.variant-outline {
  background-color: transparent;
  border: 1px solid var(--border);
  color: var(--foreground);
}

/* Sizes */
.size-sm {
  height: 2rem;
  padding: 0 0.75rem;
  font-size: 0.875rem;
}

.size-md {
  height: 2.5rem;
  padding: 0 1rem;
  font-size: 1rem;
}

.size-lg {
  height: 3rem;
  padding: 0 1.5rem;
  font-size: 1.125rem;
}

/* States */
.disabled {
  opacity: 0.5;
  pointer-events: none;
  cursor: not-allowed;
}

/* Focus visible */
.root:focus-visible {
  outline: 2px solid var(--ring);
  outline-offset: 2px;
}

/* Hover states */
.variant-default:hover:not(.disabled) {
  background-color: var(--accent);
}

.variant-primary:hover:not(.disabled) {
  opacity: 0.9;
}

.variant-secondary:hover:not(.disabled) {
  opacity: 0.8;
}

.variant-outline:hover:not(.disabled) {
  background-color: var(--accent);
  color: var(--accent-foreground);
}
```
