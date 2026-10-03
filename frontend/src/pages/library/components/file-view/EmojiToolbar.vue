<script setup>
import { ref } from 'vue'

import { DropdownToolbar } from 'md-editor-v3'

const props = defineProps({
  insert: {
    type: Function,
    default: () => {},
  },

  disabled: {
    type: Boolean,
    default: false,
  },
})

const emojiGroups = [
  {
    name: '表情',
    emojis: [
      '😀', '😃', '😄', '😁', '😆',
      '😊', '🙂', '🙃', '😉', '😌',
      '😍', '🥰', '😎', '🤓', '🤔',
      '🫡', '😐', '😑', '😴', '😵',
    ],
  },
  {
    name: '手势',
    emojis: [
      '👍', '👎', '👌', '✌️', '🤞',
      '🤝', '👏', '🙌', '🙏', '💪',
      '👀', '👉', '👈', '☝️', '✋',
      '🤚', '🫶',
    ],
  },
  {
    name: '标记',
    emojis: [
      '✅', '❌', '⚠️', '🚧', '⛔',
      '❗', '❓', '⭐', '🌟', '✨',
      '💫', '🔥', '📌', '📍', '🏷️',
      '🔖',
    ],
  },
  {
    name: '文档',
    emojis: [
      '📝', '📄', '📃', '📑', '📚',
      '📖', '✏️', '🖊️', '📎', '📂',
      '📁', '🗂️', '🧠', '💡', '🔍',
      '🔎',
    ],
  },
  {
    name: '开发',
    emojis: [
      '💻', '🖥️', '⌨️', '🖱️', '⚙️',
      '🔧', '🔨', '🛠️', '🐛', '🧪',
      '🧰', '📦', '🗃️', '🗄️', '🔒',
      '🔑', '🛡️', '🌐', '🔗',
    ],
  },
  {
    name: '进度',
    emojis: [
      '🚀', '🎯', '🏁', '⏳', '⌛',
      '🕐', '📈', '📉', '📊', '💯',
      '🆕', '🔄',
    ],
  },
  {
    name: '沟通',
    emojis: [
      '🔔', '🔕', '📢', '📣', '💬',
      '🗨️', '📩', '📤', '📥', '☎️',
      '📞',
    ],
  },
  {
    name: '常用',
    emojis: [
      '❤️', '🧡', '💛', '💚', '💙',
      '💜', '🎉', '🎊', '🎁', '☕',
      '🍵', '🌙', '☀️', '🧭', '🗺️',
    ],
  },
  {
    name: '数字',
    emojis: [
      '0️⃣', '1️⃣', '2️⃣', '3️⃣', '4️⃣',
      '5️⃣', '6️⃣', '7️⃣', '8️⃣', '9️⃣',
      '🔟', '#️⃣', '*️⃣',
    ],
  },
]

const visible = ref(false)

const changeVisible = (value) => {
  visible.value = value
}

const insertEmoji = (emoji) => {
  props.insert(() => ({
    targetValue: emoji,
    select: false,
  }))
}

/*
 * 面板只保留一个 click 监听，避免为每个 Emoji
 * 创建独立的 Vue 事件处理器。
 */
const handlePanelClick = (event) => {
  if (!(event.target instanceof Element)) {
    return
  }

  const button = event.target.closest(
    '[data-emoji]',
  )

  if (
    !button
    || !event.currentTarget.contains(button)
  ) {
    return
  }

  insertEmoji(button.dataset.emoji)
}
</script>

<template>
  <DropdownToolbar
    title="Emoji"
    :visible="visible"
    :disabled="disabled"
    :on-change="changeVisible"
  >
    <template #overlay>
      <div
        class="emoji-panel"
        aria-label="Emoji picker"
        @click="handlePanelClick"
      >
        <section
          v-for="group in emojiGroups"
          :key="group.name"
          class="emoji-group"
        >
          <div class="emoji-group-title">
            {{ group.name }}
          </div>

          <div class="emoji-grid">
            <button
              v-for="emoji in group.emojis"
              :key="emoji"
              type="button"
              class="emoji-button"
              :data-emoji="emoji"
              :title="emoji"
              :aria-label="`Insert ${emoji}`"
            >
              {{ emoji }}
            </button>
          </div>
        </section>
      </div>
    </template>

    <span
      class="
        md-editor-icon
        emoji-toolbar-icon
      "
      aria-hidden="true"
    />
  </DropdownToolbar>
</template>

<style scoped>
.emoji-toolbar-icon {
  display: block;
  flex: none;
  box-sizing: content-box;
  width: 16px;
  height: 16px;
  padding: 4px;
  background-color: currentColor;
  mask-image: url('@/assets/emoji.svg');
  mask-position: center;
  mask-repeat: no-repeat;
  mask-size: 16px 16px;
  -webkit-mask-image: url('@/assets/emoji.svg');
  -webkit-mask-position: center;
  -webkit-mask-repeat: no-repeat;
  -webkit-mask-size: 16px 16px;
}

.emoji-panel {
  width: 360px;
  max-width: calc(100vw - 2rem);
  max-height: 320px;
  overflow-x: hidden;
  overflow-y: auto;
  contain: content;
  overscroll-behavior: contain;
  box-sizing: border-box;
  padding: 10px 12px 12px;
  border: 1px solid var(--md-border-color);
  border-radius: 8px;
  background: var(--md-bk-color);
  box-shadow: 0 8px 24px rgb(0 0 0 / 10%);
  scrollbar-color:
    var(--md-scrollbar-thumb-color)
    transparent;
  scrollbar-width: thin;
}

.emoji-panel::-webkit-scrollbar {
  width: 6px;
}

.emoji-panel::-webkit-scrollbar-track {
  background: transparent;
}

.emoji-panel::-webkit-scrollbar-thumb {
  border-radius: 999px;
  background: var(--md-scrollbar-thumb-color);
}

.emoji-group + .emoji-group {
  margin-top: 8px;
}

.emoji-group-title {
  margin-bottom: 3px;
  color: var(--md-color);
  font-size: 11px;
  font-weight: 500;
  line-height: 18px;
  opacity: 0.48;
}

.emoji-grid {
  display: grid;
  grid-template-columns:
    repeat(9, minmax(0, 1fr));
  gap: 2px;
}

.emoji-button {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 32px;
  height: 32px;
  min-height: 0;
  padding: 0;
  border: 0;
  border-radius: 6px;
  appearance: none;
  background: transparent;
  color: inherit;
  cursor: pointer;
  font-size: 19px;
  line-height: 1;
}

.emoji-button:hover,
.emoji-button:focus-visible {
  background: var(--md-bk-hover-color);
  outline: none;
}
</style>
