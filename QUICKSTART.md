# 🚀 Quick Start - RAG Visualization

Get the RAG pipeline visualization running in 5 minutes!

## Prerequisites
- Python 3.10+ installed
- Node.js 16+ installed
- A working Gemini API key (in `backend/.env`)

## 1️⃣ Start the Frontend (Terminal 1)

```bash
cd frontend
npm install        # Only first time
npm run dev
```

Output will show:
```
VITE v8.3.3  ready in XXX ms
  ➜  Local:   http://localhost:5173/
```

**✅ Open browser to http://localhost:5173**

---

## 2️⃣ Start the Backend (Terminal 2)

### First Time Setup
```bash
cd backend
pip install -r requirements.txt
python -m scripts.ingest    # Process PDF into chunks (takes ~30s)
```

### Run Backend
```bash
cd backend
python -m uvicorn app.main:app --reload --port 8000
```

Output will show:
```
INFO:     Uvicorn running on http://127.0.0.1:8000
INFO:     Application startup complete
```

---

## 3️⃣ Open in Browser

Go to: **http://localhost:5173**

## ✅ You'll See:

### 1. Header
- Status showing chunked count
- GPO Annual Report Assistant title

### 2. **Document Flow** Section (New! 📄)
- How documents are ingested
- How queries are processed
- System benefits
- Technical details (expandable)

### 3. **Chunk Visualization** Section (New! 📦)
- PDF book animation
- Chunks with overlaps
- Database table
- Sample chunks with embeddings
- 5-step retrieval process

### 4. Search Form
- Ask your question
- Sample questions to get started

### 5. **Pipeline Visualization** (Appears after search!)
- Interactive 5-step visualization
- Retrieval metrics and chart
- Context chunks list
- LLM context preview
- Final answer with citations

## 🎯 Try This First Query

**Question:** "What was GPO's budget in 2018?"

**What you'll see:**
1. Search processes (45ms animation)
2. Charts showing which chunks matched
3. List of retrieved chunks with relevance scores
4. The exact context sent to Claude
5. Final answer with [S#] citations
6. Sources actually used

---

## 🎨 What's New to Explore

### Document Flow
Click on different sections to learn:
- 5-step ingestion process
- 6-step query process
- Why this approach works
- Technical details (expand the box at bottom)

### Chunk Visualization
Scroll down to see:
- How PDF becomes chunks
- Chunks stored in database
- Sample chunks (look for embeddings visualization!)
- Retrieval process explained

### Pipeline Visualization
After asking a question:
- Click each step button to learn more
- See retrieval metrics and similarity chart
- Watch which chunks were retrieved
- Understand what AI sees
- Verify citations in final answer

---

## 🎓 Key Things to Understand

After using the visualizations, you'll understand:

1. **Chunks**
   - Document split into 800-1024 token pieces
   - 20% overlap prevents losing context
   - Each becomes a 768-dim vector

2. **Embeddings**
   - Questions & chunks → numbers
   - Similar meaning = similar numbers
   - Similarity search finds relevant chunks

3. **Context**
   - Top 5-10 chunks sent to AI
   - AI only uses this context
   - No hallucinations possible

4. **Citations**
   - [S1], [S2], etc. link to chunks
   - Each [S#] has a page number
   - Verify claims in source

5. **Speed**
   - Retrieval: 40-100ms
   - Generation: 1-3 seconds
   - Total: < 5 seconds

---

## 🔍 Debugging Tips

### If you see "Backend offline"
- Check backend is running on port 8000
- Check `/api/health` returns status

### If chunks seem wrong
- Verify `/api/ingest` was run
- Check `backend/data/gpo_2018_annual_report.pdf` exists

### If embedding visualization doesn't work
- Check browser console (F12)
- Verify JavaScript is enabled

### If generation is slow
- First query is slower (model warming up)
- Check Gemini API quota
- Verify GEMINI_API_KEY in `backend/.env`

---

## 📊 Try These Questions

Ask these to see different results:

1. **"What was GPO's budget in 2018?"**
   - Short, factual → high similarity scores

2. **"Describe GPO's printing operations"**
   - Longer, needs multiple chunks → see multiple citations

3. **"What are the main challenges GPO faces?"**
   - Complex → see how multiple chunks combine

4. **"How many employees does GPO have?"**
   - Specific number → high confidence answer

5. **"What did GPO do in 2018?"**
   - Very broad → see lots of chunks

---

## 🎯 Key Metrics to Check

After each query, look for:

- **Retrieval Time**: How fast was the search?
- **Chunks Found**: How many were relevant?
- **Similarity Scores**: 0.8+ = very relevant, 0.5+ = somewhat relevant
- **Generation Time**: How fast was the answer?
- **Citations**: Are sources cited? [S1], [S2], etc.?

---

## 💡 Pro Tips

1. **Mobile**: Swipe through pipeline steps
2. **Desktop**: Click step buttons to navigate
3. **Learning**: Read "Document Flow" section first
4. **Questions**: Try yes/no vs. open-ended questions
5. **Debugging**: Check similarity scores if answer seems wrong
6. **Details**: Expand "Technical Details" section to learn more

---

## ❌ Troubleshooting

| Problem | Solution |
|---------|----------|
| "Backend offline" | Start backend on port 8000 |
| "Index is empty" | Run `python -m scripts.ingest` |
| Frontend not updating | Hard refresh browser (Ctrl+Shift+R) |
| Slow generation | First query is slower, then speeds up |
| Wrong answers | Check similarity scores of chunks |
| No citations | Make sure answer references [S#] |

---

## 📚 Learn More

1. **CHANGES_SUMMARY.md** - What was added
2. **VISUALIZATION_GUIDE.md** - Detailed technical guide
3. **RAG_VISUALIZATION_README.md** - Complete user guide

---

## 🎉 You're Ready!

The visualization is live. Start by:

1. Opening http://localhost:5173
2. Reading the Document Flow section
3. Trying a sample question
4. Clicking through the pipeline steps
5. Checking the sources

**Enjoy exploring your RAG pipeline!** 🚀

---

## 📞 Need Help?

- Frontend issues? Check `frontend/src/` files
- Backend issues? Check `backend/app/` files
- Visualization not showing? Clear browser cache
- Embeddings look weird? That's normal! They're 768-dimensional
