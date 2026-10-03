import {
  nextTick,
  ref,
} from 'vue'

import { getCollections } from '@/api/library'

import { normalizeCollection } from './normalize'

const PAGE_SIZE = 20

export const useCollectionPagination = ({
  browserViewState,
  scrollRef,
}) => {
  const sentinelRef = ref(null)

  let observer = null

  /*
   * Filter/Reload 会使当前请求失效；只有版本一致的响应可以写入状态。
   */
  let collectionQueryVersion = 0

  const isSentinelVisible = () => {
    const scroll = scrollRef.value
    const sentinel = sentinelRef.value

    if (
      !scroll
      || !sentinel
    ) {
      return false
    }

    const scrollRect =
      scroll.getBoundingClientRect()

    const sentinelRect =
      sentinel.getBoundingClientRect()

    return (
      sentinelRect.top
        < scrollRect.bottom
      && sentinelRect.bottom
        > scrollRect.top
    )
  }

  const loadMore = async () => {
    if (
      browserViewState.editMode
      || browserViewState.loading
      || !browserViewState.hasMore
    ) {
      return
    }

    const queryVersion =
      collectionQueryVersion

    browserViewState.loading = true

    try {
      const collections =
        await getCollections({
          keywords: [
            ...browserViewState.filters
              .keywords,
          ],

          offset:
            browserViewState.collections
              .length,

          limit:
            PAGE_SIZE,
        })

      if (
        queryVersion
        !== collectionQueryVersion
      ) {
        return
      }

      const newCollections =
        collections.map(
          normalizeCollection,
        )

      browserViewState.collections.push(
        ...newCollections,
      )

      if (
        newCollections.length
        < PAGE_SIZE
      ) {
        browserViewState.hasMore = false
      }
    } catch (error) {
      if (
        queryVersion
        === collectionQueryVersion
      ) {
        console.error(
          'Failed to load collections:',
          error,
        )
      }
    } finally {
      if (
        queryVersion
        === collectionQueryVersion
      ) {
        browserViewState.loading = false
      }
    }

    if (
      queryVersion
      !== collectionQueryVersion
    ) {
      return
    }

    await nextTick()

    /* 首屏不足一页时继续加载，直到填满 viewport 或没有更多数据。 */
    if (
      !browserViewState.editMode
      && browserViewState.hasMore
      && isSentinelVisible()
    ) {
      await loadMore()
    }
  }

  const resetCollections = () => {
    /*
     * 使正在进行中的旧请求失效，
     * 防止切换 Filter 时旧请求回来污染新结果。
     */
    collectionQueryVersion += 1

    browserViewState.loading = false
    browserViewState.hasMore = true

    browserViewState.collections.splice(
      0,
      browserViewState.collections.length,
    )

    scrollRef.value?.scrollTo({
      top: 0,
    })
  }

  const reloadCollections = async () => {
    resetCollections()

    await loadMore()
  }

  const createObserver = () => {
    observer?.disconnect()
    observer = null

    if (
      !scrollRef.value
      || !sentinelRef.value
    ) {
      return
    }

    observer =
      new IntersectionObserver(
        (entries) => {
          if (
            entries.some(
              entry =>
                entry.isIntersecting,
            )
          ) {
            loadMore()
          }
        },
        {
          root:
            scrollRef.value,

          rootMargin:
            '0px 0px 200px 0px',

          threshold:
            0,
        },
      )

    observer.observe(
      sentinelRef.value,
    )
  }

  const disconnectObserver = () => {
    /* 由 BrowserView 的 onBeforeUnmount 在原生命周期时机调用。 */
    observer?.disconnect()
  }

  return {
    sentinelRef,
    isSentinelVisible,
    loadMore,
    reloadCollections,
    resetCollections,
    createObserver,
    disconnectObserver,
  }
}
