from anki_helpers import (
    update_note,
    find_all_notes_in_deck,
    get_note_by_id,
)
from scraper_lxml import generate_default_note, generate_simple_note


def update_existing_note_in_deck(note_id, deck_name):

    old_note = get_note_by_id(note_id)

    word = old_note["fields"]["Dutch"]["value"]
    word = word.split(";")[0]

    try:
        new_note = generate_default_note(word)
        model_name = "dutch_default"
    except:
        new_note = generate_simple_note(word)
        model_name = "dutch_simple"

    update_note(new_note, deck_name, model_name)
    print(f"succesfully updated word [{word}]")


if __name__ == "__main__":
    import argparse
    import sys

    parser = argparse.ArgumentParser(description="name of anki deck to update")
    parser.add_argument("-d", "--deck", help="name of deck")
    args = parser.parse_args()

    if args.deck is None:
        print("no deck name supplied!")
        sys.exit()

    deck_name = args.deck
    all_notes_id = find_all_notes_in_deck(deck_name)
    for note_id in all_notes_id:
        try:
            update_existing_note_in_deck(note_id, deck_name)
        except Exception as e:
            print(f"failed for {note_id}", e)
