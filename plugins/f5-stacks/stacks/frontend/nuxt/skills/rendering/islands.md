---
name: nuxt-islands
description: Nuxt Islands architecture for partial hydration
applies_to: nuxt
---

# Nuxt Islands Architecture

## Overview

Nuxt Islands enable partial hydration - rendering interactive components as isolated islands within static HTML, reducing JavaScript payload.

## Enabling Islands

```typescript
// nuxt.config.ts
export default defineNuxtConfig({
  experimental: {
    componentIslands: true,
  },
});
```

## Creating Island Components

### Basic Island
```vue
<!-- components/islands/Counter.vue -->
<script setup lang="ts">
interface Props {
  initial?: number;
}

const props = withDefaults(defineProps<Props>(), {
  initial: 0,
});

const count = ref(props.initial);
</script>

<template>
  <div class="counter-island">
    <span>Count: {{ count }}</span>
    <button @click="count++">Increment</button>
  </div>
</template>
```

### Using NuxtIsland
```vue
<!-- pages/index.vue -->
<template>
  <div>
    <!-- Static content - no JS -->
    <h1>Welcome to our site</h1>
    <p>This is static content with no JavaScript.</p>

    <!-- Interactive island - hydrated separately -->
    <NuxtIsland name="Counter" :props="{ initial: 5 }" />

    <!-- More static content -->
    <footer>Static footer</footer>
  </div>
</template>
```

## Server Components

### .server.vue Files
```vue
<!-- components/ProductCard.server.vue -->
<script setup lang="ts">
interface Props {
  productId: string;
}

const props = defineProps<Props>();

// Runs ONLY on server
const { data: product } = await useFetch(`/api/products/${props.productId}`);
</script>

<template>
  <div class="product-card">
    <img :src="product?.image" :alt="product?.name" />
    <h3>{{ product?.name }}</h3>
    <p>{{ product?.price }}</p>

    <!-- Client island for interactivity -->
    <NuxtIsland
      name="AddToCartButton"
      :props="{ productId: props.productId }"
    />
  </div>
</template>
```

### Server Component Slots
```vue
<!-- components/ServerWrapper.server.vue -->
<template>
  <div class="server-wrapper">
    <slot />
  </div>
</template>

<!-- Usage with client island in slot -->
<ServerWrapper>
  <NuxtIsland name="InteractiveWidget" />
</ServerWrapper>
```

## Island Patterns

### Static Page with Interactive Elements
```vue
<!-- pages/blog/[slug].vue -->
<script setup lang="ts">
const route = useRoute();
const { data: post } = await useFetch(`/api/posts/${route.params.slug}`);
</script>

<template>
  <article>
    <!-- All static - rendered once -->
    <h1>{{ post?.title }}</h1>
    <div v-html="post?.content" />

    <!-- Interactive islands -->
    <NuxtIsland
      name="CommentSection"
      :props="{ postId: post?.id }"
    />

    <NuxtIsland
      name="ShareButtons"
      :props="{ url: $route.fullPath, title: post?.title }"
    />

    <NuxtIsland
      name="RelatedPosts"
      :props="{ tags: post?.tags }"
    />
  </article>
</template>
```

### Interactive Product Listing
```vue
<!-- pages/products/index.vue -->
<script setup lang="ts">
const { data: products } = await useFetch('/api/products');
</script>

<template>
  <div class="products">
    <h1>Products</h1>

    <!-- Filter island - needs interactivity -->
    <NuxtIsland name="ProductFilters" />

    <!-- Static product grid -->
    <div class="grid">
      <div v-for="product in products" :key="product.id" class="product">
        <img :src="product.image" :alt="product.name" />
        <h3>{{ product.name }}</h3>
        <p>{{ product.price }}</p>

        <!-- Interactive add to cart -->
        <NuxtIsland
          name="AddToCart"
          :props="{ productId: product.id }"
        />
      </div>
    </div>
  </div>
</template>
```

## Island Components Best Practices

### Keep Islands Small
```vue
<!-- Good - focused island -->
<!-- components/islands/LikeButton.vue -->
<script setup lang="ts">
const props = defineProps<{ postId: string }>();
const likes = ref(0);
const liked = ref(false);

async function toggleLike() {
  liked.value = !liked.value;
  likes.value += liked.value ? 1 : -1;
  await $fetch(`/api/posts/${props.postId}/like`, {
    method: 'POST',
    body: { liked: liked.value },
  });
}
</script>

<template>
  <button @click="toggleLike" :class="{ liked }">
    <HeartIcon />
    {{ likes }}
  </button>
</template>
```

### Pass Minimal Props
```vue
<!-- Good - only essential data -->
<NuxtIsland
  name="CartButton"
  :props="{ productId: product.id, price: product.price }"
/>

<!-- Avoid - too much data -->
<NuxtIsland
  name="CartButton"
  :props="{ product: entireProductObject }"
/>
```

### Use Source for Remote Islands
```vue
<!-- Fetch island from another server -->
<NuxtIsland
  name="RemoteWidget"
  source="https://widgets.example.com"
  :props="{ widgetId: '123' }"
/>
```

## Lazy Islands

```vue
<script setup lang="ts">
const showComments = ref(false);
</script>

<template>
  <article>
    <h1>{{ post.title }}</h1>
    <div v-html="post.content" />

    <button @click="showComments = true">
      Load Comments
    </button>

    <!-- Lazy loaded island -->
    <LazyNuxtIsland
      v-if="showComments"
      name="CommentSection"
      :props="{ postId: post.id }"
    />
  </article>
</template>
```

## Performance Benefits

### Before Islands
```
Page Load:
├── HTML (full page)
├── JavaScript (entire app)
└── Hydration (full page)
```

### With Islands
```
Page Load:
├── HTML (full page, static)
├── Island JS (small bundles)
└── Hydration (islands only)
```

### Bundle Size Comparison
```typescript
// Traditional SPA
// main.js: 150KB (all components)

// With Islands
// main.js: 10KB (minimal runtime)
// counter-island.js: 2KB
// comments-island.js: 5KB
// Total: 17KB (only loaded islands)
```

## When to Use Islands

### Good Use Cases
- Blog posts with interactive comments
- Product pages with add-to-cart
- Documentation with code playgrounds
- Landing pages with forms
- Content sites with minimal interactivity

### When Not to Use
- Highly interactive applications
- Real-time dashboards
- Complex single-page apps
- Apps where most content is dynamic

## Best Practices

1. **Start static** - Default to static, add islands for interactivity
2. **Small islands** - Keep interactive parts focused
3. **Minimal props** - Pass only what's needed
4. **Lazy load** - Load islands on demand when possible
5. **Server components** - Use for data-heavy, static content
