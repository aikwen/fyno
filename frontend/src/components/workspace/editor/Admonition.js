import { mergeAttributes, Node } from '@tiptap/core'
import { VueNodeViewRenderer } from '@tiptap/vue-3'
import EditorAdmonition from './EditorAdmonition.vue'

const DEFAULT_TITLES = {
  note: 'Note',
  tip: 'Tip',
  warning: 'Warning',
  danger: 'Danger',
}

function selectionInsideAdmonition(selection) {
  return [selection.$from, selection.$to].some(($position) => {
    for (let depth = $position.depth; depth > 0; depth -= 1) {
      if ($position.node(depth).type.name === 'admonition') {
        return true
      }
    }
    return false
  })
}

const Admonition = Node.create({
  name: 'admonition',
  group: 'block',
  content: 'block+',
  defining: true,
  isolating: true,

  addAttributes() {
    return {
      variant: {
        default: 'note',
        parseHTML: element => element.getAttribute('data-variant') || 'note',
      },
      title: {
        default: 'Note',
        parseHTML: element => element.getAttribute('data-title') || 'Note',
      },
    }
  },

  parseHTML() {
    return [{ tag: 'div[data-type="admonition"]' }]
  },

  renderHTML({ HTMLAttributes }) {
    const { variant, title, ...attributes } = HTMLAttributes
    return [
      'div',
      mergeAttributes(attributes, {
        'data-type': 'admonition',
        'data-variant': variant,
        'data-title': title,
      }),
      0,
    ]
  },

  addCommands() {
    return {
      insertAdmonition: attributes => ({ state, commands }) => {
        if (selectionInsideAdmonition(state.selection) || state.selection.$from.parent.type.spec.code) {
          return false
        }

        const variant = DEFAULT_TITLES[attributes?.variant] ? attributes.variant : 'note'
        const title = attributes?.title ?? DEFAULT_TITLES[variant]
        const position = state.selection.to

        return commands.insertContentAt(position, {
          type: this.name,
          attrs: { variant, title },
          content: [{ type: 'paragraph' }],
        }, {
          updateSelection: true,
          errorOnInvalidContent: true,
        })
      },
    }
  },

  addNodeView() {
    return VueNodeViewRenderer(EditorAdmonition)
  },
})

export default Admonition
