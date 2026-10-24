<script setup>
import { computed, nextTick, ref } from 'vue'
import { NodeSelection } from '@tiptap/pm/state'
import { NodeViewContent, NodeViewWrapper, nodeViewProps } from '@tiptap/vue-3'
import Icon from '../../Icon.vue'
import chevronDownIcon from '../../../assets/icon/editor/chevron-down.svg'
import chevronUpIcon from '../../../assets/icon/editor/chevron-up.svg'

const props = defineProps(nodeViewProps)

const LANGUAGE_ALIASES = {
  js: 'javascript',
  jsx: 'javascript',
  ts: 'typescript',
  tsx: 'typescript',
  py: 'python',
  sh: 'bash',
  shell: 'bash',
  html: 'xml',
  plaintext: 'text',
  plain: 'text',
  txt: 'text',
}

const collapsed = ref(false)
const editingLanguage = ref(false)
const languageDraft = ref('')
const languageInput = ref(null)

const language = computed(() => props.node.attrs.language || 'text')

function normalizeLanguage(value) {
  const normalized = value.trim().toLowerCase() || 'text'
  return LANGUAGE_ALIASES[normalized] || normalized
}

async function startLanguageEdit() {
  languageDraft.value = language.value
  editingLanguage.value = true
  await nextTick()
  languageInput.value?.focus()
  languageInput.value?.select()
}

function commitLanguage() {
  if (!editingLanguage.value) {
    return
  }

  const nextLanguage = normalizeLanguage(languageDraft.value)
  editingLanguage.value = false
  if (nextLanguage !== props.node.attrs.language) {
    props.updateAttributes({ language: nextLanguage })
  }
}

function cancelLanguageEdit() {
  languageDraft.value = language.value
  editingLanguage.value = false
}

function selectionIsInsideCodeBlock(position) {
  const { from, to } = props.editor.state.selection
  return from > position && to < position + props.node.nodeSize
}

function toggleCollapsed() {
  if (!collapsed.value) {
    const position = props.getPos()
    if (typeof position === 'number' && selectionIsInsideCodeBlock(position)) {
      const selection = NodeSelection.create(props.editor.state.doc, position)
      props.editor.view.dispatch(props.editor.state.tr.setSelection(selection))
    }
  }

  collapsed.value = !collapsed.value
}
</script>

<template>
  <NodeViewWrapper
    as="div"
    class="fyno-code-block"
    :data-language="language"
  >
    <div
      class="fyno-code-block__header"
      contenteditable="false"
    >
      <input
        v-if="editingLanguage"
        ref="languageInput"
        v-model="languageDraft"
        class="fyno-code-block__language-input"
        aria-label="代码语言"
        spellcheck="false"
        @mousedown.stop
        @dblclick.stop
        @keydown.enter.prevent="commitLanguage"
        @keydown.escape.prevent="cancelLanguageEdit"
        @blur="commitLanguage"
      >
      <span
        v-else
        class="fyno-code-block__language"
        title="双击修改代码语言"
        @dblclick.stop.prevent="startLanguageEdit"
      >{{ language }}</span>

      <button
        type="button"
        class="fyno-code-block__toggle"
        :title="collapsed ? '展开代码' : '折叠代码'"
        :aria-label="collapsed ? '展开代码' : '折叠代码'"
        :aria-expanded="!collapsed"
        @mousedown.stop.prevent
        @click.stop="toggleCollapsed"
      >
        <span>{{ collapsed ? '展开' : '折叠' }}</span>
        <Icon
          :src="collapsed ? chevronDownIcon : chevronUpIcon"
          class="h-3.5 w-3.5"
        />
      </button>
    </div>

    <div v-show="!collapsed" class="fyno-code-block__body">
      <pre class="fyno-code-block__pre"><NodeViewContent as="code" class="fyno-code-block__content" /></pre>
    </div>
  </NodeViewWrapper>
</template>
