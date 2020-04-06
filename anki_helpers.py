import json
from urllib.request import urlopen, Request
from urllib.parse import quote, urlencode
from difflib import SequenceMatcher


ANKICONN_VERSION = 6
ANKICONN_HOST = "http://localhost:8765"


def generate_ankiconnect_json_request(action, **params):
    request_dict = {"action": action, "params": params, "version": ANKICONN_VERSION}
    request_json = json.dumps(request_dict)
    return request_json


def invoke(action, url=None, **params):
    if url is None:
        url = ANKICONN_HOST

    request_json = generate_ankiconnect_json_request(action, **params)
    request_json = str.encode(request_json)

    with urlopen(Request(url, request_json)) as u:
        response = json.load(u)

    if len(response) != 2:
        raise Exception("response has an unexpected number of fields")
    if "error" not in response:
        raise Exception("response is missing required error field")
    if "result" not in response:
        raise Exception("response is missing required result field")
    if response["error"] is not None:
        raise Exception(response["error"])
    return response["result"]


def check_version():
    result = invoke("version")
    assert result == ANKICONN_VERSION, "supported version is {}".format(
        result["version"]
    )


def deck_is_available(deck_name):
    result = invoke("deckNames")
    return deck_name in result


def create_deck(deck_name, verbose=False):
    result = invoke("createDeck", deck=deck_name)

    if verbose:
        deck_names = invoke("deckNames")
        print("got list of decks: {}".format(deck_names))
        return result

    return result


def model_is_available(model_name):
    result = invoke("modelNames")
    return model_name in result


def add_model(model_name, note_fields, card_templates):
    result = invoke(
        "createModel",
        modelName=model_name,
        inOrderFields=note_fields,
        cardTemplates=card_templates,
    )
    return result


def add_note(note_fields, deck_name, model_name):
    note_content = dict(
        deckName=deck_name,
        modelName=model_name,
        fields=note_fields,
        options=dict(allowDuplicate=False),
        tags=["dutch"],
    )
    result = invoke("addNote", note=note_content)


def get_note_by_id(note_id):
    results = invoke("notesInfo", notes=[note_id])
    return results[0]


def find_all_notes_in_deck(deck_name):
    results = invoke("findNotes", query=f"deck:{deck_name}")
    return results


def find_note_by_word(word, deck_name):
    results = invoke("findNotes", query=f"deck:{deck_name} {word}")

    if not results:
        return

    if len(results) == 1:
        return results[0]

    note_names = [
        get_note_by_id(note_id)["fields"]["Dutch"]["value"] for note_id in results
    ]
    similarities = [
        SequenceMatcher(None, word, note_name).ratio() for note_name in note_names
    ]
    results_sorted_by_similarity = sorted(
        list(zip(results, similarities)), key=lambda x: x[1]
    )
    return results_sorted_by_similarity[-1][0]


def update_note(note_fields, deck_name, model_name, note_id=None):

    if note_id is None:
        note_id = find_note_by_word(note_fields["Dutch"], deck_name)

    results = invoke("updateNoteFields", note={"id": note_id, "fields": note_fields})
    return results


if __name__ == "__main__":
    check_version()
