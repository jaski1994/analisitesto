import nltk
from nltk.corpus import stopwords
from collections import Counter
import string
import re
import json
import asyncio
from spellchecker import SpellChecker
from llm.llmManager import LLMManager
from langdetect import detect


class TextElaborator:
    """
    Classe per:
    - tokenizzazione
    - rimozione stopword
    - calcolo frequenze
    - calcolo complessità testuale
    - scoring avanzato (Gulpease, TTR, AI Rating, ecc.)
    """

    def __init__(self, chars_to_avoid=0, common_words=None):
        self.chars_to_avoid = chars_to_avoid
        self.common_words = set(common_words) if common_words else set()

        self.stopwords_it = set(stopwords.words("italian"))
        self.symbols = set(string.punctuation).union({"''", "``", "...", "..", "–", "—"})

        # statistiche
        self.terms_count = 0
        self.terms_with_frequency = {}
        self.average_frequency = 0
        self.phrases_number = 0
        self.characters_count = 0

    @property
    def _common_words(self):
        return list(self.common_words)

    @_common_words.setter
    def _common_words(self, value):
        self.common_words = set(value) if value else set()

    def calculate_complexity(self):
        """
        Alias for check_dale_chall for backward compatibility.
        """
        return self.check_dale_chall()

    def detect_language(self, text: str) -> str:
        try:
            return detect(text)
        except Exception:
            return "it"

    def tokenize(self, text: str) -> list[str]:
        return nltk.word_tokenize(text, language="italian")

    def eliminate_stopwords(self, tokens: list[str]) -> list[str]:
        clean_list = []
        for t in tokens:
            t_low = t.lower()
            # 1. Check if it's a stopword or a known symbol
            if t_low in self.stopwords_it or t in self.symbols:
                continue
            
            # 2. Check if it's a number (including decimals)
            if re.match(r'^-?\d+(?:\.\d+)?$', t):
                continue
                
            # 3. Final check: ignore if it's purely punctuation missed by set
            if all(char in string.punctuation for char in t):
                continue

            clean_list.append(t_low)
        return clean_list

    def count_phrases(self, text: str):
        self.phrases_number = sum(text.count(p) for p in ".?!")
        return max(self.phrases_number, 1)

    def count_occurrences_and_characters(self, tokens: list[str]) -> list[str]:
        clean_tokens = [
            t for t in tokens
            if len(t) > self.chars_to_avoid and t not in {"..", "..."}
        ]

        self.characters_count = sum(len(t) for t in clean_tokens)
        self.terms_with_frequency = dict(Counter(clean_tokens))
        self.terms_count = len(clean_tokens)

        if self.terms_with_frequency:
            self.average_frequency = round(
                self.terms_count / len(self.terms_with_frequency)
            )
        else:
            self.average_frequency = 0

        return clean_tokens

    def elaborate_text(self, text: str):
        self.count_phrases(text)
        tokens = self.tokenize(text)
        tokens = self.eliminate_stopwords(tokens)
        self.count_occurrences_and_characters(tokens)


    def check_dale_chall(self) -> float:
        """
        Calcola l'indice di leggibilità Dale-Chall.
        Formula: 0.1579 * (numero_parole_non_comuni / numero_parole_comuni) * 100 + 0.0496 * (numero_parole / numero_frasi)
        """ 
        if self.terms_count == 0:
            return 0.0

        common = []
        non_common = []
        for t in self.terms_with_frequency:
            if t in self.common_words:
                common.append(t)
            else:
                non_common.append(t)
        
        return (
            (0.1579 * len(non_common) / ((len(common) + 1) * 1.5) * 100)
            + (0.0496 * (self.terms_count / self.phrases_number))
        )


    def get_gulpease(self, text):
        """
        Calcola l'indice di leggibilità Gulpease.
        Formula: 89 + (300 * numero_frasi - 10 * numero_lettere) / numero_parole
        """
        if not text:
            return 0
        
        sentences = nltk.sent_tokenize(text, language='italian')
        words = self.tokenize(text)
        
        num_sentences = len(sentences)
        # Conteggio lettere preciso (spazi esclusi)
        num_letters = sum(len(word) for word in words if word.isalnum())
        # Conteggio parole (token alfanumerici)
        num_words = len([word for word in words if word.isalnum()])
        
        if num_words == 0:
            return 0
            
        score = 89 + (((300 * num_sentences) - (10 * num_letters)) / num_words)
        return max(0, min(100, score)) # Limitiamo tra 0 e 100

    def get_vocab_score(self, text):
        """
        Calcola la diversità lessicale (TTR).
        """
        if not text:
            return 0
        tokens = self.tokenize(text)
        # Filtro punteggiatura
        tokens = [t for t in tokens if t.isalnum()]
        
        if not tokens:
            return 0
            
        unique = set(tokens)
        ttr = len(unique) / len(tokens)
        return ttr

    def get_spelling_score(self, text):
        """
        Calcola un punteggio basato sugli errori ortografici.
        """
        if not text:
            return 0
            
        spell = SpellChecker(language='it')
        # Pulizia base: rimuovi punteggiatura
        translator = str.maketrans('', '', string.punctuation)
        clean_text = text.translate(translator)
        words = clean_text.split()
        
        if not words:
            return 10 
            
        misspelled = spell.unknown(words)
        error_rate = len(misspelled) / len(words)
        
        return max(0, 1 - error_rate) * 10

    def get_clarity_score(self, text):
        """
        Calcola chiarezza basata sulla lunghezza media delle frasi.
        """
        if not text:
            return 0
            
        sentences = nltk.sent_tokenize(text, language='italian')
        if not sentences:
            return 0
            
        # Lunghezza media in parole
        avg_len = sum(len(s.split()) for s in sentences) / len(sentences)

        if avg_len < 20:
            return 9
        elif avg_len < 30:
            return 7
        else:
            return 4

    async def get_ai_analysis_async(self, text):
        """
        Richiede a Ollama un'analisi grammaticale e stilistica in JSON.
        """
        prompt = f"""
            Analyze the following Italian text and provide a structured assessment in JSON format.
            Return ONLY the JSON, no other text.
            JSON structure:
            {{
            "grammar": <score 0-10>,
            "clarity": <score 0-10>,
            "coherence": <score 0-10>,
            "comment": "<short comment string>"
            }}

            Text:
            {text}
            """
        manager = LLMManager()
        try:
            response_obj = await manager.call_the_llm(model="llama3.2:3b", prompt=prompt, options={"temperature": 0.2, "num_predict": 200})
            
            if isinstance(response_obj, dict):
                content = response_obj.get('response', '')
            else:
                content = str(response_obj)
                
            # Pulizia JSON
            json_str = content
            if "```json" in json_str:
                json_str = json_str.split("```json")[1].split("```")[0].strip()
            elif "```" in json_str:
                json_str = json_str.split("```")[1].split("```")[0].strip()
                
            start = json_str.find('{')
            end = json_str.rfind('}') + 1
            if start != -1 and end != -1:
                json_str = json_str[start:end]
                
            data = json.loads(json_str)
            return data
        except Exception as e:
            print(f"Error calling LLM: {e}")
            return {"grammar": 5, "clarity": 5, "coherence": 5, "comment": "Error connecting to AI"}

    def call_ollama_for_rating(self, text):
        """
        Wrapper sincrono per ottenere il rating AI (media dei punteggi).
        """
        try:
            data = asyncio.run(self.get_ai_analysis_async(text))
            
            g = float(data.get('grammar', 0))
            c = float(data.get('clarity', 0))
            co = float(data.get('coherence', 0))
            avg = (g + c + co) / 3.0
            return avg
        except Exception as e:
            print(f"Error in call_ollama_for_rating: {e}")
            return 5.0 

    def calculate_score(self, text):
        """
        Calcola il punteggio finale composito.
        """
        # 1. Calcola Leggibilità (Gulpease) 0-100
        readability = self.get_gulpease(text)
        
        # 2. Calcola Diversità Lessicale (TTR) 0-1
        ttr = self.get_vocab_score(text)
        
        # 3. Chiedi a Ollama (0-10)
        ai_rating = self.call_ollama_for_rating(text)
        
        # Formula finale
        final_score = (readability * 0.25) + (ttr * 100 * 0.25) + (ai_rating * 10 * 0.50)
        
        # Punteggi aggiuntivi per report
        spelling = self.get_spelling_score(text)
        clarity_nltk = self.get_clarity_score(text)
        
        return {
            "final_score": round(final_score, 2),
            "readability_gulpease": round(readability, 2),
            "lexical_diversity": round(ttr, 2),
            "ai_rating": round(ai_rating, 2),
            "spelling_score": round(spelling, 2),
            "clarity_score_nltk": clarity_nltk
        }

# Module-level wrapper for backward compatibility
def calculate_score(text):
    elaborator = TextElaborator()
    return elaborator.calculate_score(text)
