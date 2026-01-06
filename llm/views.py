import requests
from django.shortcuts import render, get_object_or_404, redirect
from django.http import HttpResponse
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from testo.models import Articolo
from .models import LLMResult
from .forms import LlmForm, LlmEmptyForm
import ollama   
from .llmManager import LLMManager

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
            
            try:
                payload = call_llm(model, prompt,tipo)
                response = requests.post("http://localhost:11434/api/generate", json=payload)
                risultato_testo = response.json().get('response', 'Error: No response key')
                # return HttpResponse(risultato_testo)
                
                llm_entry = LLMResult(
                    utente=request.user,
                    articolo=articolo,
                    tipo_operazione=tipo,
                    risultato=risultato_testo,
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
                client = ollama.Client()
                tipo = form.cleaned_data.get('tipo_operazione')
                text = form.cleaned_data.get('text')
                
                model = get_specialized_model(tipo)
                prompt = get_specialized_prompt(text, tipo) if text else "Ciao, come va?"
                
                response = client.generate(
                    model=model,
                    prompt=prompt,
                    stream=False
                )
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

def call_llm(model, prompt,tipo):
    return {
        "model": model,
        "prompt": prompt,
        "stream": False,
        "options": {
            "temperature": 0.3 if tipo == "grammatica" else 0.7 
            # Temperatura bassa = precisione (grammatica)
            # Temperatura alta = creatività (email/miglioramento)
        }
    }


## Prompt Specialistici v2
def get_specialized_prompt(testo_utente, task):
    if task == "grammatica":
        return f"Sei un correttore di bozze esperto. Analizza il testo seguente, correggi errori grammaticali, di punteggiatura e ortografia. Restituisci il testo corretto.\n\nTesto: {testo_utente}"
    elif task == "miglioramento":
        return f"Sei un editor professionista. Riscrivi il testo seguente per renderlo più formale, fluido e persuasivo: {testo_utente}"
    elif task == "traduci":
        return f"Agisci come un traduttore professionista madrelingua. Traduci il testo seguente in inglese: {testo_utente}"
    return testo_utente


def get_specialized_model(task):
    if task == "grammatica":
        return "llama3.2:3b"
    elif task == "miglioramento":
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
