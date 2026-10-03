<script setup>
import {
  computed,
  ref,
} from 'vue'

import closeIcon from '@/assets/close.svg'
import controlsIcon from '@/assets/controls.svg'
import createIcon from '@/assets/create.svg'
import doneIcon from '@/assets/done.svg'
import editIcon from '@/assets/edit.svg'
import filterIcon from '@/assets/filter.svg'
import resetIcon from '@/assets/reset.svg'
import settingsIcon from '@/assets/settings.svg'

import { browserViewState } from './state'

const props = defineProps({
  filterOpen: {
    type: Boolean,
    default: false,
  },

  libraryReady: {
    type: Boolean,
    default: false,
  },
})

const emit = defineEmits([
  'create',
  'filter',
  'reset-filter',
  'settings',
])

const actionsOpen = ref(false)

const editing = computed(() => {
  return browserViewState.editMode
})

const hasFilter = computed(() => {
  return (
    browserViewState.filters.keywords.length > 0
  )
})

const filtering = computed(() => {
  return (
    props.filterOpen
    || hasFilter.value
  )
})

const toggleActions = () => {
  actionsOpen.value =
    !actionsOpen.value
}

const closeActions = () => {
  actionsOpen.value = false
}

const toggleEditMode = () => {
  if (
    filtering.value
    || !props.libraryReady
  ) {
    return
  }

  browserViewState.editMode =
    !browserViewState.editMode
}

const handleFilter = () => {
  if (
    editing.value
    || !props.libraryReady
  ) {
    return
  }

  if (hasFilter.value) {
    emit('reset-filter')
    return
  }

  emit(
    'filter',
    !props.filterOpen,
  )
}

const createCollection = () => {
  if (
    editing.value
    || filtering.value
    || !props.libraryReady
  ) {
    return
  }

  emit('create')
}

const openSettings = () => {
  if (
    editing.value
    || filtering.value
  ) {
    return
  }

  closeActions()

  emit('settings')
}
</script>

<template>
  <div
    class="
      absolute
      bottom-6 right-6
      z-20
      flex flex-col
      items-end
      gap-3
    "
  >
    <!-- Actions -->
    <div
      v-show="actionsOpen"
      class="
        flex flex-col
        items-end
        gap-3
      "
    >
      <!-- Settings -->
      <div
        class="tooltip tooltip-left"
        data-tip="Settings"
      >
        <button
          type="button"
          class="
            btn btn-lg btn-circle
            shadow-[0_4px_12px_rgba(0,0,0,0.10)]
            transition-shadow
            hover:shadow-[0_6px_16px_rgba(0,0,0,0.14)]
          "
          :disabled="
            editing
            || filtering
          "
          @click="openSettings"
        >
          <img
            :src="settingsIcon"
            alt=""
            class="
              size-5
              opacity-75
            "
          >
        </button>
      </div>

      <!-- Filter / Reset -->
      <div
        class="tooltip tooltip-left"
        :data-tip="
          hasFilter
            ? 'Reset Filter'
            : 'Filter'
        "
      >
        <button
          type="button"
          class="
            btn btn-lg btn-circle
            border-none
            shadow-[0_4px_12px_rgba(0,0,0,0.10)]
            transition-shadow
            hover:shadow-[0_6px_16px_rgba(0,0,0,0.14)]
          "
          :class="
            hasFilter
              ? 'bg-[#EB5971] text-white hover:bg-[#D74C63]'
              : ''
          "
          :disabled="
            editing
            || !libraryReady
          "
          @click="handleFilter"
        >
          <img
            :src="
              hasFilter
                ? resetIcon
                : filterIcon
            "
            alt=""
            class="size-5"
            :class="
              hasFilter
                ? 'brightness-0 invert'
                : 'opacity-75'
            "
          >
        </button>
      </div>

      <!-- Create -->
      <div
        class="tooltip tooltip-left"
        data-tip="Create"
      >
        <button
          type="button"
          class="
            btn btn-lg btn-circle
            shadow-[0_4px_12px_rgba(0,0,0,0.10)]
            transition-shadow
            hover:shadow-[0_6px_16px_rgba(0,0,0,0.14)]
          "
          :disabled="
            editing
            || filtering
            || !libraryReady
          "
          @click="createCollection"
        >
          <img
            :src="createIcon"
            alt=""
            class="
              size-5
              opacity-75
            "
          >
        </button>
      </div>

      <!-- Edit / Done -->
      <div
        class="tooltip tooltip-left"
        :data-tip="
          editing
            ? 'Done'
            : 'Edit'
        "
      >
        <button
          type="button"
          class="
            btn btn-lg btn-circle
            border-none
            shadow-[0_4px_12px_rgba(0,0,0,0.10)]
            transition-shadow
            hover:shadow-[0_6px_16px_rgba(0,0,0,0.14)]
          "
          :class="
            editing
              ? 'btn-success text-white'
              : ''
          "
          :disabled="
            filtering
            || !libraryReady
          "
          @click="toggleEditMode"
        >
          <img
            :src="
              editing
                ? doneIcon
                : editIcon
            "
            alt=""
            class="size-5"
            :class="
              editing
                ? 'brightness-0 invert'
                : 'opacity-75'
            "
          >
        </button>
      </div>
    </div>

    <!-- Main / Close button -->
    <button
      type="button"
      class="
        btn btn-lg btn-circle
        border-none
        text-white
        shadow-[0_5px_16px_rgba(0,0,0,0.14)]
        transition-shadow
        hover:shadow-[0_7px_20px_rgba(0,0,0,0.18)]
      "
      :class="
        actionsOpen
          ? 'bg-[rgb(235,89,113)] hover:bg-[rgb(215,76,99)]'
          : 'bg-[#005BAC] hover:bg-[#004C91]'
      "
      @click="
        actionsOpen
          ? closeActions()
          : toggleActions()
      "
    >
      <img
        v-if="actionsOpen"
        :src="closeIcon"
        alt=""
        class="
          size-5
          brightness-0 invert
        "
      >

      <img
        v-else
        :src="controlsIcon"
        alt=""
        class="
          size-5
          brightness-0 invert
        "
      >
    </button>
  </div>
</template>
