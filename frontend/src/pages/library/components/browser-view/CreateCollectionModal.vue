<script setup>
import {
  nextTick,
  ref,
  watch,
} from 'vue'

const props = defineProps({
  open: {
    type: Boolean,
    default: false,
  },

  loading: {
    type: Boolean,
    default: false,
  },
})

const emit = defineEmits([
  'close',
  'confirm',
])

const inputRef = ref(null)
const name = ref('')

const close = () => {
  if (props.loading) {
    return
  }

  name.value = ''
  emit('close')
}

const confirm = () => {
  const value = name.value.trim()

  if (
    !value
    || props.loading
  ) {
    return
  }

  emit('confirm', value)
}

watch(
  () => props.open,
  async (open) => {
    if (!open) {
      return
    }

    name.value = ''

    await nextTick()

    inputRef.value?.focus()
  },
)
</script>

<template>
  <dialog
    class="modal"
    :open="open"
  >
    <div class="modal-box">
      <h3 class="text-lg font-semibold">
        Create Collection
      </h3>

      <div class="mt-5">
        <input
          ref="inputRef"
          v-model="name"
          type="text"
          class="input input-bordered w-full"
          placeholder="Collection name"
          :disabled="loading"
          @keyup.enter="confirm"
          @keyup.esc="close"
        >
      </div>

      <div class="modal-action">
        <button
          type="button"
          class="btn"
          :disabled="loading"
          @click="close"
        >
          Cancel
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
          :disabled="
            loading
            || !name.trim()
          "
          @click="confirm"
        >
          <span
            v-if="loading"
            class="loading loading-spinner loading-sm"
          />

          <span v-else>
            Create
          </span>
        </button>
      </div>
    </div>

    <div
      class="modal-backdrop"
      @click="close"
    />
  </dialog>
</template>