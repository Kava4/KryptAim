import { STEPS } from '../data/site'
import styles from './HowItWorks.module.css'

export function HowItWorks() {
  return (
    <section id="how-it-works" className={`section ${styles.section}`}>
      <div className="container">
        <p className="section-label">How it works</p>
        <h2 className="section-title">Two machines, one pipeline</h2>
        <p className="section-lead">
          Video leaves the gaming PC over NDI. Input returns through Makcu. AimSync never needs to
          run on the machine where CS2 is playing.
        </p>

        <div className={styles.diagram}>
          <div className={styles.node}>
            <span className={styles.nodeTag}>Gaming PC</span>
            <p>CS2 + NDI out</p>
          </div>
          <div className={styles.arrow} aria-hidden>
            <span>NDI</span>
          </div>
          <div className={`${styles.node} ${styles.nodePrimary}`}>
            <span className={styles.nodeTag}>AimSync PC</span>
            <p>YOLO · Recoil · Makcu</p>
          </div>
          <div className={styles.arrow} aria-hidden>
            <span>HID</span>
          </div>
          <div className={styles.node}>
            <span className={styles.nodeTag}>Gaming PC</span>
            <p>Mouse input</p>
          </div>
        </div>

        <ol className={styles.steps}>
          {STEPS.map((item) => (
            <li key={item.step} className="card">
              <span className={styles.stepNum}>{item.step}</span>
              <div>
                <h3 className={styles.stepTitle}>{item.title}</h3>
                <p className={styles.stepBody}>{item.body}</p>
              </div>
            </li>
          ))}
        </ol>
      </div>
    </section>
  )
}
