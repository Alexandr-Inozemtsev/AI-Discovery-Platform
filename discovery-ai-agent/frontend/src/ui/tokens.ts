import { colors } from './colors'
import { radius } from './radius'
import { shadows } from './shadows'
import { spacing } from './spacing'
import { transitions } from './transitions'
import { typography } from './typography'

export const uiTokens = {
  colors,
  spacing,
  radius,
  typography,
  shadows,
  transitions,
} as const

export { colors, radius, shadows, spacing, transitions, typography }
