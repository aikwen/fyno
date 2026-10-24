<script setup>
import { computed, nextTick, onBeforeUnmount, onMounted, reactive, ref, watch } from 'vue'
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
import deleteIcon from '../../../assets/icon/delete.svg'
import { clearLinkSelection, showLinkSelection } from './LinkSelection.js'

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

const toolbarItems = [
  { id: 'heading', title: '段落与标题', icon: headingIcon, activeName: 'heading' },
  { id: 'ordered-list', title: '有序列表', icon: orderedListIcon, activeName: 'orderedList' },
  { id: 'bullet-list', title: '无序列表', icon: bulletListIcon, activeName: 'bulletList' },
  { id: 'task-list', title: '任务列表', icon: taskListIcon, activeName: 'taskList' },
  { id: 'blockquote', title: '引用块', icon: quoteIcon, activeName: 'blockquote' },
  { id: 'code-block', title: '代码块', icon: codeBlockIcon, activeName: 'codeBlock' },
  { id: 'admonition', title: 'Admonition 提示块将在后续版本支持', icon: admonitionIcon, disabled: true },
  { id: 'math', title: '数学公式将在后续版本支持', icon: mathIcon, disabled: true },
  { id: 'separator', type: 'separator' },
  { id: 'bold', title: '加粗', icon: boldIcon, activeName: 'bold' },
  { id: 'italic', title: '斜体', icon: italicIcon, activeName: 'italic' },
  { id: 'strike', title: '删除线', icon: strikeIcon, activeName: 'strike' },
  { id: 'code', title: '行内代码', icon: codeIcon, activeName: 'code' },
  { id: 'underline', title: '下划线', icon: underlineIcon, activeName: 'underline' },
  { id: 'highlight', title: '高亮', icon: highlightIcon, activeName: 'highlight' },
  { id: 'link', title: '插入、修改或移除链接', icon: linkIcon, activeName: 'link' },
]

const highlightColors = [
  { name: '黄色', value: '#fef3c7' },
  { name: '绿色', value: '#dcfce7' },
  { name: '蓝色', value: '#dbeafe' },
  { name: '紫色', value: '#ede9fe' },
  { name: '粉色', value: '#fce7f3' },
  { name: '红色', value: '#fee2e2' },
]

const root = ref(null)
const measurement = ref(null)
const headingButton = ref(null)
const headingMenu = ref(null)
const headingMenuOpen = ref(false)
const highlightButton = ref(null)
const highlightMenu = ref(null)
const highlightMenuOpen = ref(false)
const linkButton = ref(null)
const linkMenu = ref(null)
const linkInput = ref(null)
const linkMenuOpen = ref(false)
const linkDraft = ref('')
const linkError = ref('')
const editorVersion = ref(0)
const visibleCount = ref(toolbarItems.length)
const menuPosition = reactive({ left: 0, top: 0 })
const highlightMenuPosition = reactive({ left: 0, top: 0 })
const linkMenuPosition = reactive({ left: 0, top: 0 })

let resizeObserver = null
let resizeFrame = 0

const toolbarDisabled = computed(() => (
  props.disabled || !props.editor || !props.editor.isEditable
))
const hasHiddenItems = computed(() => visibleCount.value < toolbarItems.length)
const buttonClass = 'flex h-8 w-8 shrink-0 items-center justify-center rounded-lg text-slate-600 transition-colors hover:bg-slate-100/90 hover:text-slate-900 focus:outline-none focus-visible:ring-2 focus-visible:ring-violet-300/70 disabled:pointer-events-none disabled:text-slate-300'

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

function isItemActive(item) {
  return item.activeName ? isActive(item.activeName) : false
}

function activeClass(active) {
  return active ? 'bg-violet-100 text-violet-700 hover:bg-violet-100 hover:text-violet-700' : ''
}

function isVisible(index) {
  return index < visibleCount.value
}

function setHeadingButton(element) {
  if (element) {
    headingButton.value = element
  }
}

function setHighlightButton(element) {
  if (element) {
    highlightButton.value = element
  }
}

function setLinkButton(element) {
  if (element) {
    linkButton.value = element
  }
}

function execute(item) {
  if (toolbarDisabled.value || item.disabled) {
    return
  }

  const commands = {
    'ordered-list': () => props.editor.chain().focus().toggleOrderedList().run(),
    'bullet-list': () => props.editor.chain().focus().toggleBulletList().run(),
    'task-list': () => props.editor.chain().focus().toggleTaskList().run(),
    blockquote: () => props.editor.chain().focus().toggleBlockquote().run(),
    'code-block': () => props.editor.chain().focus().toggleCodeBlock().run(),
    bold: () => props.editor.chain().focus().toggleBold().run(),
    italic: () => props.editor.chain().focus().toggleItalic().run(),
    strike: () => props.editor.chain().focus().toggleStrike().run(),
    code: () => props.editor.chain().focus().toggleCode().run(),
    underline: () => props.editor.chain().focus().toggleUnderline().run(),
  }

  if (item.id === 'heading') {
    toggleHeadingMenu()
  } else if (item.id === 'highlight') {
    toggleHighlightMenu()
  } else if (item.id === 'link') {
    toggleLinkMenu()
  } else {
    commands[item.id]?.()
  }
}

function itemOuterWidth(element) {
  const style = window.getComputedStyle(element)
  return element.getBoundingClientRect().width +
    Number.parseFloat(style.marginLeft || 0) +
    Number.parseFloat(style.marginRight || 0)
}

function recalculateVisibleItems() {
  const availableWidth = root.value?.clientWidth ?? 0
  const measureElement = measurement.value
  if (!availableWidth || !measureElement) {
    return
  }

  const itemElements = Array.from(measureElement.querySelectorAll('[data-toolbar-item]'))
  const ellipsisElement = measureElement.querySelector('[data-toolbar-ellipsis]')
  if (itemElements.length !== toolbarItems.length || !ellipsisElement) {
    return
  }

  const style = window.getComputedStyle(measureElement)
  const gap = Number.parseFloat(style.columnGap || 0)
  const chrome = Number.parseFloat(style.paddingLeft || 0) +
    Number.parseFloat(style.paddingRight || 0) +
    Number.parseFloat(style.borderLeftWidth || 0) +
    Number.parseFloat(style.borderRightWidth || 0)
  const widths = itemElements.map(itemOuterWidth)
  const ellipsisWidth = itemOuterWidth(ellipsisElement)
  const fullWidth = chrome + widths.reduce((sum, width) => sum + width, 0) +
    gap * Math.max(0, widths.length - 1)

  if (fullWidth <= availableWidth) {
    visibleCount.value = toolbarItems.length
    return
  }

  let nextCount = 0
  for (let count = toolbarItems.length - 1; count >= 0; count -= 1) {
    if (count === 9) {
      continue
    }

    const prefixWidth = widths.slice(0, count).reduce((sum, width) => sum + width, 0)
    const requiredWidth = chrome + prefixWidth + ellipsisWidth + gap * count
    if (requiredWidth <= availableWidth) {
      nextCount = count
      break
    }
  }

  visibleCount.value = nextCount
}

function scheduleToolbarMeasurement() {
  window.cancelAnimationFrame(resizeFrame)
  resizeFrame = window.requestAnimationFrame(recalculateVisibleItems)
}

function updateMenuPosition(button, position, menuWidth) {
  const rect = button?.getBoundingClientRect()
  if (!rect) {
    return
  }

  position.left = Math.max(8, Math.min(rect.left, window.innerWidth - menuWidth - 8))
  position.top = rect.bottom + 8
}

function toggleHeadingMenu() {
  if (toolbarDisabled.value) {
    return
  }

  headingMenuOpen.value = !headingMenuOpen.value
  if (headingMenuOpen.value) {
    highlightMenuOpen.value = false
    linkMenuOpen.value = false
    updateMenuPosition(headingButton.value, menuPosition, 148)
  }
}

function toggleHighlightMenu() {
  if (toolbarDisabled.value) {
    return
  }

  highlightMenuOpen.value = !highlightMenuOpen.value
  if (highlightMenuOpen.value) {
    headingMenuOpen.value = false
    linkMenuOpen.value = false
    updateMenuPosition(highlightButton.value, highlightMenuPosition, 260)
  }
}

function setHighlightColor(color) {
  if (toolbarDisabled.value) {
    return
  }

  props.editor.chain().focus().setHighlight({ color }).run()
  highlightMenuOpen.value = false
}

function clearHighlight() {
  if (toolbarDisabled.value) {
    return
  }

  props.editor.chain().focus().unsetHighlight().run()
  highlightMenuOpen.value = false
}

async function toggleLinkMenu() {
  if (toolbarDisabled.value) {
    return
  }

  linkMenuOpen.value = !linkMenuOpen.value
  if (!linkMenuOpen.value) {
    return
  }

  showLinkSelection(props.editor)
  headingMenuOpen.value = false
  highlightMenuOpen.value = false
  linkDraft.value = props.editor.getAttributes('link').href ?? ''
  linkError.value = ''
  updateMenuPosition(linkButton.value, linkMenuPosition, 300)
  await nextTick()
  linkInput.value?.focus({ preventScroll: true })
  linkInput.value?.select()
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
  return value.trim()
}

function applyLinkDraft() {
  if (toolbarDisabled.value) {
    return
  }

  const href = normalizeLink(linkDraft.value)
  if (!href) {
    linkError.value = ''
    return
  }

  if (href && props.editor.state.selection.empty && !isActive('link')) {
    linkError.value = '请先选择要添加链接的文字'
    return
  }

  const chain = props.editor.chain()
  if (isActive('link')) {
    chain.extendMarkRange('link')
  }
  chain.setLink({ href }).run()
  linkError.value = ''
}

function removeLink() {
  if (toolbarDisabled.value) {
    return
  }

  props.editor.chain().focus().extendMarkRange('link').unsetLink().run()
  linkDraft.value = ''
  linkMenuOpen.value = false
  linkError.value = ''
}

function handlePointerDown(event) {
  if (
    headingMenuOpen.value &&
    !root.value?.contains(event.target) &&
    !headingMenu.value?.contains(event.target)
  ) {
    headingMenuOpen.value = false
  }
  if (
    highlightMenuOpen.value &&
    !root.value?.contains(event.target) &&
    !highlightMenu.value?.contains(event.target)
  ) {
    highlightMenuOpen.value = false
  }
  if (
    linkMenuOpen.value &&
    !root.value?.contains(event.target) &&
    !linkMenu.value?.contains(event.target)
  ) {
    linkMenuOpen.value = false
    linkError.value = ''
  }
}

function handleKeyDown(event) {
  if (event.key === 'Escape') {
    headingMenuOpen.value = false
    highlightMenuOpen.value = false
    linkMenuOpen.value = false
    linkError.value = ''
  }
}

function closeHeadingMenuOnScroll() {
  headingMenuOpen.value = false
  highlightMenuOpen.value = false
  if (document.activeElement !== linkInput.value) {
    linkMenuOpen.value = false
    linkError.value = ''
  }
}

watch(() => props.editor, bindEditor, { immediate: true })
watch(linkMenuOpen, (open) => {
  if (!open) {
    clearLinkSelection(props.editor)
  }
})
watch(toolbarDisabled, (disabled) => {
  if (disabled) {
    headingMenuOpen.value = false
    highlightMenuOpen.value = false
    linkMenuOpen.value = false
    linkError.value = ''
  }
})
watch(visibleCount, (count) => {
  if (count === 0) {
    headingMenuOpen.value = false
  }
  const highlightIndex = toolbarItems.findIndex(item => item.id === 'highlight')
  if (highlightIndex >= count) {
    highlightMenuOpen.value = false
  }
  const linkIndex = toolbarItems.findIndex(item => item.id === 'link')
  if (linkIndex >= count) {
    linkMenuOpen.value = false
  }
})

onMounted(async () => {
  document.addEventListener('pointerdown', handlePointerDown, true)
  document.addEventListener('keydown', handleKeyDown)
  window.addEventListener('resize', closeHeadingMenuOnScroll)
  document.addEventListener('scroll', closeHeadingMenuOnScroll, true)
  resizeObserver = new ResizeObserver(scheduleToolbarMeasurement)
  resizeObserver.observe(root.value)
  await nextTick()
  scheduleToolbarMeasurement()
})

onBeforeUnmount(() => {
  clearLinkSelection(props.editor)
  props.editor?.off('transaction', refreshState)
  props.editor?.off('selectionUpdate', refreshState)
  resizeObserver?.disconnect()
  window.cancelAnimationFrame(resizeFrame)
  document.removeEventListener('pointerdown', handlePointerDown, true)
  document.removeEventListener('keydown', handleKeyDown)
  window.removeEventListener('resize', closeHeadingMenuOnScroll)
  document.removeEventListener('scroll', closeHeadingMenuOnScroll, true)
})
</script>

<template>
  <div
    ref="root"
    data-editor-toolbar-dock
    class="sticky top-0 z-20 mb-6 mt-4 w-full bg-white py-3"
  >
    <div
      class="mx-auto flex w-fit max-w-full items-center gap-0.5 overflow-hidden rounded-2xl border border-slate-200/75 bg-white/85 p-1.5 shadow-[0_8px_28px_rgba(15,23,42,0.10)] backdrop-blur-xl"
      role="toolbar"
      aria-label="正文格式工具栏"
    >
      <template v-for="(item, index) in toolbarItems" :key="item.id">
        <span
          v-if="item.type === 'separator' && isVisible(index)"
          aria-hidden="true"
          class="mx-1 h-5 w-px shrink-0 bg-slate-200/90"
        />
        <button
          v-else-if="item.type !== 'separator' && isVisible(index)"
          :ref="item.id === 'heading' ? setHeadingButton : item.id === 'highlight' ? setHighlightButton : item.id === 'link' ? setLinkButton : undefined"
          type="button"
          :class="[buttonClass, activeClass(isItemActive(item))]"
          :disabled="toolbarDisabled || item.disabled"
          :title="item.title"
          :aria-label="item.title"
          :aria-expanded="item.id === 'heading' ? headingMenuOpen : item.id === 'highlight' ? highlightMenuOpen : item.id === 'link' ? linkMenuOpen : undefined"
          @mousedown.prevent
          @click="execute(item)"
        >
          <Icon :src="item.icon" class="h-[18px] w-[18px]" />
          <Icon v-if="item.id === 'heading'" :src="chevronDownIcon" class="ml-[-3px] h-2.5 w-2.5" />
        </button>
      </template>

      <span
        v-if="hasHiddenItems"
        class="flex h-8 w-8 shrink-0 cursor-default select-none items-center justify-center rounded-lg text-base font-semibold tracking-[-0.12em] text-slate-400"
        title="部分工具因空间不足而隐藏"
        aria-label="部分工具因空间不足而隐藏"
      >···</span>
    </div>

    <div
      ref="measurement"
      aria-hidden="true"
      class="invisible absolute left-[-9999px] top-0 flex w-max items-center gap-0.5 rounded-2xl border border-transparent p-1.5"
    >
      <span
        v-for="item in toolbarItems"
        :key="item.id"
        data-toolbar-item
        :class="item.type === 'separator' ? 'mx-1 h-5 w-px shrink-0' : 'h-8 w-8 shrink-0'"
      />
      <span data-toolbar-ellipsis class="h-8 w-8 shrink-0" />
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
      <button v-for="level in [1, 2, 3, 4, 5]" :key="level" type="button" role="menuitem" class="flex h-8 w-full items-center rounded-lg px-3 text-left hover:bg-slate-100" :class="activeClass(isActive('heading', { level }))" @mousedown.prevent @click="setTextStyle(level)">H{{ level }}</button>
    </div>
  </Teleport>

  <Teleport to="body">
    <div
      v-if="highlightMenuOpen"
      ref="highlightMenu"
      role="menu"
      aria-label="高亮颜色"
      class="fixed z-50 flex w-max max-w-[calc(100vw-16px)] items-center gap-1.5 rounded-xl border border-slate-200/80 bg-white/95 p-2 shadow-[0_10px_30px_rgba(15,23,42,0.13)] backdrop-blur-xl"
      :style="{ left: `${highlightMenuPosition.left}px`, top: `${highlightMenuPosition.top}px` }"
    >
      <button
        v-for="color in highlightColors"
        :key="color.value"
        type="button"
        role="menuitem"
        class="h-7 w-7 shrink-0 cursor-pointer rounded-full border border-slate-300 transition-transform hover:scale-110 focus:outline-none focus-visible:ring-2 focus-visible:ring-violet-400"
        :class="isActive('highlight', { color: color.value }) ? 'ring-2 ring-violet-500 ring-offset-1' : ''"
        :style="{ backgroundColor: color.value }"
        :title="`${color.name}高亮`"
        :aria-label="`${color.name}高亮`"
        @mousedown.prevent
        @click="setHighlightColor(color.value)"
      />
      <span aria-hidden="true" class="mx-0.5 h-5 w-px bg-slate-200" />
      <button
        type="button"
        role="menuitem"
        class="flex h-7 w-7 shrink-0 cursor-pointer items-center justify-center rounded-full border border-slate-300 bg-white text-sm text-slate-500 transition-colors hover:bg-slate-100 hover:text-slate-800 focus:outline-none focus-visible:ring-2 focus-visible:ring-violet-400"
        title="清除高亮"
        aria-label="清除高亮"
        @mousedown.prevent
        @click="clearHighlight"
      >×</button>
    </div>
  </Teleport>

  <Teleport to="body">
    <div
      v-if="linkMenuOpen"
      ref="linkMenu"
      role="dialog"
      aria-label="编辑链接"
      class="fixed z-50 w-[300px] max-w-[calc(100vw-16px)] rounded-xl border border-slate-200/80 bg-white/95 p-2 shadow-[0_10px_30px_rgba(15,23,42,0.13)] backdrop-blur-xl"
      :style="{ left: `${linkMenuPosition.left}px`, top: `${linkMenuPosition.top}px` }"
    >
      <div class="flex items-center gap-1.5">
        <input
          ref="linkInput"
          v-model="linkDraft"
          type="text"
          class="h-9 min-w-0 flex-1 rounded-lg border border-slate-200 bg-white px-3 text-sm text-slate-700 outline-none transition-colors placeholder:text-slate-400 focus:border-violet-400 focus:ring-2 focus:ring-violet-100"
          placeholder="输入链接，编辑后自动应用"
          aria-label="链接地址"
          @input="applyLinkDraft"
          @keydown.enter.prevent="linkMenuOpen = false"
          @keydown.escape.prevent="linkMenuOpen = false"
        >
        <button
          type="button"
          class="flex h-9 w-9 shrink-0 cursor-pointer items-center justify-center rounded-lg text-slate-500 transition-colors hover:bg-red-50 hover:text-red-600 focus:outline-none focus-visible:ring-2 focus-visible:ring-red-200"
          title="删除链接"
          aria-label="删除链接"
          @mousedown.prevent
          @click="removeLink"
        >
          <Icon :src="deleteIcon" class="h-4 w-4" />
        </button>
      </div>
      <p v-if="linkError" class="mt-1.5 px-0.5 text-xs text-red-600">
        {{ linkError }}
      </p>
    </div>
  </Teleport>
</template>
