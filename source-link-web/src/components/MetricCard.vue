<script setup lang="ts">
defineProps<{
  title: string
  value: string | number
  note?: string
  accent?: 'teal' | 'copper' | 'slate'
}>()
</script>

<template>
  <div
    class="group rounded-[22px] border p-5 transition-transform duration-300 hover:-translate-y-0.5"
    :class="{
      'border-teal-200 bg-teal-50/80': accent === 'teal',
      'border-amber-200 bg-amber-50/80': accent === 'copper',
      'border-slate-200 bg-slate-50/80': accent === 'slate' || !accent,
    }"
  >
    <p class="text-xs uppercase tracking-[0.28em] text-[color:var(--text-muted)]">{{ title }}</p>
    <div class="mt-3 flex items-end justify-between gap-3">
      <div class="text-3xl font-semibold tracking-tight text-[color:var(--text-main)]">{{ value }}</div>
      <div class="h-px flex-1 bg-black/5" />
    </div>
    <p v-if="note" class="mt-3 text-sm text-[color:var(--text-secondary)]">{{ note }}</p>
  </div>
</template>
