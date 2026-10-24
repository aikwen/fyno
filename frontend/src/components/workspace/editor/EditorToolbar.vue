<script setup>
import { computed, onBeforeUnmount, onMounted, reactive, ref, watch } from 'vue'
import Icon from '../../Icon.vue'
import headingIcon from '../../../assets/icon/editor/heading.svg'
import chevronDownIcon from '../../../assets/icon/editor/chevron-down.svg'
import orderedListIcon from '../../../assets/icon/editor/list-ordered.svg'
import bulletListIcon from '../../../assets/icon/editor/list.svg'
import taskListIcon from '../../../assets/icon/editor/list-checks.svg'
import quoteIcon from '../../../assets/icon/editor/quote.svg'
import codeBlockIcon from '../../../assets/icon/editor/square-code.svg'
import admonitionIcon from '../../../assets/icon/editor/message-square-warning.svg'
import mathIcon from '../../../assets/icon/editor/sigma.svg'
import boldIcon from '../../../assets/icon/editor/bold.svg'
import italicIcon from '../../../assets/icon/editor/italic.svg'
import strikeIcon from '../../../assets/icon/editor/strikethrough.svg'
import codeIcon from '../../../assets/icon/editor/code.svg'
import underlineIcon from '../../../assets/icon/editor/underline.svg'
import highlightIcon from '../../../assets/icon/editor/highlighter.svg'
import linkIcon from '../../../assets/icon/editor/link.svg'

const props = defineProps({
  editor: {
    type: Object,
    default: null,
  },
  disabled: {
    type: Boolean,
    default: false,
  },
})

const root = ref(null)
const headingButton = ref(null)
const headingMenu = ref(null)
const headingMenuOpen = ref(false)
const editorVersion = ref(0)
const menuPosition = reactive({ left: 0, top: 0 })

const toolbarDisabled = computed(() => (
  props.disabled || !props.editor || !props.editor.isEditable
))

const buttonClass = 'editor-toolbar-button flex h-8 w-8 shrink-0 items-center justify-center rounded-lg text-slate-600 transition-colors hover:bg-slate-100/90 hover:text-slate-900 focus:outline-none focus-visible:ring-2 focus-visible:ring-violet-300/70 disabled:pointer-events-none disabled:text-slate-300'

function refreshState() {
  editorVersion.value += 1
}

function bindEditor(current, previous) {
  previous?.off('transaction', refreshState)
  previous?.off('selectionUpdate', refreshState)
  current?.on('transaction', refreshState)
  current?.on('selectionUpdate', refreshState)
  refreshState()
}

function isActive(name, attributes) {
  editorVersion.value
  return props.editor?.isActive(name, attributes) ?? false
}

function activeClass(active) {
  return active ? 'bg-violet-100 text-violet-700 hover:bg-violet-100 hover:text-violet-700' : ''
}

function run(command) {
  if (!toolbarDisabled.value) {
    command()
  }
}

function updateHeadingMenuPosition() {
  const rect = headingButton.value?.getBoundingClientRect()
  if (!rect) {
    return
  }

  const menuWidth = 148
  menuPosition.left = Math.max(8, Math.min(rect.left, window.innerWidth - menuWidth - 8))
  menuPosition.top = rect.bottom + 8
}

function toggleHeadingMenu() {
  if (toolbarDisabled.value) {
    return
  }

  headingMenuOpen.value = !headingMenuOpen.value
  if (headingMenuOpen.value) {
    updateHeadingMenuPosition()
  }
}

function setTextStyle(level = null) {
  if (toolbarDisabled.value) {
    return
  }

  const chain = props.editor.chain().focus()
  if (level === null) {
    chain.setParagraph().run()
  } else {
    chain.toggleHeading({ level }).run()
  }
  headingMenuOpen.value = false
}

function normalizeLink(value) {
  const href = value.trim()
  if (!href) {
    return ''
  }

  if (/^(https?:\/\/|mailto:|tel:|#|\/(?!\/)|\.{1,2}\/)/i.test(href)) {
    return href
  }
  if (/^[\w.-]+\.[a-z]{2,}(?:[/?#].*)?$/i.test(href)) {
    return `https://${href}`
  }
  return null
}

function editLink() {
  if (toolbarDisabled.value) {
    return
  }

  const currentHref = props.editor.getAttributes('link').href ?? ''
  const value = window.prompt('输入链接地址；留空可移除链接', currentHref)
  if (value === null) {
    return
  }

  const href = normalizeLink(value)
  if (href === null) {
    window.alert('请输入有效的 http、https、mailto、tel 或相对链接。')
    return
  }

  const chain = props.editor.chain().focus()
  if (!href) {
    chain.extendMarkRange('link').unsetLink().run()
    return
  }

  if (isActive('link')) {
    chain.extendMarkRange('link')
  }
  chain.setLink({ href }).run()
}

function handlePointerDown(event) {
  if (
    headingMenuOpen.value &&
    !root.value?.contains(event.target) &&
    !headingMenu.value?.contains(event.target)
  ) {
    headingMenuOpen.value = false
  }
}

function handleKeyDown(event) {
  if (event.key === 'Escape') {
    headingMenuOpen.value = false
  }
}

function closeHeadingMenuOnScroll() {
  headingMenuOpen.value = false
}

watch(() => props.editor, bindEditor, { immediate: true })
watch(toolbarDisabled, (disabled) => {
  if (disabled) {
    headingMenuOpen.value = false
  }
})

onMounted(() => {
  document.addEventListener('pointerdown', handlePointerDown, true)
  document.addEventListener('keydown', handleKeyDown)
  window.addEventListener('resize', closeHeadingMenuOnScroll)
  document.addEventListener('scroll', closeHeadingMenuOnScroll, true)
})

onBeforeUnmount(() => {
  props.editor?.off('transaction', refreshState)
  props.editor?.off('selectionUpdate', refreshState)
  document.removeEventListener('pointerdown', handlePointerDown, true)
  document.removeEventListener('keydown', handleKeyDown)
  window.removeEventListener('resize', closeHeadingMenuOnScroll)
  document.removeEventListener('scroll', closeHeadingMenuOnScroll, true)
})
</script>

<template>
  <div
    ref="root"
    class="sticky top-3 z-20 mx-auto mb-6 mt-4 flex w-fit max-w-full items-center rounded-2xl border border-slate-200/75 bg-white/85 p-1.5 shadow-[0_8px_28px_rgba(15,23,42,0.10)] backdrop-blur-xl"
    role="toolbar"
    aria-label="正文格式工具栏"
  >
    <div class="editor-toolbar-scroll flex min-w-0 max-w-full items-center gap-0.5 overflow-x-auto">
      <button
        ref="headingButton"
        type="button"
        :class="[buttonClass, activeClass(isActive('heading'))]"
        :disabled="toolbarDisabled"
        title="段落与标题"
        aria-label="段落与标题"
        :aria-expanded="headingMenuOpen"
        @mousedown.prevent
        @click="toggleHeadingMenu"
      >
        <Icon :src="headingIcon" class="h-[18px] w-[18px]" />
        <Icon :src="chevronDownIcon" class="ml-[-3px] h-2.5 w-2.5" />
      </button>

      <button type="button" :class="[buttonClass, activeClass(isActive('orderedList'))]" :disabled="toolbarDisabled" title="有序列表" aria-label="有序列表" @mousedown.prevent @click="run(() => editor.chain().focus().toggleOrderedList().run())">
        <Icon :src="orderedListIcon" class="h-[18px] w-[18px]" />
      </button>
      <button type="button" :class="[buttonClass, activeClass(isActive('bulletList'))]" :disabled="toolbarDisabled" title="无序列表" aria-label="无序列表" @mousedown.prevent @click="run(() => editor.chain().focus().toggleBulletList().run())">
        <Icon :src="bulletListIcon" class="h-[18px] w-[18px]" />
      </button>
      <button type="button" :class="[buttonClass, activeClass(isActive('taskList'))]" :disabled="toolbarDisabled" title="任务列表" aria-label="任务列表" @mousedown.prevent @click="run(() => editor.chain().focus().toggleTaskList().run())">
        <Icon :src="taskListIcon" class="h-[18px] w-[18px]" />
      </button>
      <button type="button" :class="[buttonClass, activeClass(isActive('blockquote'))]" :disabled="toolbarDisabled" title="引用块" aria-label="引用块" @mousedown.prevent @click="run(() => editor.chain().focus().toggleBlockquote().run())">
        <Icon :src="quoteIcon" class="h-[18px] w-[18px]" />
      </button>
      <button type="button" :class="[buttonClass, activeClass(isActive('codeBlock'))]" :disabled="toolbarDisabled" title="代码块" aria-label="代码块" @mousedown.prevent @click="run(() => editor.chain().focus().toggleCodeBlock().run())">
        <Icon :src="codeBlockIcon" class="h-[18px] w-[18px]" />
      </button>
      <button type="button" :class="buttonClass" disabled title="Admonition 提示块将在后续版本支持" aria-label="Admonition 提示块，暂未支持">
        <Icon :src="admonitionIcon" class="h-[18px] w-[18px]" />
      </button>
      <button type="button" :class="buttonClass" disabled title="数学公式将在后续版本支持" aria-label="数学公式，暂未支持">
        <Icon :src="mathIcon" class="h-[18px] w-[18px]" />
      </button>

      <span aria-hidden="true" class="mx-1 h-5 w-px shrink-0 bg-slate-200/90" />

      <button type="button" :class="[buttonClass, activeClass(isActive('bold'))]" :disabled="toolbarDisabled" title="加粗" aria-label="加粗" @mousedown.prevent @click="run(() => editor.chain().focus().toggleBold().run())">
        <Icon :src="boldIcon" class="h-[18px] w-[18px]" />
      </button>
      <button type="button" :class="[buttonClass, activeClass(isActive('italic'))]" :disabled="toolbarDisabled" title="斜体" aria-label="斜体" @mousedown.prevent @click="run(() => editor.chain().focus().toggleItalic().run())">
        <Icon :src="italicIcon" class="h-[18px] w-[18px]" />
      </button>
      <button type="button" :class="[buttonClass, activeClass(isActive('strike'))]" :disabled="toolbarDisabled" title="删除线" aria-label="删除线" @mousedown.prevent @click="run(() => editor.chain().focus().toggleStrike().run())">
        <Icon :src="strikeIcon" class="h-[18px] w-[18px]" />
      </button>
      <button type="button" :class="[buttonClass, activeClass(isActive('code'))]" :disabled="toolbarDisabled" title="行内代码" aria-label="行内代码" @mousedown.prevent @click="run(() => editor.chain().focus().toggleCode().run())">
        <Icon :src="codeIcon" class="h-[18px] w-[18px]" />
      </button>
      <button type="button" :class="[buttonClass, activeClass(isActive('underline'))]" :disabled="toolbarDisabled" title="下划线" aria-label="下划线" @mousedown.prevent @click="run(() => editor.chain().focus().toggleUnderline().run())">
        <Icon :src="underlineIcon" class="h-[18px] w-[18px]" />
      </button>
      <button type="button" :class="[buttonClass, activeClass(isActive('highlight'))]" :disabled="toolbarDisabled" title="高亮" aria-label="高亮" @mousedown.prevent @click="run(() => editor.chain().focus().toggleHighlight().run())">
        <Icon :src="highlightIcon" class="h-[18px] w-[18px]" />
      </button>
      <button type="button" :class="[buttonClass, activeClass(isActive('link'))]" :disabled="toolbarDisabled" title="插入、修改或移除链接" aria-label="链接" @mousedown.prevent @click="editLink">
        <Icon :src="linkIcon" class="h-[18px] w-[18px]" />
      </button>
    </div>
  </div>

  <Teleport to="body">
    <div
      v-if="headingMenuOpen"
      ref="headingMenu"
      role="menu"
      class="fixed z-50 w-[148px] rounded-xl border border-slate-200/80 bg-white/95 p-1.5 text-sm text-slate-700 shadow-[0_10px_30px_rgba(15,23,42,0.13)] backdrop-blur-xl"
      :style="{ left: `${menuPosition.left}px`, top: `${menuPosition.top}px` }"
    >
      <button type="button" role="menuitem" class="flex h-8 w-full items-center rounded-lg px-3 text-left hover:bg-slate-100" :class="activeClass(isActive('paragraph'))" @mousedown.prevent @click="setTextStyle()">正文</button>
      <button v-for="level in [1, 2, 3]" :key="level" type="button" role="menuitem" class="flex h-8 w-full items-center rounded-lg px-3 text-left hover:bg-slate-100" :class="activeClass(isActive('heading', { level }))" @mousedown.prevent @click="setTextStyle(level)">H{{ level }}</button>
    </div>
  </Teleport>
</template>

<style scoped>
.editor-toolbar-scroll {
  scrollbar-width: none;
}

.editor-toolbar-scroll::-webkit-scrollbar {
  display: none;
}
</style>
