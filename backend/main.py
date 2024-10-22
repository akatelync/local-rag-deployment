from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
from rag import LlamaIndexRAG  # Import the RAG class we created earlier
import os
from dotenv import load_dotenv

load_dotenv()

app = FastAPI()

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],  # Your frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize RAG chatbot
rag = LlamaIndexRAG(
    astra_token=os.getenv("ASTRA_DB_APPLICATION_TOKEN"),
    openai_api_key=os.getenv("OPENAI_API_KEY"),
    collection_name=os.getenv("ASTRA_DB_COLLECTION"),
    astra_db_id=os.getenv("ASTRA_DB_ID"),
    astra_db_region=os.getenv("ASTRA_DB_REGION"),
    astra_keyspace=os.getenv("ASTRA_DB_KEYSPACE")
)

class QuestionRequest(BaseModel):
    question: str

class ChatResponse(BaseModel):
    response: str
    relevant_sources: Optional[list[str]] = None

@app.post("/api/chat")
async def chat(request: QuestionRequest) -> ChatResponse:
    try:
        # Get response from RAG chatbot
        response = rag.query(request.question)
        
        # Optionally get relevant sources
        relevant_sources = rag.get_relevant_nodes(request.question)
        
        return ChatResponse(
            response=response,
            relevant_sources=relevant_sources
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)