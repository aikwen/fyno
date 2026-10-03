import {
  cp,
  rm,
} from 'node:fs/promises'

import path from 'node:path'
import { fileURLToPath } from 'node:url'

const __filename = fileURLToPath(import.meta.url)
const __dirname = path.dirname(__filename)

const frontendRoot = path.resolve(
  __dirname,
  '..',
)

const projectRoot = path.resolve(
  frontendRoot,
  '..',
)

const source = path.join(
  frontendRoot,
  'dist',
)

const target = path.join(
  projectRoot,
  'src',
  'fyno',
  'static',
)

await rm(
  target,
  {
    recursive: true,
    force: true,
  },
)

await cp(
  source,
  target,
  {
    recursive: true,
  },
)

console.log(
  `Copied frontend build:\n${source}\n→ ${target}`,
)