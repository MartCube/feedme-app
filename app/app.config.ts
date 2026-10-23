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
    // Focus is one primary line: the stock theme stacks a 3px primary/25
    // outline outside the ring, which read as two green lines. Only the
    // compound variant can drop it — it's where the outline comes from.
    input: {
      slots: {
        base: 'rounded-xl',
      },
      compoundVariants: [
        {
          color: 'primary',
          variant: ['outline', 'subtle'],
          class: 'focus-visible:outline-0',
        },
      ],
    },
    // Mirror input so a textarea (report, future forms) shares the same shape.
    textarea: {
      slots: {
        base: 'rounded-xl',
      },
      compoundVariants: [
        {
          color: 'primary',
          variant: ['outline', 'subtle'],
          class: 'focus-visible:outline-0',
        },
      ],
    },
    card: {
      slots: {
        root: 'rounded-2xl',
      },
    },
    // The icon buttons' labels (ui/IconButton.vue): bare muted text, no
    // surface, instead of Nuxt UI's ringed chip — the label names the button,
    // it isn't a thing of its own. One step under caption (11px), so it
    // doesn't outweigh the small button it sits over; 15px tall, which is
    // what fits it above the desktop top row.
    tooltip: {
      slots: {
        content: 'h-auto bg-transparent p-0 text-[0.6875rem]/[1.4] text-muted shadow-none ring-0',
      },
    },
  },
})
