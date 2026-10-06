import { useEffect, useState } from 'react'
import { ArrowLeft, ArrowRight, X } from 'lucide-react'
import { day, lakh, shortName, useApi, type Row } from './api'
import { useApp } from './App'

type Data = { pnr: Row | null; plan: Row | null; drones: Row | null; whatif: Row[] | null }
// cardIn: show the card in the top-right corner of that element instead of a screen corner
type Step = { route: string; target: string; title: string; say: (d: Data) => string; cardIn?: string }

const STEPS: Step[] = [
  // the map's north-east has no posts at any screen size, so the card there never hides a post at risk
  { route: 'dashboard', target: 'risk', cardIn: 'map', title: 'Posts at risk', say: ({ pnr }) => {
    const first: Record<string, Row> = {} // items come most urgent first; keep the first per post
    for (const i of pnr?.items ?? []) if (['passed', 'urgent'].includes(i.status) && !first[i.post]) first[i.post] = i
    const risk = Object.values(first)
    if (!risk.length) return 'No post is at risk right now: every supply lasts until its route reopens, or its gap is within the forecast margin.'
    return `${risk.length} post${risk.length === 1 ? '' : 's'} will run short before the routes reopen: ${risk.map((i: Row) => `${shortName(i.post_name)} (${i.label.toLowerCase()})`).join(', ')}. RASAD found them by joining stock, IoT fuel sensors, the forecast and road status.`
  } },
  { route: 'pnr', target: 'pnr-PA', title: 'The point of no return', say: ({ pnr }) => {
    const a = pnr?.items.find((i: Row) => i.post === 'PA' && i.class === 'kerosene')
    return a ? `Alpha's kerosene: the last safe ${a.dispatch_by.replace(' + ', ' and ')} dispatch is ${day(a.last_safe_dispatch)}, with 80% confidence. Pass closures are learned from real closure dates; this forward track uses a placeholder scaling of that rule, replayed over ${pnr!.winters_replayed} real winters of weather. After that only air, about ${a.cost_multiple} times the road cost; the cost inputs are shown and tagged placeholder.`
      : 'Each route gets a closure window, not a fixed date, and a last safe dispatch day with 80% confidence.'
  } },
  { route: 'plan', target: 'plan-PD-drone', title: 'Mixed-fleet plan', say: ({ plan, pnr }) => {
    const d = plan?.lines.find((l: Row) => l.post === 'PD' && l.mode === 'drone')
    if (!d) return 'The planner picks the mode for every load, with a one-line reason and its cost.'
    const item = pnr?.items.find((i: Row) => i.post === 'PD' && i.class === d.class)
    const note = (item?.route_note ?? '').replace(/\.$/, '')
    const why = !item ? '' : item.route_closed ? `Delta's ground route is closed${note ? ` (${note[0].toLowerCase()}${note.slice(1)})` : ''}, so ` : item.status === 'passed' ? 'A convoy can no longer reach Delta before its route closes, so ' : ''
    const pay = d.assumptions.find((x: Row) => x.name === 'drone payload')?.value
    const times = item && d.kg ? Math.round(item.air_inr_per_kg / (d.cost_inr / d.kg)) : 0
    const alpha = plan!.lines.filter((l: Row) => l.post === 'PA' && l.class === 'kerosene' && l.mode !== 'not moved').sort((x: Row, y: Row) => y.kg - x.kg)[0]
    return `The planner picks the mode for every load. ${why}${why ? 'its' : "Delta's"} ${d.label.toLowerCase()} load goes by drone: ${d.trips} sorties on ${d.when} from ${d.from}${pay ? `, ${pay} each` : ''}${times > 1 ? `, about ${times} times cheaper per kg than a helicopter` : ''}.${alpha ? ` Alpha's kerosene goes mainly by ${alpha.mode}, before its last road day.` : ''}`
  } },
  { route: 'drones', target: 'drone-headline', title: 'Drone advisor', say: ({ drones }) => {
    if (!drones) return 'The advisor tests every base for new drones and ranks them by what they save.'
    const f = drones.focus
    if (f.saved_inr <= 0) return `20 high-altitude drones would save nothing this week: no base can reach the posts in need.`
    return `If 20 high-altitude drones arrive, base them at ${f.base}: ${f.post ? `${shortName(f.post)} then needs ${f.heli_sorties_after} helicopter sorties instead of ${f.heli_sorties_before}, ` : ''}saving ${lakh(f.saved_inr)} this week. That is the question behind the Army's 2,715-drone RFI, answered here for one simulated week with placeholder battery and cost figures.`
  } },
  { route: 'whatif/pass_early', target: 'whatif-table', title: 'What-if: pass closes 10 days early', say: ({ whatif }) => {
    const w = whatif?.find((r) => r.id === 'pass_early')
    const added = w ? w.after.at_risk.filter((p: string) => !w.before.at_risk.includes(p)).map(shortName) : []
    return w ? `One click: if the pass closes ten days early, ${added.length ? `${added.join(' and ')} join${added.length === 1 ? 's' : ''} the posts at risk (${w.before.posts_at_risk} to ${w.after.posts_at_risk}), ` : ''}helicopter sorties rise from ${w.before.heli_sorties} to ${w.after.heli_sorties} and ${w.after.not_moved_kg.toLocaleString('en-IN')} kg cannot move this week. The commander sees the cost of waiting before it happens.`
      : 'One click re-runs everything with the pass closing ten days early and shows before and after.'
  } },
  { route: 'sources', target: 'sources', title: 'How data plugs in', say: () =>
    'Each data stream is a single config file. Weather, terrain, the national highways and the pass-closure dates are real; the posts and their tracks, inventory, IoT fuel sensors and the BRO and IAF feeds are simulated because military data is classified. A new stream that fits the existing tables is one new file, with no change to existing Army systems.' },
  { route: 'plan', target: 'approve', title: 'The commander approves', say: ({ plan }) => {
    const d = plan?.lines.find((l: Row) => l.post === 'PD' && l.mode === 'drone')
    return `As Commander, press Approve on ${d ? `${shortName(d.post_name)}'s ${d.mode} line` : 'a plan line'}. The decision, the role and the time go straight into the audit log; a Post QM cannot approve.`
  } },
]

export default function GuidedDemo({ step, setStep }: { step: number; setStep: (s: number | null) => void }) {
  const { go } = useApp()
  const s = STEPS[step]
  const data: Data = {
    pnr: useApi('pnr?mode=demo', true).data, plan: useApi('plan?mode=demo').data,
    drones: useApi('drones?mode=demo&n=20&band=12000_20000ft', true).data, whatif: useApi<Row[]>('scenarios?mode=demo', true).data,
  }
  const [rect, setRect] = useState<DOMRect | null>(null)
  const [home, setHome] = useState<DOMRect | null>(null)

  useEffect(() => { go(s.route) }, [s.route, go])
  useEffect(() => {
    setRect(null)
    setHome(null)
    let timer = 0, tries = 0, scrolled = false
    const find = () => { // the screen loads its data after navigation, so keep looking for the target
      const el = document.querySelector(`[data-demo="${s.target}"]`)
      if (el && !scrolled) { el.scrollIntoView({ block: 'nearest' }); scrolled = true }
      setRect(el ? el.getBoundingClientRect() : null)
      const box = s.cardIn ? document.querySelector(`[data-demo="${s.cardIn}"]`) : null
      setHome(box ? box.getBoundingClientRect() : null)
      if (tries++ < 150) timer = window.setTimeout(find, el ? 400 : 200)
    }
    find()
    return () => clearTimeout(timer)
  }, [s.target, s.cardIn])
  useEffect(() => {
    const key = (e: KeyboardEvent) => {
      if (e.key === 'Escape') setStep(null)
      if (e.key === 'ArrowRight' && step < STEPS.length - 1) setStep(step + 1)
      if (e.key === 'ArrowLeft' && step > 0) setStep(step - 1)
    }
    window.addEventListener('keydown', key)
    return () => window.removeEventListener('keydown', key)
  }, [step, setStep])

  const pad = 6
  const leftSide = rect ? rect.left + rect.width / 2 > window.innerWidth / 2 : false
  const place = home ? { top: home.top + 44, right: window.innerWidth - home.right + 12, bottom: 'auto', left: 'auto' } // 44: below the map's chips
    : leftSide ? { left: '6.4rem', right: 'auto' } : undefined
  return (
    <>
      {rect && <div className="demo-spot" aria-hidden style={{ top: rect.top - pad, left: rect.left - pad, width: rect.width + 2 * pad, height: rect.height + 2 * pad }} />}
      {!rect && <div className="demo-dim" style={{ background: 'rgba(22,33,43,.25)' }} />}
      <div className="demo-card" role="dialog" aria-label="Guided demo" style={place}>
        <div className="row"><span className="step">Moment {step + 1} of {STEPS.length}</span>
          <button className="btn btn-line btn-sm push" onClick={() => setStep(null)} aria-label="Close the guided demo"><X />Close</button></div>
        <h2>{s.title}</h2>
        <p className="say"><b>Say: </b>{s.say(data)}</p>
        <div className="row">
          <button className="btn btn-line" disabled={step === 0} onClick={() => setStep(step - 1)}><ArrowLeft />Back</button>
          {step === STEPS.length - 1 && <a className="btn btn-line" href="#/audit">Show audit log</a>}
          {step < STEPS.length - 1
            ? <button className="btn btn-ink push" onClick={() => setStep(step + 1)} autoFocus>Next<ArrowRight /></button>
            : <button className="btn btn-ink push" onClick={() => setStep(null)}>Finish</button>}
        </div>
      </div>
    </>
  )
}
