<script setup>
defineProps({
  selectedPageID: {
    type: Number,
    default: null,
  },
  warning: {
    type: String,
    default: '',
  },
})
</script>

<template>
  <section class="min-w-0 flex-1 overflow-y-auto bg-white">
    <div class="min-h-full px-14 pt-8">
      <p
        v-if="warning"
        role="status"
        class="mb-4 text-sm text-amber-700"
      >
        {{ warning }}
      </p>

      <template v-if="selectedPageID !== null">
        <div class="w-full max-w-xl">
          <input
            type="text"
            aria-label="页面标题"
            class="h-14 w-full border-0 border-b border-slate-300 bg-transparent px-4 text-3xl font-normal text-slate-900 outline-none focus:border-violet-500"
          />
        </div>
        <div class="mt-2 flex gap-10 px-4 text-sm text-slate-500">
          <span>2026年10月16日</span>
          <span>20:01</span>
        </div>
      </template>
    </div>
  </section>
</template>
