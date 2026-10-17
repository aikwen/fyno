<script setup>
import { ref } from 'vue'
import Icon from '../Icon.vue'
import panelIcon from '../../assets/icon/panel-left.svg'
import chevronIcon from '../../assets/icon/chevron-right.svg'
import notebookIcon from '../../assets/icon/notebook.svg'
import sectionIcon from '../../assets/icon/section.svg'
import homeIcon from '../../assets/icon/house.svg'
import notebookAddIcon from '../../assets/icon/notebook-add.svg'

const props = defineProps({
  expanded: {
    type: Boolean,
    required: true,
  },
  selectedNotebookID: {
    type: String,
    default: '',
  },
  selectedSectionID: {
    type: String,
    default: '',
  },
})

const emit = defineEmits(['toggle', 'select-notebook', 'select-section'])

const notebooks = ref([
  {
    id: 'personal',
    name: 'Personal Notes',
    color: '#7967c3',
    expanded: true,
    sections: [
      { id: 'quick-notes', name: 'Quick Notes', color: '#de8c56' },
      { id: 'projects', name: 'Projects', color: '#5a9b8c' },
      { id: 'fyno-v2', name: 'Fyno v2', color: '#5a9b8c' },
      { id: 'reading-list', name: 'Reading List', color: '#b06b87' },
    ],
  },
  {
    id: 'work',
    name: 'Work Notebook With A Longer Name',
    color: '#4c88c7',
    expanded: false,
    sections: [
      { id: 'meetings', name: 'Meetings', color: '#4c88c7' },
      { id: 'planning', name: 'Planning', color: '#d0a442' },
    ],
  },
  {
    id: 'archive',
    name: 'Archive',
    color: '#768390',
    expanded: true,
    sections: [{ id: 'ideas', name: 'Ideas', color: '#768390' }],
  },
])

</script>

<template>
  <aside
    class="flex h-full shrink-0 flex-col overflow-hidden border-r border-slate-300/55 bg-[#e8edf1]"
    :class="expanded ? 'w-64' : 'w-14'"
  >
    <div class="flex h-14 shrink-0 items-center px-2.5" :class="expanded ? 'justify-start' : 'justify-center'">
      <button
        type="button"
        class="flex h-9 w-9 shrink-0 items-center justify-center rounded-lg text-slate-600 transition-colors hover:bg-white/55 active:bg-slate-300/55 focus:outline-none focus-visible:ring-2 focus-visible:ring-slate-400/60"
        :aria-label="expanded ? '折叠侧边栏' : '展开侧边栏'"
        @click="emit('toggle')"
      >
        <img :src="panelIcon" alt="" class="h-5 w-5" />
      </button>

    </div>

    <div v-if="expanded" class="min-h-0 flex-1 overflow-y-auto px-2 pb-3">
      <div v-for="notebook in notebooks" :key="notebook.id" class="mb-1">
        <div
          class="flex h-9 w-full min-w-0 items-center gap-1.5 rounded-lg px-2 text-left text-sm font-medium text-slate-700 hover:bg-white/50"
          :class="{ 'bg-white/65 text-slate-900': props.selectedNotebookID === notebook.id }"
        >
          <button
            type="button"
            class="flex h-8 w-4 shrink-0 items-center justify-center focus:outline-none"
            :aria-label="notebook.expanded ? `折叠 ${notebook.name}` : `展开 ${notebook.name}`"
            @click="notebook.expanded = !notebook.expanded"
          >
            <img
              :src="chevronIcon"
              alt=""
              class="h-3.5 w-3.5 opacity-65 transition-transform"
              :class="{ 'rotate-90': notebook.expanded }"
            />
          </button>
          <button
            type="button"
            class="flex h-full min-w-0 flex-1 items-center gap-1.5 rounded-md text-left focus:outline-none focus-visible:ring-2 focus-visible:ring-slate-400/60"
            @click="emit('select-notebook', notebook.id)"
          >
            <Icon :src="notebookIcon" :color="notebook.color" class="h-4 w-4 shrink-0" />
            <span class="min-w-0 truncate">{{ notebook.name }}</span>
          </button>
        </div>

        <div v-if="notebook.expanded" class="mt-1.5 flex flex-col gap-1">
          <button
            v-for="section in notebook.sections"
            :key="section.id"
            type="button"
            class="flex h-8 w-full min-w-0 items-center gap-1.5 rounded-md pr-2 pl-7 text-left text-sm text-slate-600 transition-colors hover:bg-white/50 focus:outline-none focus-visible:ring-2 focus-visible:ring-slate-400/60"
            :class="{ 'bg-white/65 font-semibold text-slate-900': props.selectedSectionID === section.id }"
            @click="emit('select-section', { notebookID: notebook.id, sectionID: section.id })"
          >
            <span class="h-3 w-3 shrink-0" />
            <Icon :src="sectionIcon" :color="section.color" class="h-6 w-6 shrink-0" />
            <span class="min-w-0 truncate">{{ section.name }}</span>
          </button>
        </div>
      </div>
    </div>

    <div v-if="expanded" class="flex h-14 shrink-0 items-center border-t border-slate-300/45">
      <div class="flex flex-1 justify-center">
        <button
          type="button"
          aria-label="主页"
          class="flex h-9 w-9 items-center justify-center rounded-lg text-slate-600 transition-colors hover:bg-white/55 active:bg-slate-300/55 focus:outline-none focus-visible:ring-2 focus-visible:ring-slate-400/60"
        >
          <Icon :src="homeIcon" class="h-5 w-5" />
        </button>
      </div>
      <div aria-hidden="true" class="h-6 w-px shrink-0 bg-slate-300/70" />
      <div class="flex flex-1 justify-center">
        <button
          type="button"
          aria-label="新建笔记本"
          class="flex h-9 w-9 items-center justify-center rounded-lg text-slate-600 transition-colors hover:bg-white/55 active:bg-slate-300/55 focus:outline-none focus-visible:ring-2 focus-visible:ring-slate-400/60"
        >
          <Icon :src="notebookAddIcon" class="h-5 w-5" />
        </button>
      </div>
    </div>
  </aside>
</template>
