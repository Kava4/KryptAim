import styles from './Showcase.module.css'

const PREVIEWS = [
  {
    id: 'global',
    tab: 'Global Settings',
    title: 'Master control & safety',
    lines: ['Recoil toggle + hotkey', 'Shutdown PC on stop', 'Makcu input method', 'X/Y randomisation'],
  },
  {
    id: 'game',
    tab: 'Game Engine',
    title: 'CS2 weapon profiles',
    lines: ['CT / T side picker', 'Rifles & SMGs tabs', 'Weapon icons + spray select', 'In-game sensitivity'],
  },
  {
    id: 'ai',
    tab: 'AimSync AI',
    title: 'Detection & aim pipeline',
    lines: ['NDI capture source', 'YOLO model upload', 'Aim + trigger panels', 'Live FPS / Makcu status'],
  },
] as const

export function Showcase() {
  return (
    <section id="showcase" className={`section ${styles.section}`}>
      <div className="container">
        <p className="section-label">Dashboard</p>
        <h2 className="section-title">The same UI you run locally</h2>
        <p className="section-lead">
          AimSync opens a browser tab on your LAN — dark theme, tabbed settings, and live hardware status
          in the footer. No cloud account required.
        </p>

        <div className={styles.grid}>
          {PREVIEWS.map((preview) => (
            <article key={preview.id} className={styles.frame}>
              <div className={styles.chrome}>
                <span />
                <span />
                <span />
                <p className={styles.url}>http://192.168.x.x:5000</p>
              </div>
              <div className={styles.body}>
                <div className={styles.tabs}>
                  {PREVIEWS.map((t) => (
                    <span
                      key={t.id}
                      className={t.id === preview.id ? styles.tabActive : styles.tab}
                    >
                      {t.tab}
                    </span>
                  ))}
                </div>
                <h3 className={styles.previewTitle}>{preview.title}</h3>
                <ul className={styles.lines}>
                  {preview.lines.map((line) => (
                    <li key={line}>{line}</li>
                  ))}
                </ul>
              </div>
            </article>
          ))}
        </div>
      </div>
    </section>
  )
}
