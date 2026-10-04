<script setup>
import { MdPreview } from 'md-editor-v3'
import 'md-editor-v3/lib/preview.css'
import './markdown.css'

defineProps({
  content: {
    type: String,
    default: '',
  },

  previewId: {
    type: String,
    default: undefined,
  },

  mdHeadingId: {
    type: Function,
    default: undefined,
  },
})
</script>

<template>
  <div class="fyno-markdown">
    <MdPreview
      :id="previewId"
      :model-value="content"
      :md-heading-id="mdHeadingId"
      theme="light"
      preview-theme="vuepress"
    />
  </div>
</template>

<style scoped>
.fyno-markdown {
  min-width: 0;
  max-width: 100%;
  overflow-x: hidden;
  background: transparent;
}

.fyno-markdown :deep(.md-editor-preview-wrapper),
.fyno-markdown :deep(.md-editor-preview) {
  min-width: 0;
  max-width: 100%;
  background: transparent;
}

.fyno-markdown :deep(.md-editor-preview-wrapper) {
  padding: 0;
}

.fyno-markdown :deep(.md-editor-preview) {
  overflow-wrap: anywhere;
}

.fyno-markdown :deep(pre) {
  max-width: 100%;
  overflow-x: auto;
}

.fyno-markdown :deep(.md-editor-code) {
  max-width: 100%;
}

.fyno-markdown :deep(table) {
  display: block;
  max-width: 100%;
  overflow-x: auto;
  white-space: nowrap;
}

.fyno-markdown :deep(img),
.fyno-markdown :deep(svg),
.fyno-markdown :deep(canvas) {
  max-width: 100%;
}
</style>
