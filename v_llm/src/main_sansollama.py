import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import asyncio
import chromadb

# ---- Import your RAG + Mistral wrapper ----
from local_rag import rag_biomistral_query
from indexage import create_index

# ---- Load / initialize ChromaDB collection ----
def load_or_create_collection():
    client = chromadb.PersistentClient(path="./chroma_db")
    try: # If it exists, load it
        return client.get_collection("guidelines")
    except chromadb.errors.NotFoundError:
        # Otherwise create index from PDFs / text files
        print("⚠️  No Chroma collection found — creating index...")
        return create_index(client)

collection = load_or_create_collection()

# ---- FastAPI setup ----
app = FastAPI(title="Local BioMistral RAG API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],   # you can restrict to your Next.js domain
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ---- Request schema ----
class ChatRequest(BaseModel):
    message: str


# ---- Chat endpoint ----
@app.post("/chat")
async def chat(req: ChatRequest):
    """Main RAG endpoint called by your frontend."""
    
    question = req.message.strip()
    if not question:
        return {"response": "Message vide."}

    # Running the model in a thread so FastAPI stays responsive
    loop = asyncio.get_running_loop()
    response = await loop.run_in_executor(
        None,
        rag_biomistral_query,
        question,
        collection
    )

    return {"response": response}


@app.get("/")
def root():
    return {"status": "BioMistral RAG backend is running"}


# ---- Launch ----
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main_sansollama:app", host="0.0.0.0", port=8000, reload=True)
