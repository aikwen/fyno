import { config } from 'md-editor-v3'

/*
 * Markdown 链接在独立 Tab 中打开，避免阅读外部资料时离开 Fyno。
 * 当前文档内的标题锚点仍由原页面处理，保留目录式跳转体验。
 */
config({
  markdownItConfig: (markdownIt) => {
    const defaultLinkOpen =
      markdownIt.renderer.rules.link_open

    markdownIt.renderer.rules.link_open = (
      tokens,
      index,
      options,
      environment,
      renderer,
    ) => {
      const token = tokens[index]
      const href = token.attrGet('href') || ''

      if (
        href
        && !href.startsWith('#')
      ) {
        token.attrSet('target', '_blank')
        token.attrSet(
          'rel',
          'noopener noreferrer',
        )
      }

      if (defaultLinkOpen) {
        return defaultLinkOpen(
          tokens,
          index,
          options,
          environment,
          renderer,
        )
      }

      return renderer.renderToken(
        tokens,
        index,
        options,
      )
    }
  },
})
