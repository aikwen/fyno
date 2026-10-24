<script setup>
import { nextTick, onBeforeUnmount, onMounted, ref, watch } from 'vue'

const props = defineProps({
  editor: {
    type: Object,
    default: null,
  },
  scrollContainer: {
    type: Object,
    default: null,
  },
})

const items = ref([])
const activePosition = ref(null)

let activeFrame = 0

function headingElement(position) {
  const node = props.editor?.view.nodeDOM(position)
  return node instanceof HTMLElement ? node : node?.parentElement ?? null
}

function updateActiveHeading() {
  const container = props.scrollContainer
  if (!container || items.value.length === 0) {
    activePosition.value = null
    return
  }

  if (container.scrollTop + container.clientHeight >= container.scrollHeight - 2) {
    activePosition.value = items.value.at(-1).position
    return
  }

  const toolbar = container.querySelector('[data-editor-toolbar-dock]')
  const referenceLine = (toolbar?.getBoundingClientRect().bottom ??
    container.getBoundingClientRect().top) + 16
  let currentPosition = items.value[0].position

  for (const item of items.value) {
    const element = headingElement(item.position)
    if (!element) {
      continue
    }
    if (element.getBoundingClientRect().top <= referenceLine) {
      currentPosition = item.position
    } else {
      break
    }
  }

  activePosition.value = currentPosition
}

function scheduleActiveHeading() {
  window.cancelAnimationFrame(activeFrame)
  activeFrame = window.requestAnimationFrame(updateActiveHeading)
}

async function rebuildItems() {
  const nextItems = []
  props.editor?.state.doc.descendants((node, position) => {
    if (node.type.name === 'heading' && node.attrs.level >= 1 && node.attrs.level <= 5) {
      nextItems.push({
        key: `${position}-${node.attrs.level}`,
        position,
        level: node.attrs.level,
        text: node.textContent.trim() || '未命名标题',
      })
    }
  })

  items.value = nextItems
  await nextTick()
  scheduleActiveHeading()
}

function handleEditorTransaction({ transaction }) {
  if (transaction.docChanged) {
    void rebuildItems()
  }
}

function bindEditor(current, previous) {
  previous?.off('transaction', handleEditorTransaction)
  current?.on('transaction', handleEditorTransaction)
  void rebuildItems()
}

function bindScrollContainer(current, previous) {
  previous?.removeEventListener('scroll', scheduleActiveHeading)
  current?.addEventListener('scroll', scheduleActiveHeading, { passive: true })
  scheduleActiveHeading()
}

function jumpToHeading(item) {
  const element = headingElement(item.position)
  if (!element) {
    return
  }

  activePosition.value = item.position
  props.editor.chain()
    .setTextSelection(item.position + 1)
    .focus(undefined, { scrollIntoView: false })
    .run()
  element.scrollIntoView({ behavior: 'smooth', block: 'start' })
}

watch(() => props.editor, bindEditor, { immediate: true })
watch(() => props.scrollContainer, bindScrollContainer, { immediate: true })

onMounted(() => {
  window.addEventListener('resize', scheduleActiveHeading)
  void rebuildItems()
})

onBeforeUnmount(() => {
  props.editor?.off('transaction', handleEditorTransaction)
  props.scrollContainer?.removeEventListener('scroll', scheduleActiveHeading)
  window.removeEventListener('resize', scheduleActiveHeading)
  window.cancelAnimationFrame(activeFrame)
})
</script>

<template>
  <aside
    v-if="items.length"
    aria-label="页面目录"
    class="workspace-scroll sticky top-[76px] max-h-[calc(100vh-7rem)] w-48 shrink-0 self-start overflow-y-auto pr-1"
  >
    <p class="mb-2 px-2 text-xs font-medium tracking-wide text-slate-400">
      目录
    </p>
    <nav>
      <button
        v-for="item in items"
        :key="item.key"
        type="button"
        class="mb-0.5 block h-8 w-full cursor-pointer truncate border-l-2 pr-2 text-left text-[13px] transition-colors focus:outline-none focus-visible:ring-2 focus-visible:ring-violet-300/70"
        :class="activePosition === item.position
          ? 'border-violet-500 bg-violet-50/70 text-violet-700'
          : 'border-transparent text-slate-500 hover:bg-slate-100/80 hover:text-slate-700'"
        :style="{ paddingLeft: `${8 + (item.level - 1) * 12}px` }"
        :title="item.text"
        @click="jumpToHeading(item)"
      >
        {{ item.text }}
      </button>
    </nav>
  </aside>
</template>
