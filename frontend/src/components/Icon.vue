<script setup>
import { computed } from 'vue'

const props = defineProps({
  name: {
    type: String,
    required: true,
  },
})

const icons = import.meta.glob(
  '../assets/rail/*.svg',
  {
    eager: true,
    query: '?raw',
    import: 'default',
  },
)

const svg = computed(() => {
  const path = `../assets/rail/${props.name}.svg`

  if (!icons[path]) {
    console.warn(`[Icon] icon not found: ${props.name}`)
    return ''
  }

  return icons[path]
})
</script>

<template>
  <span
    class="inline-flex shrink-0 items-center justify-center [&>svg]:h-full [&>svg]:w-full"
    aria-hidden="true"
    v-html="svg"
  />
</template>