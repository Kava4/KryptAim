import { copyFileSync } from 'node:fs'
import { resolve } from 'node:path'

const index = resolve('dist', 'index.html')
copyFileSync(index, resolve('dist', '404.html'))
console.log('Copied dist/index.html → dist/404.html (SPA fallback for GitHub Pages)')
