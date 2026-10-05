import { useEffect, useState } from 'react'

type Source = { id: string; name: string; health: string; records: number | null; last_record: string | null; notes: string[]; simulated: boolean }

// Step 2 placeholder: proves the backend, adapters and build work. Real screens come in Step 7.
export default function App() {
  const [sources, setSources] = useState<Source[]>([])
  const [error, setError] = useState('')
  useEffect(() => {
    fetch('/api/sources').then(r => r.json()).then(setSources).catch(e => setError(String(e)))
  }, [])
  return (
    <main style={{ maxWidth: 900, margin: '32px auto', padding: '0 16px' }}>
      <h1>RASAD</h1>
      <p>Sector X (fictional) · Runs fully on-premise · Simulated for prototype</p>
      {error && <p role="alert">Backend not reachable: {error}</p>}
      <table cellPadding={6}>
        <thead><tr><th align="left">Source</th><th>Health</th><th align="right">Records</th><th>Newest record</th></tr></thead>
        <tbody>
          {sources.map(s => (
            <tr key={s.id}>
              <td>{s.name}{s.simulated ? ' (simulated)' : ''}</td>
              <td>{s.health}{s.notes.length ? ` - ${s.notes.join('; ')}` : ''}</td>
              <td align="right">{s.records ?? '-'}</td>
              <td>{s.last_record ?? '-'}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </main>
  )
}
