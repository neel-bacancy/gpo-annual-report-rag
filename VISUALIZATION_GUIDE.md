# RAG Pipeline Visualization Guide

## Overview

The GPO Annual Report Assistant now includes comprehensive visualizations that explain the entire RAG (Retrieval Augmented Generation) process. Users can see exactly how their questions are answered, from document ingestion to final response generation.

## New Features

### 1. **Document Flow Component** (`DocumentFlow.tsx`)
An educational section that appears at the top of the page, explaining:
- **Phase 1: Document Ingestion** - How the PDF is processed:
  1. Load PDF file
  2. Extract pages
  3. Create overlapping chunks (800-1024 tokens each)
  4. Create embeddings (768-dimensional vectors)
  5. Store in vector database

- **Phase 2: Query Processing** - How questions are answered:
  1. User asks a question
  2. Question is embedded
  3. Database is searched for similar chunks
  4. Context is built from top matches
  5. AI generates an answer
  6. Answer is returned with citations

- **Benefits Section** - Shows why this approach works:
  - Accurate answers grounded in source material
  - Cited sources for verification
  - Fast retrieval through embeddings
  - Always up-to-date with indexed documents

- **Expandable Technical Details** - For users who want to learn more:
  - How embeddings work
  - Chunking strategy
  - Similarity scoring
  - LLM integration

### 2. **Chunk Visualization Component** (`ChunkVisualization.tsx`)
Shows how chunks are created and stored:
- **Chunk Explanation** - What makes up a chunk
- **Visual Representation**:
  - PDF book animation showing pages
  - Chunks being created with overlap
  - Database table structure
  - Embedding visualization
- **Sample Chunks** - Real examples from the document with:
  - Chunk ID and metadata
  - Text preview
  - Embedding visualization
- **Retrieval Process** - 5-step breakdown of what happens when you search

### 3. **Pipeline Visualization Component** (`PipelineVisualization.tsx`)
An interactive visualization that updates after you ask a question, showing:

#### Step 1: Your Question
- Shows the exact question you asked
- Explains what happens next

#### Step 2: Search & Retrieval
- Shows retrieval time
- Number of chunks found
- Visual chart of similarity scores
- Bar chart showing how relevant each chunk is

#### Step 3: Retrieved Context Chunks
- Lists all chunks found by the search
- Shows:
  - Chunk number and relevance score
  - Page numbers
  - Preview of text
  - Badge showing if chunk was used in answer
- Color-coded: green for cited chunks, lighter for unused

#### Step 4: AI Model Processing
- Shows what the AI model receives:
  - The question
  - The retrieved chunks as context
  - Instructions to cite sources
- Preview of how context is formatted

#### Step 5: Final Answer
- Shows the complete answer
- Performance metrics:
  - Time to generate
  - Number of sources cited
  - AI model used
- List of sources actually cited in the answer

## User Experience Flow

1. **Page Load**: User sees:
   - Header with system status
   - Document Flow (educational)
   - Chunk Visualization (educational)
   - Search form

2. **Ask a Question**: User enters question and clicks Ask

3. **Results**: The page shows:
   - Search form (still visible)
   - Pipeline Visualization (interactive steps)
   - Detailed Answer Card (existing component)

4. **Exploration**: User can:
   - Click through pipeline steps to learn more
   - Expand source details in the answer
   - Ask follow-up questions

## Design Principles

- **Non-Technical Language**: All explanations use simple, clear language
- **Visual Learning**: Heavy use of diagrams, animations, and color coding
- **Progressive Disclosure**: Basic information visible, technical details expandable
- **Interactive**: Users can click steps in the pipeline to learn more
- **Responsive**: Works on mobile, tablet, and desktop
- **Consistent**: Uses the existing color scheme and design patterns

## Color Coding

- **Blue (#4a90e2)**: Primary actions, important information, embeddings
- **Green (#4caf50)**: Success, cited sources
- **Gray/Light**: Background, secondary information
- **Red**: Errors (existing)

## Component Structure

```
App
├── DocumentFlow
│   ├── Phase 1: Ingestion flow
│   ├── Phase 2: Query flow
│   ├── Benefits section
│   └── Technical details (expandable)
├── ChunkVisualization
│   ├── Chunk explanation
│   ├── Visual representation (PDF → chunks → database)
│   ├── Sample chunks with embeddings
│   └── Retrieval process steps
├── Search Form
├── PipelineVisualization (only after query)
│   ├── Steps navigation
│   └── Step content (5 steps)
└── Answer Cards (one per previous query)
```

## Technical Details

### API Integration
- Uses existing `/api/health` endpoint for chunk count
- Uses existing `/api/query` endpoint for question/answer
- Displays returned metrics (retrieval_ms, generation_ms)
- Shows source information with similarity scores

### Performance
- All visualizations are CSS-based animations
- Minimal JavaScript overhead
- Responsive images use CSS gradients
- No external animation libraries

### Accessibility
- Semantic HTML structure
- Clear color contrast
- Expandable sections for detailed info
- Clear step indicators

## Files Modified

- `frontend/src/App.tsx` - Added component imports and integration
- `frontend/src/api.ts` - Added optional `model` field to QueryResponse

## Files Created

### Components
- `frontend/src/components/DocumentFlow.tsx` - Educational flow diagram
- `frontend/src/components/DocumentFlow.css` - Styling
- `frontend/src/components/ChunkVisualization.tsx` - Chunk visualization
- `frontend/src/components/ChunkVisualization.css` - Styling
- `frontend/src/components/PipelineVisualization.tsx` - Query pipeline visualization
- `frontend/src/components/PipelineVisualization.css` - Styling

## Future Enhancements

1. **Actual chunk data** - Could fetch real chunks from backend
2. **Embedding visualization** - 3D visualization of embedding space
3. **Performance metrics** - Historical charts of retrieval times
4. **Comparison mode** - Show multiple queries side-by-side
5. **Learning mode** - Gamified explanation of RAG concepts
6. **Export** - Share pipeline visualization as image/PDF

## Testing Checklist

- [ ] Frontend builds without errors
- [ ] Page loads and displays educational sections
- [ ] Status shows chunk count from backend
- [ ] Can enter and submit questions
- [ ] Pipeline visualization appears after query
- [ ] Can click through pipeline steps
- [ ] Source information displays correctly
- [ ] Responsive on mobile devices
- [ ] All animations are smooth
- [ ] No console errors
