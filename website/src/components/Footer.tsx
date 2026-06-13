import { LINKS } from '../data/site'
import styles from './Footer.module.css'

export function Footer() {
  return (
    <footer className={styles.footer}>
      <div className={`container ${styles.inner}`}>
        <div className={styles.brand}>
          <img src="/AimSync_logo.png" alt="" width={32} height={32} className={styles.logo} />
          <div>
            <p className={styles.name}>AimSync</p>
            <p className={styles.note}>Educational &amp; hardware testing use</p>
          </div>
        </div>

        <nav className={styles.nav} aria-label="Footer">
          <a href={LINKS.github} target="_blank" rel="noreferrer">
            GitHub
          </a>
          <a href={LINKS.wiki} target="_blank" rel="noreferrer">
            Wiki
          </a>
          <a href={LINKS.kofi} target="_blank" rel="noreferrer">
            Ko-fi
          </a>
          <a href={LINKS.paypal} target="_blank" rel="noreferrer">
            PayPal
          </a>
        </nav>

        <p className={styles.disclaimer}>
          Using input automation in online games may violate publisher terms of service. You are
          responsible for how you use this software. Not affiliated with aimsync.ai.
        </p>

        <p className={styles.copy}>© {new Date().getFullYear()} AimSync</p>
      </div>
    </footer>
  )
}
