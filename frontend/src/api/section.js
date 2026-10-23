import {
  CreateSection,
  DeleteSection,
  ListSections,
  UpdateSection,
} from '../../wailsjs/go/app/App.js'

export const sectionApi = {
  create(notebookId, name, color) {
    return CreateSection(notebookId, name, color)
  },

  list(notebookId) {
    return ListSections(notebookId)
  },

  update(id, name, color) {
    return UpdateSection(id, name, color)
  },

  remove(id) {
    return DeleteSection(id)
  },
}
