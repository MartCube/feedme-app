# Components directory reorganization — design

**Date:** 2026-07-04
**Scope:** pure file reorganization of `app/components/` plus one `nuxt.config.ts` entry.
Also removes `pages/design.vue` and `layouts/plain.vue` (user decision, 2026-07-04): the
design page is no longer needed, and it was the only consumer of the `plain` layout, so
`default.vue` becomes the app's sole layout.
**Out of scope:** the settings→routed-pages migration described in
[screens-and-flows.md](../../screens-and-flows.md#5-settings--pagessettingsvue--nested-subpages)
stays a separate future task. No component internals change.

## Goal

The flat `app/components/` root (10 files, manual name prefixes) becomes domain folders
before the upcoming feed work (folder rows, context menus, add-feed form, confirmation
dialogs) lands. Grouping rule: **primitives get short names, domain components get
folder-derived prefixes.**

## Target structure

```
app/components/
  ui/                    # app-agnostic primitives — NO name prefix
    IconButton.vue       → <IconButton>
  feed/                  # feed domain — prefixed
    PostCard.vue         → <FeedPostCard>
  settings/              # settings domain — prefixed
    Drawer.vue           → <SettingsDrawer>
    Home.vue             → <SettingsHome>
    Page.vue             → <SettingsPage>
    Account.vue          → <SettingsAccount>
    Appearance.vue       → <SettingsAppearance>
    About.vue            → <SettingsAbout>
    Report.vue           → <SettingsReport>
  Navbar.vue             → <Navbar>   # app shell, stays at root
```

Future components follow the same rule: `ui/ConfirmDialog.vue` → `<ConfirmDialog>`,
`feed/FolderRow.vue` → `<FeedFolderRow>`.

## nuxt.config.ts

```ts
components: [
  { path: '~/components/ui', pathPrefix: false },
  '~/components',
]
```

The `ui/` entry registers primitives unprefixed; the catch-all keeps Nuxt's default
path-prefix naming for `feed/` and `settings/`. **Verify during implementation** that the
catch-all does not also register `ui/` components under `Ui*` names (earlier entries win on
name conflicts, but these names differ); if both names appear, add an ignore pattern for
`ui/**` to the catch-all entry. Respect the established nuxt.config key order.

## Template impact

Exactly one rename: `<PostCard>` → `<FeedPostCard>` in `app/pages/feed/[uid]/index.vue`.
All `Settings*` usages and `<IconButton>` usages are unchanged because the new
folder-derived (or unprefixed) names equal the current names.

## Verification

1. `pnpm lint` passes.
2. Dev server renders with no missing-component warnings: home (Navbar + IconButton +
   settings drawer), a feed page (PostCards), and `/design`.
3. `.nuxt/components.d.ts` lists each component exactly once under the expected name.

## Docs follow-up

`docs/screens-and-flows.md` references `components/PostCard.vue`, `components/Navbar.vue`,
`components/IconButton.vue`, and the `Settings*` component paths. Update those paths at
session end / pre-commit, per the established docs-update timing.
