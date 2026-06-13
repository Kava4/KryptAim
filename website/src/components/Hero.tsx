import { Link } from 'react-router-dom'
import heroArt from '../assets/hero.png'
import { LINKS } from '../data/site'
import styles from './Hero.module.css'

export function Hero() {
  return (
    <section className={styles.hero}>
      <div className={`container ${styles.inner}`}>
        <div className={styles.copy}>
          <div className="pill">
            <span className="pill-dot" />
            Counter-Strike 2 · Dual-PC
          </div>
          <h1 className={styles.title}>
            Dual-PC control for <span className={styles.highlight}>Counter-Strike 2</span>
          </h1>
          <p className={styles.lead}>
            AimSync is a ~100 MB Windows app with a local web dashboard — spray recoil profiles,
            Makcu hardware input, and a GPU-powered aim engine over NDI. AI installs on first use;
            no system Python required.
          </p>
          <div className={styles.cta}>
            <a href="#download" className="btn btn-primary">
              Download &amp; install
            </a>
            <Link to="/docs" className="btn btn-ghost">
              Documentation
            </Link>
            <a href={LINKS.wiki} className="btn btn-ghost" target="_blank" rel="noreferrer">
              GitHub Wiki
            </a>
          </div>
          <ul className={styles.stats}>
            <li>
              <strong>2 PCs</strong>
              <span>Gaming + AimSync</span>
            </li>
            <li>
              <strong>12</strong>
              <span>CS2 spray weapons</span>
            </li>
            <li>
              <strong>:5000</strong>
              <span>LAN dashboard</span>
            </li>
          </ul>
        </div>

        <div className={styles.visual}>
          <div className={styles.logoGlow} aria-hidden />
          <img src={heroArt} alt="AimSync logo" className={styles.heroArt} />
        </div>
      </div>
    </section>
  )
}
