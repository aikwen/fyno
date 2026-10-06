<script setup>
import { computed } from 'vue'

import editMarkdownIcon from '@/assets/edit-markdown.svg'
import filePathIcon from '@/assets/file-path.svg'
import refreshIcon from '@/assets/refresh.svg'

const props = defineProps({
  collectionName: {
    type: String,
    default: '',
  },

  fileName: {
    type: String,
    default: '',
  },

  loading: {
    type: Boolean,
    default: false,
  },

  canEdit: {
    type: Boolean,
    default: false,
  },

  canCopyPath: {
    type: Boolean,
    default: false,
  },

  pathCopyStatus: {
    type: String,
    default: 'idle',
  },
})

const emit = defineEmits([
  'refresh',
  'edit',
  'copy-path',
])

const pathTooltip = computed(() => {
  if (props.pathCopyStatus === 'copied') {
    return 'File path copied'
  }

  if (props.pathCopyStatus === 'error') {
    return 'Failed to copy file path'
  }

  return 'Copy Markdown file path'
})
</script>

<template>
  <header
    class="
      relative z-10
      flex h-14 shrink-0
      items-center justify-between
      gap-4
      border-b border-base-content/10
      bg-base-100
      px-6
      shadow-[0_3px_10px_rgb(0_0_0/0.06)]
    "
  >
    <div
      class="
        min-w-0 truncate
        text-sm font-medium
        text-base-content
      "
      :title="
        `${collectionName} / ${fileName}`
      "
    >
      <span>{{ collectionName }}</span>
      <span class="px-1">/</span>
      <span>{{ fileName }}</span>
    </div>

    <div
      class="
        flex shrink-0
        items-center gap-1
      "
    >
      <div
        class="tooltip tooltip-bottom"
        data-tip="Refresh Markdown"
      >
        <button
          type="button"
          class="
            flex size-8
            cursor-pointer
            items-center justify-center
            rounded-md
            transition-colors
            hover:bg-base-content/5
            disabled:cursor-not-allowed
            disabled:opacity-35
          "
          :disabled="loading"
          aria-label="Refresh Markdown"
          @click="emit('refresh')"
        >
          <img
            :src="refreshIcon"
            alt=""
            class="size-[17px]"
          >
        </button>
      </div>

      <div
        class="tooltip tooltip-left"
        :data-tip="pathTooltip"
      >
        <button
          type="button"
          class="
            flex size-8
            cursor-pointer
            items-center justify-center
            rounded-md
            transition-colors
            hover:bg-base-content/5
            disabled:cursor-not-allowed
            disabled:opacity-35
          "
          :disabled="
            loading || !canCopyPath
          "
          aria-label="Copy Markdown file path"
          @click="emit('copy-path')"
        >
          <img
            :src="filePathIcon"
            alt=""
            class="size-[17px]"
          >
        </button>
      </div>

      <div
        class="tooltip tooltip-left"
        data-tip="Edit Markdown"
      >
        <button
          type="button"
          class="
            flex size-8
            cursor-pointer
            items-center justify-center
            rounded-md
            transition-colors
            hover:bg-base-content/5
            disabled:cursor-not-allowed
            disabled:opacity-35
          "
          :disabled="
            loading || !canEdit
          "
          aria-label="Edit Markdown"
          @click="emit('edit')"
        >
          <img
            :src="editMarkdownIcon"
            alt=""
            class="size-[17px]"
          >
        </button>
      </div>
    </div>
  </header>
</template>
