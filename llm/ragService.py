import faiss
import numpy as np
import requests
from sentence_transformers import SentenceTransformer
from .llmManager import LLMManager
import asyncio

embedding_model = SentenceTransformer("all-MiniLM-L6-v2")


def load_index(path):
    return faiss.read_index(path)


def retrieve(text, document, k=3):
    index = load_index(document.faiss_index_path)
    query_embedding = embedding_model.encode([text])

    distances, indices = index.search(
        np.array(query_embedding).astype("float32"), k
    )

    return [document.chunks[i] for i in indices[0]]


def call_ollama(prompt):
    options = {
        "temperature": 0.7,
        "top_p": 0.9,
        "top_k": 40,
        "num_ctx": 2048,
        "num_predict": 256,
        "repeat_penalty": 1.1,
        "presence_penalty": 0.0,
        "frequency_penalty": 0.0,
        "stop": ["\n\n"],
    }
    try:
        response = asyncio.run(LLMManager().call_the_llm("phi4-mini",prompt,options))
        return response.get("response", "")
    except requests.exceptions.RequestException as e:
        return f"Error communicating with Ollama: {e}"


def contextual_correction(text, document):
    retrieved_chunks = retrieve(text, document)

    context = "\n\n".join(retrieved_chunks)

    prompt = f"""
Sei un editor professionista.

Contesto:
{context}

Testo:
{text}

Correggi grammatica e mantieni coerenza con il contesto.
"""

    return call_ollama(prompt)
