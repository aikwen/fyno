import CodeBlockLowlight from '@tiptap/extension-code-block-lowlight'
import { VueNodeViewRenderer } from '@tiptap/vue-3'
import EditorCodeBlock from './EditorCodeBlock.vue'

const CodeBlock = CodeBlockLowlight.extend({
  addNodeView() {
    return VueNodeViewRenderer(EditorCodeBlock)
  },
})

export default CodeBlock
