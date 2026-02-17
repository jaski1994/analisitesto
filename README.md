# Django Text Analysis Tool

A Python-based text analysis tool developed with **Django** and **NLTK**.  
It automates frequency analysis and content quality checks to significantly reduce manual review.  
The project also integrates the **Ollama** tool with custom models and prompt engineering to enhance analysis capabilities. And implemented RAG (Retrieval-Augmented Generation) to improve the quality of the analysis.

## Features

- Frequency analysis of text content
- Automated content quality checks
- Integration with Ollama for advanced text analysis
- Admin panel for managing data and results
- RAG (Retrieval-Augmented Generation) for improved analysis quality

## Requirements

- Docker
- Docker Compose

## Ollama Integration

Ollama can be used via its Python client `pip install ollama`.
This enables model inference using custom prompts directly from the Django backend.

# RAG Integration

The RAG (Retrieval-Augmented Generation) feature allows the application to retrieve relevant context from a document and use it to generate a response to a query. This can be used to improve the quality of the analysis by providing more context to the model. i used **faiss** to index the documents and retrieve the relevant context.

## Installation

1. **Clone the repository**  
   ```bash
   git clone https://github.com/jaski1994/analisitesto.git
   cd analisitesto
   ```

2. **run the docker**
   ```bash
   docker-compose up --build
   ```

3. **Open the app in your browser**
   ```bash
   http://localhost:8000
   ```
