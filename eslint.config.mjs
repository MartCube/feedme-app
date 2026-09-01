// @ts-check
import withNuxt from './.nuxt/eslint.config.mjs'

export default withNuxt(
  {
    // Generated from the backend's OpenAPI schema by `pnpm types:api` — its
    // formatting is the generator's business, not the style rules'.
    ignores: ['app/types/api.d.ts'],
  },
)
