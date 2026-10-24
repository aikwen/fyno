import { Extension } from '@tiptap/core'
import { Plugin, PluginKey } from '@tiptap/pm/state'
import { Decoration, DecorationSet } from '@tiptap/pm/view'

const linkSelectionKey = new PluginKey('fynoLinkSelection')

export function showLinkSelection(editor) {
  const { from, to, empty } = editor.state.selection
  if (empty) {
    return
  }

  editor.view.dispatch(editor.state.tr.setMeta(linkSelectionKey, { from, to }))
}

export function clearLinkSelection(editor) {
  if (!editor || editor.isDestroyed) {
    return
  }

  editor.view.dispatch(editor.state.tr.setMeta(linkSelectionKey, { clear: true }))
}

const LinkSelection = Extension.create({
  name: 'fynoLinkSelection',

  addProseMirrorPlugins() {
    return [
      new Plugin({
        key: linkSelectionKey,
        state: {
          init: () => DecorationSet.empty,
          apply(transaction, decorations) {
            const meta = transaction.getMeta(linkSelectionKey)
            if (meta?.clear) {
              return DecorationSet.empty
            }
            if (meta && meta.from < meta.to) {
              return DecorationSet.create(transaction.doc, [
                Decoration.inline(meta.from, meta.to, { class: 'fyno-link-selection' }),
              ])
            }
            return decorations.map(transaction.mapping, transaction.doc)
          },
        },
        props: {
          decorations(state) {
            return linkSelectionKey.getState(state)
          },
        },
      }),
    ]
  },
})

export default LinkSelection
