ankiDutchNotes
======
Automatically creates anki notes with contents scraped from mijnwoordenboek.nl.


requirements
------
* Python 3.6+
* Anki 2.1+
* [AnkiConnect](https://ankiweb.net/shared/info/2055492159) add-on installed on your Anki



how-to
------
* If you have a text file containing new Dutch words separated by new lines, add them with
`python add_cards.py -f some_file_containing_your_words.txt`
* Or type in the list in command line with
`python add_cards.py -l woord1,woord2,woord3`
* Use `-o output_file_name.txt` in case this tool wasn't able to find some words in mijnwoordenbook.nl, and you still want to save those words somewhere so you can go over them later.


misc
------
Supports mac and linux, probably also windows


update Apr 06, 2020
------
* fixed bug where some newlines are missing between different example sentences
* added prettier html format
* added `update_notes.py` script for updating existing cards to the new prettier format. Usage:
    - `python update_notes.py -d [deck_name]` to update notes in the specified deck
    - use the `-o [output_file_name]` flag to store failed updates in a file
