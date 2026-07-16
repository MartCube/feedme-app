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
  },
})
