import { reactive } from 'vue'

import type {
  CollectionMeta,
  FileMeta,
} from '../../model'

export interface BrowserFilters {
  keywords: string[]
}

export interface CollectionViewModel extends CollectionMeta {
  expanded: boolean
  loaded: boolean
  loading: boolean
  files: FileMeta[]
}

export interface BrowserViewState {
  collections: CollectionViewModel[]
  filters: BrowserFilters
  loading: boolean
  hasMore: boolean
  editMode: boolean
}

export const browserViewState = reactive<BrowserViewState>({
  collections: [],

  filters: {
    keywords: [],
  },

  loading: false,

  hasMore: true,

  editMode: false,
})