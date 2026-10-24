<script setup>
import { computed, nextTick, onBeforeUnmount, onMounted, reactive, ref } from 'vue'
import katex from 'katex'

const props = defineProps({
  editor: {
    type: Object,
    default: null,
  },
})

const panel = ref(null)
const textarea = ref(null)
const visible = ref(false)
const mode = ref('inline')
const latex = ref('')
const commandError = ref('')
const editingPosition = ref(null)
const insertionPosition = ref(null)
const panelPosition = reactive({ left: 0, top: 0 })
let anchorRect = null

const isEditing = computed(() => editingPosition.value !== null)
const preview = computed(() => {
  const source = latex.value.trim()
  if (!source) {
    return { html: '', error: '' }
  }

  try {
    return {
      html: katex.renderToString(source, {
        displayMode: mode.value === 'block',
        throwOnError: true,
        trust: false,
      }),
      error: '',
    }
  } catch (error) {
    return {
      html: '',
      error: error instanceof Error ? error.message : '公式语法无效',
    }
  }
})

function positionPanel(rect) {
  anchorRect = rect ? {
    left: rect.left,
    right: rect.right,
    top: rect.top,
    bottom: rect.bottom,
  } : null

  const width = 400
  const anchorLeft = anchorRect?.left ?? (window.innerWidth - width) / 2
  panelPosition.left = Math.max(8, Math.min(anchorLeft, window.innerWidth - width - 8))
  panelPosition.top = (anchorRect?.bottom ?? 72) + 8

  nextTick(() => {
    const height = panel.value?.getBoundingClientRect().height ?? 0
    if (panelPosition.top + height > window.innerHeight - 8 && anchorRect) {
      panelPosition.top = Math.max(8, anchorRect.top - height - 8)
    }
  })
}

async function focusInput() {
  await nextTick()
  textarea.value?.focus({ preventScroll: true })
  textarea.value?.select()
}

function openInsert(options = {}) {
  if (!props.editor) {
    return
  }

  mode.value = options.mode === 'block' ? 'block' : 'inline'
  latex.value = ''
  commandError.value = ''
  editingPosition.value = null
  insertionPosition.value = Number.isInteger(options.position)
    ? options.position
    : props.editor.state.selection.to
  visible.value = true
  positionPanel(options.rect)
  void focusInput()
}

function openEdit(options = {}) {
  if (!props.editor || !Number.isInteger(options.position)) {
    return
  }

  mode.value = options.kind === 'block' ? 'block' : 'inline'
  latex.value = options.latex ?? ''
  commandError.value = ''
  editingPosition.value = options.position
  insertionPosition.value = null
  visible.value = true
  positionPanel(options.rect)
  void focusInput()
}

function close() {
  visible.value = false
  commandError.value = ''
  editingPosition.value = null
  insertionPosition.value = null
}

function applyFormula() {
  const source = latex.value.trim()
  if (!props.editor || !source) {
    commandError.value = '请输入公式'
    return
  }
  if (preview.value.error) {
    commandError.value = preview.value.error
    return
  }

  try {
    let applied = false
    if (isEditing.value) {
      const command = mode.value === 'block' ? 'updateBlockMath' : 'updateInlineMath'
      applied = props.editor.chain().focus()[command]({
        latex: source,
        pos: editingPosition.value,
      }).run()
    } else {
      const command = mode.value === 'block' ? 'insertBlockMath' : 'insertInlineMath'
      applied = props.editor.chain().focus()[command]({
        latex: source,
        pos: insertionPosition.value,
      }).run()
    }

    if (!applied) {
      commandError.value = '当前位置无法插入公式'
      return
    }
    close()
  } catch (error) {
    commandError.value = error instanceof Error ? error.message : '公式操作失败'
  }
}

function handleDocumentPointerDown(event) {
  if (visible.value && !panel.value?.contains(event.target)) {
    close()
  }
}

function handleDocumentKeyDown(event) {
  if (visible.value && event.key === 'Escape') {
    event.preventDefault()
    close()
  }
}

function handleViewportChange() {
  if (visible.value && anchorRect) {
    positionPanel(anchorRect)
  }
}

function handleDocumentScroll(event) {
  if (visible.value && !panel.value?.contains(event.target)) {
    close()
  }
}

onMounted(() => {
  document.addEventListener('pointerdown', handleDocumentPointerDown, true)
  document.addEventListener('keydown', handleDocumentKeyDown)
  document.addEventListener('scroll', handleDocumentScroll, true)
  window.addEventListener('resize', handleViewportChange)
})

onBeforeUnmount(() => {
  document.removeEventListener('pointerdown', handleDocumentPointerDown, true)
  document.removeEventListener('keydown', handleDocumentKeyDown)
  document.removeEventListener('scroll', handleDocumentScroll, true)
  window.removeEventListener('resize', handleViewportChange)
})

defineExpose({ openInsert, openEdit, close })
</script>

<template>
  <Teleport to="body">
    <div
      v-if="visible"
      ref="panel"
      class="fixed z-50 w-[min(400px,calc(100vw-16px))] rounded-xl border border-slate-200/80 bg-white/95 p-3 shadow-lg shadow-slate-900/10 backdrop-blur-xl"
      :style="{ left: `${panelPosition.left}px`, top: `${panelPosition.top}px` }"
      role="dialog"
      aria-label="数学公式编辑器"
      @mousedown.stop
    >
      <div class="mb-2 flex items-center justify-between gap-3">
        <span class="text-xs font-medium text-slate-600">
          {{ isEditing ? '编辑公式' : '插入公式' }}
        </span>
        <div class="flex rounded-lg bg-slate-100 p-0.5" aria-label="公式类型">
          <button
            type="button"
            class="rounded-md px-2 py-1 text-xs transition-colors"
            :class="mode === 'inline' ? 'bg-white text-violet-700 shadow-sm' : 'text-slate-500 hover:text-slate-700'"
            :disabled="isEditing"
            @click="mode = 'inline'"
          >
            行内
          </button>
          <button
            type="button"
            class="rounded-md px-2 py-1 text-xs transition-colors"
            :class="mode === 'block' ? 'bg-white text-violet-700 shadow-sm' : 'text-slate-500 hover:text-slate-700'"
            :disabled="isEditing"
            @click="mode = 'block'"
          >
            块级
          </button>
        </div>
      </div>

      <textarea
        ref="textarea"
        v-model="latex"
        rows="3"
        class="block w-full resize-y rounded-lg border border-slate-200 bg-white px-3 py-2 font-mono text-sm leading-5 text-slate-800 outline-none transition focus:border-violet-400 focus:ring-2 focus:ring-violet-100"
        placeholder="例如：E = mc^2"
        spellcheck="false"
        @keydown.ctrl.enter.prevent="applyFormula"
      />

      <p class="mt-1 text-right text-[11px] text-slate-400">
        Ctrl + Enter 应用 · Esc 取消
      </p>

      <div class="mt-2 min-h-12 overflow-x-auto rounded-lg border border-slate-100 bg-slate-50 px-3 py-2 text-center text-slate-800">
        <span v-if="!latex.trim()" class="text-xs text-slate-400">公式预览</span>
        <div v-else-if="preview.html" v-html="preview.html" />
        <span v-else class="text-xs text-red-600">{{ preview.error }}</span>
      </div>

      <div class="mt-2 flex min-h-8 items-center justify-between gap-3">
        <p class="min-w-0 text-xs text-red-600">
          {{ commandError }}
        </p>
        <button
          type="button"
          class="shrink-0 rounded-lg bg-violet-600 px-3 py-1.5 text-xs font-medium text-white transition-colors hover:bg-violet-700 focus:outline-none focus-visible:ring-2 focus-visible:ring-violet-300 disabled:cursor-not-allowed disabled:bg-slate-300"
          :disabled="!latex.trim() || Boolean(preview.error)"
          @click="applyFormula"
        >
          应用
        </button>
      </div>
    </div>
  </Teleport>
</template>
