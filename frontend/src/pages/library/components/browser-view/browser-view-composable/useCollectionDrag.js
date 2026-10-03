import { moveCollection } from '@/api/library'

const DRAG_SCROLL_EDGE = 180
const DRAG_SCROLL_MIN_SPEED = 4
const DRAG_SCROLL_MAX_SPEED = 32

export const useCollectionDrag = ({
  browserViewState,
  scrollRef,
}) => {
  /* 拖拽期间的指针位置、动画帧与失败回滚快照。 */
  let dragPointerY = null
  let dragScrollFrame = null
  let dragSnapshot = []

  const updateDragPointer = (event) => {
    if (
      typeof event.clientY !== 'number'
    ) {
      return
    }

    dragPointerY = event.clientY
  }

  const getDragScrollSpeed = (
    distance,
  ) => {
    const ratio = Math.min(
      distance / DRAG_SCROLL_EDGE,
      1,
    )

    return (
      DRAG_SCROLL_MIN_SPEED
      + (
        DRAG_SCROLL_MAX_SPEED
        - DRAG_SCROLL_MIN_SPEED
      ) * ratio
    )
  }

  const runDragScroll = () => {
    const scroll = scrollRef.value

    if (
      !scroll
      || dragPointerY === null
    ) {
      dragScrollFrame =
        requestAnimationFrame(
          runDragScroll,
        )

      return
    }

    const rect =
      scroll.getBoundingClientRect()

    const topBoundary =
      rect.top + DRAG_SCROLL_EDGE

    const bottomBoundary =
      rect.bottom - DRAG_SCROLL_EDGE

    let speed = 0

    if (
      dragPointerY
      < topBoundary
    ) {
      const distance =
        topBoundary - dragPointerY

      speed =
        -getDragScrollSpeed(
          distance,
        )
    } else if (
      dragPointerY
      > bottomBoundary
    ) {
      const distance =
        dragPointerY - bottomBoundary

      speed =
        getDragScrollSpeed(
          distance,
        )
    }

    if (speed !== 0) {
      scroll.scrollTop += speed
    }

    dragScrollFrame =
      requestAnimationFrame(
        runDragScroll,
      )
  }

  const handleDragStart = () => {
    /* API 失败时使用拖拽前快照恢复完整排序。 */
    dragSnapshot = [
      ...browserViewState.collections,
    ]

    dragPointerY = null

    document.addEventListener(
      'pointermove',
      updateDragPointer,
    )

    document.addEventListener(
      'dragover',
      updateDragPointer,
    )

    if (
      dragScrollFrame === null
    ) {
      dragScrollFrame =
        requestAnimationFrame(
          runDragScroll,
        )
    }
  }

  const stopDragScroll = () => {
    /* drag end、退出 edit mode 和组件卸载都会进入同一清理入口。 */
    dragPointerY = null

    document.removeEventListener(
      'pointermove',
      updateDragPointer,
    )

    document.removeEventListener(
      'dragover',
      updateDragPointer,
    )

    if (
      dragScrollFrame !== null
    ) {
      cancelAnimationFrame(
        dragScrollFrame,
      )

      dragScrollFrame = null
    }
  }

  const handleDragEnd = async (event) => {
    stopDragScroll()

    const {
      oldIndex,
      newIndex,
    } = event

    if (
      oldIndex == null
      || newIndex == null
      || oldIndex === newIndex
    ) {
      dragSnapshot = []
      return
    }

    const movedCollection =
      browserViewState.collections[
        newIndex
      ]

    const previousCollection =
      browserViewState.collections[
        newIndex - 1
      ]
      ?? null

    if (!movedCollection) {
      dragSnapshot = []
      return
    }

    try {
      await moveCollection({
        collectionId:
          movedCollection.collectionId,

        afterCollectionId:
          previousCollection
            ?.collectionId
          ?? null,
      })
    } catch (error) {
      console.error(
        'Failed to move collection:',
        error,
      )

      browserViewState.collections.splice(
        0,
        browserViewState.collections.length,
        ...dragSnapshot,
      )
    } finally {
      dragSnapshot = []
    }
  }

  return {
    handleDragStart,
    stopDragScroll,
    handleDragEnd,
  }
}
