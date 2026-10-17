<script setup>
import { nextTick, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import Icon from './Icon.vue'

const props = defineProps({
  open: {
    type: Boolean,
    required: true,
  },
  x: {
    type: Number,
    default: 0,
  },
  y: {
    type: Number,
    default: 0,
  },
  items: {
    type: Array,
    default: () => [],
  },
})

const emit = defineEmits(['select', 'close'])
const menu = ref(null)
const left = ref(0)
const top = ref(0)

async function updatePosition() {
  if (!props.open) {
    return
  }

  await nextTick()

  const margin = 8
  const width = menu.value?.offsetWidth ?? 208
  const height = menu.value?.offsetHeight ?? 0

  left.value = Math.max(margin, Math.min(props.x, window.innerWidth - width - margin))
  top.value = Math.max(margin, Math.min(props.y, window.innerHeight - height - margin))
}

function selectAction(item) {
  emit('select', { id: item.id })
  emit('close')
}

function selectColor(color) {
  emit('select', { id: 'color', color })
  emit('close')
}

function handlePointerDown(event) {
  if (props.open && menu.value && !menu.value.contains(event.target)) {
    emit('close')
  }
}

function handleKeyDown(event) {
  if (props.open && event.key === 'Escape') {
    emit('close')
  }
}

watch(() => [props.open, props.x, props.y, props.items], updatePosition)

onMounted(() => {
  document.addEventListener('pointerdown', handlePointerDown, true)
  document.addEventListener('keydown', handleKeyDown)
  window.addEventListener('resize', updatePosition)
})

onBeforeUnmount(() => {
  document.removeEventListener('pointerdown', handlePointerDown, true)
  document.removeEventListener('keydown', handleKeyDown)
  window.removeEventListener('resize', updatePosition)
})
</script>

<template>
  <Teleport to="body">
    <div
      v-if="open"
      ref="menu"
      role="menu"
      class="fixed z-50 max-h-[calc(100vh-1rem)] w-52 overflow-y-auto rounded-md border border-slate-200 bg-white py-1 text-[13px] text-slate-700 shadow-lg"
      :style="{ left: `${left}px`, top: `${top}px` }"
      @contextmenu.prevent
    >
      <template v-for="(item, index) in items" :key="item.id ?? `${item.type}-${index}`">
        <button
          v-if="item.type === 'action'"
          type="button"
          role="menuitem"
          class="flex h-8 w-full items-center gap-2.5 px-3 text-left hover:bg-slate-100 active:bg-slate-200 focus:outline-none focus-visible:bg-slate-100"
          @click.stop="selectAction(item)"
        >
          <Icon :src="item.icon" class="h-4 w-4 shrink-0 text-slate-600" />
          <span class="truncate">{{ item.label }}</span>
        </button>

        <div v-else-if="item.type === 'separator'" class="mx-2 my-1 border-t border-slate-200" />

        <div v-else-if="item.type === 'colors'" class="px-3 py-2">
          <p class="mb-2 text-xs text-slate-500">颜色</p>
          <div class="flex items-center justify-between">
            <button
              v-for="color in item.options"
              :key="color"
              type="button"
              class="flex h-6 w-6 items-center justify-center rounded-full focus:outline-none focus-visible:ring-2 focus-visible:ring-slate-400/60"
              :class="{ 'ring-1 ring-slate-500': item.current === color }"
              :aria-label="`选择颜色 ${color}`"
              @click.stop="selectColor(color)"
            >
              <span class="h-4 w-4 rounded-full" :style="{ backgroundColor: color }" />
            </button>
          </div>
        </div>
      </template>
    </div>
  </Teleport>
</template>
