export const colors = {
  // Backgrounds
  bgVoid: '#07090e',
  bgBase: '#0b0f17',
  bgSurface: '#121824',
  bgCard: '#172030',
  bgCardHover: '#1d273b',
  bgGlass: 'rgba(23, 32, 48, 0.72)',
  bgGlassBorder: 'rgba(64, 88, 128, 0.28)',

  // Borders
  borderSubtle: '#1f2a3e',
  borderDefault: '#293752',
  borderStrong: '#3d4f73',
  borderFocus: '#0f62fe',

  // Primary IBM Bob Accents
  primary: '#0f62fe',
  primaryHover: '#0043ce',
  primaryMuted: 'rgba(15, 98, 254, 0.15)',
  cyanAccent: '#11cbef',
  cyanMuted: 'rgba(17, 203, 239, 0.12)',

  // Text
  textPrimary: '#f4f6fb',
  textSecondary: '#9fb0cc',
  textMuted: '#687794',
  textInverse: '#07090e',

  // Status & Severity
  severityCritical: '#da1e28',
  severityCriticalBg: 'rgba(218, 30, 40, 0.15)',
  severityHigh: '#ff832b',
  severityHighBg: 'rgba(255, 131, 43, 0.15)',
  severityMedium: '#f1c21b',
  severityMediumBg: 'rgba(241, 194, 27, 0.15)',
  severityLow: '#4589ff',
  severityLowBg: 'rgba(69, 137, 255, 0.15)',
  severityInfo: '#8a3ffc',
  severityInfoBg: 'rgba(138, 63, 252, 0.15)',

  // Semantic
  success: '#24a148',
  successBg: 'rgba(36, 161, 72, 0.15)',
  danger: '#da1e28',
  dangerBg: 'rgba(218, 30, 40, 0.15)',
  warning: '#f1c21b',
  warningBg: 'rgba(241, 194, 27, 0.15)',

  // Code / Diff
  diffAddBg: 'rgba(36, 161, 72, 0.18)',
  diffAddText: '#42be65',
  diffRemoveBg: 'rgba(218, 30, 40, 0.18)',
  diffRemoveText: '#ff8389',
} as const

export type ColorToken = keyof typeof colors
