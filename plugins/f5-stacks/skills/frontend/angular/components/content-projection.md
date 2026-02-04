# Angular Content Projection

## Overview

Content projection allows components to accept and render content from their parent component, similar to "slots" in other frameworks.

## Basic Content Projection

### Single Slot

```typescript
import { Component } from '@angular/core';

@Component({
  selector: 'app-card',
  standalone: true,
  template: `
    <div class="card">
      <div class="card-body">
        <ng-content />
      </div>
    </div>
  `,
  styles: [`
    .card {
      border: 1px solid #ddd;
      border-radius: 8px;
      padding: 1rem;
    }
  `],
})
export class CardComponent {}

// Usage
@Component({
  template: `
    <app-card>
      <h2>Card Title</h2>
      <p>This content is projected into the card.</p>
      <button>Action</button>
    </app-card>
  `,
})
export class ParentComponent {}
```

## Multi-Slot Projection

### Named Slots with select

```typescript
@Component({
  selector: 'app-dialog',
  standalone: true,
  template: `
    <div class="dialog-backdrop" (click)="close.emit()">
      <div class="dialog" (click)="$event.stopPropagation()">
        <header class="dialog-header">
          <ng-content select="[dialog-title]" />
          <button class="close-btn" (click)="close.emit()">×</button>
        </header>

        <main class="dialog-body">
          <ng-content />
        </main>

        <footer class="dialog-footer">
          <ng-content select="[dialog-actions]" />
        </footer>
      </div>
    </div>
  `,
})
export class DialogComponent {
  close = output<void>();
}

// Usage
@Component({
  template: `
    <app-dialog (close)="onClose()">
      <h2 dialog-title>Confirm Action</h2>

      <p>Are you sure you want to proceed?</p>
      <p>This action cannot be undone.</p>

      <div dialog-actions>
        <button (click)="onCancel()">Cancel</button>
        <button (click)="onConfirm()">Confirm</button>
      </div>
    </app-dialog>
  `,
})
export class ParentComponent {}
```

### Select by Element

```typescript
@Component({
  selector: 'app-layout',
  standalone: true,
  template: `
    <div class="layout">
      <aside class="sidebar">
        <ng-content select="app-sidebar" />
      </aside>

      <main class="main-content">
        <header>
          <ng-content select="app-header" />
        </header>

        <div class="content">
          <ng-content />
        </div>
      </main>
    </div>
  `,
})
export class LayoutComponent {}

// Usage
@Component({
  template: `
    <app-layout>
      <app-header>
        <h1>Page Title</h1>
      </app-header>

      <app-sidebar>
        <nav>Navigation</nav>
      </app-sidebar>

      <p>Main content goes here</p>
    </app-layout>
  `,
})
export class PageComponent {}
```

### Select by CSS Class

```typescript
@Component({
  selector: 'app-panel',
  standalone: true,
  template: `
    <div class="panel">
      <div class="panel-header">
        <ng-content select=".panel-title" />
        <ng-content select=".panel-actions" />
      </div>
      <div class="panel-body">
        <ng-content />
      </div>
    </div>
  `,
})
export class PanelComponent {}

// Usage
@Component({
  template: `
    <app-panel>
      <span class="panel-title">Settings</span>
      <button class="panel-actions">Edit</button>
      <form>Form content here</form>
    </app-panel>
  `,
})
export class SettingsComponent {}
```

## Conditional Content Projection

### Check for Projected Content

```typescript
import { Component, ContentChild, TemplateRef } from '@angular/core';

@Component({
  selector: 'app-expandable',
  standalone: true,
  template: `
    <div class="expandable">
      <div class="header" (click)="toggle()">
        @if (hasCustomHeader) {
          <ng-content select="[expandable-header]" />
        } @else {
          <span>{{ title() }}</span>
        }
        <span class="icon">{{ isExpanded ? '▼' : '▶' }}</span>
      </div>

      @if (isExpanded) {
        <div class="content">
          <ng-content />
        </div>
      }
    </div>
  `,
})
export class ExpandableComponent {
  @ContentChild('expandableHeader') headerContent?: TemplateRef<unknown>;

  title = input('Details');
  isExpanded = false;

  get hasCustomHeader() {
    return !!this.headerContent;
  }

  toggle() {
    this.isExpanded = !this.isExpanded;
  }
}
```

### Default Content with ngProjectAs

```typescript
@Component({
  selector: 'app-tabs',
  standalone: true,
  template: `
    <div class="tabs">
      <div class="tab-headers">
        <ng-content select="[tab-header]" />
      </div>
      <div class="tab-content">
        <ng-content />
      </div>
    </div>
  `,
})
export class TabsComponent {}

// Usage with ngProjectAs
@Component({
  template: `
    <app-tabs>
      <button ngProjectAs="[tab-header]">Tab 1</button>
      <button ngProjectAs="[tab-header]">Tab 2</button>

      <div>Content for selected tab</div>
    </app-tabs>
  `,
})
export class ParentComponent {}
```

## Content Children Query

### Accessing Projected Content

```typescript
import {
  Component,
  ContentChildren,
  QueryList,
  AfterContentInit,
} from '@angular/core';

@Component({
  selector: 'app-tab',
  standalone: true,
  template: `<ng-content />`,
})
export class TabComponent {
  label = input.required<string>();
  isActive = signal(false);
}

@Component({
  selector: 'app-tab-group',
  standalone: true,
  imports: [CommonModule],
  template: `
    <div class="tab-group">
      <div class="tab-headers">
        @for (tab of tabs; track tab) {
          <button
            [class.active]="tab.isActive()"
            (click)="selectTab(tab)"
          >
            {{ tab.label() }}
          </button>
        }
      </div>
      <div class="tab-content">
        <ng-content />
      </div>
    </div>
  `,
})
export class TabGroupComponent implements AfterContentInit {
  @ContentChildren(TabComponent) tabs!: QueryList<TabComponent>;

  ngAfterContentInit() {
    // Select first tab by default
    if (this.tabs.length > 0) {
      this.selectTab(this.tabs.first);
    }

    // React to dynamic tab changes
    this.tabs.changes.subscribe(() => {
      // Handle tab list changes
    });
  }

  selectTab(tab: TabComponent) {
    this.tabs.forEach(t => t.isActive.set(false));
    tab.isActive.set(true);
  }
}

// Usage
@Component({
  template: `
    <app-tab-group>
      <app-tab label="Profile">
        <h2>Profile Content</h2>
      </app-tab>
      <app-tab label="Settings">
        <h2>Settings Content</h2>
      </app-tab>
      <app-tab label="Notifications">
        <h2>Notifications Content</h2>
      </app-tab>
    </app-tab-group>
  `,
})
export class UserPageComponent {}
```

### ContentChild vs ContentChildren

```typescript
import { ContentChild, ContentChildren, QueryList } from '@angular/core';

@Component({...})
export class ContainerComponent {
  // Single element
  @ContentChild('header') headerRef?: ElementRef;
  @ContentChild(HeaderComponent) headerComponent?: HeaderComponent;

  // Multiple elements
  @ContentChildren(ItemComponent) items!: QueryList<ItemComponent>;
  @ContentChildren('item') itemRefs!: QueryList<ElementRef>;

  // With read option
  @ContentChild(SomeDirective, { read: ElementRef }) element?: ElementRef;
  @ContentChild('template', { read: TemplateRef }) template?: TemplateRef<unknown>;
}
```

## Template Projection

### Passing Templates to Components

```typescript
@Component({
  selector: 'app-list',
  standalone: true,
  imports: [CommonModule, NgTemplateOutlet],
  template: `
    <ul class="list">
      @for (item of items(); track item) {
        <li>
          <ng-container
            *ngTemplateOutlet="itemTemplate() || defaultTemplate; context: { $implicit: item }"
          />
        </li>
      }
    </ul>

    <ng-template #defaultTemplate let-item>
      {{ item }}
    </ng-template>
  `,
})
export class ListComponent<T> {
  items = input<T[]>([]);
  itemTemplate = input<TemplateRef<{ $implicit: T }>>();
}

// Usage with custom template
@Component({
  template: `
    <app-list [items]="users" [itemTemplate]="userTemplate">
      <ng-template #userTemplate let-user>
        <div class="user-item">
          <img [src]="user.avatar" />
          <span>{{ user.name }}</span>
        </div>
      </ng-template>
    </app-list>
  `,
})
export class UserListComponent {
  users = signal([...]);
}
```

### Structural Directive Pattern

```typescript
@Component({
  selector: 'app-data-table',
  standalone: true,
  imports: [CommonModule, NgTemplateOutlet],
  template: `
    <table>
      <thead>
        <tr>
          @for (col of columns(); track col.key) {
            <th>{{ col.header }}</th>
          }
        </tr>
      </thead>
      <tbody>
        @for (row of data(); track trackBy()(row)) {
          <tr>
            @for (col of columns(); track col.key) {
              <td>
                @if (cellTemplates()[col.key]) {
                  <ng-container
                    *ngTemplateOutlet="cellTemplates()[col.key]; context: { $implicit: row, column: col }"
                  />
                } @else {
                  {{ row[col.key] }}
                }
              </td>
            }
          </tr>
        }
      </tbody>
    </table>
  `,
})
export class DataTableComponent<T> {
  data = input<T[]>([]);
  columns = input<Column[]>([]);
  cellTemplates = input<Record<string, TemplateRef<unknown>>>({});
  trackBy = input<(item: T) => unknown>(() => (item: any) => item.id);
}
```

## Best Practices

1. **Use meaningful selectors**: Make slot purposes clear
2. **Provide fallback content**: Handle missing projected content
3. **Document slot names**: Clearly document available slots
4. **Keep slots focused**: Each slot should have a clear purpose
5. **Consider accessibility**: Ensure projected content is accessible
6. **Use ContentChildren for dynamic content**: Query and react to changes
