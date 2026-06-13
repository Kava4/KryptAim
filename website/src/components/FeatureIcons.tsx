import type { FeatureAccent } from '../data/site'
import styles from './Features.module.css'

const ACCENT_CLASS: Record<FeatureAccent, string> = {
  blue: styles.iconBlue,
  green: styles.iconGreen,
  amber: styles.iconAmber,
}

type Props = { id: string; accent: FeatureAccent }

export function FeatureIcon({ id, accent }: Props) {
  const className = `${styles.iconSvg} ${ACCENT_CLASS[accent]}`

  switch (id) {
    case 'dual-pc':
      return (
        <svg className={className} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.75" aria-hidden>
          <rect x="2" y="4" width="9" height="7" rx="1" />
          <rect x="13" y="4" width="9" height="7" rx="1" />
          <path d="M6.5 11v2M17.5 11v2M4 17h6M14 17h6" strokeLinecap="round" />
        </svg>
      )
    case 'makcu':
      return (
        <svg className={className} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.75" aria-hidden>
          <rect x="6" y="2" width="12" height="18" rx="2" />
          <path d="M9 7h6M9 11h6M12 20v2" strokeLinecap="round" />
        </svg>
      )
    case 'recoil':
      return (
        <svg className={className} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.75" aria-hidden>
          <circle cx="12" cy="12" r="3" />
          <path d="M12 2v3M12 19v3M2 12h3M19 12h3" strokeLinecap="round" />
          <path d="M4.9 4.9l2.1 2.1M16.9 16.9l2.1 2.1M4.9 19.1l2.1-2.1M16.9 7.1l2.1-2.1" strokeLinecap="round" />
        </svg>
      )
    case 'ai':
      return (
        <svg className={className} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.75" aria-hidden>
          <path d="M12 3l2.2 6.8H21l-5.6 4.1 2.1 6.8L12 16.6 6.5 20.7l2.1-6.8L3 9.8h6.8L12 3z" strokeLinejoin="round" />
        </svg>
      )
    case 'dashboard':
      return (
        <svg className={className} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.75" aria-hidden>
          <rect x="3" y="4" width="18" height="14" rx="2" />
          <path d="M3 9h18M8 15h2M12 15h5" strokeLinecap="round" />
        </svg>
      )
    default:
      return (
        <svg className={className} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.75" aria-hidden>
          <rect x="4" y="4" width="16" height="16" rx="2" />
          <path d="M9 9h6v6H9z" />
        </svg>
      )
  }
}
