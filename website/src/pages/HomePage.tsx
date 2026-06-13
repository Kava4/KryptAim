import { Download } from '../components/Download'
import { Features } from '../components/Features'
import { Hero } from '../components/Hero'
import { HowItWorks } from '../components/HowItWorks'
import { Showcase } from '../components/Showcase'

export function HomePage() {
  return (
    <>
      <Hero />
      <Showcase />
      <Features />
      <HowItWorks />
      <Download />
    </>
  )
}
