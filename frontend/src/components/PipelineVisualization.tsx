import { useEffect, useState } from 'react'
import { type QueryResponse, type Source } from '../api'
import './PipelineVisualization.css'

type Step = 'input' | 'retrieve' | 'context' | 'llm' | 'output'

export function PipelineVisualization({ result, loading }: { result: QueryResponse | null; loading: boolean }) {
  const [activeStep, setActiveStep] = useState<Step>('input')

  useEffect(() => {
    if (loading) {
      setActiveStep('input')
    }
  }, [loading])

  const steps: { id: Step; title: string; icon: string }[] = [
    { id: 'input', title: 'Your Question', icon: '❓' },
    { id: 'retrieve', title: 'Search for Chunks', icon: '🔍' },
    { id: 'context', title: 'Context Chunks', icon: '📚' },
    { id: 'llm', title: 'Send to AI', icon: '🤖' },
    { id: 'output', title: 'AI Answer', icon: '💬' },
  ]

  return (
    <div className="pipeline-visualization">
      <div className="pipeline-header">
        <h2>RAG Pipeline Visualization</h2>
        <p>See how your question is answered using retrieval-augmented generation</p>
      </div>

      {/* Steps Navigation */}
      <div className="steps-nav">
        {steps.map((step) => (
          <button
            key={step.id}
            className={`step-button ${activeStep === step.id ? 'active' : ''} ${!result && step.id !== 'input' ? 'disabled' : ''}`}
            onClick={() => result && setActiveStep(step.id)}
            disabled={!result && step.id !== 'input'}
          >
            <span className="step-icon">{step.icon}</span>
            <span className="step-title">{step.title}</span>
          </button>
        ))}
      </div>

      {/* Step Details */}
      <div className="step-content">
        {activeStep === 'input' && <StepInput question={result?.question} loading={loading} />}
        {activeStep === 'retrieve' && result && <StepRetrieve result={result} />}
        {activeStep === 'context' && result && <StepContext sources={result.sources} />}
        {activeStep === 'llm' && result && <StepLLM sources={result.sources} />}
        {activeStep === 'output' && result && <StepOutput result={result} />}
      </div>
    </div>
  )
}

function StepInput({ question, loading }: { question?: string; loading: boolean }) {
  return (
    <div className="step">
      <div className="step-title-large">Your Question</div>
      <p className="step-description">
        This is your question. The system will:
        <br />
        1. Convert it into a numerical representation (embedding)
        <br />
        2. Search for similar document chunks
        <br />
        3. Send the relevant chunks to an AI model for answering
      </p>
      <div className="content-box question-box">
        {loading ? (
          <div className="placeholder">Enter a question and click Ask to see the pipeline in action...</div>
        ) : question ? (
          <p>{question}</p>
        ) : (
          <p className="placeholder">No question yet. Ask a question to start!</p>
        )}
      </div>
    </div>
  )
}

function StepRetrieve({ result }: { result: QueryResponse }) {
  return (
    <div className="step">
      <div className="step-title-large">Search & Retrieval</div>
      <p className="step-description">
        Your question is converted to an embedding (a list of numbers representing its meaning), then the system searches the vector database to find
        the most similar document chunks. It found {result.sources.length} matching chunks in {result.retrieval_ms}ms.
      </p>
      <div className="retrieval-info">
        <div className="info-card">
          <div className="info-label">Time Taken</div>
          <div className="info-value">{result.retrieval_ms}ms</div>
        </div>
        <div className="info-card">
          <div className="info-label">Chunks Found</div>
          <div className="info-value">{result.sources.length}</div>
        </div>
      </div>

      <div className="similarity-chart">
        <div className="chart-label">Relevance Score (0-1 = not similar to highly similar)</div>
        <div className="chart-bars">
          {result.sources.slice(0, 5).map((source, i) => (
            <div key={i} className="bar-item">
              <div className="bar-wrapper">
                <div className="bar" style={{ height: `${source.similarity * 100}%` }}></div>
              </div>
              <div className="bar-label">Chunk {source.index}</div>
              <div className="bar-value">{source.similarity.toFixed(2)}</div>
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}

function StepContext({ sources }: { sources: Source[] }) {
  return (
    <div className="step">
      <div className="step-title-large">Retrieved Context Chunks</div>
      <p className="step-description">
        These are the document chunks most similar to your question. Only chunks with a high similarity score are used to answer your question. The AI
        will read these chunks and use them as context when generating the answer.
      </p>

      <div className="chunks-list">
        {sources.map((source) => (
          <div key={source.chunk_id} className={`chunk-card ${source.cited ? 'cited' : 'not-cited'}`}>
            <div className="chunk-header">
              <span className="chunk-number">Chunk {source.index}</span>
              <span className="chunk-score">
                Relevance: <strong>{source.similarity.toFixed(3)}</strong>
              </span>
              <span className="chunk-location">
                Page{source.page_start === source.page_end ? '' : 's'} {source.page_start}
                {source.page_start !== source.page_end ? `–${source.page_end}` : ''}
              </span>
              {source.cited && <span className="chunk-badge">used in answer</span>}
            </div>
            <div className="chunk-preview">
              <p>{source.text.substring(0, 200)}...</p>
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}

function StepLLM({ sources }: { sources: Source[] }) {
  return (
    <div className="step">
      <div className="step-title-large">AI Model Processing</div>
      <p className="step-description">
        The AI model (Gemini) receives:
        <br />
        1. Your original question
        <br />
        2. The {sources.length} relevant document chunks as context
        <br />
        3. Instructions to answer based only on the provided context
      </p>

      <div className="llm-prompt">
        <div className="prompt-label">What the AI sees:</div>
        <div className="prompt-box">
          <div className="prompt-section">
            <h4>📋 Your Question:</h4>
            <p>(The question from the first step)</p>
          </div>

          <div className="prompt-section">
            <h4>📚 Context from Document:</h4>
            <div className="context-chunks">
              {sources.slice(0, 3).map((source, i) => (
                <div key={i} className="mini-chunk">
                  <strong>From page {source.page_start}:</strong>
                  <p>{source.text.substring(0, 150)}...</p>
                </div>
              ))}
              {sources.length > 3 && (
                <div className="mini-chunk">
                  <em>+ {sources.length - 3} more chunks...</em>
                </div>
              )}
            </div>
          </div>

          <div className="prompt-section">
            <h4>✍️ Instructions:</h4>
            <p>"Answer the question using only the provided context. Cite which chunk you used for each fact. If you cannot answer from the context, say so."</p>
          </div>
        </div>
      </div>
    </div>
  )
}

function StepOutput({ result }: { result: QueryResponse }) {
  return (
    <div className="step">
      <div className="step-title-large">Final Answer</div>
      <p className="step-description">The AI has processed all the context and generated an answer. The citations [S#] show which chunks were used.</p>

      <div className="answer-display">
        <div className="answer-box">
          <p>{result.answer}</p>
        </div>

        <div className="generation-info">
          <div className="info-card">
            <div className="info-label">Time to Generate</div>
            <div className="info-value">{result.generation_ms}ms</div>
          </div>
          <div className="info-card">
            <div className="info-label">Sources Cited</div>
            <div className="info-value">{result.sources.filter((s) => s.cited).length}</div>
          </div>
          <div className="info-card">
            <div className="info-label">AI Model</div>
            <div className="info-value">{result.model || 'Gemini'}</div>
          </div>
        </div>

        <div className="cited-sources">
          <h4>Sources Cited in Answer:</h4>
          <ul>
            {result.sources.filter((s) => s.cited).map((source) => (
              <li key={source.chunk_id}>
                <strong>[S{source.index}]</strong> Page {source.page_start}: {source.text.substring(0, 100)}...
              </li>
            ))}
          </ul>
        </div>
      </div>
    </div>
  )
}
