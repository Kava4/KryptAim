export const LINKS = {
  github: 'https://github.com/Kava4/AimSync',
  releases: 'https://github.com/Kava4/AimSync/releases',
  wiki: 'https://github.com/Kava4/AimSync/wiki',
  kofi: 'https://ko-fi.com/kava4',
  paypal: 'https://paypal.me/kava4',
} as const

export type FeatureAccent = 'blue' | 'green' | 'amber'

export type Feature = {
  id: string
  title: string
  description: string
  accent: FeatureAccent
}

export const FEATURES: Feature[] = [
  {
    id: 'dual-pc',
    title: 'Dual-PC workflow',
    description:
      'CS2 on the gaming PC. AimSync, Makcu, and GPU on a second machine — nothing to install on the game box.',
    accent: 'blue',
  },
  {
    id: 'makcu',
    title: 'Makcu HID input',
    description:
      'Hardware mouse movement in production. Low latency path from AimSync PC back to your game setup.',
    accent: 'green',
  },
  {
    id: 'recoil',
    title: 'CS2 spray profiles',
    description:
      '12 weapons with tuned patterns. CT/T picker, rifles & SMGs, sensitivity scaling, randomisation.',
    accent: 'amber',
  },
  {
    id: 'ai',
    title: 'AimSync AI engine',
    description:
      'YOLO detection, aim assist, and triggerbot. NDI capture from the gaming feed — no hook on CS2.',
    accent: 'blue',
  },
  {
    id: 'dashboard',
    title: 'Local web dashboard',
    description:
      'Dark UI on port 5000. Configure recoil, weapons, and AI from any device on your LAN.',
    accent: 'green',
  },
  {
    id: 'desktop',
    title: 'Small exe, full power',
    description:
      '~100 MB release build. Recoil works day one; AI installs to AppData with embeddable Python — no system Python on the AimSync PC.',
    accent: 'amber',
  },
]

export const STEPS = [
  {
    step: '01',
    title: 'Gaming PC',
    body: 'Run CS2 and send video out via NDI. No AimSync install required on this machine.',
  },
  {
    step: '02',
    title: 'AimSync PC',
    body: 'Run AimSync.exe, install CUDA + NDI Runtime, connect Makcu. AI tab installs the runtime on first use — then add your ONNX model.',
  },
  {
    step: '03',
    title: 'Configure & play',
    body: 'Open the dashboard, pick weapons, set NDI source, start the AI engine, and verify Makcu shows Connected.',
  },
] as const
