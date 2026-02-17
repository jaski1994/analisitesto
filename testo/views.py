import os
import re
from math import floor
from os import truncate
from urllib import request
from django.contrib.auth import user_logged_out, authenticate, login
from django.db.models.functions import Length
from django.shortcuts import render, redirect, get_object_or_404, get_list_or_404
from django.urls import reverse, reverse_lazy
from django.utils.decorators import method_decorator
from django.views.generic import DeleteView
from django_tables2 import SingleTableView, TemplateColumn, RequestConfig
from django.contrib.auth.decorators import login_required
from django.contrib import auth
from django.contrib.auth.models import AnonymousUser, User
from datetime import datetime
from django_tables2.utils import A
from nltk.lm.vocabulary import _
from django.http import HttpResponse
from django.views.decorators.clickjacking import xframe_options_exempt
from .forms import ArticoloForm, ArticoloSearchForm, RegisterForm, BlacklistForm
from .elaborate_text import Text_elaborator
from .elaborate_text_v2 import TextElaborator
from django.db.models import Q
import django_tables2 as tables
from django.contrib import messages
from django_tables2 import RequestConfig,CheckBoxColumn

# Create your views here.
from testo.models import Articolo, Termine, Blacklist
from llm.models import LLMResult

# llm 
from llm.llmManager import LLMManager

def homepage(request):
    """
        homepage, la pagina principale
    """
    return render(request, 'registration/login.html')


@login_required()
def articolo_insert(request):
    """
        Richiesta di inserimento articolo con i vari fields

        Args:
            request (list): con i dati ricevuti dal utente

        Returns:
            basestring : messaggio sul successo dell'inserimento nel db del dato o errore su dati errati
    """
    # importato file parole comuni in italiano ed inserito in lista
    module_dir = os.path.dirname(__file__)  # get current directory
    file_path = os.path.join(module_dir, '1000_parole_italiane_comuni.txt')
    list_common_words = []
    with open(file_path, 'r') as importfile:
        for line in importfile:
            list_common_words.append(line.strip('\n'))

    if request.method == 'POST':
        form = ArticoloForm(request.POST)
        if form.is_valid():
            elaborator = TextElaborator()
            elaborator._common_words = list_common_words
            articolo = form.save(commit=False)
            articolo.data_caricamento = datetime.today().strftime('%Y-%m-%d')
            elaborator.chars_to_avoid = form.cleaned_data.get('n_cart')
            elaborator.elaborate_text(articolo.testo)
            articolo.frequenza_media = elaborator.average_frequency
            articolo.quantita_termini = elaborator.terms_count
            articolo.complessita = elaborator.calculate_complexity()
            
            # Calcolo punteggi avanzati
            scores = elaborator.calculate_score(articolo.testo)
            articolo.readability_score = scores.get('readability_gulpease')
            articolo.lexical_diversity = scores.get('lexical_diversity')
            articolo.spelling_score = scores.get('spelling_score')
            articolo.clarity_score = scores.get('clarity_score_nltk')
            articolo.ai_rating = scores.get('ai_rating')
            articolo.final_score = scores.get('final_score')

            articolo.autore = request.user
            articolo.save()
            # print(elaborator.phrases_number)

            termini_con_frequenze = elaborator.terms_with_frequency
            for [parola, occorrenza] in termini_con_frequenze.items():
                termine = Termine()
                termine.articolo = articolo
                termine.parola = parola
                termine.occorrenze = occorrenza
                termine.save()
            del (elaborator)
            messages.success(request, 'Salvataggio ha avuto successo!')
            return redirect('testo:articolo-details', id=articolo.id)
        else:
            messages.error(request, 'Salvataggio non ha avuto successo!')
    else:
        form = ArticoloForm()
    logged_user_username = request.user.username
    context = {'form': form, 'logged_user_username': logged_user_username}
    return render(request, 'testo/articolo_add.html', context)


@login_required()
def articolo_details(request, id):
    """
    Renderizza la pagina dei dettagli in seguito al click su un risultato di ricerca
    che mostra il grafico , frequenza media e complessità

    Args:
        request: id

    Returns:
        La pagina renderizzata
    """
    # articolo = Articolo.objects.get(id=id)
    articolo = get_object_or_404(Articolo, pk=id)
    llm = LLMResult.objects.filter(articolo_id=id)

    frequenza_media_float = float(articolo.frequenza_media)
    criterio_grafico = floor(frequenza_media_float / 2)
    termini = Termine.objects.filter(articolo_id=id)
    logged_user_username = request.user.username

    # Selezione dei termini e relative occorrenze da visualizzare escludendo quelli presenti nella blacklist
    logged_user_id = request.user.id
    blacklist_utente = Blacklist.objects.filter(id_utente=logged_user_id)
    blacklist_utente_str = list()
    for b in blacklist_utente:
        blacklist_utente_str.append(str(b))

    context = {'articolo': articolo, 'llm': llm,'termini': termini, 'logged_user_username': logged_user_username,
               'criterio_grafico': criterio_grafico, 'blacklist_utente': blacklist_utente_str}
    return render(request, 'testo/articolo_details.html', context)


def register(request):
    """
        Funzione che si occupa della registrazione dell'utente all'interno della piattaforma e gestisce
        anche il processo di login
    """

    if request.method == 'POST':
        form = RegisterForm(request.POST)
        print(form.error_messages)
        if form.is_valid():
            form.save()
            username = form.cleaned_data.get('username')
            email_user = form.cleaned_data.get('email')
            raw_password = form.cleaned_data.get('password1')
            user = authenticate(username=username, email=email_user, password=raw_password)
            login(request, user)
            return redirect('testo:login')
    else:
        form = RegisterForm()
    return render(request, 'register/register.html', {'form': form})


class ResultsTable(tables.Table):
    """
        Definisce tabella personalizzata per visualizzare i risultati della ricerca
    """
    data = tables.DateTimeColumn(format='d/m/Y')
    data_caricamento = tables.DateTimeColumn(format='d/m/Y')

    class Meta:
        model = Articolo
        template_name = "django_tables2/bootstrap4.html"
        fields = ("titolo", "fonte", "data", "autore", "complessita", "data_caricamento")
        attrs = {"class": "table table-striped table-bordered sortable",
                 "data-toggle": "table"
                 }

    detail = TemplateColumn(exclude_from_export=False, template_name='testo/detail.html', orderable=False,
                            verbose_name='')



@login_required()
def translate_termine(request, id_term):
    """
        Funzione che richiama e renderizza la pagina di traduzione passandole il termine da tradurre
        (Google ha impostato delle limitazioni sull’utilizzo del servizio, quindi occorre evitare di
        sovraccaricare il server di richieste traduzione dei termini)

        Args:
             id_term: id del termine da tradurre
    """
    termine = Termine.objects.get(id=id_term)
    logged_user_username = request.user.username
    context = {'termine': termine, 'logged_user_username': logged_user_username}
    return render(request, 'testo/translate_termine.html', context)


def logout(request):
    """
        funzione che si occupa del processo di logout dell'utente
    """
    user = getattr(request, 'user', None)
    if hasattr(user, 'is_authenticated') and not user.is_authenticated():
        user = None
    user_logged_out.send(sender=User.__class__, request=request, user=User)
    request.session.flush()
    if hasattr(request, 'user'):
        request.user = AnonymousUser()

@login_required()
def profile_view(request):
    """
        Visualizza il profilo dell'utente e l'elenco dei testi caricati.
    """
    logged_user_username = request.user.username
    email = request.user.email

    loaded_articles = Articolo.objects.filter(autore=request.user.id)
    table = ProfileTextTable(loaded_articles)
    RequestConfig(request).configure(table)
    
    # Inizializza il manager dell'LLM
    manager = LLMManager() 
    try:
        available_on_disk = {m['name'].removesuffix(":latest") for m in manager.get_available_models() }
        already_loaded = {m['name'].removesuffix(":latest") for m in manager.check_loaded_models()}
    except ConnectionError:
        available_on_disk = set()
        already_loaded = set()
    model_detail = []
    for m in manager.modelsSelected:
        model_detail.append({
            'name': m,
            'onDisk': m in available_on_disk,
            'isLoaded': m in already_loaded
        })
    context = {
        'logged_user_username': logged_user_username,
        'email': email,
        'table': table,
        'available_models': model_detail,
    }
    return render(request, 'testo/profile.html', context)


class ProfileTextTable(tables.Table):
    # Add selection column
    selection = CheckBoxColumn(accessor='pk', attrs={"th__input": {"onclick": "toggle(this)"}, "td__input": {"class": "select-checkbox"}})
    
    data = tables.DateTimeColumn(format='d/m/Y')
    data_caricamento = tables.DateTimeColumn(format='d/m/Y')

    class Meta:
        model = Articolo
        template_name = "django_tables2/bootstrap4.html"
        # Include 'selection' in fields
        fields = ("selection", "titolo", "fonte", "data", "autore", "complessita", "data_caricamento")
        attrs = {"class": "table table-striped table-bordered sortable"}

    llm = TemplateColumn(template_name='testo/llm.html', orderable=False, verbose_name='')
    detail = TemplateColumn(template_name='testo/detail.html', orderable=False, verbose_name='')
    delete = TemplateColumn(template_name='testo/delete.html', orderable=False, verbose_name='')

def articolo_delete(request, id):
    """
        Elimina il testo corrispondente alla riga in cui viene premuto il tasto delete nella pagina che mostra la
        tabella contenente i testi dell'utente attualmente loggato.

        Args:
            id: id dell'articolo

        Returns:
             Ritorna la stessa pagina aggiornata
    """
    Articolo.objects.get(id=id).delete()
    return redirect('testo:profile')

@login_required
def compare_redirect(request):
    if request.method == 'POST':
        # Get list of selected IDs from the checkboxes (named 'selection' in table)
        selected_ids = request.POST.getlist('selection')
        
        if len(selected_ids) == 2:
            return redirect('testo:compare-details', id1=selected_ids[0], id2=selected_ids[1])
        
        messages.error(request, "Seleziona esattamente due testi da comparare.")
    return redirect('testo:profile_view')

@login_required()
def compare_details(request, id1, id2):
    """
        Funzione che si occupa della rappresentazione dei dettagli nella pagina del confronto

    """
    articolo1 = Articolo.objects.get(id=id1)
    articolo2 = Articolo.objects.get(id=id2)
    termini1 = Termine.objects.filter(articolo_id=id1)
    termini2 = Termine.objects.filter(articolo_id=id2)
    logged_user_username = request.user.username

    # Selezione dei termini e relative occorrenze da visualizzare escludendo quelli presenti nella blacklist
    logged_user_id = request.user.id
    blacklist_utente = Blacklist.objects.filter(id_utente=logged_user_id)
    blacklist_utente_str = list()
    for b in blacklist_utente:
        blacklist_utente_str.append(str(b))
    context = {'articolo1': articolo1, 'articolo2': articolo2, 'termini1': termini1, 'termini2': termini2,
               'logged_user_username': logged_user_username, 'blacklist_utente': blacklist_utente_str}

    return render(request, 'testo/compare_details.html', context)


@login_required()
def statistiche_articoli(request):
    """
        Mostra le statistiche su tutti i testi e termini presenti nel database

        Returns:
            render: ritorna la pagina renderizzata
    """
    articoli = Articolo.objects.all()

    # Controllo per gestire il caso in cui non ci siano articoli inseriti
    if articoli.__len__() == 0:
        complessita_media = 0
        quantita_media = 0
        frequenza_media = 0
        autore_max = "-"
        termini_con_frequenze = dict()
        testi_tot = 0
        quantita_totale = 0
        termini = None
    else:
        # Calcolo complessità media per tutti i testi e numero testi
        complessita_totale = 0
        testi_tot = 0
        for articolo in articoli:
            complessita_totale += articolo.complessita
            testi_tot += 1
        complessita_media = round(complessita_totale / articoli.__len__())

        # Calcolo quantità media di termini per tutti i testi
        quantita_totale = 0
        for articolo in articoli:
            quantita_totale += int(articolo.quantita_termini)
        quantita_media = round(quantita_totale / articoli.__len__())

        # Calcolo frequenza media di termini per tutti i testi
        frequenza_totale = 0
        for articolo in articoli:
            frequenza_totale += int(articolo.frequenza_media)
        frequenza_media = round(frequenza_totale / articoli.__len__())

        # Ricerca dell'utente che ha caricato più testi
        autori = list()
        for articolo in articoli:
            autori.append(articolo.autore)
        counter = 0
        autore_max = autori[0]
        for autore_i in autori:
            curr_frequency = autori.count(autore_i)
            if (curr_frequency > counter):
                counter = curr_frequency
                autore_max = autore_i

        # Calcolo frequenza complessiva parole
        termini = Termine.objects.all()
        termini_con_frequenze = dict()
        for termine in termini:
            if (termine.parola not in termini_con_frequenze.keys()):
                termini_con_frequenze[termine.parola] = termine.occorrenze
            else:
                termini_con_frequenze[termine.parola] += termine.occorrenze

    logged_user_username = request.user.username
    context = {'logged_user_username': logged_user_username, 'termini': termini, 'complessita_media': complessita_media,
               'quantita_media': quantita_media, 'frequenza_media': frequenza_media, 'autore_max': autore_max,
               'termini_con_frequenze': termini_con_frequenze, 'testi_tot': testi_tot, 'termini_tot': quantita_totale}
    return render(request, 'testo/statistiche_articoli.html', context)


def blacklist(request):
    """
        Funzione che si occupa della aggiunta delle parole all'interno della blacklist, esegue i controlli
        sulla univocità dei termini, sul fatto che la blacklist sia dedicata all'utente e sul fatto che il
        termine sia già presente all'interno della blacklist

        Returns:
              notifica di errore sull'inserimento dei dati o di successo se l'inserimento avvenuto correttamente
    """

    if request.method == 'POST':
        form = BlacklistForm(request.POST)
        regex = re.compile('[@_!#$%^&*()<>?/\|}{~: ]')
        if regex.search(form.data['termine_bl']) == None:

            check_rex = True
        else:
            check_rex = False

        if form.is_valid() and check_rex and (form.data['termine_bl'] != ""):
            id_utente = request.user
            termine_bl = form.data['termine_bl']
            f = Blacklist(termine_bl=termine_bl, id_utente=id_utente)

            if f.save() != 1:
                messages.success(request, 'Il salvataggio ha avuto successo!')
            else:
                messages.error(request, 'Salvataggio fallito! Il termine è gia presente nella blacklist')
            return redirect('testo:user-blacklist')
        else:
            messages.error(request,
                           'Salvataggio fallito! Hai inserito un termine vuoto o con caratteri speciali. Riprova')
            form = BlacklistForm()

    blacklist = Blacklist.objects.filter(id_utente=request.user)
    logged_user_username = request.user.username
    context = {'blacklist': blacklist, 'logged_user_username': logged_user_username}
    return render(request, 'testo/blacklist.html', context)


def blacklist_delete(request, termine_bl):
    """
        Funzione che si occupa della eliminazione dei termini all'interno della blacklist

        Args:
            termine_bl: termine blacklist
    """

    id_utente = request.user
    Blacklist.objects.get(termine_bl=termine_bl, id_utente=id_utente).delete()
    return redirect('testo:user-blacklist')

@login_required()
def sinonimi_view(request, id_term):
    """
    Vista per i sinonimi

    Args:
        id_term: termine di cui trovare i sinonimi

    Returns:
         pagina dei sinonimi renderizzata
    """
    termine = Termine.objects.get(id=id_term)
    sinonimi = get_synonyms(termine.parola)
    logged_user_username = request.user.username
    context = {'termine': termine, 'logged_user_username': logged_user_username, 'sinonimi': sinonimi}
    return render(request, 'testo/sinonimi.html', context)
