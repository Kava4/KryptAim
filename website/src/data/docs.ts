export type DocSection = {
  id: string
  title: string
  paragraphs?: string[]
  list?: string[]
  code?: string
  note?: string
}

export const DOC_SECTIONS: DocSection[] = [
  {
    id: 'requirements',
    title: 'Requirements',
    list: [
      'Windows 10/11 on the AimSync PC',
      'NVIDIA GPU + CUDA 12.6 for the AI engine',
      'NDI Runtime 6+ on both PCs',
      'Makcu HID device (production mouse input)',
      'Slim exe: no system Python — AI runtime installs to AppData',
      'From source: Python 3.12 + scripts\\install_aimsync_pc.bat',
    ],
  },
  {
    id: 'install-exe',
    title: 'Slim exe (releases)',
    paragraphs: [
      'Default release is ~50–120 MB. Recoil and the dashboard work immediately. AI installs once from the AI tab — embeddable Python is downloaded automatically.',
    ],
    list: [
      'Extract AimSync.exe from the release zip',
      'Run AimSync.exe',
      'Global Settings → AI Runtime → Install (10–20 min, internet required)',
      'Restart AimSync, then configure NDI + model',
    ],
    note: 'Runtime lives in %APPDATA%\\AimSync\\runtime\\ (embed Python + venv). Full offline build (~2–4 GB) available for maintainers via build_app_full.bat.',
  },
  {
    id: 'install',
    title: 'Install from source',
    paragraphs: ['On the AimSync PC, from the project folder:'],
    code: `scripts\\install_aimsync_pc.bat
scripts\\run.bat`,
    note: 'Opens http://<local-ip>:5000 in your browser. Config: %APPDATA%\\AimSync\\config.json',
  },
  {
    id: 'dual-pc',
    title: 'Dual-PC setup',
    list: [
      'Gaming PC: CS2 + NDI video out. No AimSync install needed.',
      'AimSync PC: AimSync app, Makcu, GPU, ONNX model in %APPDATA%\\AimSync\\bin\\models\\',
      'Connect gaming mouse through Makcu so button state is read on the AimSync PC.',
    ],
  },
  {
    id: 'recoil',
    title: 'Recoil & Game Engine',
    list: [
      'Global Settings → enable master switch and set hotkey (default M4).',
      'Input method → Hardware (Makcu) for dual-PC production.',
      'Game Engine → pick CT/T, weapon type, and spray profile.',
      'Match in-game sensitivity to your CS2 settings.',
    ],
  },
  {
    id: 'ai',
    title: 'AimSync AI',
    list: [
      'Slim exe: install AI runtime from the banner on first use, then restart.',
      'Upload or select an ONNX/PT model (e.g. cs2_640.onnx).',
      'Capture → NDI → refresh sources → pick gaming PC stream.',
      'Set main PC resolution (e.g. 1920×1080).',
      'Configure Aim / Trigger panels, then Start AI engine.',
      'Footer should show Makcu Connected when hardware is linked.',
    ],
  },
  {
    id: 'build',
    title: 'Build (maintainers)',
    paragraphs: ['Lite (default) vs full offline bundle:'],
    code: `scripts\\create_build_venv.bat
scripts\\build_app.bat          REM lite ~100 MB
scripts\\build_app_full.bat     REM full ~2–4 GB
scripts\\package_release.bat`,
    note: 'Lite: dist\\AimSync.exe (single file). Full: dist\\AimSync\\ folder. Lite users get one-click AI install with embeddable Python.',
  },
  {
    id: 'troubleshoot',
    title: 'Troubleshooting',
    list: [
      'Makcu disconnected → check USB, replug, verify Input method is Hardware.',
      'NDI no sources → install NDI Runtime on gaming PC and enable NDI out.',
      'AI won’t start (slim exe) → Install AI runtime, restart, check %APPDATA%\\AimSync\\aimsync.log',
      'AI won’t start (venv) → run scripts\\repair_ai_deps.bat and verify CUDA.',
      'Dev mode (local mouse) → set AIMSYNC_DEV=1 via run_dev.bat only for testing.',
    ],
  },
]
