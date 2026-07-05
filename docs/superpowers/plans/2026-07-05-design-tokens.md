# Design Tokens & Theming Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace the ad-hoc color ramps with a 9-role token vocabulary + 4-size type scale, ship two switchable dark themes (Ink, Claude), and sweep all components onto the vocabulary.

**Architecture:** Override Nuxt UI's semantic CSS variables (`--ui-*`) directly per theme in `main.css` (no color ramps). Theme choice lives in a persisted Pinia `settings` store, exposed through a `useTheme` composable, applied as `data-theme` on `<html>`. Spec: `docs/superpowers/specs/2026-07-05-design-tokens-design.md`.

**Tech Stack:** Nuxt 4, Nuxt UI 4, Tailwind CSS 4, Pinia 3 + `pinia-plugin-persistedstate` (new dep), pnpm.

## Global Constraints

- Package manager is **pnpm**.
- Code style: 2-space indent, single quotes, no semicolons; **no `<style>` blocks in components** — non-utility CSS goes in `main.css` only.
- Token vocabulary after this plan: **9 color roles + `shadow-elevated`; text sizes `title/subtitle/body/caption` only; font weights 400 and 600 only.** No other color/size/weight classes in app code.
- **Not a git repository** — all commit steps are omitted; each task ends with a verification step instead.
- **No test framework exists** and this work is visual/theming — verification is `pnpm lint` (must exit 0) plus dev-server checks (`pnpm dev`, app at the printed localhost URL). Do not install a test framework.
- Never mutate body/layout backgrounds outside the theme blocks in `main.css`.

---

### Task 1: Token foundation — themes, type scale, shadow; kill the ramps

**Files:**
- Modify: `app/assets/css/main.css:1-50` (the `@theme` block; rest of file untouched)
- Modify: `app/app.config.ts` (colors, separator)
- Modify: `nuxt.config.ts` (fonts weights)
- Modify: `app/components/ui/IconButton.vue:28` (consumes a deleted ramp var — must move in the same task)
- Modify: `app/pages/index.vue:49,73,88`, `app/pages/feed/[uid]/index.vue:47` (`border-silver-200` — same reason)

**Interfaces:**
- Produces: CSS variables `--ui-bg`, `--ui-bg-elevated`, `--ui-bg-muted`, `--ui-text`, `--ui-text-muted`, `--ui-text-dimmed`, `--ui-border`, `--ui-primary`, `--ui-error` themed on `:root, .dark` (Ink) and `html[data-theme='claude']` (Claude); Tailwind utilities `text-title`, `text-subtitle`, `text-body`, `text-caption`, `shadow-elevated`. Later tasks rely on exactly these names.

- [ ] **Step 1: Replace lines 1–50 of `app/assets/css/main.css`** (the imports + `@theme` ramps) with:

```css
@import "tailwindcss";
@import "@nuxt/ui";

@theme static {
  --font-sora: "Sora", system-ui, sans-serif;

  /* Type scale — the only four text sizes app code may use. rem-based so a
     future font-size setting is a single root multiplier. Weights: 400 and
     600 only (title/subtitle carry 600 via the tokens below). */
  --text-title: 1.5rem;
  --text-title--line-height: 1.25;
  --text-title--font-weight: 600;
  --text-subtitle: 1.125rem;
  --text-subtitle--line-height: 1.35;
  --text-subtitle--font-weight: 600;
  --text-body: 1rem;
  --text-body--line-height: 1.6;
  --text-caption: 0.75rem;
  --text-caption--line-height: 1.4;

  /* Glass edge for lifted surfaces (cards, drawers, icon buttons): hairline
     ring + soft drop shadow + faint top inner highlight. Flat-on-page
     elements use border-default hairlines instead. */
  --shadow-elevated: 0 0 0 1px var(--ui-border), 0 2px 8px -4px rgb(0 0 0 / 0.5), inset 0 1px 0 rgb(255 255 255 / 0.04);
}

/* ---- Themes ---------------------------------------------------------------
   A theme = the 9 color roles, nothing more. Both launch themes are dark; a
   light theme is just another block (elevation flips darker, the hairline
   flips to black at low alpha). Lines marked "alias" exist only so Nuxt UI
   internals never render an unmapped color — they are not app vocabulary.
   The Ink block targets `:root, .dark` so it outranks Nuxt UI's own `.dark`
   variable definitions (same specificity, later in the cascade). */

/* Theme: Ink (default) — cool neutral greys, teal accent. */
:root,
.dark {
  --ui-bg: #1f1f21; /* page */
  --ui-bg-elevated: #252527; /* cards, drawers, navbar buttons */
  --ui-bg-muted: #303032; /* inputs, hover/pressed, avatar placeholders */
  --ui-bg-accented: #303032; /* alias → bg-muted */
  --ui-bg-inverted: #f2f2f2; /* alias → text */

  --ui-text: #f2f2f2; /* titles + body */
  --ui-text-highlighted: #f2f2f2; /* alias → text (Nuxt UI headings) */
  --ui-text-muted: #9a9a9e; /* dates, counts, descriptions */
  --ui-text-toned: #9a9a9e; /* alias → text-muted */
  --ui-text-dimmed: #6e6e72; /* placeholders + disabled ONLY, never content */
  --ui-text-inverted: #1f1f21; /* alias → bg */

  --ui-border: rgba(255, 255, 255, 0.07); /* hairline: dividers, input outlines */
  --ui-border-muted: rgba(255, 255, 255, 0.07); /* alias → border */
  --ui-border-accented: rgba(255, 255, 255, 0.07); /* alias → border */

  --ui-primary: #2dd4bf; /* accent: active states, links, key actions */
  --ui-error: #f87171; /* validation + destructive */
}

/* Theme: Claude — warm greys with a brown undertone, cream text, terracotta
   accent; muted text is the warm "oat" grey. Values eyeballed from claude.ai
   dark mode — fine-tune on screen. */
html[data-theme='claude'] {
  --ui-bg: #262624;
  --ui-bg-elevated: #30302e;
  --ui-bg-muted: #3a3a38;
  --ui-bg-accented: #3a3a38;
  --ui-bg-inverted: #f5f4ef;

  --ui-text: #f5f4ef;
  --ui-text-highlighted: #f5f4ef;
  --ui-text-muted: #b8b5a9;
  --ui-text-toned: #b8b5a9;
  --ui-text-dimmed: #83827d;
  --ui-text-inverted: #262624;

  --ui-border: rgba(255, 255, 255, 0.08);
  --ui-border-muted: rgba(255, 255, 255, 0.08);
  --ui-border-accented: rgba(255, 255, 255, 0.08);

  --ui-primary: #d97757;
  --ui-error: #e5695e;
}
```

Everything from `@layer base` (line 52) down stays exactly as is.

- [ ] **Step 2: Update `app/app.config.ts`** — point the aliases at Tailwind's built-in ramps (Tailwind's own `teal-400` is `#2dd4bf`, the same primary; these ramps only matter as a fallback for any Nuxt UI internal that wants a shade step — our `--ui-*` overrides win everywhere visible), and delete the separator override (the Separator's default already uses `--ui-border`, which is now our hairline):

```ts
export default defineAppConfig({
  ui: {
    colors: {
      primary: 'teal',
      neutral: 'zinc',
    },
    drawer: {
```

(i.e. `neutral: 'ink'` → `neutral: 'zinc'`, and the whole `separator:` block is removed; `drawer`, `button`, `input`, `card` blocks unchanged.)

- [ ] **Step 3: Load only Sora 400 + 600.** In `nuxt.config.ts`, add a `fonts` key directly after the `colorMode` block:

```ts
  colorMode: {
    preference: 'dark',
    fallback: 'dark',
  },
  // Only the two weights the type scale allows (400 body, 600 titles).
  fonts: {
    families: [
      { name: 'Sora', provider: 'google', weights: [400, 600] },
    ],
  },
```

- [ ] **Step 4: Move the two ramp consumers onto tokens** (they break the moment the ramps are gone):

`app/components/ui/IconButton.vue:28` — replace the hand-rolled shadow with the token:

```
before: shadow-[0_0_0_1px_var(--color-ink-800),0_2px_6px_-3px_rgba(0,0,0,0.4)]
after:  shadow-elevated
```

so the line reads:

```vue
    :ui="{ base: `rounded-full justify-center bg-elevated ${buttonSize} shadow-elevated hover:bg-elevated` }"
```

`border-silver-200` → `border-default` in all four places:
- `app/pages/index.vue:49` `class="flex items-center border-b border-default"`
- `app/pages/index.vue:73` (the `:class` for member feed rows) `border-b border-default`
- `app/pages/index.vue:88` `border-b border-default`
- `app/pages/feed/[uid]/index.vue:47` `class="border-b border-default"`

- [ ] **Step 5: Verify no ramp references survive**

Run: `grep -rn "silver-\|ink-\|teal-[0-9]" app/ --include='*.vue' --include='*.ts' --include='*.css'`
Expected: no output.

- [ ] **Step 6: Lint and look**

Run: `pnpm lint` — expected exit 0.
Run: `pnpm dev` (background), open the app. Expected: home list, feed page, post page, settings drawer, add drawer all look like before (same greys, teal accent, dividers now hairline-subtle, icon buttons still ringed). Manually set `document.documentElement.dataset.theme = 'claude'` in the browser console: entire app flips to warm browns / cream text / terracotta instantly. Remove with `delete document.documentElement.dataset.theme`.

---

### Task 2: Sweep all text onto the 4-size scale

**Files:**
- Modify: `app/pages/index.vue`, `app/pages/feed/[uid]/index.vue`, `app/pages/feed/[uid]/post/[postUid].vue`, `app/components/feed/PostCard.vue`, `app/components/settings/{Account,About,Report,Page,Home,Appearance}.vue`

**Interfaces:**
- Consumes: `text-title` / `text-subtitle` / `text-body` / `text-caption` utilities from Task 1.
- Produces: no app code uses stock Tailwind text sizes or `font-bold` anymore.

- [ ] **Step 1: Apply the exact replacements.** Sizes carry their weight/line-height via the tokens, so paired `font-semibold`/`font-bold` and `leading-*` on the same element are dropped (weights on *other* elements, like uppercase caption headers, stay — 600 is an allowed weight).

`app/pages/index.vue`:
- L37 `mt-8 text-2xl font-semibold tracking-tight` → `mt-8 text-title tracking-tight`
- L54 `truncate text-xl leading-8` → `truncate text-body`
- L55 `text-sm text-muted` → `text-caption text-muted`
- L77 `'block truncate py-4 pl-6 text-xl leading-8'` → `'block truncate py-4 pl-6 text-body'`
- L92 `block truncate py-4 text-xl leading-8` → `block truncate py-4 text-body`

`app/components/feed/PostCard.vue`:
- L17 `text-sm text-muted` → `text-caption text-muted`
- L19 `text-xl leading-7` → `text-subtitle` (post titles in lists = subtitle)

`app/pages/feed/[uid]/index.vue`:
- L39 `mt-8 text-2xl font-semibold tracking-tight` → `mt-8 text-title tracking-tight`

`app/pages/feed/[uid]/post/[postUid].vue`:
- L30 `mt-8 text-2xl font-semibold tracking-tight` → `mt-8 text-title tracking-tight`
- L35 `mt-1 text-sm text-muted` → `mt-1 text-caption text-muted`
- L37 `mt-6 text-lg leading-8` → `mt-6 text-body` (reading text = body, 16px/1.6)

`app/components/settings/Account.vue`:
- L7 `text-xs font-semibold uppercase tracking-wide text-muted` → `text-caption font-semibold uppercase tracking-wide text-muted`
- L17, L21 `text-sm text-muted` → `text-caption text-muted`

`app/components/settings/About.vue`:
- L10, L14, L17 `text-sm text-muted` → `text-caption text-muted`

`app/components/settings/Report.vue`:
- L8 `text-sm text-muted` → `text-caption text-muted`

`app/components/settings/Page.vue`:
- L17 `text-xl font-semibold` → `text-subtitle`

`app/components/settings/Home.vue`:
- L24 `mt-10 text-4xl font-bold tracking-tight` → `mt-10 text-title tracking-tight` (screen title = title; 600 replaces the stray bold)
- L35 `flex items-center gap-4 py-4 text-xl` → `flex items-center gap-4 py-4 text-body`

`app/components/settings/Appearance.vue`:
- L7, L26 `text-xs font-semibold uppercase tracking-wide text-muted` → `text-caption font-semibold uppercase tracking-wide text-muted`
- L13, L17, L20, L31 `text-sm text-muted` → `text-caption text-muted`

- [ ] **Step 2: Verify the sweep is total**

Run: `grep -rnE "text-(xs|sm|base|lg|xl|2xl|3xl|4xl)([^-]|$)|font-bold" app/ --include='*.vue'`
Expected: no output.

- [ ] **Step 3: Lint and look**

Run: `pnpm lint` — expected exit 0.
Dev server: home rows now 16px regular, post titles in lists 18px semibold, screen titles 24px semibold, all meta 12px. If home feed rows read too small on a phone-width viewport, note it for the user — do not invent a fifth size.

---

### Task 3: Theme state — persisted settings store + useTheme composable

**Files:**
- Modify: `package.json` (via pnpm), `nuxt.config.ts` (module), `app/app.vue`
- Create: `app/stores/settings.ts`, `app/composables/useTheme.ts`

**Interfaces:**
- Produces: `useSettingsStore()` with `theme: Ref<ThemeName>`; `useTheme()` returning `{ theme: Ref<ThemeName>, themes: readonly { name: ThemeName, label: string }[], setTheme(name: ThemeName): void }`; type `ThemeName = 'ink' | 'claude'`. Task 4 consumes `useTheme()` exactly as typed here.

- [ ] **Step 1: Install the persistence plugin**

Run: `pnpm add pinia-plugin-persistedstate`
Expected: added to `dependencies`, exit 0.

- [ ] **Step 2: Register its Nuxt module** — in `nuxt.config.ts`, the plugin's module must come after `@pinia/nuxt`:

```ts
  modules: ['@nuxt/eslint', '@nuxt/ui', '@pinia/nuxt', 'pinia-plugin-persistedstate/nuxt', '@vueuse/motion/nuxt'],
```

- [ ] **Step 3: Create `app/stores/settings.ts`**

```ts
export type ThemeName = 'ink' | 'claude'

// App-wide user preferences, persisted to localStorage. Future appearance
// settings (font size, card style, layout) belong here too.
export const useSettingsStore = defineStore('settings', () => {
  const theme = ref<ThemeName>('ink')

  return { theme }
}, {
  persist: true,
})
```

- [ ] **Step 4: Create `app/composables/useTheme.ts`**

```ts
import type { ThemeName } from '~/stores/settings'

export const themes: readonly { name: ThemeName, label: string }[] = [
  { name: 'ink', label: 'Ink' },
  { name: 'claude', label: 'Claude' },
]

// The only theming interface components use; the settings store stays an
// implementation detail behind it.
export function useTheme() {
  const settings = useSettingsStore()
  const { theme } = storeToRefs(settings)

  function setTheme(name: ThemeName) {
    settings.theme = name
  }

  return { theme, themes, setTheme }
}
```

- [ ] **Step 5: Apply the attribute once at the root.** (Deliberate small deviation from the spec: `useHead` lives in `app.vue`, not inside `useTheme()`, so components using the composable don't each register a duplicate head entry.) Replace `app/app.vue`'s script-less top with:

```vue
<script setup lang="ts">
// data-theme drives the theme blocks in assets/css/main.css.
const { theme } = useTheme()
useHead({ htmlAttrs: { 'data-theme': theme } })
</script>

<template>
  <UApp>
    <NuxtLayout>
      <!-- Reader-flow slide transitions come from route meta, set by middleware/page-slide.global.ts. -->
      <NuxtPage />
    </NuxtLayout>
  </UApp>
</template>
```

- [ ] **Step 6: Verify state, application, and persistence**

Run: `pnpm lint` — expected exit 0.
Dev server, browser console:
1. `document.documentElement.getAttribute('data-theme')` → `'ink'`.
2. Pinia devtools (or console): set the store — `useNuxtApp().$pinia.state.value.settings.theme = 'claude'` — the app flips warm instantly and `data-theme` is `'claude'`.
3. `localStorage.getItem('settings')` → contains `"theme":"claude"`.
4. Hard-refresh: app comes back in Claude theme (a one-frame Ink flash is the accepted trade-off from the spec).

---

### Task 4: Theme switch UI in Settings → Appearance

**Files:**
- Modify: `app/components/settings/Appearance.vue` (the Theme section, lines 25–33 after Task 2's sweep)

**Interfaces:**
- Consumes: `useTheme()` → `{ theme, themes, setTheme }` from Task 3.

- [ ] **Step 1: Replace the static Theme section.** Add the script block and swap the section (Cards section stays mock):

```vue
<script setup lang="ts">
const { theme, themes, setTheme } = useTheme()
</script>
```

```vue
    <section>
      <h3 class="text-caption font-semibold uppercase tracking-wide text-muted">
        Theme
      </h3>
      <div class="mt-3 flex flex-col gap-px overflow-hidden rounded-2xl">
        <button
          v-for="option in themes"
          :key="option.name"
          type="button"
          class="flex items-center justify-between bg-elevated p-4 text-left"
          @click="setTheme(option.name)"
        >
          <span>{{ option.label }}</span>
          <UIcon
            v-if="theme === option.name"
            name="i-ph-check-bold"
            class="size-5 text-primary"
          />
        </button>
      </div>
    </section>
```

- [ ] **Step 2: Verify end to end**

Run: `pnpm lint` — expected exit 0.
Dev server: open settings drawer → Appearance. Tapping Claude flips the whole app (page bg, drawers, text, teal→terracotta accent) with the drawer still open; check shows on the active row; refresh keeps the choice; tapping Ink returns everything. Also run `pnpm build` — expected: completes without errors.

---

### Task 5: Documentation

**Files:**
- Create: `docs/design-system.md`
- Modify: `docs/current-state.md`, `docs/README.md` (add the new doc to its index list, matching its existing line format)

- [ ] **Step 1: Create `docs/design-system.md`** with exactly the agreed system (copy tables from the spec `docs/superpowers/specs/2026-07-05-design-tokens-design.md`): the 9-role table, `shadow-elevated`, the Ink/Claude value table, the 4-size type scale table (24/18/16/12, weights 400/600, line-heights 1.25/1.35/1.6/1.4), and the two rules stated verbatim:

> **9 color roles, 4 text sizes.** If you need something outside them, that's a design discussion, not a new class.

Plus one paragraph on how theming works (`--ui-*` blocks in `main.css`, `data-theme` attribute, `useTheme()` / `stores/settings.ts`, persisted to localStorage) and the "later" list (light themes, font-size setting, user layouts).

- [ ] **Step 2: Update `docs/current-state.md`:**
- "Theme tokens" bullet → describe the new system in one line (9 `--ui-*` roles themed in `main.css`, two dark themes, type scale utilities; ramps removed) and link `design-system.md`.
- Remove the stale `app/pages/design.vue` bullet (the file no longer exists).
- Add a Built bullet: theme switch (Settings → Appearance) via persisted Pinia `settings` store + `useTheme`.
- Update the "Installed but unused" Pinia line (stores exist now: `feeds`, `settings`).
- Bump the "_Last reviewed:_" date to the implementation date.

- [ ] **Step 3: Final check**

Run: `pnpm lint` — expected exit 0. Confirm every doc link resolves (paths exist).

---

## Self-review notes (already applied)

- Spec coverage: vocabulary (T1), themes (T1), glass border/shadow (T1), type scale + caption 12px (T1/T2), store/composable/switch (T3/T4), cleanup list (T1/T2), docs rules (T5). The spec's `text-highlighted`/`toned` alias note is implemented in the theme blocks.
- Known deviation, intentional: `useHead` in `app.vue` instead of inside `useTheme()` (avoids duplicate head entries; spec's intent — reactive `data-theme` — unchanged).
- Fallback if any Nuxt UI internal renders an odd green/slate: it hit a ramp step we don't override; fix by overriding that single `--ui-color-*` step in the theme blocks — do not reintroduce full ramps.
