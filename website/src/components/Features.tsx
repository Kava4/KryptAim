import { FEATURES, type FeatureAccent } from '../data/site'
import { FeatureIcon } from './FeatureIcons'
import styles from './Features.module.css'

const ICON_BOX: Record<FeatureAccent, string> = {
  blue: styles.iconBlue,
  green: styles.iconGreen,
  amber: styles.iconAmber,
}

export function Features() {
  return (
    <section id="features" className="section">
      <div className="container">
        <p className="section-label">Features</p>
        <h2 className="section-title">Built for dual-PC CS2</h2>
        <p className="section-lead">
          Recoil, Makcu, and AI in one local app — same look and feel as the dashboard you already use.
        </p>

        <ul className={styles.grid}>
          {FEATURES.map((feature) => (
            <li key={feature.id} className={styles.card}>
              <div className={`${styles.iconBox} ${ICON_BOX[feature.accent]}`}>
                <FeatureIcon id={feature.id} accent={feature.accent} />
              </div>
              <div className={styles.copy}>
                <h3 className={styles.title}>{feature.title}</h3>
                <p className={styles.text}>{feature.description}</p>
              </div>
            </li>
          ))}
        </ul>
      </div>
    </section>
  )
}
