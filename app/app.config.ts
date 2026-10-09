export default defineAppConfig({
  ui: {
    // Teach Nuxt UI's tailwind-merge our custom @theme scales (spacing.css,
    // typography.css) so `:ui` overrides like px-sm properly REPLACE component
    // defaults like px-3 instead of coexisting and racing on CSS order.
    tv: {
      twMergeConfig: {
        extend: {
          theme: {
            spacing: ['2xs', 'xs', 'sm', 'md', 'lg', 'xl'],
            text: ['caption', 'body', 'subtitle', 'title'],
            // main.css's one shadow token — so shadow-elevated replaces a default
            // like shadow-sm instead of both landing and the default winning
            shadow: ['elevated'],
          },
        },
      },
    },
    colors: {
      primary: 'teal',
      neutral: 'zinc',
    },
    drawer: {
      slots: {
        // Overlay darker than the sheet so the rounded top edge is visible —
        // sheet and page share the same bg color.
        overlay: 'bg-black/60',
        content: 'bg-default',
      },
      // The radius lives in the theme's compound variants (per direction), so
      // a slot class can't override it — this compound variant can.
      compoundVariants: [
        {
          direction: 'bottom',
          inset: false,
          class: {
            content: 'rounded-t-[3rem]',
          },
        },
      ],
    },
    button: {
      slots: {
        base: 'rounded-xl',
      },
    },
    input: {
      slots: {
        base: 'rounded-xl',
      },
    },
    // Mirror input so a textarea (report, future forms) shares the same shape.
    textarea: {
      slots: {
        base: 'rounded-xl',
      },
    },
    card: {
      slots: {
        root: 'rounded-2xl',
      },
    },
    // The icon buttons' labels (ui/IconButton.vue), in the house vocabulary
    // instead of Nuxt UI's ring + text-xs. bg-muted, not bg-elevated: a tooltip
    // floats over cards, which are elevated themselves and would swallow it.
    // No shadow-elevated either — its edge is drawn in bg-elevated, a darker
    // outline on muted (design-system.md § Hover state).
    tooltip: {
      slots: {
        content: 'h-auto rounded-xl bg-muted px-xs py-2xs text-caption text-default shadow-none ring-0',
      },
    },
  },
})
