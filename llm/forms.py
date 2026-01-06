from django import forms
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Submit, Row, Column
from .models import LLMResult

class LlmForm(forms.ModelForm):
    # Choices for the type of LLM task
    TIPO_CHOICES = [
        ('grammatica', 'Analisi Grammaticale'),
        ('miglioramento', 'Miglioramento Testo'),
        ('traduci', 'Traduzione Professionale'),
    ]

    tipo_operazione = forms.ChoiceField(
        choices=TIPO_CHOICES, 
        label="Cosa vuoi fare?",
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    
    #n_min_lettere = forms.IntegerField(
    #    min_value=0, 
    #    max_value=10, 
    #    initial=3, 
    #    label="Ignora termini più corti di (n. lettere):",
    #    widget=forms.NumberInput(attrs={'class': 'form-control'})
    #)

    class Meta:
        model = LLMResult
        fields = ['tipo_operazione']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_method = 'post'
        self.helper.layout = Layout(
            Row(
                Column('tipo_operazione', css_class='form-group col-md-6 mb-0'),
                css_class='form-row'
            ),
            Submit('submit', 'Avvia Analisi AI', css_class='btn btn-primary mt-3')
        )

class LlmEmptyForm(forms.Form):
    # Choices for the type of LLM task
    TIPO_CHOICES = [
        ('grammatica', 'Analisi Grammaticale'),
        ('miglioramento', 'Miglioramento Testo'),
        ('traduci', 'Traduzione Professionale'),
    ]

    tipo_operazione = forms.ChoiceField(
        choices=TIPO_CHOICES, 
        label="Cosa vuoi fare?",
        widget=forms.Select(attrs={'class': 'form-select'})
    )

    text = forms.CharField(
        label="Istruzioni aggiuntive o Testo custom (opzionale)",
        widget=forms.Textarea(attrs={
            'class': 'form-control', 
            'rows': 4, 
            'placeholder': 'Inserisci qui eventuali istruzioni specifiche per l\'IA...'
        }),
        required=False
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_method = 'post'
        self.helper.layout = Layout(
            Row(
                Column('tipo_operazione', css_class='form-group col-12 mb-3'),
                Column('text', css_class='form-group col-12 mb-3'),
                css_class='form-row'
            ),
            Submit('submit', 'Avvia Analisi AI', css_class='btn btn-primary w-100')
        )
