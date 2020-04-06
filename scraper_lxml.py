import re
import requests
import lxml.html
from itertools import chain


ERR_STRING = "We hebben geen vertalingen voor"
# UITDRUKKING_DEEL = "deel van de uitdrukking"
UITDRUKKING_DEEL = '<a onClick="shoh'


def _join_with_br(l):
    return "<br>".join(l)


def _get_table_row_bgcolor(ct):
    if ct % 2 == 0:
        return '#FFFFFF'
    else:
        return '#FFF8DC'


def _get_html_table(list_of_columnes):
    rows = [f'<td>{"</td> <td>".join(x)}</td>' for x in zip(*list_of_columnes)]
    columns = [f'<tr bgcolor="{_get_table_row_bgcolor(ct)}">{row}</tr>' for ct, row in enumerate(rows)]
    columns = " ".join(columns)
    return f"<table>{columns}</table>"


class NoExplanationException(Exception):
    pass


class ExplanationsDoNotMatchException(Exception):
    pass


class NoExampleException(Exception):
    pass


class ExamplesDoNotMatchException(Exception):
    pass


def get_mwb_html(word):
    url = f"https://www.mijnwoordenboek.nl/vertaal/nl/en/{word}"
    html = requests.get(url)
    return html


class NoteExpression:
    def __init__(self, input_word, html_content):
        self.input_word = input_word

        start_idx = html_content.find(UITDRUKKING_DEEL)
        self.html_content = html_content[start_idx:]
        self.doc = lxml.html.fromstring(self.html_content)

    def parse_expression(self):
        expressions = [
            x.text_content()
            for x in self.doc.xpath(
                '//a[contains(@onclick, "shoh")]/following-sibling::font[1]'
            )
        ]

        equivalents = [
            x.text_content() for x in self.doc.xpath('//font[@style="color:darkgreen"]')
        ]

        translations = [
            x.text_content()
            for x in self.doc.xpath(
                '//font[@style="color:darkgreen"]/following-sibling::font[@style="color:navy"][1]'
            )
        ]

        assert (len(expressions) == len(equivalents)) and (
            len(expressions) == len(translations)
        ), "number of expressions and translations do not match for word [{self.input_word}]"

        return expressions, equivalents, translations

    def parse_examples(self):
        examples_dutch = [
            x.text_content()
            for x in self.doc.xpath(
                '//font[@style="color:darkgreen"]/following-sibling::font[@style="color:#444"]'
            )
        ]
        examples_english = [
            x.text_content()
            for x in self.doc.xpath(
                '//font[@style="color:darkgreen"]/following-sibling::font[@style="color:#444"]/following-sibling::font[@style="color:navy"]'
            )
        ]

        return examples_dutch, examples_english


class NoteDefault:
    def __init__(self, word):
        html = get_mwb_html(word)
        html_content = html.content.decode("utf-8")
        start_idx = html_content.find("NL>EN")
        end_idx = html_content.find("Overige bronnen")

        self.input_word = word
        self.html_content = html_content
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

        return dutch

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

        return misc

    def parse_explanations(self):
        explanations_english = [
            x.text_content()
            for x in self.doc.xpath(f'//div/font[@style="color:navy;font-size:10pt"]')
        ]

        explanations_dutch = [
            x.text_content()
            for x in self.doc.xpath(
                f'//div/font[@style="color:navy;font-size:10pt"]/preceding-sibling::font[1]'
            )
            if not x.text_content()[:-1].isdigit()
        ]

        if (not explanations_english) and (not explanations_dutch):
            raise NoExplanationException(
                f"No default explanations found on mwb for word [{self.input_word}]"
            )
        if len(explanations_english) != len(explanations_dutch):
            raise ExplanationsDoNotMatchException(
                f"Number of Dutch explanations and English explanations do not match each other for word [{self.input_word}]"
            )

        return explanations_dutch, explanations_english

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
            raise NoExampleException(
                f"No example sentences found for word [{self.input_word}]"
            )
        if len(examples_english) != len(examples_dutch):
            raise ExamplesDoNotMatchException(
                f"Examples do not have matchin Dutch and Endlish translations for word [{self.input_word}]"
            )

        return examples_dutch, examples_english

    def generate_notes(self):
        if ERR_STRING in self.doc.text_content():
            return None

        dutch = self.parse_dutch_word()
        misc = self.parse_misc()

        try:
            explanations_dutch, explanations_english = self.parse_explanations()
        except NoExplanationException:
            (
                explanations_dutch,
                explanations_english,
            ) = self.parse_explanations_other_sources()

        try:
            examples_dutch, examples_english = self.parse_examples()
        except NoExampleException:
            examples_dutch, examples_english = self.parse_examples_other_sources()

        if UITDRUKKING_DEEL in self.html_content:
            uitdrukking = NoteExpression(self.input_word, self.html_content)
            expressions, equivalents, translations = uitdrukking.parse_expression()
            u_examples_dutch, u_examples_english = uitdrukking.parse_examples()

            explanations = _get_html_table(
                [explanations_dutch, explanations_english]
            ) + _get_html_table([expressions, equivalents, translations])
            examples = _get_html_table(
                [
                    examples_dutch + u_examples_dutch,
                    examples_english + u_examples_english,
                ]
            )
        else:
            explanations = _get_html_table([explanations_dutch, explanations_english])
            examples = _get_html_table([examples_dutch, examples_english])

        notefields = {
            "Dutch": dutch,
            "Misc": misc,
            "Explanations": explanations,
            "Examples": examples,
        }
        return notefields

    def parse_explanations_other_sources(self):
        start_idx = self.html_content.find("Overige bronnen")
        other_sources = lxml.html.fromstring(self.html_content[start_idx:])

        xpath_english = '//table[@border=0]/tr/td[@style="padding-left:20px"]'
        explanations_english = [
            x.text_content() for x in other_sources.xpath(xpath_english)
        ]
        explanations_dutch = [
            x.text_content()
            for x in other_sources.xpath(f"{xpath_english}/preceding-sibling::*")
        ]

        if (not explanations_english) and (not explanations_dutch):
            raise NoExplanationException(
                f"No explanations found in other sources for word [{self.input_word}]"
            )
        if len(explanations_english) != len(explanations_dutch):
            raise ExplanationsDoNotMatchException(
                f"Number of Dutch explanations and English explanations in other sources do not match each other for word [{self.input_word}]"
            )

        return explanations_dutch, explanations_english

    def parse_examples_other_sources(self, num_examples=5):
        start_idx = self.html_content.find("Voorbeeldzinnen met `")
        other_examples = lxml.html.fromstring(self.html_content[start_idx:])

        examples_url = [
            x.text_content()
            for x in other_examples.xpath("//script[contains(., load)]")
            if "zinnendiv" in x.text_content()
        ][0]
        examples_url = examples_url.split('load("')[-1].split('");')[0]

        html_content = requests.get(examples_url).content.decode("utf-8")
        doc = lxml.html.fromstring(html_content)

        examples = [x.text_content() for x in doc.xpath("//ol/li")]
        examples = [e[5:].split(" EN: ") for e in examples][
            : min(len(examples), num_examples)
        ]
        examples_dutch = [e[0] for e in examples]
        examples_english = [e[1] for e in examples]

        if (not examples_english) and (not examples_dutch):
            raise NoExampleException(
                f"No example sentences found in other sources for word [{self.input_word}]"
            )

        return examples_dutch, examples_english


def get_note_simple(word):
    html = get_mwb_html(word)
    doc = lxml.html.fromstring(html.content)

    if ERR_STRING in doc.text_content():
        return None

    dutch = doc.xpath("//table[@border=0]/tr[1]/td[1]")[0].text_content()
    explanations = doc.xpath("//table[@border=0]/tr[1]/td[2]")[0].text_content()

    notefields = {"Dutch": dutch, "Explanations": explanations}
    return notefields
