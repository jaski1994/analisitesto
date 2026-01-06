# Django Text Analysis Tool

A Python-based text analysis tool developed with **Django** and **NLTK**.  
It automates frequency analysis and content quality checks to significantly reduce manual review.  
The project also integrates the **Ollama** tool with custom models and prompt engineering to enhance analysis capabilities.

## Features

- Frequency analysis of text content
- Automated content quality checks
- Integration with Ollama for advanced text analysis
- Admin panel for managing data and results

## Requirements

- Python 3.10+
- pip
- Virtual environment (recommended)

## Ollama Integration

Ollama can also be used via Python by installing the `requests` library with pip.
The application sends HTTP POST requests to the local Ollama API (`http://localhost:11434`). Alternatively, Ollama can be used via its Python client `pip install ollama`.
This enables model inference using custom prompts directly from the Django backend.



## Installation

1. **Clone the repository**  
   ```bash
   git clone <your-repo-url>
   cd <your-project-folder>
   ```

2. **Create and activate a virtual environment**  
   ```bash
   python -m venv venv
   source venv/bin/activate  
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Apply database migrations**
   ```bash
   python manage.py migrate
   ```

5. **Create a superuser**
   ```bash
   python manage.py createsuperuser
   ```

6. **Run the development server**
   ```bash
   python manage.py runserver
   ```

7. **Open the app in your browser**
   ```bash
   http://localhost:8000
   ```
