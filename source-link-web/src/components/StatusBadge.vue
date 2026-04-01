<script setup lang="ts">
import { computed } from 'vue'
import { NTag } from 'naive-ui'

const props = defineProps<{
  value?: string | number | boolean | null
  successLabel?: string
  errorLabel?: string
}>()

const isEnabled = computed(() => props.value === '0' || props.value === 0 || props.value === true)
const tagType = computed(() => (isEnabled.value ? 'success' : 'warning'))
const label = computed(() => (isEnabled.value ? props.successLabel ?? '启用' : props.errorLabel ?? '停用'))
</script>

<template>
  <NTag :type="tagType" size="small" round>
    {{ label }}
  </NTag>
</template>
