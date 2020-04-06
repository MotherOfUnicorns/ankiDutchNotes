from anki_helpers import (
    update_note,
    find_all_notes_in_deck,
    get_note_by_id,
)
from scraper_lxml import get_note_default, get_note_simple

# TODO rename get_note_default to generate_default_note


def update_existing_note_in_deck(note_id, deck_name):

    old_note = get_note_by_id(note_id)

    word = old_note["fields"]["Dutch"]["value"]
    word = word.split(";")[0]

    try:
        new_note = get_note_default(word)
        model_name = "dutch_default"
    except:
        new_note = get_note_simple(word)
        model_name = "dutch_simple"

    update_note(new_note, deck_name, model_name)
    print(f"succesfully updated word [{word}]")


if __name__ == "__main__":
    deck_name = "tttest"
    all_notes_id = find_all_notes_in_deck(deck_name)
    for note_id in all_notes_id:
        try:
            update_existing_note_in_deck(note_id, deck_name)
        except Exception as e:
            print(f"failed for {note_id}", e)
