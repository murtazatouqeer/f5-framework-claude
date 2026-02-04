---
name: nestjs-entity-generator
description: Agent for generating NestJS TypeORM entities
applies_to: nestjs
category: agent
---

# NestJS Entity Generator Agent

## Purpose

Generate production-ready TypeORM entities with proper column definitions, relations, and indexes.

## Input Requirements

```yaml
required:
  - entity_name: string        # e.g., "user"
  - table_name: string         # e.g., "users"
  - columns: array             # Column definitions

optional:
  - module_name: string        # Module path (defaults to entity_name + 's')
  - relations: array           # Relation definitions
  - indexes: array             # Index definitions
  - soft_delete: boolean       # Add soft delete (default: true)
  - timestamps: boolean        # Add timestamps (default: true)
  - subscribers: boolean       # Generate subscriber (default: false)
```

## Column Definition Schema

```yaml
columns:
  - name: string               # Column name
    type: string               # TypeORM column type
    options:                   # Column options
      length: number           # For varchar
      precision: number        # For decimal
      scale: number            # For decimal
      nullable: boolean        # Allow null
      unique: boolean          # Unique constraint
      default: any             # Default value
      enum: string             # Enum type name
      array: boolean           # Array type
    index: boolean             # Create index
```

## Relation Definition Schema

```yaml
relations:
  - type: string               # ManyToOne, OneToMany, ManyToMany, OneToOne
    target: string             # Target entity name
    property: string           # Property name
    options:
      cascade: boolean         # Cascade operations
      eager: boolean           # Eager loading
      nullable: boolean        # For ManyToOne
      onDelete: string         # CASCADE, SET NULL, etc.
      joinColumn: string       # Custom join column name
```

## Generation Process

### Step 1: Parse Column Definitions

```typescript
interface ColumnDefinition {
  name: string;
  type: string;
  options: {
    length?: number;
    precision?: number;
    scale?: number;
    nullable?: boolean;
    unique?: boolean;
    default?: any;
    enum?: string;
    array?: boolean;
  };
  index?: boolean;
}

const columns: ColumnDefinition[] = [
  {
    name: 'email',
    type: 'varchar',
    options: { length: 255, unique: true },
    index: true,
  },
  {
    name: 'name',
    type: 'varchar',
    options: { length: 100 },
  },
  {
    name: 'status',
    type: 'enum',
    options: { enum: 'UserStatus', default: 'UserStatus.ACTIVE' },
  },
  {
    name: 'metadata',
    type: 'jsonb',
    options: { nullable: true },
  },
];
```

### Step 2: Generate Entity

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
  ManyToOne,
  OneToMany,
  ManyToMany,
  JoinTable,
  JoinColumn,
  BeforeInsert,
  BeforeUpdate,
} from 'typeorm';
{{#each imports}}
import { {{this.name}} } from '{{this.path}}';
{{/each}}

@Entity('{{tableName}}')
{{#each classIndexes}}
@Index(['{{this.columns}}']{{#if this.options}}, {{this.options}}{{/if}})
{{/each}}
export class {{Entity}} {
  @PrimaryGeneratedColumn('uuid')
  id: string;

{{#each columns}}
  {{#if index}}
  @Index()
  {{/if}}
  @Column({
    type: '{{type}}',
    {{#if options.length}}length: {{options.length}},{{/if}}
    {{#if options.precision}}precision: {{options.precision}},{{/if}}
    {{#if options.scale}}scale: {{options.scale}},{{/if}}
    {{#if options.nullable}}nullable: true,{{/if}}
    {{#if options.unique}}unique: true,{{/if}}
    {{#if options.default}}default: {{options.default}},{{/if}}
    {{#if options.enum}}enum: {{options.enum}},{{/if}}
    {{#if options.array}}array: true,{{/if}}
  })
  {{name}}{{#if options.nullable}}?{{/if}}: {{tsType}};

{{/each}}
{{#each relations}}
  {{#if (eq type 'ManyToOne')}}
  @Column({{#if options.nullable}}{ nullable: true }{{/if}})
  {{property}}Id{{#if options.nullable}}?{{/if}}: string;

  @ManyToOne(() => {{target}}, ({{targetLower}}) => {{targetLower}}.{{inverseProperty}}, {
    {{#if options.onDelete}}onDelete: '{{options.onDelete}}',{{/if}}
    {{#if options.eager}}eager: true,{{/if}}
  })
  @JoinColumn({ name: '{{property}}Id' })
  {{property}}{{#if options.nullable}}?{{/if}}: {{target}};

  {{/if}}
  {{#if (eq type 'OneToMany')}}
  @OneToMany(() => {{target}}, ({{targetLower}}) => {{targetLower}}.{{inverseProperty}}{{#if options.cascade}}, {
    cascade: true,
  }{{/if}})
  {{property}}: {{target}}[];

  {{/if}}
  {{#if (eq type 'ManyToMany')}}
  @ManyToMany(() => {{target}}, ({{targetLower}}) => {{targetLower}}.{{inverseProperty}})
  {{#if options.owning}}
  @JoinTable({
    name: '{{joinTable}}',
    joinColumn: { name: '{{entity}}_id', referencedColumnName: 'id' },
    inverseJoinColumn: { name: '{{target}}_id', referencedColumnName: 'id' },
  })
  {{/if}}
  {{property}}: {{target}}[];

  {{/if}}
{{/each}}
  @CreateDateColumn()
  createdAt: Date;

  @UpdateDateColumn()
  updatedAt: Date;

{{#if softDelete}}
  @DeleteDateColumn()
  deletedAt?: Date;

{{/if}}
{{#if hasHooks}}
  @BeforeInsert()
  @BeforeUpdate()
  async validate(): Promise<void> {
    // Add custom validation logic
  }
{{/if}}
}
```

### Step 3: Generate Enum (if needed)

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

### Step 4: Generate Subscriber (if requested)

```typescript
// modules/{{module}}/subscribers/{{entity}}.subscriber.ts
import {
  EntitySubscriberInterface,
  EventSubscriber,
  InsertEvent,
  UpdateEvent,
  RemoveEvent,
  SoftRemoveEvent,
} from 'typeorm';
import { {{Entity}} } from '../entities/{{entity}}.entity';

@EventSubscriber()
export class {{Entity}}Subscriber implements EntitySubscriberInterface<{{Entity}}> {
  listenTo() {
    return {{Entity}};
  }

  beforeInsert(event: InsertEvent<{{Entity}}>): void {
    console.log('Before insert:', event.entity);
  }

  afterInsert(event: InsertEvent<{{Entity}}>): void {
    console.log('After insert:', event.entity);
  }

  beforeUpdate(event: UpdateEvent<{{Entity}}>): void {
    console.log('Before update:', event.entity);
  }

  afterUpdate(event: UpdateEvent<{{Entity}}>): void {
    console.log('After update:', event.entity);
  }

  beforeSoftRemove(event: SoftRemoveEvent<{{Entity}}>): void {
    console.log('Before soft remove:', event.entity);
  }

  afterSoftRemove(event: SoftRemoveEvent<{{Entity}}>): void {
    console.log('After soft remove:', event.entity);
  }
}
```

### Step 5: Generate Migration Command

```bash
# Generate migration
npm run migration:generate -- -n Create{{Entity}}Table

# Or manual migration
```

```typescript
// migrations/{{timestamp}}-Create{{Entity}}Table.ts
import { MigrationInterface, QueryRunner, Table, TableIndex } from 'typeorm';

export class Create{{Entity}}Table{{timestamp}} implements MigrationInterface {
  public async up(queryRunner: QueryRunner): Promise<void> {
    await queryRunner.createTable(
      new Table({
        name: '{{tableName}}',
        columns: [
          {
            name: 'id',
            type: 'uuid',
            isPrimary: true,
            generationStrategy: 'uuid',
            default: 'uuid_generate_v4()',
          },
{{#each columns}}
          {
            name: '{{name}}',
            type: '{{dbType}}',
            {{#if options.length}}length: '{{options.length}}',{{/if}}
            {{#if options.precision}}precision: {{options.precision}},{{/if}}
            {{#if options.scale}}scale: {{options.scale}},{{/if}}
            {{#if options.nullable}}isNullable: true,{{else}}isNullable: false,{{/if}}
            {{#if options.unique}}isUnique: true,{{/if}}
            {{#if options.default}}default: {{options.default}},{{/if}}
          },
{{/each}}
          {
            name: 'created_at',
            type: 'timestamp',
            default: 'now()',
          },
          {
            name: 'updated_at',
            type: 'timestamp',
            default: 'now()',
          },
{{#if softDelete}}
          {
            name: 'deleted_at',
            type: 'timestamp',
            isNullable: true,
          },
{{/if}}
        ],
      }),
      true,
    );

{{#each indexes}}
    await queryRunner.createIndex(
      '{{../tableName}}',
      new TableIndex({
        name: 'IDX_{{../tableName}}_{{columns}}',
        columnNames: ['{{columns}}'],
        {{#if unique}}isUnique: true,{{/if}}
      }),
    );
{{/each}}
  }

  public async down(queryRunner: QueryRunner): Promise<void> {
    await queryRunner.dropTable('{{tableName}}');
  }
}
```

## Type Mapping

| TypeORM Type | TypeScript Type | PostgreSQL Type |
|--------------|-----------------|-----------------|
| varchar | string | varchar(n) |
| text | string | text |
| int | number | integer |
| bigint | string | bigint |
| decimal | number | decimal(p,s) |
| boolean | boolean | boolean |
| date | Date | date |
| timestamp | Date | timestamp |
| jsonb | object | jsonb |
| uuid | string | uuid |
| enum | EnumType | enum |

## Output Files

```
modules/{{module}}/
├── entities/
│   └── {{entity}}.entity.ts
├── enums/
│   └── {{entity}}-status.enum.ts (if enum columns exist)
└── subscribers/
    └── {{entity}}.subscriber.ts (if requested)
```

## Usage Example

```bash
# Generate entity via agent
@nestjs:entity-generator {
  "entity_name": "product",
  "table_name": "products",
  "columns": [
    { "name": "name", "type": "varchar", "options": { "length": 255 } },
    { "name": "description", "type": "text", "options": { "nullable": true } },
    { "name": "price", "type": "decimal", "options": { "precision": 10, "scale": 2 } },
    { "name": "status", "type": "enum", "options": { "enum": "ProductStatus", "default": "ProductStatus.DRAFT" } }
  ],
  "relations": [
    { "type": "ManyToOne", "target": "Category", "property": "category" },
    { "type": "OneToMany", "target": "Review", "property": "reviews" }
  ],
  "soft_delete": true
}
```

## Validation Checklist

- [ ] All columns have appropriate types
- [ ] Nullable columns are marked correctly
- [ ] Relations have proper cascade settings
- [ ] Indexes are created for search columns
- [ ] Unique constraints are defined
- [ ] Enum values are exported
- [ ] Timestamps are included
- [ ] Soft delete is configured if needed
- [ ] Entity is registered in module
