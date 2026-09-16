---
paths:
  - "app/layouts/**"
  - "app/components/desktop/**"
  - "app/pages/**"
  - "app/middleware/**"
  - "nuxt.config.ts"
---

# Shell and routing rules

`app/layouts/default.vue` is the only layout and the single mobile/desktop branch point, on
`useIsDesktop()` (VueUse `useMediaQuery` at `lg`, gated behind `useMounted` so SSR and hydration
always render the mobile tree). The `frontend-dev` skill has the narrative; these are the traps.

- **Drawers (settings, add, edit) mount in the layout, never as pages.**
  `app/pages/{settings,add,edit}*` is blocked by a hook. Their URLs are synthesized in
  `nuxt.config.ts` `pages:extend` against the home page with `meta: { key: 'home' }`, so the
  list stays mounted behind them. Nested route pages remount the parent (nuxt#13094) — tried
  twice, reverted twice.
- **On desktop no route renders a `<NuxtPage>`**, so inside the shell `useRoute()` never
  updates after the first navigation. Read `useRouter().currentRoute` there. Mobile drawer
  hosts may keep `useRoute()` — the mobile tree always renders `<NuxtPage>`.
- **`pageTransition` in `definePageMeta` leaks into the root `<NuxtPage>` meta and remounts
  the whole page tree.** Route transitions come from `middleware/page-slide.global.ts`; a nested
  `<NuxtPage>` takes the `:transition` prop.
- **Panel slide direction rides CSS variables under a fixed transition name**
  (`utils/panel-slide.ts`, `.panel-slide-*` in `assets/css/transitions.css`). Never switch the
  transition *name*: Vue binds leave hooks to the name a panel entered under.
  `--panel-duration: 0s` is the no-direction default and is load-bearing. Equal depth is
  sideways (`none`), not a push.
- The `isDesktopNow()` guards in the drawer hosts and the `useMounted()` gate in
  `useIsDesktop()` are load-bearing — don't simplify them away.
- Navbar content is fixed per page instance (params captured once in setup, no route-driven
  computeds) — the route changes before the leave slide finishes.
- A page whose root component teleports (`UDrawer`) needs a real element root.
