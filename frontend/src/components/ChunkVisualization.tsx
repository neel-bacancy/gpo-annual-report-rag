import './ChunkVisualization.css'

export function ChunkVisualization({ chunksCount }: { chunksCount: number }) {
  const sampleChunks = [
    {
      id: 1,
      section: 'Financial Overview',
      page: 45,
      preview: 'The Government Publishing Office incurred total costs of $141.6 million during fiscal year 2018, with the largest expense being...',
      similarity: 0.89,
    },
    {
      id: 2,
      section: 'Operations Report',
      page: 78,
      preview: 'GPO operations span across multiple facilities including the main headquarters in Washington D.C. and regional printing centers...',
      similarity: 0.76,
    },
    {
      id: 3,
      section: 'Performance Metrics',
      page: 156,
      preview: 'During FY 2018, GPO processed approximately 2.5 million titles and distributed over 350 million pages of government documents...',
      similarity: 0.68,
    },
  ]

  return (
    <div className="chunk-visualization">
      <div className="chunk-vis-container">
        <h2>📦 How Chunks Work in the Database</h2>

        <div className="chunk-explanation">
          <p>
            The document is split into <strong>{chunksCount}+ chunks</strong>. Each chunk is a piece of text that:
          </p>
          <ul>
            <li>Contains 800-1024 tokens (roughly 600-800 words)</li>
            <li>Has 20% overlap with the previous chunk to preserve context</li>
            <li>Is converted to an embedding (768 numbers representing its meaning)</li>
            <li>Is stored with metadata like page number and section title</li>
          </ul>
        </div>

        <div className="visual-representation">
          <h3>Visual Representation of Chunks</h3>
          <div className="document-viz">
            <div className="pdf-book">
              <div className="book-spine">
                <div className="book-title">GPO 2018<br />Annual<br />Report</div>
              </div>
              <div className="pages">
                {Array.from({ length: 12 }).map((_, i) => (
                  <div key={i} className="page" style={{ animationDelay: `${i * 50}ms` }}>
                    {i + 1}
                  </div>
                ))}
              </div>
            </div>

            <div className="arrow-right">→</div>

            <div className="chunks-stack">
              <div className="label">Split into chunks with overlap</div>
              <div className="chunks">
                {Array.from({ length: 5 }).map((_, i) => (
                  <div key={i} className="chunk-item" style={{ zIndex: 5 - i, top: `${i * 20}px` }}>
                    <div className="chunk-inner">
                      <span className="chunk-label">Chunk {i + 1}</span>
                      <span className="overlap-indicator">20% overlap →</span>
                    </div>
                  </div>
                ))}
              </div>
            </div>

            <div className="arrow-right">→</div>

            <div className="database">
              <div className="label">Stored in Vector Database</div>
              <div className="db-box">
                <div className="db-row">
                  <span className="db-col">ID</span>
                  <span className="db-col">Text</span>
                  <span className="db-col">Embedding</span>
                  <span className="db-col">Page</span>
                </div>
                {Array.from({ length: 4 }).map((_, i) => (
                  <div key={i} className="db-row data-row">
                    <span className="db-col">{i + 1}</span>
                    <span className="db-col truncate">Lorem ipsum dolor sit...</span>
                    <span className="db-col">[0.12, -0.45, 0.89...]</span>
                    <span className="db-col">{45 + i}</span>
                  </div>
                ))}
                <div className="db-row footer">
                  <span className="db-col">...</span>
                  <span className="db-col">...</span>
                  <span className="db-col">...</span>
                  <span className="db-col">...</span>
                </div>
              </div>
            </div>
          </div>
        </div>

        <div className="sample-chunks">
          <h3>Sample Chunks from the Database</h3>
          <div className="chunks-grid">
            {sampleChunks.map((chunk) => (
              <div key={chunk.id} className="sample-chunk">
                <div className="chunk-meta">
                  <span className="chunk-id">#{chunk.id}</span>
                  <span className="chunk-section">{chunk.section}</span>
                  <span className="chunk-page">p. {chunk.page}</span>
                </div>
                <div className="chunk-text">{chunk.preview}</div>
                <div className="chunk-footer">
                  <div className="embedding-visual">
                    <span>Embedding:</span>
                    <div className="embedding-bars">
                      {Array.from({ length: 8 }).map((_, i) => (
                        <div
                          key={i}
                          className="bar"
                          style={{
                            height: `${Math.random() * 100}%`,
                            opacity: 0.6 + Math.random() * 0.4,
                          }}
                        ></div>
                      ))}
                    </div>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>

        <div className="retrieval-process">
          <h3>🔍 What Happens When You Ask a Question</h3>
          <div className="process-steps">
            <div className="process-step">
              <div className="step-icon">1️⃣</div>
              <div className="step-text">
                <strong>Your question is embedded</strong>
                <p>Converted to numbers: [0.08, 0.52, -0.41, ...] (same embedding space as chunks)</p>
              </div>
            </div>
            <div className="process-step">
              <div className="step-icon">2️⃣</div>
              <div className="step-text">
                <strong>Search for similar embeddings</strong>
                <p>Calculate similarity score (0 = different, 1 = identical) for all chunks</p>
              </div>
            </div>
            <div className="process-step">
              <div className="step-icon">3️⃣</div>
              <div className="step-text">
                <strong>Retrieve top matches</strong>
                <p>Get the 5-10 chunks with highest similarity scores</p>
              </div>
            </div>
            <div className="process-step">
              <div className="step-icon">4️⃣</div>
              <div className="step-text">
                <strong>Pass to AI model</strong>
                <p>Gemini reads your question and the similar chunks together</p>
              </div>
            </div>
            <div className="process-step">
              <div className="step-icon">5️⃣</div>
              <div className="step-text">
                <strong>Get cited answer</strong>
                <p>AI generates answer with [S#] citations to the original chunks</p>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
