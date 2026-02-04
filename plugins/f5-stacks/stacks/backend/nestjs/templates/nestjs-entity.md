---
name: nestjs-entity
description: NestJS TypeORM entity template
applies_to: nestjs
category: template
---

# NestJS Entity Template

## Basic Entity

```typescript
// modules/{{module}}/entities/{{entity}}.entity.ts
import {
  Entity,
  PrimaryGeneratedColumn,
  Column,
  CreateDateColumn,
  UpdateDateColumn,
  DeleteDateColumn,
  Index,
  BeforeInsert,
  BeforeUpdate,
} from 'typeorm';

@Entity('{{table_name}}')
export class {{Entity}} {
  @PrimaryGeneratedColumn('uuid')
  id: string;

  @Column({ type: 'varchar', length: {{max_length}} })
  @Index()
  {{field}}: string;

  @Column({ type: 'varchar', unique: true })
  email: string;

  @Column({ type: 'text', nullable: true })
  description?: string;

  @Column({ type: 'int', default: 0 })
  count: number;

  @Column({ type: 'decimal', precision: 10, scale: 2, default: 0 })
  amount: number;

  @Column({ type: 'boolean', default: true })
  isActive: boolean;

  @Column({
    type: 'enum',
    enum: {{EnumName}},
    default: {{EnumName}}.{{default_value}},
  })
  status: {{EnumName}};

  @Column({ type: 'jsonb', nullable: true })
  metadata?: Record<string, any>;

  @Column({ type: 'simple-array', nullable: true })
  tags?: string[];

  @CreateDateColumn()
  createdAt: Date;

  @UpdateDateColumn()
  updatedAt: Date;

  @DeleteDateColumn()
  deletedAt?: Date;

  @BeforeInsert()
  @BeforeUpdate()
  validate() {
    // Custom validation logic
  }
}
```

## Entity with Relations

```typescript
// modules/{{module}}/entities/{{entity}}.entity.ts
import {
  Entity,
  PrimaryGeneratedColumn,
  Column,
  ManyToOne,
  OneToMany,
  ManyToMany,
  JoinTable,
  JoinColumn,
} from 'typeorm';
import { Parent } from '../../parents/entities/parent.entity';
import { Child } from '../../children/entities/child.entity';
import { Related } from '../../related/entities/related.entity';

@Entity('{{table_name}}')
export class {{Entity}} {
  @PrimaryGeneratedColumn('uuid')
  id: string;

  // Many-to-One (N:1)
  @Column()
  parentId: string;

  @ManyToOne(() => Parent, (parent) => parent.{{entities}}, {
    onDelete: 'CASCADE',
  })
  @JoinColumn({ name: 'parentId' })
  parent: Parent;

  // One-to-Many (1:N)
  @OneToMany(() => Child, (child) => child.{{entity}}, {
    cascade: true,
  })
  children: Child[];

  // Many-to-Many (N:N)
  @ManyToMany(() => Related, (related) => related.{{entities}})
  @JoinTable({
    name: '{{entity}}_related',
    joinColumn: { name: '{{entity}}_id', referencedColumnName: 'id' },
    inverseJoinColumn: { name: 'related_id', referencedColumnName: 'id' },
  })
  relatedItems: Related[];
}
```

## Entity with Embedded

```typescript
// modules/{{module}}/entities/{{entity}}.entity.ts
import { Entity, Column } from 'typeorm';
import { Address } from './embeddables/address.embeddable';

@Entity('{{table_name}}')
export class {{Entity}} {
  @PrimaryGeneratedColumn('uuid')
  id: string;

  @Column(() => Address)
  address: Address;
}

// modules/{{module}}/entities/embeddables/address.embeddable.ts
import { Column } from 'typeorm';

export class Address {
  @Column({ type: 'varchar', length: 255 })
  street: string;

  @Column({ type: 'varchar', length: 100 })
  city: string;

  @Column({ type: 'varchar', length: 20 })
  postalCode: string;

  @Column({ type: 'varchar', length: 2 })
  countryCode: string;
}
```

## Entity with Single Table Inheritance

```typescript
// modules/{{module}}/entities/{{entity}}.entity.ts
import {
  Entity,
  TableInheritance,
  ChildEntity,
  Column,
} from 'typeorm';

@Entity('{{table_name}}')
@TableInheritance({ column: { type: 'varchar', name: 'type' } })
export abstract class {{Entity}} {
  @PrimaryGeneratedColumn('uuid')
  id: string;

  @Column()
  commonField: string;
}

@ChildEntity('type_a')
export class TypeA{{Entity}} extends {{Entity}} {
  @Column()
  specificFieldA: string;
}

@ChildEntity('type_b')
export class TypeB{{Entity}} extends {{Entity}} {
  @Column()
  specificFieldB: number;
}
```

## Entity with Subscribers

```typescript
// modules/{{module}}/subscribers/{{entity}}.subscriber.ts
import {
  EntitySubscriberInterface,
  EventSubscriber,
  InsertEvent,
  UpdateEvent,
  RemoveEvent,
} from 'typeorm';
import { {{Entity}} } from '../entities/{{entity}}.entity';

@EventSubscriber()
export class {{Entity}}Subscriber implements EntitySubscriberInterface<{{Entity}}> {
  listenTo() {
    return {{Entity}};
  }

  beforeInsert(event: InsertEvent<{{Entity}}>) {
    console.log('Before insert:', event.entity);
  }

  afterInsert(event: InsertEvent<{{Entity}}>) {
    console.log('After insert:', event.entity);
  }

  beforeUpdate(event: UpdateEvent<{{Entity}}>) {
    console.log('Before update:', event.entity);
  }

  afterUpdate(event: UpdateEvent<{{Entity}}>) {
    console.log('After update:', event.entity);
  }

  beforeRemove(event: RemoveEvent<{{Entity}}>) {
    console.log('Before remove:', event.entity);
  }

  afterRemove(event: RemoveEvent<{{Entity}}>) {
    console.log('After remove:', event.entity);
  }
}
```

## Enum Definition

```typescript
// modules/{{module}}/enums/{{entity}}-status.enum.ts
export enum {{Entity}}Status {
  DRAFT = 'draft',
  PENDING = 'pending',
  ACTIVE = 'active',
  INACTIVE = 'inactive',
  ARCHIVED = 'archived',
}
```

## Variables

| Variable | Description | Example |
|----------|-------------|---------|
| `{{module}}` | Module name (lowercase) | users |
| `{{entity}}` | Entity name (lowercase) | user |
| `{{entities}}` | Entity name (plural, lowercase) | users |
| `{{Entity}}` | Entity name (PascalCase) | User |
| `{{table_name}}` | Database table name | users |
| `{{field}}` | Field name | name |
| `{{max_length}}` | Maximum string length | 100 |
| `{{EnumName}}` | Enum type name | UserStatus |
| `{{default_value}}` | Default enum value | ACTIVE |
