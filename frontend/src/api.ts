import { useCallback, useEffect, useState } from 'react'

// The API returns plain JSON rows; the screens read only the fields they show.
// eslint-disable-next-line @typescript-eslint/no-explicit-any
export type Row = Record<string, any>

export type Mode = 'demo' | 'live'

export async function api<T = Row>(path: string, init?: RequestInit): Promise<T> {
  const r = await fetch('/api/' + path, init)
  if (!r.ok) {
    let msg = `${r.status} ${r.statusText}`
    try { msg = (await r.json()).detail ?? msg } catch { /* not JSON */ }
    throw new Error(String(msg))
  }
  return r.json()
}

// heavy, rarely-changing results are kept for the session (the plan is never cached: decisions change it)
const cache = new Map<string, unknown>()
export const clearCache = () => cache.clear()

export function useApi<T = Row>(path: string | null, keep = false) {
  const [data, setData] = useState<T | null>(() => (path && keep ? (cache.get(path) as T) ?? null : null))
  const [error, setError] = useState<string | null>(null)
  const [tick, setTick] = useState(0)
  useEffect(() => {
    if (!path) return
    let live = true
    setError(null)
    if (keep && cache.has(path) && tick === 0) { setData(cache.get(path) as T); return }
    api<T>(path)
      .then((d) => { if (keep) cache.set(path, d); if (live) setData(d) })
      .catch((e) => live && setError(String(e.message ?? e)))
    return () => { live = false }
  }, [path, tick, keep])
  const reload = useCallback(() => setTick((t) => t + 1), [])
  return { data, error, reload }
}

export const fmt = (n: number, d = 0) =>
  Number(n).toLocaleString('en-IN', { maximumFractionDigits: d, minimumFractionDigits: d })

export const day = (iso: string) =>
  new Date(iso.slice(0, 10) + 'T00:00').toLocaleDateString('en-GB', { day: 'numeric', month: 'short' })

export const lakh = (inr: number) => (inr >= 1e7 ? `₹${fmt(inr / 1e7, 2)} crore` : `₹${fmt(inr / 1e5, 1)} lakh`)

export const shortName = (name: string) => name.replace('Post ', '')

export const plural = (n: number, word: string) => `${fmt(n)} ${word}${n === 1 ? '' : 's'}`

// backend sentences say 'Rs'; the screen uses the rupee sign
export const rupee = (s: string) => s.replace(/Rs /g, '₹')

export const RANK: Record<string, number> = { passed: 0, urgent: 1, watch: 2, margin: 3, stocked: 4 }


// worst Point-of-No-Return item per post, with its plan lines and forecast cover
export function postSummaries(pnr: Row, plan: Row | null, cover: Row[] | null) {
  const out: Record<string, Row> = {}
  for (const i of pnr.items) {
    const cur = out[i.post]
    if (!cur || RANK[i.status] < RANK[cur.item.status]) out[i.post] = { item: i }
  }
  for (const [post, s] of Object.entries(out)) {
    s.lines = plan ? plan.lines.filter((l: Row) => l.post === post) : []
    s.cover = cover?.find((c) => c.post === post && c.class === s.item.class)
  }
  return out
}

export const atRisk = (s: Row) => s.item.status === 'passed' || s.item.status === 'urgent'
