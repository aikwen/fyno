<script setup>
import Icon from '../Icon.vue'
import pageEditorIcon from '../../assets/icon/page-editor.svg'

const props = defineProps({
  selectedPageID: {
    type: Number,
    default: null,
  },
  selectedSectionID: {
    type: String,
    default: '',
  },
})

const emit = defineEmits(['select-page'])

const pages = [
  { id: 1, title: '1111' },
  { id: 2, title: '未命名' },
  { id: 3, title: '未命名' },
]
</script>

<template>
  <section class="relative flex h-full w-60 shrink-0 flex-col bg-white">
    <div aria-hidden="true" class="absolute bottom-0 right-0 top-2 w-1 bg-[#f3f3f3]" />
    <header class="flex h-16 shrink-0 items-center px-3">
      <button
        type="button"
        class="inline-flex h-7 w-32 items-center justify-center gap-2 rounded-md border border-slate-300/80 bg-slate-50/80 text-sm text-violet-600 transition-[background-color,transform] hover:bg-violet-50 active:translate-y-px active:bg-violet-100 focus:outline-none focus-visible:ring-2 focus-visible:ring-violet-300/70 disabled:cursor-default disabled:opacity-45"
        :disabled="!props.selectedSectionID"
      >
        <Icon :src="pageEditorIcon" class="h-4 w-4 shrink-0" />
        <span>添加页</span>
      </button>
    </header>

    <div class="min-h-0 flex-1 overflow-y-auto px-3 pb-3">
      <template v-if="props.selectedSectionID">
        <button
          v-for="page in pages"
          :key="page.id"
          type="button"
          class="mb-1 flex h-11 w-full items-center rounded-md px-4 text-left text-sm text-slate-600 transition-colors hover:bg-slate-100/80 active:bg-slate-300/70 focus:outline-none focus-visible:ring-2 focus-visible:ring-slate-400/60"
          :class="{
            'bg-slate-200/80 font-semibold text-slate-900': props.selectedPageID === page.id,
          }"
          @click="emit('select-page', page.id)"
        >
          <span class="min-w-0 truncate">{{ page.title }}</span>
        </button>
      </template>
    </div>
  </section>
</template>
