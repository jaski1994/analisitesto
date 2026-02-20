# Django Text Analysis Tool

A Python-based text analysis tool developed with **Django** and **NLTK**.  
It automates frequency analysis and content quality checks to significantly reduce manual review.  
The project also integrates the **Ollama** tool with custom models and prompt engineering to enhance analysis capabilities, and implements RAG (Retrieval-Augmented Generation) to improve the quality of the analysis.

## Features

- Frequency analysis of text content
- Automated content quality checks (Leggibilità, TTR, ecc.)
- Integration with Ollama for advanced text analysis and correction
- Admin panel for managing data and results
- RAG (Retrieval-Augmented Generation) for improved analysis quality

## Requirements

- Python 3.12
- Docker
- Docker Compose

## Ollama & RAG Integration

Ollama can be used via its Python client. This enables model inference using custom prompts directly from the Django backend.

The RAG (Retrieval-Augmented Generation) feature allows the application to retrieve relevant context from a document and use it to generate a response to a query. This is achieved using **FAISS** to index the documents and retrieve the relevant context efficiently.

---

## Getting Started with Docker

The project uses GitHub Container Registry (GHCR) to host the pre-built Docker images, making it incredibly fast to deploy without needing to build the image locally.

### 1. Clone the repository
```bash
git clone https://github.com/jaski1994/analisitesto.git
cd analisitesto
```

### 2. Pull the latest image and run
The image `ghcr.io/jaski1994/analisi:latest` is **public** — no authentication required. Just run:

```bash
docker-compose up -d
```

### 3. Open the app
Visit the application in your browser:
```text
http://localhost:8000
```
