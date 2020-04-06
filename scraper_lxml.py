import re
import requests
import lxml.html
from itertools import chain


ERR_STRING = "We hebben geen vertalingen voor"
UITDRUKKING_DEEL = "deel van de uitdrukking"


def _join_with_br(l):
    return "<br>".join(l)


def _get_html_table(dutch, english):
    rows = [f"<td>{d}</td>  <td>{e}</td>" for d, e in zip(dutch, english)]
    columns = [f"<tr>{row}</tr>" for row in rows]
    columns = " ".join(columns)
    return f"<table>{columns}</table>"


def get_mwb_html(word):
    url = f"https://www.mijnwoordenboek.nl/vertaal/nl/en/{word}"
    html = requests.get(url)
    return html


class NoteDefault:
    # TODO seperate uitdrukking

    def __init__(self, word):
        html = get_mwb_html(word)
        html_content = html.content.decode("utf-8")
        start_idx = html_content.find("NL>EN")
        end_idx = html_content.find("Overige bronnen")
        self.doc = lxml.html.fromstring(html_content[start_idx:end_idx])

    def parse_dutch_word(self):
        sections = self.doc.xpath(f'//div/h2[@class="inline"]')
        # combine multiple entries when one word have different parts of speech
        if len(sections) > 1:
            dutch = "; ".join(
                [" ".join(sec.text_content().split()[1:]) for sec in sections]
            )
        else:
            dutch = sections[0].text_content()

        self.dutch = dutch

    def parse_misc(self):
        part_of_speech = self.doc.xpath(f'//div/h2[@class="inline"]/parent::*/text()')
        part_of_speech = [
            x.strip()
            for x in part_of_speech
            if (not x.isspace()) and (x.strip() != "-")
        ]
        part_of_speech = "; ".join(part_of_speech)

        # pronunciation and plurals (for nouns) / conjugations (for verbs)
        misc = [
            x.text_content()
            for x in self.doc.xpath(
                f'//div/h2[@class="inline"]/following-sibling::table[1]/tr'
            )
        ]
        misc = list({x.replace("\xa0", " ") for x in misc})
        misc.sort()
        misc = _join_with_br([part_of_speech] + misc)

        self.misc = misc

    def parse_explanations(self):
        explanations_english = [
            x.text_content()
            for x in self.doc.xpath(f'//div/font[@style="color:navy;font-size:10pt"]')
        ]
        # TODO if this is empty (eg for maling, use other sources)

        explanations_dutch = [
            x.text_content()
            for x in self.doc.xpath(
                f'//div/font[@style="color:navy;font-size:10pt"]/preceding-sibling::font[1]'
            )
            if not x.text_content()[:-1].isdigit()
        ]

        if (not explanations_english) and (not explanations_dutch):
            raise Exception
        if len(explanations_english) != len(explanations_dutch):
            raise Exception
        explanations = _get_html_table(explanations_dutch, explanations_english)

        self.explanations = explanations

    def parse_examples(self):
        examples_dutch = [
            x.text_content()
            for x in self.doc.xpath(f'//i/font[@style="color:#422526"]')
        ]
        examples_english = [
            x.text_content()
            for x in self.doc.xpath(f'//i/following-sibling::font[@style="color:navy"]')
        ]

        if (not examples_english) and (not examples_dutch):
            raise Exception
        if len(examples_english) != len(examples_dutch):
            raise Exception
        examples = _get_html_table(examples_dutch, examples_english)

        self.examples = examples

    def generate_notes(self):
        if ERR_STRING in self.doc.text_content():
            return None

        self.parse_dutch_word()
        self.parse_misc()
        self.parse_explanations()
        self.parse_examples()

        notefields = {
            "Dutch": self.dutch,
            "Misc": self.misc,
            "Explanations": self.explanations,
            "Examples": self.examples,
        }
        return notefields


def get_note_simple(word):
    html = get_mwb_html(word)
    doc = lxml.html.fromstring(html.content)

    if ERR_STRING in doc.text_content():
        return None

    dutch = doc.xpath("//table[@border=0]/tr[1]/td[1]")[0].text_content()
    explanations = doc.xpath("//table[@border=0]/tr[1]/td[2]")[0].text_content()

    notefields = {"Dutch": dutch, "Explanations": explanations}
    return notefields
