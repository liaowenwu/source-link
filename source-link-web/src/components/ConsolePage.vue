<script setup lang="ts">
defineProps<{
  title: string
  eyebrow?: string
  description?: string
}>()
</script>

<template>
  <div class="space-y-5">
    <div class="rounded-[24px] border border-[color:var(--panel-border)] bg-[color:var(--panel-soft)] p-6 shadow-[0_20px_60px_rgba(18,35,41,0.06)]">
      <div class="flex flex-col gap-4 lg:flex-row lg:items-end lg:justify-between">
        <div class="space-y-2">
          <p v-if="eyebrow" class="text-xs uppercase tracking-[0.3em] text-[color:var(--text-muted)]">{{ eyebrow }}</p>
          <h1 class="text-3xl font-semibold tracking-tight text-[color:var(--text-main)]">{{ title }}</h1>
          <p v-if="description" class="max-w-3xl text-sm leading-6 text-[color:var(--text-secondary)]">{{ description }}</p>
        </div>
        <div class="flex flex-wrap items-center gap-3">
          <slot name="actions" />
        </div>
      </div>
    </div>
    <slot />
  </div>
</template>
