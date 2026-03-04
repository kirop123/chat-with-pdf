# 📄 Chat with Your PDF

Ask questions about any PDF document using AI. Powered by Claude and local vector search.

![Python](https://img.shields.io/badge/Python-3.10+-blue)
![Streamlit](https://img.shields.io/badge/Streamlit-1.41-red)
![Claude](https://img.shields.io/badge/LLM-Claude_Sonnet-orange)

## Features

- **Upload any PDF** — text is extracted and chunked automatically
- **Semantic search** — finds the most relevant sections for your question
- **AI-powered answers** — Claude answers using only your document (no hallucination)
- **Chat interface** — conversational, with full history
- **Local embeddings** — your data stays on your machine (only the question + relevant chunks go to Claude)

## Tech Stack

| Component | Technology |
|-----------|-----------|
| Frontend | Streamlit |
| LLM | Claude Sonnet (Anthropic API) |
| Vector DB | ChromaDB (in-memory) |
| Embeddings | sentence-transformers (all-MiniLM-L6-v2) |
| PDF Parsing | pypdf |
| Text Splitting | LangChain |

## Quick Start

```bash
# Clone the repo
git clone https://github.com/yourusername/chat-with-pdf.git
cd chat-with-pdf

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run the app
streamlit run app.py
```

Then enter your Anthropic API key in the sidebar and upload a PDF.

## Getting an API Key

1. Go to [console.anthropic.com](https://console.anthropic.com)
2. Create an account and add credits ($5 is plenty to start)
3. Generate an API key
4. Paste it into the app sidebar

## How It Works

1. **PDF Upload** → Text extracted using pypdf
2. **Chunking** → Text split into ~800 character overlapping chunks
3. **Embedding** → Chunks embedded locally using sentence-transformers
4. **Storage** → Embeddings stored in ChromaDB (in-memory)
5. **Query** → Your question is embedded and matched against stored chunks
6. **Answer** → Top 5 matching chunks + your question sent to Claude for a grounded answer

## Deployment

Deploy free on Streamlit Cloud:

1. Push to GitHub
2. Go to [share.streamlit.io](https://share.streamlit.io)
3. Connect your repo
4. Deploy

## License

MIT