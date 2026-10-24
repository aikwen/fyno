<script setup>
import { computed, nextTick, ref } from 'vue'
import { NodeViewContent, NodeViewWrapper, nodeViewProps } from '@tiptap/vue-3'
import Icon from '../../Icon.vue'
import chevronDownIcon from '../../../assets/icon/editor/chevron-down.svg'
import noteIcon from '../../../assets/icon/editor/admonition-note.svg'
import tipIcon from '../../../assets/icon/editor/admonition-tip.svg'
import warningIcon from '../../../assets/icon/editor/admonition-warning.svg'
import dangerIcon from '../../../assets/icon/editor/admonition-danger.svg'

const props = defineProps(nodeViewProps)

const variants = [
  { id: 'note', label: 'Note', icon: noteIcon, color: '#2563eb' },
  { id: 'tip', label: 'Tip', icon: tipIcon, color: '#16a34a' },
  { id: 'warning', label: 'Warning', icon: warningIcon, color: '#d97706' },
  { id: 'danger', label: 'Danger', icon: dangerIcon, color: '#dc2626' },
]

const editingTitle = ref(false)
const titleDraft = ref('')
const titleInput = ref(null)
const typeMenuOpen = ref(false)

const currentVariant = computed(() => (
  variants.find(item => item.id === props.node.attrs.variant) || variants[0]
))

async function startTitleEdit() {
  titleDraft.value = props.node.attrs.title
  editingTitle.value = true
  typeMenuOpen.value = false
  await nextTick()
  titleInput.value?.focus({ preventScroll: true })
  titleInput.value?.select()
}

function commitTitle() {
  if (!editingTitle.value) {
    return
  }

  const title = titleDraft.value.trim() || currentVariant.value.label
  editingTitle.value = false
  if (title !== props.node.attrs.title) {
    props.updateAttributes({ title })
  }
}

function cancelTitleEdit() {
  titleDraft.value = props.node.attrs.title
  editingTitle.value = false
}

function changeVariant(nextVariant) {
  const oldDefaultTitle = currentVariant.value.label
  const nextTitle = props.node.attrs.title === oldDefaultTitle
    ? nextVariant.label
    : props.node.attrs.title

  props.updateAttributes({
    variant: nextVariant.id,
    title: nextTitle,
  })
  typeMenuOpen.value = false
}
</script>

<template>
  <NodeViewWrapper
    as="div"
    class="fyno-admonition"
    :data-variant="currentVariant.id"
  >
    <div class="fyno-admonition__header" contenteditable="false">
      <div class="fyno-admonition__heading">
        <Icon
          :src="currentVariant.icon"
          :color="currentVariant.color"
          class="h-4 w-4 shrink-0"
        />
        <input
          v-if="editingTitle"
          ref="titleInput"
          v-model="titleDraft"
          class="fyno-admonition__title-input"
          aria-label="提示块标题"
          @mousedown.stop
          @keydown.enter.prevent="commitTitle"
          @keydown.escape.prevent="cancelTitleEdit"
          @blur="commitTitle"
        >
        <span
          v-else
          class="fyno-admonition__title"
          title="双击修改标题"
          @dblclick.stop.prevent="startTitleEdit"
        >{{ node.attrs.title }}</span>
      </div>

      <div class="fyno-admonition__type-control">
        <button
          type="button"
          class="fyno-admonition__type-button"
          :aria-expanded="typeMenuOpen"
          title="切换提示块类型"
          @mousedown.stop.prevent
          @click.stop="typeMenuOpen = !typeMenuOpen"
        >
          {{ currentVariant.label }}
          <Icon :src="chevronDownIcon" class="h-3 w-3" />
        </button>
        <div v-if="typeMenuOpen" class="fyno-admonition__type-menu" role="menu">
          <button
            v-for="variant in variants"
            :key="variant.id"
            type="button"
            role="menuitem"
            class="fyno-admonition__type-option"
            :class="variant.id === currentVariant.id ? 'is-active' : ''"
            :data-variant="variant.id"
            @mousedown.stop.prevent
            @click.stop="changeVariant(variant)"
          >
            <Icon :src="variant.icon" :color="variant.color" class="h-3.5 w-3.5" />
            {{ variant.label }}
          </button>
        </div>
      </div>
    </div>
    <NodeViewContent as="div" class="fyno-admonition__content" />
  </NodeViewWrapper>
</template>
