<script setup>
import {
  nextTick,
  ref,
  watch,
} from 'vue'

import closeIcon from '@/assets/close.svg'

const props = defineProps({
  open: {
    type: Boolean,
    default: false,
  },

  keywords: {
    type: Array,
    default: () => [],
  },

  compact: {
    type: Boolean,
    default: false,
  },
})

const emit = defineEmits([
  'apply',
  'close',
])

const inputRef = ref(null)
const keywordInput = ref('')
const draftKeywords = ref([])

const resetDraft = () => {
  draftKeywords.value = [
    ...props.keywords,
  ]

  keywordInput.value = ''
}

const addKeyword = () => {
  const keyword = keywordInput.value.trim()

  if (!keyword) {
    return
  }

  if (
    draftKeywords.value.includes(keyword)
  ) {
    keywordInput.value = ''
    return
  }

  draftKeywords.value.push(keyword)
  keywordInput.value = ''
}

const removeKeyword = (keyword) => {
  draftKeywords.value =
    draftKeywords.value.filter(
      item => item !== keyword,
    )
}

const clearKeywords = () => {
  draftKeywords.value = []
  keywordInput.value = ''
}

const applyFilter = () => {
  addKeyword()

  emit(
    'apply',
    [...draftKeywords.value],
  )
}

const closeFilter = () => {
  emit('close')
}

watch(
  () => props.open,
  async (open) => {
    if (!open) {
      return
    }

    resetDraft()

    await nextTick()

    inputRef.value?.focus()
  },
)

watch(
  () => props.keywords,
  () => {
    if (!props.open) {
      return
    }

    resetDraft()
  },
  {
    deep: true,
  },
)
</script>

<template>
  <div
    v-if="open"
    class="
      absolute
      bottom-6
      z-50
      w-[360px]
      rounded-2xl
      border border-base-300/80
      bg-base-100
      p-5
      shadow-[0_12px_36px_rgba(0,0,0,0.12)]
    "
    :class="
      compact
        ? 'left-[calc(100%+12px)]'
        : 'right-24'
    "
  >
    <!-- Header -->
    <div
      class="
        flex
        items-center justify-between
      "
    >
      <div>
        <h3
          class="
            text-base
            font-semibold
            text-base-content
          "
        >
          Filter Collections
        </h3>

        <p
          class="
            mt-1
            text-xs
            text-base-content/45
          "
        >
          Match collections by keywords
        </p>
      </div>

      <button
        type="button"
        class="
          btn btn-sm btn-circle
          btn-ghost
        "
        title="Close"
        @click="closeFilter"
      >
        <img
          :src="closeIcon"
          alt=""
          class="
            size-3.5
            opacity-60
          "
        >
      </button>
    </div>

    <!-- Keyword input -->
    <div
      class="
        mt-5
        flex gap-2
      "
    >
      <input
        ref="inputRef"
        v-model="keywordInput"
        type="text"
        class="
          input input-bordered
          min-w-0 flex-1
        "
        placeholder="Keyword"
        @keyup.enter="addKeyword"
        @keyup.esc="closeFilter"
      >

      <button
        type="button"
        class="
          btn
          border-none
          bg-[#005BAC]
          text-white
          hover:bg-[#004C91]
        "
        :disabled="!keywordInput.trim()"
        @click="addKeyword"
      >
        +
      </button>
    </div>

    <!-- Keywords -->
    <div
      v-if="draftKeywords.length > 0"
      class="
        mt-4
        flex flex-wrap
        gap-2
      "
    >
      <div
        v-for="keyword in draftKeywords"
        :key="keyword"
        class="
          badge
          h-auto
          gap-1.5
          border-base-300
          bg-base-200
          px-3 py-2
          text-sm
        "
      >
        <span
          class="
            max-w-[220px]
            truncate
          "
          :title="keyword"
        >
          {{ keyword }}
        </span>

        <button
          type="button"
          class="
            group/remove
            flex size-4
            cursor-pointer
            items-center justify-center
            rounded-full
          "
          :title="`Remove ${keyword}`"
          @click="removeKeyword(keyword)"
        >
          <img
            :src="closeIcon"
            alt=""
            class="
              size-2.5
              opacity-45
              transition
              group-hover/remove:opacity-90
            "
          >
        </button>
      </div>
    </div>

    <div
      v-else
      class="
        mt-4
        rounded-lg
        border border-dashed
        border-base-300
        px-4 py-5
        text-center
        text-xs
        text-base-content/35
      "
    >
      No keywords
    </div>

    <!-- Actions -->
    <div
      class="
        mt-6
        flex
        items-center justify-between
      "
    >
      <button
        type="button"
        class="
          btn btn-ghost
          btn-sm
        "
        :disabled="
          draftKeywords.length === 0
        "
        @click="clearKeywords"
      >
        Clear
      </button>

      <button
        type="button"
        class="
          btn
          border-none
          bg-[#005BAC]
          text-white
          hover:bg-[#004C91]
        "
        @click="applyFilter"
      >
        Apply
      </button>
    </div>
  </div>
</template>