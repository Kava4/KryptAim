import { LINKS } from '../data/site'
import styles from './Download.module.css'

const REQUIREMENTS = [
  'Windows 10/11 on AimSync PC',
  'NVIDIA GPU + CUDA 12.6 (AI)',
  'NDI Runtime 6+',
  'Makcu device (production input)',
  'Slim exe: no system Python required',
] as const

export function Download() {
  return (
    <section id="download" className="section">
      <div className="container">
        <div className={styles.layout}>
          <div>
            <p className="section-label">Download</p>
            <h2 className="section-title">Get AimSync on your AimSync PC</h2>
            <p className="section-lead">
              Grab a release build (~100 MB) or clone for development. Recoil works on first
              launch. AI installs once from the dashboard — embeddable Python downloads to{' '}
              <code className={styles.code}>%APPDATA%\AimSync\runtime</code> automatically.
            </p>

            <div className={styles.actions}>
              <a href={LINKS.releases} className="btn btn-primary" target="_blank" rel="noreferrer">
                GitHub Releases
              </a>
              <a href={LINKS.github} className="btn btn-ghost" target="_blank" rel="noreferrer">
                View source
              </a>
            </div>

            <div className={`card ${styles.install}`}>
              <h3 className={styles.installTitle}>Slim exe</h3>
              <pre className={styles.pre}>
                <code>{`AimSync.exe
→ Global Settings → Install AI runtime
→ Restart → Start AI engine`}</code>
              </pre>
              <p className={styles.hint}>
                Config: <code className={styles.code}>%APPDATA%\AimSync\config.json</code>
              </p>
            </div>

            <div className={`card ${styles.install}`}>
              <h3 className={styles.installTitle}>From source</h3>
              <pre className={styles.pre}>
                <code>{`scripts\\install_aimsync_pc.bat
scripts\\run.bat`}</code>
              </pre>
            </div>
          </div>

          <aside className={`card ${styles.aside}`}>
            <h3 className={styles.asideTitle}>Requirements</h3>
            <ul className={styles.list}>
              {REQUIREMENTS.map((item) => (
                <li key={item}>{item}</li>
              ))}
            </ul>
            <hr className={styles.divider} />
            <h3 className={styles.asideTitle}>Also install</h3>
            <ul className={styles.links}>
              <li>
                <a href="https://ndi.link/NDIRedistV6" target="_blank" rel="noreferrer">
                  NDI Tools / Runtime
                </a>
              </li>
              <li>
                <a
                  href="https://developer.nvidia.com/cuda-12-6-0-download-archive"
                  target="_blank"
                  rel="noreferrer"
                >
                  CUDA 12.6
                </a>
              </li>
              <li>
                <a href={LINKS.wiki} target="_blank" rel="noreferrer">
                  Wiki — slim exe guide
                </a>
              </li>
            </ul>
          </aside>
        </div>
      </div>
    </section>
  )
}
