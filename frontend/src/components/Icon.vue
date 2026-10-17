<script setup>
import { computed } from 'vue'

const props = defineProps({
  src: {
    type: String,
    required: true,
  },
  color: {
    type: String,
    default: 'currentColor',
  },
})

const iconStyle = computed(() => ({
  '--icon-url': `url(${JSON.stringify(props.src)})`,
  color: props.color,
}))
</script>

<template>
  <span class="mask-icon" :style="iconStyle" aria-hidden="true" />
</template>
