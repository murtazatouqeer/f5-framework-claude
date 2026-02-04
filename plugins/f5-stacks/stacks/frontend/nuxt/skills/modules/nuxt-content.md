---
name: nuxt-content
description: Nuxt Content module for file-based CMS
applies_to: nuxt
---

# Nuxt Content

## Overview

Nuxt Content is a file-based CMS that allows you to write Markdown, YAML, and JSON files and query them like a database.

## Setup

```bash
npx nuxi@latest module add content
```

```typescript
// nuxt.config.ts
export default defineNuxtConfig({
  modules: ['@nuxt/content'],

  content: {
    highlight: {
      theme: 'github-dark',
      preload: ['typescript', 'vue', 'bash'],
    },
  },
});
```

## Content Directory

```
content/
├── index.md              # Homepage content
├── about.md              # /about
├── blog/
│   ├── index.md          # /blog
│   ├── post-1.md         # /blog/post-1
│   └── post-2.md         # /blog/post-2
└── docs/
    ├── 1.getting-started/
    │   └── 1.introduction.md
    └── 2.guide/
        └── 1.installation.md
```

## Markdown Front Matter

```markdown
---
title: My Blog Post
description: A great article about Nuxt
date: 2024-01-15
author: John Doe
tags:
  - nuxt
  - vue
  - tutorial
image: /images/blog/post-1.jpg
draft: false
---

# Introduction

This is my blog post content...
```

## Querying Content

### Basic Query

```vue
<script setup lang="ts">
// Single document
const { data: page } = await useAsyncData('home', () =>
  queryContent('/').findOne()
);

// List documents
const { data: posts } = await useAsyncData('posts', () =>
  queryContent('blog').find()
);
</script>
```

### Filtered Query

```vue
<script setup lang="ts">
const { data: posts } = await useAsyncData('posts', () =>
  queryContent('blog')
    .where({ draft: { $ne: true } })
    .sort({ date: -1 })
    .limit(10)
    .find()
);
</script>
```

### Full Query API

```typescript
const posts = await queryContent('blog')
  // Filtering
  .where({ published: true })
  .where({ tags: { $contains: 'nuxt' } })
  .where({ date: { $gte: '2024-01-01' } })

  // Sorting
  .sort({ date: -1, title: 1 })

  // Pagination
  .skip(0)
  .limit(10)

  // Field selection
  .only(['title', 'description', 'date', '_path'])
  .without(['body'])

  // Execute
  .find();
```

## Rendering Content

### ContentDoc Component

```vue
<!-- pages/[...slug].vue -->
<template>
  <ContentDoc>
    <template #not-found>
      <h1>404 - Page Not Found</h1>
    </template>
  </ContentDoc>
</template>
```

### ContentRenderer

```vue
<script setup lang="ts">
const { data: post } = await useAsyncData('post', () =>
  queryContent(route.path).findOne()
);
</script>

<template>
  <article v-if="post">
    <h1>{{ post.title }}</h1>
    <ContentRenderer :value="post" />
  </article>
</template>
```

### Prose Components

```vue
<!-- Custom h1 rendering -->
<!-- components/content/ProseH1.vue -->
<template>
  <h1 class="text-4xl font-bold mb-4">
    <slot />
  </h1>
</template>

<!-- Custom code block -->
<!-- components/content/ProseCode.vue -->
<script setup lang="ts">
defineProps<{
  code: string;
  language: string;
  filename?: string;
}>();
</script>

<template>
  <div class="code-block">
    <div v-if="filename" class="filename">{{ filename }}</div>
    <pre><code :class="`language-${language}`">{{ code }}</code></pre>
  </div>
</template>
```

## Blog Example

### Blog List Page

```vue
<!-- pages/blog/index.vue -->
<script setup lang="ts">
const { data: posts } = await useAsyncData('posts', () =>
  queryContent('blog')
    .where({ draft: { $ne: true } })
    .sort({ date: -1 })
    .find()
);
</script>

<template>
  <div>
    <h1>Blog</h1>

    <div class="grid gap-6">
      <article v-for="post in posts" :key="post._path">
        <NuxtLink :to="post._path">
          <img v-if="post.image" :src="post.image" :alt="post.title" />
          <h2>{{ post.title }}</h2>
          <p>{{ post.description }}</p>
          <time>{{ formatDate(post.date) }}</time>
        </NuxtLink>
      </article>
    </div>
  </div>
</template>
```

### Blog Post Page

```vue
<!-- pages/blog/[...slug].vue -->
<script setup lang="ts">
const route = useRoute();
const { data: post } = await useAsyncData(`post-${route.path}`, () =>
  queryContent(route.path).findOne()
);

if (!post.value) {
  throw createError({ statusCode: 404, message: 'Post not found' });
}

useSeoMeta({
  title: post.value.title,
  description: post.value.description,
  ogImage: post.value.image,
});
</script>

<template>
  <article v-if="post">
    <header>
      <h1>{{ post.title }}</h1>
      <p>{{ post.description }}</p>
      <time>{{ formatDate(post.date) }}</time>
    </header>

    <ContentRenderer :value="post" />

    <!-- Table of Contents -->
    <aside v-if="post.body?.toc">
      <nav>
        <ul>
          <li v-for="link in post.body.toc.links" :key="link.id">
            <a :href="`#${link.id}`">{{ link.text }}</a>
          </li>
        </ul>
      </nav>
    </aside>
  </article>
</template>
```

## Navigation

### Auto-generated Navigation

```vue
<script setup lang="ts">
const { data: navigation } = await useAsyncData('navigation', () =>
  fetchContentNavigation()
);
</script>

<template>
  <nav>
    <ContentNavigation v-slot="{ navigation }">
      <ul>
        <li v-for="link in navigation" :key="link._path">
          <NuxtLink :to="link._path">{{ link.title }}</NuxtLink>
        </li>
      </ul>
    </ContentNavigation>
  </nav>
</template>
```

### Custom Navigation Query

```vue
<script setup lang="ts">
const { data: navigation } = await useAsyncData('docs-nav', () =>
  fetchContentNavigation(queryContent('docs'))
);
</script>
```

## MDC (Markdown Components)

### Using Components in Markdown

```markdown
<!-- content/blog/post.md -->
---
title: My Post
---

# Introduction

::alert{type="info"}
This is an info alert!
::

::card
  ::card-header
  Card Title
  ::
  Card content here.
::

::code-group
  ```ts [nuxt.config.ts]
  export default defineNuxtConfig({})
  ```

  ```ts [app.vue]
  <template><div>Hello</div></template>
  ```
::
```

### Creating MDC Components

```vue
<!-- components/content/Alert.vue -->
<script setup lang="ts">
defineProps<{
  type?: 'info' | 'warning' | 'error' | 'success';
}>();
</script>

<template>
  <div :class="['alert', `alert-${type}`]">
    <slot />
  </div>
</template>
```

## Search

```vue
<script setup lang="ts">
const search = ref('');

const { data: results } = await useAsyncData(
  'search',
  () => {
    if (!search.value) return [];
    return queryContent()
      .where({
        $or: [
          { title: { $icontains: search.value } },
          { description: { $icontains: search.value } },
        ],
      })
      .find();
  },
  { watch: [search] }
);
</script>

<template>
  <div>
    <input v-model="search" placeholder="Search..." />
    <ul v-if="results?.length">
      <li v-for="result in results" :key="result._path">
        <NuxtLink :to="result._path">{{ result.title }}</NuxtLink>
      </li>
    </ul>
  </div>
</template>
```

## Best Practices

1. **Use front matter** - Structured metadata
2. **Organize with folders** - Clear content hierarchy
3. **Custom prose components** - Consistent styling
4. **MDC for interactivity** - Components in markdown
5. **Generate navigation** - Use fetchContentNavigation
6. **SEO from content** - Use front matter for meta
