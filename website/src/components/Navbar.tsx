import { Link, useLocation } from 'react-router-dom'
import { LINKS } from '../data/site'
import styles from './Navbar.module.css'

const HOME_NAV = [
  { href: '/#showcase', label: 'Dashboard' },
  { href: '/#features', label: 'Features' },
  { href: '/#how-it-works', label: 'How it works' },
  { href: '/#download', label: 'Download' },
] as const

export function Navbar() {
  const { pathname } = useLocation()
  const onHome = pathname === '/'

  return (
    <header className={styles.header}>
      <div className={`container ${styles.inner}`}>
        <Link to="/" className={styles.brand}>
          <img src="/AimSync_logo.png" alt="" className={styles.logo} width={40} height={40} />
          <span className={styles.brandText}>
            <span className={styles.name}>AimSync</span>
            <span className={styles.tag}>Dual-PC · CS2</span>
          </span>
        </Link>

        <nav className={styles.nav} aria-label="Primary">
          {HOME_NAV.map((item) => (
            <a key={item.href} href={item.href} className={styles.navLink}>
              {item.label}
            </a>
          ))}
          <Link
            to="/docs"
            className={`${styles.navLink} ${!onHome ? styles.navLinkActive : ''}`}
          >
            Docs
          </Link>
        </nav>

        <div className={styles.actions}>
          <a href={LINKS.github} className="btn btn-ghost" target="_blank" rel="noreferrer">
            GitHub
          </a>
          <a href={onHome ? '#download' : '/#download'} className="btn btn-primary">
            Get started
          </a>
        </div>
      </div>
    </header>
  )
}
