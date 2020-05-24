import os
import re
import json
import pymorphy2


from string import ascii_letters

class Normalizer():
    def __init__(self):
        self._morph_analyzer = pymorphy2.MorphAnalyzer()

        self._stop_words = self._read_stop_words()
        self._parts_of_speech_to_remove = ['NUMR', 'NPRO', 'PREP']

    def normalize_text(self, text):
        # Удаляем стоп-слова
        cleaned_text = list()

        for word in re.findall(r'\w+', text):
            if not self._contains_latin_letter(word) and word.isalpha():
              word_parser = self._morph_analyzer.parse(word)[0]
              normal_word = word_parser.normal_form
              if not word_parser.tag.POS in self._parts_of_speech_to_remove and\
                    not self._is_stop_word(normal_word):
                  cleaned_text.append(normal_word)

        return ' '.join(cleaned_text).strip()

    @staticmethod
    def _contains_latin_letter(word):
        if word:
            return all(map(lambda c: c in ascii_letters, word))
    
    def _read_stop_words(self):
        if os.path.exists("for_adis/classes/data/stop_words.json"):
            with open("for_adis/classes/data/stop_words.json", 'r', encoding='utf-8') as file:
                return json.load(file)

    def _is_stop_word(self, word):
        word = f' {word} '

        for stop_words in self._stop_words:
            if word in stop_words:
                return True

        return False