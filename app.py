import streamlit as st
import anthropic
import chromadb
import os
import tempfile
import hashlib
from pypdf import PdfReader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from chromadb.utils.embedding_functions import SentenceTransformerEmbeddingFunction

# ─── Page Config ───
st.set_page_config(page_title="Chat with Your PDF", page_icon="📄", layout="centered")

st.title("📄 Chat with Your PDF")
st.caption("Upload a PDF and ask questions — powered by Claude AI")

# ─── Sidebar: API Key ───
with st.sidebar:
    st.header("⚙️ Settings")
    api_key = st.text_input("Anthropic API Key", type="password", help="Get yours at console.anthropic.com")
    st.divider()
    st.markdown("**How it works:**")
    st.markdown(
        "1. Upload a PDF\n"
        "2. The app chunks & embeds the text\n"
        "3. Ask any question\n"
        "4. Claude answers using only your document"
    )
    st.divider()
    st.markdown("Built by **KK** · [GitHub](https://github.com)")

# ─── Initialize ChromaDB ───
@st.cache_resource
def get_chroma_client():
    return chromadb.EphemeralClient()

@st.cache_resource
def get_embedding_function():
    return SentenceTransformerEmbeddingFunction(model_name="all-MiniLM-L6-v2")

chroma_client = get_chroma_client()
embedding_fn = get_embedding_function()

# ─── PDF Processing ───
def extract_text_from_pdf(pdf_file) -> str:
    """Extract all text from uploaded PDF."""
    reader = PdfReader(pdf_file)
    text = ""
    for page in reader.pages:
        page_text = page.extract_text()
        if page_text:
            text += page_text + "\n\n"
    return text

def chunk_text(text: str) -> list[str]:
    """Split text into overlapping chunks for embedding."""
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=800,
        chunk_overlap=150,
        separators=["\n\n", "\n", ". ", " ", ""]
    )
    return splitter.split_text(text)

def get_collection_name(file_name: str) -> str:
    """Generate a safe collection name from filename."""
    hash_str = hashlib.md5(file_name.encode()).hexdigest()[:8]
    return f"pdf_{hash_str}"

def index_document(pdf_file) -> str:
    collection_name = get_collection_name(pdf_file.name)

    text = extract_text_from_pdf(pdf_file)
    if not text.strip():
        st.error("Could not extract text from this PDF. It may be scanned/image-based.")
        return None

    chunks = chunk_text(text)

    collection = chroma_client.get_or_create_collection(
        name=collection_name,
        embedding_function=embedding_fn
    )

    if collection.count() > 0:
        return collection_name

    collection.add(
        documents=chunks,
        ids=[f"chunk_{i}" for i in range(len(chunks))]
    )

    return collection_name
    """Extract, chunk, embed, and store PDF in ChromaDB."""
    collection_name = get_collection_name(pdf_file.name)

    try:
        chroma_client.get_collection(collection_name, embedding_function=embedding_fn)
        return collection_name
    except Exception:
        pass

    # Extract and chunk
    text = extract_text_from_pdf(pdf_file)
    if not text.strip():
        st.error("Could not extract text from this PDF. It may be scanned/image-based.")
        return None

    chunks = chunk_text(text)

    # Store in ChromaDB
    collection = chroma_client.create_collection(
        name=collection_name,
        embedding_function=embedding_fn
    )
    collection.add(
        documents=chunks,
        ids=[f"chunk_{i}" for i in range(len(chunks))]
    )

    return collection_name

# ─── Query Function ───
def query_document(collection_name: str, question: str, n_results: int = 5) -> list[str]:
    """Retrieve relevant chunks for a question."""
    collection = chroma_client.get_collection(
        name=collection_name,
        embedding_function=embedding_fn
    )
    results = collection.query(query_texts=[question], n_results=n_results)
    return results["documents"][0]

def ask_claude(question: str, context_chunks: list[str], api_key: str) -> str:
    """Send question + context to Claude and get an answer."""
    client = anthropic.Anthropic(api_key=api_key)

    context = "\n\n---\n\n".join(context_chunks)

    message = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=1024,
        system=(
            "You are a helpful document assistant. Answer the user's question based ONLY on "
            "the provided document excerpts. If the answer is not in the excerpts, say so clearly. "
            "Cite relevant parts of the text to support your answer. Be concise and accurate."
        ),
        messages=[
            {
                "role": "user",
                "content": (
                    f"Here are relevant excerpts from the document:\n\n{context}\n\n"
                    f"---\n\nQuestion: {question}\n\n"
                    "Answer based only on the document above:"
                )
            }
        ]
    )

    return message.content[0].text

# ─── Main App Flow ───

# File upload
uploaded_file = st.file_uploader("Upload a PDF", type=["pdf"])

if uploaded_file:
    with st.spinner("Processing PDF..."):
        collection_name = index_document(uploaded_file)

    if collection_name:
        st.success(f"✅ **{uploaded_file.name}** indexed and ready!")

        # Initialize chat history
        if "messages" not in st.session_state:
            st.session_state.messages = []

        # Display chat history
        for msg in st.session_state.messages:
            with st.chat_message(msg["role"]):
                st.markdown(msg["content"])

        # Chat input
        if question := st.chat_input("Ask a question about your PDF..."):
            if not api_key:
                st.error("Please enter your Anthropic API key in the sidebar.")
            else:
                # Show user message
                st.session_state.messages.append({"role": "user", "content": question})
                with st.chat_message("user"):
                    st.markdown(question)

                # Get answer
                with st.chat_message("assistant"):
                    with st.spinner("Thinking..."):
                        try:
                            chunks = query_document(collection_name, question)
                            answer = ask_claude(question, chunks, api_key)
                            st.markdown(answer)
                            st.session_state.messages.append({"role": "assistant", "content": answer})
                        except anthropic.AuthenticationError:
                            st.error("Invalid API key. Please check your Anthropic API key.")
                        except Exception as e:
                            st.error(f"Error: {str(e)}")
else:
    st.info("👆 Upload a PDF to get started.")