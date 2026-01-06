import nltk
from nltk.corpus import stopwords, wordnet as wn
from collections import Counter
import string
import re


class TextElaborator:
    """
    Classe per:
    - tokenizzazione
    - rimozione stopword
    - calcolo frequenze
    - calcolo complessità testuale
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

    # ---------------- TOKENIZATION ---------------- #

    def tokenize(self, text: str) -> list[str]:
        return nltk.word_tokenize(text, language="italian")

    # ---------------- CLEANING ---------------- #

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

    # ---------------- STATISTICS ---------------- #

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

    # ---------------- PIPELINE ---------------- #

    def elaborate_text(self, text: str):
        self.count_phrases(text)
        tokens = self.tokenize(text)
        tokens = self.eliminate_stopwords(tokens)
        self.count_occurrences_and_characters(tokens)

    # ---------------- COMPLEXITY ---------------- #

    def calculate_complexity(self) -> float:
        if self.terms_count == 0:
            return 0.0

        common = [
            t for t in self.terms_with_frequency
            if t in self.common_words
        ]
        non_common = [
            t for t in self.terms_with_frequency
            if t not in self.common_words
        ]

        return (
            (0.1579 * len(non_common) / ((len(common) + 1) * 1.5) * 100)
            + (0.0496 * (self.terms_count / self.phrases_number))
        )
