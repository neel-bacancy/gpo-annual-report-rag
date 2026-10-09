import { useEffect, useRef, useState, type FormEvent } from 'react'
import { askQuestion, getHealth, type Health, type QueryResponse } from './api'
import { AnswerCard } from './components/AnswerCard'
import { PipelineVisualization } from './components/PipelineVisualization'
import { DocumentFlow } from './components/DocumentFlow'
import { ChunkVisualization } from './components/ChunkVisualization'
import { SAMPLE_QUESTIONS } from './sampleQuestions'
import './App.css'

function App() {
  const [question, setQuestion] = useState('')
  const [results, setResults] = useState<QueryResponse[]>([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [health, setHealth] = useState<Health | null>(null)
  const inputRef = useRef<HTMLTextAreaElement>(null)

  useEffect(() => {
    getHealth().then(setHealth).catch(() => setHealth(null))
  }, [])

  const ask = async (q: string) => {
    const text = q.trim()
    if (!text || loading) return
    setLoading(true)
    setError(null)
    try {
      const res = await askQuestion(text)
      setResults((prev) => [res, ...prev])
      setQuestion('')
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e))
    } finally {
      setLoading(false)
      inputRef.current?.focus()
    }
  }

  const onSubmit = (e: FormEvent) => {
    e.preventDefault()
    ask(question)
  }

  return (
    <div className="app">
      <header className="top">
        <div>
          <h1>GPO Annual Report Assistant</h1>
          <p className="sub">Questions answered from the U.S. Government Publishing Office FY 2018 Annual Report, with page citations.</p>
        </div>
        <div className={`status ${health ? 'ok' : 'down'}`}>
          {health
            ? `${health.chunks_indexed} chunks · ${health.llm_model}`
            : 'Backend offline'}
        </div>
      </header>

      <DocumentFlow />
      <ChunkVisualization chunksCount={health?.chunks_indexed ?? 0} />

      <form className="ask" onSubmit={onSubmit}>
        <textarea
          ref={inputRef}
          value={question}
          onChange={(e) => setQuestion(e.target.value)}
          onKeyDown={(e) => {
            if (e.key === 'Enter' && !e.shiftKey) onSubmit(e)
          }}
          placeholder="Ask about GPO's operations or finances in FY 2018…"
          rows={2}
          disabled={loading}
        />
        <button type="submit" disabled={loading || !question.trim()}>
          {loading ? 'Thinking…' : 'Ask'}
        </button>
      </form>

      <div className="samples">
        {SAMPLE_QUESTIONS.map((q) => (
          <button key={q} onClick={() => ask(q)} disabled={loading}>
            {q}
          </button>
        ))}
      </div>

      {error && <div className="error">{error}</div>}
      {loading && <div className="card skeleton">Retrieving sources and generating an answer…</div>}

      <PipelineVisualization result={results.length > 0 ? results[0] : null} loading={loading} />

      <main>
        {results.map((r, i) => (
          <AnswerCard key={`${results.length - i}`} result={r} />
        ))}
      </main>
    </div>
  )
}

export default App
