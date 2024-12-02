from rag import LlamaIndexRAG
from typing import Optional, List, Dict
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List
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


class Message(BaseModel):
    type: str
    content: str


class QuestionRequest(BaseModel):
    question: str


class ChatRequest(BaseModel):
    question: str
    history: List[Message] = []


class ChatResponse(BaseModel):
    response: str
    relevant_sources: Optional[List[str]] = None


@app.post("/api/chat")
async def chat(request: ChatRequest) -> ChatResponse:
    try:
        chat_history = "\n".join([
            f"{'User: ' if msg.type == 'user' else 'Assistant: '}{msg.content}"
            for msg in request.history
        ])

        full_context = f"{chat_history}\nUser: {request.question}"

        response = rag.query(full_context)
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


load_dotenv()

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

DEFAULT_SYSTEM_PROMPT = """
    You are AVA, a helpful legal assistant for the Senate of the Philippines that contains information about past projects and other available documents published by the Senate. Your main task is to help employees of the Senate 
    to track the aging of the bills and compare and contrast the amendments made over time. Be as clear and concise as possible, include important details that will help in legal analysis.

    Respond by following these instructions:\n
    1. Assign every relevant source a number `n` so that EVERY conclusion, fact, markdown table, and/or derivative from a source uses Github Markdown Flavored [^n] citation corresponding to its source.\n
    2. Organize your response in paragraph format instead of using bullet points.
    3. Use the phrase "Based on internal/external information..." if you will refer to internal/external sources.
    4. If internal/external information is not provided, do not mention its absence.
    5. Create a statement before the References section with at least 1 citation [^n] that synthesizes and summarizes your response .\n
        - With each reference, they must follow the format of `[^n]: [Title]`\n
    6. Answer the question directly using only the information shared with you.\n

    Here is an example of an input:\n\n
    ## Start of Example Input ##
    "[
        {
            'Citation Number': 1,
            'Title': 'DTI submission EMB Submission re CREATE MORE',
            'Content': 'Number of entities registered with Export Marketing Bureau from 2018 to 2024...',
        },
        {
            'Citation Number': 2,
            'Title': 'PHIVIDEC-IA Position Paper CREATE MORE',
            'Content': 'The PHIVIDEC Industrial Authority (PHIVIDEC-IA), through its Administrator and Chief Executive Officer (CEO)...',
        },
        {
            'Citation Number': 3,
            'Title': 'PPMC - Position Paper - SB No. 2654 and HB No. 9794',
            'Content': 'This has reference to your letter, dated May 7, 2024, requesting Poro Point Management Corporation...',
        },]
    ]\n\n
    ## End of Example Input##
    \n\n
    Answer the following question acting as if the above was from your knowledge: What can Vietnam do to integrate?"\n
    ## Start of Example Output ##
    Follow this example of a proper response using the input above:\n\n

    "Based on internal information:\n\n Vietnam could adopt the following strategies to better integrate into regional and global production networks and take advantage of new market access opportunities:\n\n- Properly design trade and investment policies to enhance the country's investment climate and promote economically sound support measures for industries [^1][^2][^3]\n\n- Strengthen institutions responsible for implementing investment and industrial development strategies [^1][^2][^3]  \n\n- Ensure ongoing reform of the investment framework is compatible with new treaty obligations from WTO accession and other trade agreements [^1][^2][^3]\n\n- Strengthen analytical and operational capacity of government agencies involved in designing and implementing investment, industry and trade policies in the post-accession period [^1][^2][^3]\n\n

    Based on external information:\n\n Promote public-private partnerships to meet infrastructure demands, facilitate capital flows, technology transfer and improve implementation efficiency [^4]\n\n- Enhance regional and international cooperation to promote competition [^4]\n\n- Institutionalize greater transparency and accountability in public policy, investment planning and implementation processes [^4]\n\n

    Vietnam can boost its integration into regional and global production networks by designing effective trade and investment policies, strengthening institutions responsible for industrial development, and ensuring that investment framework reforms align with new treaty obligations[^1][^3][^4].Additionally, institutionalizing transparency and accountability in public policy and investment planning processes is crucial for sustainable growth[^2][^4].\n\n

    References:
    \n
    [^1]: [DTI submission EMB Submission re CREATE MORE]\n[^2]: [PHIVIDEC-IA Position Paper CREATE MORE]\n[^3]: [PPMC - Position Paper - SB No. 2654 and HB No. 9794]"

    ## End of Example Output ##
"""


JOURNAL_SYSTEM_PROMPT = """
    You are AVA, a helpful legal assistant for the Senate of the Philippines that contains information about past projects and other available documents published by the Senate. Your main task is to generate the journal from
    transcripts of a Senate hearing. Generate a structured outline of the Senate journal from August 5, 2024. Include the following key sections:
        1. Session Details: Include session number, date, and time.
        2. Opening Formalities:
            - Call to order
            - Prayer and who led it
            - Singing of the national anthem
        3. Roll Call and Quorum: List attending members and mention the presence of a quorum.
        4. Special Mentions:
            - Acknowledgment of guests
            - Announcements, such as birthday greetings or achievements
        5. Legislative Proceedings:
            - Deferment or approval of previous session journals
            - Presentation and referral of new bills
            - Discussion and manifestation on key legislative topics (e.g., POGO regulation, CREATE MORE Act)
        6. Sponsorship and Cosponsorship Speeches:
            - Summarize the speeches supporting major bills discussed during the session.
        7. Committee Reports: Highlight reports presented, including details of bills and resolutions referred.
        8. Other Proceedings:
            - Suspension and resumption of sessions
            - Manifestations or legal concerns raised by senators
            - Additional motions or approvals
        9. Adjournment: Time and formal adjournment details.
    
    Format the output in a clean, professional style suitable for official documentation. Include headings for each section and ensure readability.
"""

# Define different system prompts
SYSTEM_PROMPTS = {
    "general": DEFAULT_SYSTEM_PROMPT,
    "journal": DEFAULT_SYSTEM_PROMPT
}

# Initialize multiple RAG instances
rag_systems: Dict[str, LlamaIndexRAG] = {}
for system_name, prompt in SYSTEM_PROMPTS.items():
    rag_systems[system_name] = LlamaIndexRAG(
        astra_token=os.getenv("ASTRA_DB_APPLICATION_TOKEN"),
        openai_api_key=os.getenv("OPENAI_API_KEY"),
        collection_name=f"{os.getenv('ASTRA_DB_COLLECTION')}_{system_name}",
        astra_db_id=os.getenv("ASTRA_DB_ID"),
        astra_db_region=os.getenv("ASTRA_DB_REGION"),
        astra_keyspace=os.getenv("ASTRA_DB_KEYSPACE"),
        system_prompt=prompt
    )


class Message(BaseModel):
    type: str
    content: str


class ChatRequest(BaseModel):
    question: str
    history: List[Message] = []
    system_type: str = "general"  # Default to DBM system


class ChatResponse(BaseModel):
    response: str
    relevant_sources: Optional[List[str]] = None


@app.post("/api/chat")
async def chat(request: ChatRequest) -> ChatResponse:
    try:
        if request.system_type not in rag_systems:
            raise HTTPException(status_code=400, detail="Invalid system type")

        rag = rag_systems[request.system_type]
        chat_history = "\n".join([
            f"{'User: ' if msg.type == 'user' else 'Assistant: '}{msg.content}"
            for msg in request.history
        ])

        full_context = f"{chat_history}\nUser: {request.question}"
        response = rag.query(full_context)
        relevant_sources = rag.get_relevant_nodes(request.question)

        return ChatResponse(
            response=response,
            relevant_sources=relevant_sources
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/systems")
async def get_systems():
    return {"systems": list(rag_systems.keys())}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
