import { Link } from 'react-router-dom'
import { DOC_SECTIONS } from '../data/docs'
import { LINKS } from '../data/site'
import styles from './DocsPage.module.css'

export function DocsPage() {
  return (
    <div className={styles.page}>
      <div className={`container ${styles.header}`}>
        <Link to="/" className={styles.back}>
          ← Back to home
        </Link>
        <div className={styles.titleRow}>
          <img src="/AimSync_logo.png" alt="" width={40} height={40} className={styles.logo} />
          <div>
            <h1 className={styles.title}>Documentation</h1>
            <p className={styles.subtitle}>Slim exe, embeddable Python, dual-PC, recoil &amp; AI</p>
          </div>
        </div>
      </div>

      <div className={`container ${styles.layout}`}>
        <nav className={styles.toc} aria-label="On this page">
          <p className={styles.tocLabel}>On this page</p>
          <ul>
            {DOC_SECTIONS.map((section) => (
              <li key={section.id}>
                <a href={`#${section.id}`}>{section.title}</a>
              </li>
            ))}
          </ul>
          <a href={LINKS.wiki} className={styles.wikiLink} target="_blank" rel="noreferrer">
            Full GitHub Wiki →
          </a>
        </nav>

        <div className={styles.content}>
          {DOC_SECTIONS.map((section) => (
            <section key={section.id} id={section.id} className="card">
              <h2 className={styles.sectionTitle}>{section.title}</h2>
              {section.paragraphs?.map((p) => (
                <p key={p} className={styles.p}>
                  {p}
                </p>
              ))}
              {section.list && (
                <ul className={styles.list}>
                  {section.list.map((item) => (
                    <li key={item}>{item}</li>
                  ))}
                </ul>
              )}
              {section.code && (
                <pre className={styles.pre}>
                  <code>{section.code}</code>
                </pre>
              )}
              {section.note && <p className={styles.note}>{section.note}</p>}
            </section>
          ))}
        </div>
      </div>
    </div>
  )
}
