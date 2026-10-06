import { createContext, useCallback, useContext, useEffect, useState } from 'react'
import { CalendarClock, Database, GitCompareArrows, Map as MapIcon, MountainSnow, Presentation, Route, ScrollText } from 'lucide-react'
import { day, useApi, type Mode, type Row } from './api'
import { Chip, Drone } from './ui'
import GuidedDemo from './GuidedDemo'
import Dashboard from './screens/Dashboard'
import PostDetail from './screens/PostDetail'
import Pnr from './screens/Pnr'
import Plan from './screens/Plan'
import Drones from './screens/Drones'
import WhatIf from './screens/WhatIf'
import Sources from './screens/Sources'
import Audit from './screens/Audit'

export type Role = 'Commander' | 'Logistics Officer' | 'Post QM'
type Ctx = { mode: Mode; setMode: (m: Mode) => void; role: Role; setRole: (r: Role) => void; route: string[]; go: (path: string) => void }
const AppCtx = createContext<Ctx>(null as never)
export const useApp = () => useContext(AppCtx)

const NAV = [
  ['dashboard', 'Dashboard', MapIcon], ['post', 'Posts', MountainSnow], ['pnr', 'Point of no return', CalendarClock],
  ['plan', 'Plan', Route], ['drones', 'Drones', Drone], ['whatif', 'What-if', GitCompareArrows],
  ['sources', 'Sources', Database], ['audit', 'Audit log', ScrollText],
] as const

const parse = () => (location.hash.replace(/^#\/?/, '').replace(/\?.*$/, '') || 'dashboard').split('/')

export default function App() {
  const [route, setRoute] = useState(parse)
  const [mode, setMode] = useState<Mode>('demo')
  const [role, setRole] = useState<Role>('Commander')
  // '#/dashboard?demo=3' opens the guided demo at moment 3 (handy to recover mid-presentation)
  const [demoStep, setDemoStep] = useState<number | null>(() => { const m = location.hash.match(/demo=(\d)/); return m ? Math.min(7, Math.max(1, Number(m[1]))) - 1 : null })
  useEffect(() => {
    const on = () => setRoute(parse())
    window.addEventListener('hashchange', on)
    return () => window.removeEventListener('hashchange', on)
  }, [])
  const go = useCallback((path: string) => { location.hash = '/' + path }, [])
  const health = useApi(`health?mode=${mode}`)
  const pnr = useApi(`pnr?mode=${mode}`, true)
  const sources = useApi<Row[]>('sources')

  const screen = { dashboard: Dashboard, post: PostDetail, pnr: Pnr, plan: Plan, drones: Drones, whatif: WhatIf, sources: Sources, audit: Audit }[route[0]] ?? Dashboard
  const Screen = screen
  const axes = pnr.data?.axes as Row[] | undefined
  const warn = sources.data?.filter((s) => s.health !== 'ok').length ?? 0

  return (
    <AppCtx.Provider value={{ mode, setMode, role, setRole, route, go }}>
      <div className="shell">
        <header className="top">
          <a className="brand" href="#/dashboard" aria-label="RASAD home"><b>RASAD</b><span lang="hi">रसद</span></a>
          <div className="sector">Sector X<small>fictional</small></div>
          <span className="spacer" />
          <span className="clock" title={mode === 'live' ? 'Live: today, with the real 16-day forecast' : 'Demo clock'}>
            {health.data ? new Date(health.data.now).toLocaleString('en-GB', { day: 'numeric', month: 'short', year: 'numeric', hour: '2-digit', minute: '2-digit' }) : '…'}
          </span>
          <div className="seg" role="group" aria-label="Clock">
            <button aria-pressed={mode === 'demo'} onClick={() => setMode('demo')}>Demo</button>
            <button aria-pressed={mode === 'live'} onClick={() => setMode('live')}>Live</button>
          </div>
          <button className="btn btn-demo" onClick={() => { setMode('demo'); setRole('Commander'); setDemoStep(0) }}><Presentation />Guided demo</button>
          <select aria-label="Role" value={role} onChange={(e) => setRole(e.target.value as Role)}>
            <option>Commander</option><option>Logistics Officer</option><option>Post QM</option>
          </select>
        </header>
        <nav className="rail" aria-label="Screens">
          {NAV.map(([id, label, Icon]) => (
            <a key={id} href={`#/${id}`} aria-current={route[0] === id ? 'page' : undefined}><Icon />{label}</a>
          ))}
        </nav>
        <main className="main" style={{ minHeight: 0, display: 'grid' }}><Screen /></main>
        <footer className="bottom">
          {axes && <>
            <span><b>Manali–Leh</b> likely closes {day(axes[1].closure_p20)} to {day(axes[1].closure_p80)}</span>
            <span><b>Zoji La</b> {day(axes[0].closure_p20)} to {day(axes[0].closure_p80)}</span>
            <Chip kind="real" label="Real closure dates">Window = 20th to 80th percentile of 31 real past winters (Open-Meteo ERA5), rule fitted on real closure dates. Leave-one-winter-out error: Zoji La {axes[0].rule.loo_error_days} days, Manali–Leh {axes[1].rule.loo_error_days} days.</Chip>
          </>}
          <span className="push"><b>{sources.data?.length ?? '–'} data sources</b>, {warn ? <span className="warn-text">{warn} warning</span> : 'all healthy'}</span>
          <Chip kind="real" label="Runs fully on-premise">Everything runs on this machine (in deployment: the Army's own network). Internet is used only for one-time real-data downloads, then cached.</Chip>
        </footer>
      </div>
      {demoStep !== null && <GuidedDemo step={demoStep} setStep={setDemoStep} />}
    </AppCtx.Provider>
  )
}
