import {
  CreatePage,
  DeletePage,
  GetPage,
  ListPages,
  SavePageContent,
  UpdatePage,
} from '../../wailsjs/go/app/App.js'

export const pageApi = {
  create(sectionId, title) {
    return CreatePage(sectionId, title)
  },

  list(sectionId) {
    return ListPages(sectionId)
  },

  get(id) {
    return GetPage(id)
  },

  update(id, title) {
    return UpdatePage(id, title)
  },

  remove(id) {
    return DeletePage(id)
  },

  saveContent(id, content) {
    return SavePageContent(id, content)
  },
}
