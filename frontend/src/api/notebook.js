import {
  CreateNotebook,
  DeleteNotebook,
  ListNotebooks,
  UpdateNotebook,
} from '../../wailsjs/go/app/App.js'

export const notebookApi = {
  create(name, color) {
    return CreateNotebook(name, color)
  },

  list() {
    return ListNotebooks()
  },

  update(id, name, color) {
    return UpdateNotebook(id, name, color)
  },

  remove(id) {
    return DeleteNotebook(id)
  },
}
