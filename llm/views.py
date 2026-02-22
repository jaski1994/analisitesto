import requests
from django.shortcuts import render, get_object_or_404, redirect
from django.http import HttpResponse
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from testo.models import Articolo
from .models import LLMResult
from .forms import LlmForm, LlmEmptyForm, ClassificationForm, RAGForm
import ollama 
import asyncio
from .llmManager import LLMManager
from .ragService import contextual_correction
import json
from django.http import JsonResponse

from .models import Document

@login_required()
def llm_elaborazione(request, articolo_id):
    """
    View to process an article using LLM based on user selection.
    """
    articolo = get_object_or_404(Articolo, id=articolo_id, autore=request.user)
    
    if request.method == 'POST':
        form = LlmForm(request.POST)
        if form.is_valid():
            tipo = form.cleaned_data.get('tipo_operazione')
            model = get_specialized_model(tipo)
            prompt = get_specialized_prompt(articolo.testo, tipo)
            options = {
                "temperature": 0.3 if tipo == "grammatica" else 0.7 
                # Temperatura bassa = precisione (grammatica)
                # Temperatura alta = creatività (email/miglioramento)
            }
            try:

                response = asyncio.run(LLMManager().call_the_llm(model,prompt,options))
                response_content = response['response']
                
                llm_entry = LLMResult(
                    utente=request.user,
                    articolo=articolo,
                    tipo_operazione=tipo,
                    risultato=response_content,
                    modello_usato=model,
                )
                llm_entry.save()
                
                messages.success(request, f'Analisi ({tipo}) completata con successo!')
                return redirect('testo:articolo-details', id=articolo.id)
            
            except Exception as e:
                messages.error(request, f"Errore durante l'elaborazione AI: {e}")
        else:
            messages.error(request, 'Errore nel modulo inviato.')
    else:
        form = LlmForm()

    context = {
        'form': form,
        'articolo': articolo,
        'logged_user_username': request.user.username
    }
    return render(request, 'llm/llm_elaborazione.html', context)

def empty_llm(request):
    """
    View for LLM analysis that returns the result to the same page.
    """
    response_content = None  # Variable to hold the AI result
    
    if request.method == 'POST':
        form = LlmEmptyForm(request.POST)
        if form.is_valid():
            try:
                tipo = form.cleaned_data.get('tipo_operazione')
                text = form.cleaned_data.get('text')
                
                model = get_specialized_model(tipo)
                prompt = get_specialized_prompt(text, tipo) if text else "Ciao, come va?"
                options = {
                    "temperature": 0.3 if tipo == "grammatica" else 0.7 
                    # Temperatura bassa = precisione (grammatica)
                    # Temperatura alta = creatività (email/miglioramento)
                }
                
                response = asyncio.run(LLMManager().call_the_llm(model,prompt,options))
                # Store the result in the variable instead of returning immediately
                response_content = response['response']
                messages.success(request, "Analisi completata!")
                
            except Exception as e:
                messages.error(request, f"Errore: {e}")
    else:
        form = LlmEmptyForm()

    context = {
        'form': form,
        'result': response_content, # Pass the result to the template
        'logged_user_username': request.user.username if request.user.is_authenticated else None
    }
    return render(request, 'llm/llm_empty.html', context)


def empty_classificazione_llm(request):
    """
    View for LLM analysis that returns the result to the same page.
    """
    response_content = None  # Variable to hold the AI result
    
    if request.method == 'POST':
        form = ClassificationForm(request.POST)
        if form.is_valid():
            try:
                tipo = "classificazione"
                text = form.cleaned_data.get('text')
                
                model = get_specialized_model(tipo)
                prompt = get_specialized_prompt(text, tipo) if text else "Ciao, come va?"
                options = {
                    "temperature": 0.1,
                    "num_predict": 20    # Poche parole necessarie
                }
                response = asyncio.run(LLMManager().call_the_llm(model,prompt,options))
                # Store the result in the variable instead of returning immediately
                response_content = response['response']
                messages.success(request, "classificazione completata!")
                
            except Exception as e:
                messages.error(request, f"Errore: {e}")
    else:
        form = ClassificationForm()

    context = {
        'form': form,
        'result': response_content, # Pass the result to the template
        'logged_user_username': request.user.username if request.user.is_authenticated else None
    }
    return render(request, 'llm/llm_empty.html', context)



## Prompt Specialistici v2
def get_specialized_prompt(testo_utente, task):
    categories = [
        "tecnologia", "sport", "politica", "economia", "cultura", "scienza",
        "salute", "ambiente", "cronaca", "esteri", "spettacolo", "arte", "musica",
        "cinema", "moda", "cucina", "viaggi", "automobilismo", "finanza",
        "istruzione", "lavoro", "diritto", "storia", "filosofia", "religione",
        "gossip", "videogame", "informatica", "altro"
    ]

    if task == "grammatica":
        return (
            "Sei un correttore di bozze esperto con venti anni di esperienza editoriale. "
            "Il tuo compito è analizzare il testo fornito e:\n"
            "1. Correggere eventuali errori grammaticali, ortografici e di punteggiatura.\n"
            "2. Mantenere lo stile e il tono originali dell'autore.\n"
            "3. NON riscrivere o parafrasare frasi che sono già corrette.\n"
            "4. Restituire SOLO il testo corretto, senza commenti o spiegazioni aggiuntive.\n\n"
            f"Testo da correggere:\n{testo_utente}"
        )

    elif task == "miglioramento":
        return (
            "Sei un editor professionista che lavora per una rivista letteraria italiana di alto livello. "
            "Il tuo compito è migliorare il testo seguente:\n"
            "1. Rendi il testo più formale, fluido e persuasivo.\n"
            "2. Elimina ridondanze, sostituisci vocaboli banali con termini più precisi ed evocativi.\n"
            "3. Assicurati che la struttura delle frasi sia bilanciata e armoniosa.\n"
            "4. Mantieni il significato e le informazioni chiave dell'originale.\n"
            "5. Restituisci SOLO il testo migliorato, senza commenti aggiuntivi.\n\n"
            f"Testo originale:\n{testo_utente}"
        )

    elif task == "traduci":
        return (
            "Sei un traduttore professionista madrelingua inglese, specializzato in testi italiani. "
            "Il tuo compito è tradurre il testo seguente dall'italiano all'inglese:\n"
            "1. La traduzione deve essere naturale e idiomatica, non letterale.\n"
            "2. Mantieni il tono e lo stile del testo originale (formale, informale, tecnico, ecc.).\n"
            "3. Se un termine non ha un equivalente diretto, usa il termine più vicino concettualmente.\n"
            "4. Restituisci SOLO il testo tradotto in inglese, senza commenti o note aggiuntive.\n\n"
            f"Testo in italiano:\n{testo_utente}"
        )

    elif task == "classificazione":
        categories_str = ', '.join(categories)
        return (
            f"Sei un esperto classificatore di contenuti editoriali. "
            f"Classifica il seguente testo in UNA SOLA delle categorie fornite.\n\n"
            f"Categorie disponibili: {categories_str}\n\n"
            f"Regole:\n"
            f"- Rispondi SOLO con il nome esatto della categoria (una parola).\n"
            f"- Non aggiungere punteggiatura, spiegazioni o testo extra.\n"
            f"- Se il testo è ambiguo, scegli la categoria più dominante.\n\n"
            f"Testo da classificare:\n{testo_utente}\n\n"
            f"Categoria:"
        )

    elif task == "riassunto":
        return (
            "Sei un esperto di comunicazione e sintesi dei contenuti. "
            "Il tuo compito è creare un riassunto chiaro e conciso del testo seguente:\n"
            "1. Il riassunto deve coprire i punti principali e le informazioni chiave.\n"
            "2. Scrivi in italiano, in modo chiaro e scorrevole.\n"
            "3. La lunghezza del riassunto deve essere circa il 20-25% del testo originale.\n"
            "4. NON aggiungere interpretazioni personali o informazioni non presenti nel testo.\n"
            "5. Restituisci SOLO il riassunto, senza prefazioni o commenti.\n\n"
            f"Testo da riassumere:\n{testo_utente}"
        )

    return testo_utente


def get_specialized_model(task):
    if task == "grammatica" or task == "riassunto":
        return "llama3.2:3b"
    elif task == "miglioramento" or task == "classificazione":
        return "phi4-mini"
    elif task == "traduci":
        return "qwen3:4b"
    return "llama3.2:3b"

def unload_llm(request, llm_name):
    manager = LLMManager() 
    manager.unload_model(llm_name)
    return redirect('testo:profile')

def load_llm(request, llm_name):
    manager = LLMManager() 
    manager.load_model(llm_name)
    return redirect('testo:profile')

def pull_llm(request, llm_name):
    manager = LLMManager() 
    manager.pull_model_thread(llm_name)
    return JsonResponse({"message": f"Pull di {llm_name} avviato in background."})

def pull_progress(request, llm_name):
    """Returns the current download progress for a given model from cache."""
    from django.core.cache import cache
    cache_key = f"ollama_pull_{llm_name.replace(':', '_')}"
    data = cache.get(cache_key)
    if data is None:
        return JsonResponse({"progress": None, "status": "not_started"})
    return JsonResponse(data)

def rag_elaborazione(request):
    """
    Renders the RAG analysis page with a list of available documents.
    """
    documents = Document.objects.all().order_by('-created_at')
    context = {
        'form': RAGForm(),  
        'documents': documents
    }
    return render(request, 'llm/rag_elaborazione.html', context)


def document_rag(request):
    if request.method != "POST":
        return JsonResponse({"error": "Only POST allowed"}, status=405)

    try:
        body = json.loads(request.body)
        title = body.get("title")
        content = body.get("content")

        if not title or not content:
            return JsonResponse(
                {"error": "Title and content are required"},
                status=400
            )

        # Il metodo save() del modello gestisce automaticamente creazione index e chunking
        document = Document.objects.create(
            title=title,
            content=content
        )

        return JsonResponse({
            "message": "Document created and indexed successfully",
            "document_id": document.id
        })

    except Exception as e:
        return JsonResponse(
            {"error": str(e)},
            status=500
        )


def rag_correct(request):
    if request.method == "POST":
        try:
            body = json.loads(request.body)
            text = body.get("text")
            document_id = body.get("document")

            if not text or not document_id:
                return JsonResponse({"error": "Missing 'text' or 'document' ID"}, status=400)

            document = get_object_or_404(Document, id=document_id)
            result = contextual_correction(text, document)

            return JsonResponse({"result": result})
        except json.JSONDecodeError:
            return JsonResponse({"error": "Invalid JSON"}, status=400)
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=500)

    return JsonResponse({"error": "Invalid request method"}, status=405)

## Prompt Specialistici v1
#def get_specialized_prompt(testo_utente, task):
#    if task == "grammatica":
#        return (
#            "Sei un correttore di bozze esperto. Analizza il testo seguente, "
#            "correggi errori grammaticali, di punteggiatura e ortografia. "
#            "Restituisci il testo corretto e, in una sezione separata, elenca brevemente le correzioni fatte.\n\n"
#            f"Testo: {testo_utente}"
#        )
#    
#    elif task == "miglioramento":
#        return (
#            "Sei un editor professionista. Riscrivi il testo seguente per renderlo più formale, "
#            "fluido e persuasivo, mantenendo però il significato originale. "
#            "Evita ripetizioni e usa un vocabolario ricercato.\n\n"
#            f"Testo: {testo_utente}"
#        )
#    
#    elif task == "traduci":
#        return (
#            "Agisci come un traduttore professionista madrelingua. Traduci il testo seguente da itagliano a inglese, mantenendo significato, tono e naturalezza. Evita traduzioni letterali se suonano innaturali."
#            "1) rivedi la traduzione"
#            "2) correggi eventuali errori"
#            "3) segnala possibili miglioramenti stilistici"
#            f"Informazioni: {testo_utente}"
#        )
