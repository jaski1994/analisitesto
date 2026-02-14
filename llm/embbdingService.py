import os
import faiss
import numpy as np
from sentence_transformers import SentenceTransformer

embedding_model = SentenceTransformer("all-MiniLM-L6-v2")

from django.conf import settings

# Use MEDIA_ROOT or a specific directory inside BASE_DIR
FAISS_FOLDER = os.path.join(settings.BASE_DIR, "faiss_indexes")


def chunk_text(text, size=500, overlap=100):
    chunks = []
    start = 0
    while start < len(text):
        end = start + size
        chunks.append(text[start:end])
        start += size - overlap
    return chunks


def create_and_save_index(document):
    chunks = chunk_text(document.content)
    embeddings = embedding_model.encode(chunks)

    dimension = embeddings.shape[1]
    index = faiss.IndexFlatL2(dimension)
    index.add(np.array(embeddings).astype("float32"))

    if not os.path.exists(FAISS_FOLDER):
        os.makedirs(FAISS_FOLDER)

    index_path = f"{FAISS_FOLDER}/doc_{document.id}.index"
    faiss.write_index(index, index_path)

    return index_path, chunks
