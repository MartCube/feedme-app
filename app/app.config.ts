export default defineAppConfig({
  ui: {
    colors: {
      primary: 'teal',
      neutral: 'ink',
    },
    separator: {
      slots: {
        border: 'border-black/40 shadow-[0_1px_0_rgba(255,255,255,0.05)]',
      },
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
    card: {
      slots: {
        root: 'rounded-2xl',
      },
    },
  },
})
