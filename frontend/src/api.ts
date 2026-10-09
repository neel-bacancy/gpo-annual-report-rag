export interface Source {
  index: number
  chunk_id: string
  section: string
  page_start: number
  page_end: number
  similarity: number
  text: string
  cited: boolean
}

export interface QueryResponse {
  question: string
  answer: string
  found: boolean
  sources: Source[]
  retrieval_ms: number
  generation_ms: number
  model?: string
}

export interface Health {
  status: string
  chunks_indexed: number
  llm_model: string
  embedding_model: string
  top_k: number
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(path, {
    ...init,
    headers: { 'Content-Type': 'application/json', ...init?.headers },
  })
  if (!res.ok) {
    const body = await res.json().catch(() => null)
    throw new Error(body?.detail ?? `Request failed (${res.status})`)
  }
  return res.json() as Promise<T>
}

export const askQuestion = (question: string) =>
  request<QueryResponse>('/api/query', { method: 'POST', body: JSON.stringify({ question }) })

export const getHealth = () => request<Health>('/api/health')

export const pageLabel = (s: Pick<Source, 'page_start' | 'page_end'>) =>
  s.page_start === s.page_end ? `p. ${s.page_start}` : `pp. ${s.page_start}–${s.page_end}`
