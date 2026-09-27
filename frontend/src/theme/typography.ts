export const typography = {
  fontSans: '"Inter", -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif',
  fontMono: '"JetBrains Mono", "Fira Code", Menlo, Monaco, Consolas, monospace',
  sizes: {
    xs: '0.75rem',    // 12px
    sm: '0.8125rem',  // 13px
    base: '0.875rem', // 14px
    md: '1rem',       // 16px
    lg: '1.125rem',   // 18px
    xl: '1.25rem',    // 20px
    '2xl': '1.5rem',  // 24px
    '3xl': '1.875rem' // 30px
  },
  weights: {
    regular: '400',
    medium: '500',
    semibold: '600',
    bold: '700'
  },
  lineHeights: {
    tight: '1.2',
    normal: '1.5',
    relaxed: '1.75'
  }
} as const
