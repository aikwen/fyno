<script setup>
import {
  computed,
  nextTick,
  ref,
  useId,
  watch,
} from 'vue'

import { MdCatalog } from 'md-editor-v3'

import { getFileContent } from '@/api/library'

import FileToolbar from './FileToolbar.vue'
import MarkdownEditorModal from './MarkdownEditorModal.vue'
import MarkdownView from './MarkdownView.vue'

const props = defineProps({
  file: {
    type: Object,
    required: true,
  },
})

const content = ref('')
const loading = ref(false)
const error = ref(null)
const loaded = ref(false)
const editorOpen = ref(false)
const contentScrollRef = ref(null)
const catalogRef = ref(null)

const previewId =
  `file-view-${useId()}`

/*
 * Preview 和 Catalog 必须使用同一套 heading id。
 * 实例前缀隔离多个预览，index 则避免重复标题冲突。
 */
const getPreviewHeadingId = ({ index }) => {
  return `${previewId}-heading-${index}`
}

const canEdit = computed(() => {
  return (
    loaded.value
    && !loading.value
    && !error.value
  )
})

/*
 * collectionId/fileId 同时充当请求快照。
 * 切换文件后，旧请求可以自然结束，但不能再写回当前界面。
 */
const loadFile = async () => {
  const collectionId =
    props.file.collectionId
  const fileId = props.file.fileId

  content.value = ''
  loading.value = true
  error.value = null
  loaded.value = false
  editorOpen.value = false

  try {
    const response = await getFileContent({
      collectionId,
      fileId,
    })

    if (
      props.file.collectionId
        !== collectionId
      || props.file.fileId !== fileId
    ) {
      return
    }

    content.value = response.content
    loaded.value = true
    loading.value = false
  } catch (requestError) {
    if (
      props.file.collectionId
        !== collectionId
      || props.file.fileId !== fileId
    ) {
      return
    }

    error.value =
      requestError?.data?.detail
      ?? requestError?.message
      ?? 'Failed to load Markdown.'

    loading.value = false
  }
}

watch(
  () => [
    props.file.collectionId,
    props.file.fileId,
  ],
  loadFile,
  {
    immediate: true,
  },
)

const openEditor = () => {
  if (!canEdit.value) {
    return
  }

  editorOpen.value = true
}

const updateContent = (value) => {
  content.value = value
}

const keepCatalogItemVisible = (item) => {
  const catalog = catalogRef.value

  if (
    !catalog
    || !item
  ) {
    return
  }

  const catalogRect =
    catalog.getBoundingClientRect()
  const itemRect =
    item.getBoundingClientRect()

  if (itemRect.top < catalogRect.top) {
    catalog.scrollTop -=
      catalogRect.top - itemRect.top
  } else if (
    itemRect.bottom > catalogRect.bottom
  ) {
    catalog.scrollTop +=
      itemRect.bottom - catalogRect.bottom
  }
}

const handleCatalogActive = (
  _heading,
  activeElement,
) => {
  void nextTick(() => {
    keepCatalogItemVisible(
      activeElement,
    )
  })
}
</script>

<template>
  <section
    class="
      flex h-full min-h-0 min-w-0
      flex-col
      overflow-x-hidden
      bg-base-100
    "
  >
    <FileToolbar
      :collection-name="file.collectionName"
      :file-name="file.name"
      :loading="loading"
      :can-edit="canEdit"
      @refresh="loadFile"
      @edit="openEditor"
    />

    <main
      ref="contentScrollRef"
      class="
        relative
        min-h-0 min-w-0
        flex-1
        overflow-x-hidden
        overflow-y-auto
        bg-base-100
        px-10 py-8
      "
    >
      <div
        v-if="loading"
        class="space-y-4"
        aria-label="Loading Markdown"
      >
        <div class="skeleton h-3 w-full" />
        <div class="skeleton h-3 w-4/5" />
        <div class="skeleton h-3 w-[95%]" />
        <div class="skeleton h-3 w-3/5" />
        <div class="skeleton h-3 w-[88%]" />
      </div>

      <p
        v-else-if="error"
        class="text-sm text-error"
      >
        {{ error }}
      </p>

      <div
        v-else-if="loaded"
        class="
          flex min-w-0
          items-start gap-10
        "
      >
        <div
          class="min-w-0 flex-1"
        >
          <MarkdownView
            :content="content"
            :preview-id="previewId"
            :md-heading-id="
              getPreviewHeadingId
            "
          />

          <!--
            为文章末尾预留滚动空间，使最后的标题也能越过
            MdCatalog 的原生激活线，不需要额外维护 active 状态。
          -->
          <div
            aria-hidden="true"
            class="
              h-[calc(100dvh-6rem)]
            "
          />
        </div>

        <aside
          ref="catalogRef"
          class="
            hidden w-[220px]
            max-h-[calc(100vh-8rem)]
            shrink-0 self-start
            overflow-y-auto
            sticky top-0
            catalog-scrollbar
            xl:block
          "
          aria-label="Markdown catalog"
        >
          <MdCatalog
            class="
              fyno-markdown-catalog
            "
            :editor-id="previewId"
            :scroll-element="contentScrollRef"
            :md-heading-id="
              getPreviewHeadingId
            "
            theme="light"
            @on-active="handleCatalogActive"
          />
        </aside>
      </div>
    </main>

    <MarkdownEditorModal
      v-if="editorOpen"
      :file="file"
      :content="content"
      @close="editorOpen = false"
      @update-content="updateContent"
    />
  </section>
</template>

<style scoped>
.catalog-scrollbar {
  scrollbar-width: none;
}

.catalog-scrollbar::-webkit-scrollbar {
  display: none;
}

:deep(.fyno-markdown-catalog.md-editor-catalog) {
  color:
    color-mix(
      in oklab,
      var(--color-base-content) 55%,
      transparent
    );
}

:deep(
  .fyno-markdown-catalog
  .md-editor-catalog-link span
) {
  border-radius: 0.375rem;
  color: inherit;
  font-size: 0.75rem;
  line-height: 1.25rem;
  padding: 0.25rem 0.5rem;
}

:deep(
  .fyno-markdown-catalog
  .md-editor-catalog-link span:hover
) {
  color:
    color-mix(
      in oklab,
      var(--color-base-content) 85%,
      transparent
    );
}

:deep(
  .fyno-markdown-catalog
  .md-editor-catalog-indicator
) {
  display: none;
}

:deep(
  .fyno-markdown-catalog
  .md-editor-catalog-active > span
) {
  background:
    color-mix(
      in oklab,
      #005bac 9%,
      transparent
    );
  color: #005bac;
  font-weight: 600;
}
</style>
