<script setup>
import { ref, watch } from 'vue'
import { appState, openService } from '../state/app.js'
import { SelectDirectory } from '../../wailsjs/go/app/App.js'
import logo from '../assets/app.svg'
import folderIcon from '../assets/icon/folder-open.svg'
import arrowIcon from '../assets/icon/arrow-right.svg'

const rootDir = ref(appState.rootDir)
const submitting = ref(false)
const selecting = ref(false)

watch(
  () => appState.rootDir,
  (value) => {
    rootDir.value = value
  },
)

async function submit() {
  if (submitting.value) {
    return
  }

  submitting.value = true
  try {
    await openService(rootDir.value)
  } finally {
    submitting.value = false
  }
}

async function selectDirectory() {
  if (selecting.value || submitting.value) {
    return
  }

  selecting.value = true
  try {
    const selected = await SelectDirectory()
    if (selected) {
      rootDir.value = selected
      appState.error = ''
    }
  } catch (error) {
    console.error('选择工作目录失败:', error)
    appState.error = '选择工作目录失败，请稍后重试'
  } finally {
    selecting.value = false
  }
}
</script>

<template>
  <main class="flex min-h-full items-center justify-center px-6 py-10">
    <section class="w-[82%] max-w-lg min-w-0">
      <header class="text-center">
        <img :src="logo" alt="Fyno" class="mx-auto h-20 w-20" />
        <h1 class="mt-5 text-3xl font-semibold tracking-tight text-slate-900">Welcome to Fyno</h1>
      </header>

      <form class="mt-10" @submit.prevent="submit">
        <p class="mb-3 text-left text-sm leading-6 text-slate-500">
          选择一个工作目录，开始管理你的本地笔记。
        </p>

        <div class="relative">
          <input
            v-model="rootDir"
            type="text"
            autocomplete="off"
            readonly
            aria-label="工作目录"
            placeholder="例如：D:\\Fyno"
            class="w-full rounded-xl border border-slate-300/90 bg-white/75 py-3 pr-12 pl-4 text-sm text-slate-900 outline-none transition placeholder:text-slate-400 focus:border-slate-400 focus:bg-white focus:ring-3 focus:ring-slate-300/45"
          />
          <button
            type="button"
            :disabled="selecting || submitting"
            :aria-busy="selecting"
            aria-label="选择工作目录"
            title="选择工作目录"
            class="absolute top-1/2 right-2 flex h-9 w-9 -translate-y-1/2 items-center justify-center rounded-lg text-slate-500 transition hover:bg-slate-100 hover:text-slate-700 focus:outline-none focus:ring-2 focus:ring-slate-300 disabled:cursor-not-allowed disabled:opacity-45"
            @click="selectDirectory"
          >
            <img :src="folderIcon" alt="" class="h-5 w-5" />
          </button>
        </div>

        <p
          role="alert"
          aria-live="polite"
          class="mt-2 min-h-5 text-left text-xs leading-5 text-red-600"
          :class="{ invisible: !appState.error }"
        >
          {{ appState.error }}
        </p>

        <div class="mt-7 flex justify-end">
          <button
            type="submit"
            :disabled="submitting"
            :aria-busy="submitting"
            aria-label="进入工作目录"
            class="flex h-12 w-12 items-center justify-center rounded-full border border-slate-300 bg-white/70 text-slate-700 transition hover:border-slate-400 hover:bg-white focus:outline-none focus:ring-3 focus:ring-slate-300/60 disabled:cursor-not-allowed disabled:opacity-45"
          >
            <img
              :src="arrowIcon"
              alt=""
              class="h-5 w-5"
              :class="{ 'animate-pulse': submitting }"
            />
          </button>
        </div>
      </form>
    </section>
  </main>
</template>
