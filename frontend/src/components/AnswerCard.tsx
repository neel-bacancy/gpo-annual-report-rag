import { useId, useState, type ReactNode } from 'react'
import { pageLabel, type QueryResponse, type Source } from '../api'

/** Renders **bold** and [S#] citation chips inside one line of answer text. */
function renderInline(text: string, sources: Source[], onCite: (i: number) => void): ReactNode[] {
  return text.split(/(\[S\d+\]|\*\*[^*]+\*\*)/g).map((part, i) => {
    const cite = part.match(/^\[S(\d+)\]$/)
    if (cite) {
      const n = Number(cite[1])
      const src = sources.find((s) => s.index === n)
      if (!src) return null
      return (
        <button key={i} className="cite" onClick={() => onCite(n)} title={src.section}>
          {pageLabel(src)}
        </button>
      )
    }
    if (part.startsWith('**') && part.endsWith('**')) return <strong key={i}>{part.slice(2, -2)}</strong>
    return part
  })
}

function AnswerText({ text, sources, onCite }: { text: string; sources: Source[]; onCite: (i: number) => void }) {
  const blocks: ReactNode[] = []
  let bullets: ReactNode[] = []
  const flush = () => {
    if (bullets.length) blocks.push(<ul key={`ul${blocks.length}`}>{bullets}</ul>)
    bullets = []
  }
  text.split('\n').forEach((line, i) => {
    const bullet = line.match(/^\s*[-*•]\s+(.*)/)
    if (bullet) {
      bullets.push(<li key={i}>{renderInline(bullet[1], sources, onCite)}</li>)
    } else {
      flush()
      if (line.trim()) blocks.push(<p key={i}>{renderInline(line, sources, onCite)}</p>)
    }
  })
  flush()
  return <div className="answer-text">{blocks}</div>
}

export function AnswerCard({ result }: { result: QueryResponse }) {
  const [open, setOpen] = useState(false)
  const [active, setActive] = useState<number | null>(null)
  const uid = useId()

  const showSource = (n: number) => {
    setOpen(true)
    setActive(n)
    requestAnimationFrame(() =>
      document.getElementById(`${uid}-S${n}`)?.scrollIntoView({ behavior: 'smooth', block: 'nearest' }),
    )
  }

  return (
    <article className="card">
      <p className="question">{result.question}</p>
      <AnswerText text={result.answer} sources={result.sources} onCite={showSource} />

      <div className="meta">
        <button className="link" onClick={() => setOpen(!open)}>
          {open ? 'Hide' : 'Show'} {result.sources.length} retrieved source{result.sources.length === 1 ? '' : 's'}
        </button>
        <span>
          retrieval {result.retrieval_ms} ms · generation {result.generation_ms} ms
        </span>
      </div>

      {open && (
        <ol className="sources">
          {result.sources.map((s) => (
            <li
              key={s.chunk_id}
              id={`${uid}-S${s.index}`}
              className={`source ${s.cited ? 'cited' : ''} ${active === s.index ? 'active' : ''}`}
            >
              <header>
                <span className="tag">S{s.index}</span>
                <span className="pages">{pageLabel(s)}</span>
                <span className="section">{s.section || '—'}</span>
                <span className="score" title="cosine similarity">
                  {s.similarity.toFixed(3)}
                </span>
                {s.cited && <span className="badge">cited</span>}
              </header>
              <pre>{s.text}</pre>
            </li>
          ))}
        </ol>
      )}
    </article>
  )
}
