from fastapi import APIRouter, Request
from pydantic import BaseModel
from transformers import AutoModelForSeq2SeqLM, AutoTokenizer
import torch

router = APIRouter()

# Load flan-t5 model and tokenizer
model_name = "google/flan-t5-base"
tokenizer = AutoTokenizer.from_pretrained(model_name)
model = AutoModelForSeq2SeqLM.from_pretrained(model_name)

# In-memory conversation store (for demo purposes, replace with persistent store in production)
conversations = {}

class QueryRequest(BaseModel):
    session_id: str
    query: str

def build_prompt(session_id: str, query: str) -> str:
    history = conversations.get(session_id, [])
    # Combine history and current query into prompt
    conversation_text = "\n".join(history + [f"User: {query}"])
    prompt = f"""
    You are a flood detection assistant providing accurate and up-to-date information about floods. Answer any flood-related questions comprehensively and accurately. Maintain context from the conversation history.

    Conversation history:
    {conversation_text}

    Assistant:"""
    return prompt

@router.post("/ask")
async def ask(request: QueryRequest):
    prompt = build_prompt(request.session_id, request.query)
    inputs = tokenizer(prompt, return_tensors="pt", truncation=True, max_length=512)
    outputs = model.generate(**inputs, max_length=256)
    answer = tokenizer.decode(outputs[0], skip_special_tokens=True)

    # Update conversation history
    conversations.setdefault(request.session_id, []).append(f"User: {request.query}")
    conversations[request.session_id].append(f"Assistant: {answer}")

    return {"answer": answer}

@router.post("/summarize")
async def summarize(request: QueryRequest):
    prompt = f"Summarize the following flood detection information:\n{request.query}"
    inputs = tokenizer(prompt, return_tensors="pt", truncation=True, max_length=512)
    outputs = model.generate(**inputs, max_length=256)
    summary = tokenizer.decode(outputs[0], skip_special_tokens=True)
    return {"summary": summary}
