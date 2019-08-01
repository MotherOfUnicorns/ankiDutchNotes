from mwb_help import deck_is_available, create_deck,\
    model_is_available, add_model, add_note
from scraper_lxml import get_note_default, get_note_simple


class AnkiDutchDeck():

    def __init__(self, deck_name=None):
        if deck_name is None:
            deck_name = 'tidbits'
        if not deck_is_available(deck_name):
            create_deck(deck_name)
        self.deck_name = deck_name

        self.default_model_name = 'dutch_default'
        self.simple_model_name = 'dutch_simple'

        if not model_is_available(self.default_model_name):
            self.add_model_default()
        if not model_is_available(self.simple_model_name):
            self.add_model_simple()

    def add_model_default(self):
        model_name = 'dutch_default'
        note_fields = ['Dutch', 'Misc', 'Explanations', 'Examples']
        card_templates = [{'Front': '{{Dutch}}',
                           'Back' : '{{Misc}}<hr><hr>{{Explanations}}'},
                          {'Front': '{{Dutch}}<hr>{{Misc}}',
                           'Back' : '{{Explanations}}<hr><hr>{{Examples}}'},
                          {'Front': '{{Explanations}}',
                           'Back' : '{{Dutch}}<hr>{{Misc}}<hr><hr>{{Examples}}'},
                          {'Front': '{{Examples}}',
                           'Back' : '{{Dutch}}<hr>{{Misc}}<hr><hr>{{Explanations}}'}]
        add_model(model_name, note_fields, card_templates)

    def add_model_simple(self):
        model_name = 'dutch_simple'
        note_fields = ['Dutch', 'Explanations']
        card_templates = [{'Front': '{{Dutch}}',
                           'Back' : '{{Explanations}}'},
                          {'Front': '{{Explanations}}',
                           'Back' : '{{Dutch}}'}]
        add_model(model_name, note_fields, card_templates)

    def add_note_default(self, note_fields):
        add_note(note_fields, self.deck_name, self.default_model_name)

    def add_note_simple(self, note_fields):
        add_note(note_fields, self.deck_name, self.simple_model_name)

    def add_note_from_word(self, word):
        is_default_model = True
        try:
            note_fields = get_note_default(word)
            if note_fields is None:
                print(f'"{word}" not found in mijnwoordenbook')
                return
        except:
            is_default_model = False
            note_fields = get_note_simple(word)

        try:
            if is_default_model:
                self.add_note_default(note_fields)
            else:
                self.add_note_simple(note_fields)
        except:
            print(f'"{word}" already exists in the deck')

    def add_note_from_list(self, word_list):
        [self.add_note_from_word(w) for w in word_list]


if __name__ == '__main__':
    word_list = ['hhhsss', 'duits', 'alsjeblieft', 'waterpokken']
    ADD = AnkiDutchDeck()
    ADD.add_note_from_list(word_list)
