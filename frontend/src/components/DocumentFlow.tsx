import './DocumentFlow.css'

export function DocumentFlow() {
  return (
    <div className="document-flow">
      <h2>📄 How the RAG System Works</h2>
      <p className="intro">
        The Retrieval Augmented Generation system works in two phases: <strong>Ingestion</strong> (one time setup) and <strong>Query</strong>
        (every time you ask a question).
      </p>

      {/* Ingestion Phase */}
      <div className="phase">
        <div className="phase-header">
          <span className="phase-icon">⚙️</span>
          <h3>Phase 1: Document Ingestion (Setup)</h3>
        </div>

        <div className="flow-diagram">
          <div className="flow-step">
            <div className="step-number">1</div>
            <div className="step-title">Load PDF</div>
            <p>The system loads the GPO Annual Report PDF file.</p>
            <div className="example">📄 gpo_2018_annual_report.pdf</div>
          </div>

          <div className="flow-arrow">→</div>

          <div className="flow-step">
            <div className="step-number">2</div>
            <div className="step-title">Extract Pages</div>
            <p>Extract text from each page, maintaining structure and information.</p>
            <div className="example">📋 Page 1, Page 2, Page 3... (256+ pages)</div>
          </div>

          <div className="flow-arrow">→</div>

          <div className="flow-step">
            <div className="step-number">3</div>
            <div className="step-title">Create Chunks</div>
            <p>Break pages into smaller, manageable chunks (800-1024 tokens each) with 20% overlap so no context is lost.</p>
            <div className="example">📚 Chunk 1, Chunk 2, Chunk 3... (1,000+ chunks)</div>
          </div>

          <div className="flow-arrow">→</div>

          <div className="flow-step">
            <div className="step-number">4</div>
            <div className="step-title">Create Embeddings</div>
            <p>Convert each chunk into a mathematical representation (embedding) that captures its meaning.</p>
            <div className="example">🔢 [0.12, -0.45, 0.89, ...] for each chunk</div>
          </div>

          <div className="flow-arrow">→</div>

          <div className="flow-step">
            <div className="step-number">5</div>
            <div className="step-title">Store in Vector DB</div>
            <p>Save all embeddings in a vector database for fast similarity searching.</p>
            <div className="example">🗄️ Vector Database (Ready for queries)</div>
          </div>
        </div>
      </div>

      {/* Query Phase */}
      <div className="phase">
        <div className="phase-header">
          <span className="phase-icon">🔍</span>
          <h3>Phase 2: Query Processing (Every Question)</h3>
        </div>

        <div className="flow-diagram">
          <div className="flow-step">
            <div className="step-number">1</div>
            <div className="step-title">You Ask a Question</div>
            <p>You type in your question about the GPO Annual Report.</p>
            <div className="example">❓ "What was GPO's budget in 2018?"</div>
          </div>

          <div className="flow-arrow">→</div>

          <div className="flow-step">
            <div className="step-number">2</div>
            <div className="step-title">Embed Question</div>
            <p>Your question is converted to an embedding (same process as chunks).</p>
            <div className="example">🔢 [-0.08, 0.52, -0.41, ...]</div>
          </div>

          <div className="flow-arrow">→</div>

          <div className="flow-step">
            <div className="step-number">3</div>
            <div className="step-title">Search Database</div>
            <p>Find the most similar chunks by comparing embeddings. Uses cosine similarity (0=different, 1=identical).</p>
            <div className="example">📊 Top 5-10 chunks ranked by similarity</div>
          </div>

          <div className="flow-arrow">→</div>

          <div className="flow-step">
            <div className="step-number">4</div>
            <div className="step-title">Build Context</div>
            <p>Take the top matching chunks and send them as context to the AI model.</p>
            <div className="example">📎 "Here are 5 relevant excerpts from the document..."</div>
          </div>

          <div className="flow-arrow">→</div>

          <div className="flow-step">
            <div className="step-number">5</div>
            <div className="step-title">AI Generates Answer</div>
            <p>Gemini (an AI model) reads your question and the context, then generates a comprehensive answer.</p>
            <div className="example">💬 "GPO's budget in 2018 was... [S1] [S3]"</div>
          </div>

          <div className="flow-arrow">→</div>

          <div className="flow-step">
            <div className="step-number">6</div>
            <div className="step-title">Return Answer</div>
            <p>The answer is sent back to you with citations showing which chunks were used.</p>
            <div className="example">✅ Answer with [S#] citations and page numbers</div>
          </div>
        </div>
      </div>

      {/* Key Benefits */}
      <div className="benefits">
        <h3>✨ Why This Approach?</h3>
        <div className="benefit-grid">
          <div className="benefit-card">
            <div className="benefit-icon">🎯</div>
            <div className="benefit-title">Accurate Answers</div>
            <p>The AI only answers based on information from the actual document, not general knowledge.</p>
          </div>
          <div className="benefit-card">
            <div className="benefit-icon">📌</div>
            <div className="benefit-title">Cited Sources</div>
            <p>Every answer includes citations showing exactly which part of the document was used.</p>
          </div>
          <div className="benefit-card">
            <div className="benefit-icon">⚡</div>
            <div className="benefit-title">Fast Retrieval</div>
            <p>Embeddings allow instant searching through 1000+ chunks without scanning the entire document.</p>
          </div>
          <div className="benefit-card">
            <div className="benefit-icon">🔐</div>
            <div className="benefit-title">Always Up-to-Date</div>
            <p>The system only uses information from the indexed document. No outdated internet data.</p>
          </div>
        </div>
      </div>

      {/* Technical Details */}
      <details className="tech-details">
        <summary>🔧 Technical Details (for the curious)</summary>
        <div className="details-content">
          <h4>Embeddings</h4>
          <p>
            An embedding is a way to represent text as numbers. Similar texts have similar embeddings. We use Google's text-embedding-005 model,
            which creates a 768-dimensional vector for each chunk.
          </p>

          <h4>Chunking Strategy</h4>
          <p>
            We break the document into overlapping chunks to preserve context:
            <br />
            • Chunk size: 800-1024 tokens
            <br />
            • Overlap: 20% (so boundaries don't split important information)
            <br />
            • This creates ~1000+ chunks from a 256-page document
          </p>

          <h4>Similarity Scoring</h4>
          <p>
            After embedding your question, we calculate cosine similarity between it and all chunk embeddings. Cosine similarity ranges from 0
            (completely different) to 1 (identical). We typically use chunks with similarity &gt; 0.35.
          </p>

          <h4>LLM Integration</h4>
          <p>
            We use Google's Gemini API (Claude model) with a system prompt that instructs it to:
            <br />
            1. Answer only based on provided context
            <br />
            2. Cite sources using [S#] notation
            <br />
            3. Say "Not found" if the answer isn't in the context
          </p>
        </div>
      </details>
    </div>
  )
}
