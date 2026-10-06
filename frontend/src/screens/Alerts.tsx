import { day, fmt, useApi, type Row } from '../api'
import { useApp } from '../App'
import { Badge, Chip, ErrorNote, Skeleton } from '../ui'

const LOOK: Record<string, [string, string]> = {
  'silent sensor': ['warning', 'Sensor silent'], 'steady excess': ['urgent', 'Unexplained excess'],
  'sharp surge': ['watch', 'Possible surge'], 'data error': ['margin', 'Possible data error'],
}

export default function Alerts() {
  const { mode } = useApp()
  const alerts = useApi<Row[]>(`alerts?mode=${mode}`, true)
  if (alerts.error) return <div className="page"><ErrorNote error={alerts.error} retry={alerts.reload} /></div>
  return (
    <div className="page">
      <div className="page-head">
        <h1>Data alerts</h1>
        <p>Unusual use compared with what the weather, height and season explain, and sensors that stopped reporting. Every alert is a possibility to verify on ground, never a finding. Tested on simulated data; thresholds need tuning on real data.</p>
        <span className="tools"><Chip kind="sim" label="Simulated data">The thresholds were set on simulated data. On the demo data they find the 3 injected anomalies; on other simulated seeds about one false alarm per run appeared. They must be re-tuned on real CICG data.</Chip></span>
      </div>
      {!alerts.data ? <Skeleton h={300} label="Checking every post's consumption" /> : alerts.data.length === 0 ? (
        <div className="notice">No unusual use found. RASAD checks every post and supply each time the data is synced.</div>
      ) : (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '.5rem', maxWidth: '68rem' }} data-demo="alerts">
          {alerts.data.map((a) => {
            const [status, label] = LOOK[a.kind] ?? ['pending', a.kind]
            return (
              <article key={`${a.post}-${a.class}-${a.kind}-${a.start}`} className="panel" style={{ display: 'grid', gridTemplateColumns: '12rem 1fr auto', gap: '.4rem 1rem', alignItems: 'start' }}>
                <div><Badge status={status} text={label} /><div style={{ font: '700 1.3rem var(--cond)', marginTop: '.3rem' }}>{a.post_name.replace('Post ', '')}</div><div className="muted">{a.label}</div></div>
                <p style={{ margin: 0 }}>{a.plain}</p>
                <div style={{ textAlign: 'right', whiteSpace: 'nowrap' }}>
                  {a.ratio !== null && <div style={{ font: '700 1.5rem var(--cond)' }}>{a.ratio}×</div>}
                  <div className="muted">{a.days > 1 ? `${day(a.start)} to ${day(a.end)}` : day(a.start)}</div>
                  {a.extra > 0 && <div className="muted">+{fmt(a.extra)} {a.unit}</div>}
                </div>
              </article>
            )
          })}
        </div>
      )}
    </div>
  )
}
