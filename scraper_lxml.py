import requests
import lxml.html
from utils import (
    join_with_br,
    get_html_table,
    pad_list,
    NoExampleException,
    NoExplanationException,
)


ERR_STRING = "We hebben geen vertalingen voor"
# UITDRUKKING_DEEL = "deel van de uitdrukking"
UITDRUKKING_DEEL = '<a onClick="shoh'


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

        # TODO exact match??
        target_length = max(len(expressions), len(equivalents), len(translations))
        expressions = pad_list(expressions, target_length)
        equivalents = pad_list(equivalents, target_length)
        translations = pad_list(translations, target_length)

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

        # TODO exact match??
        target_length = max(len(examples_dutch), len(examples_english))
        examples_english = pad_list(examples_english, target_length)
        examples_dutch = pad_list(examples_dutch, target_length)

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
        misc = join_with_br([part_of_speech] + misc)

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

        # TODO exact match??
        target_length = max(len(explanations_dutch), len(explanations_english))
        explanations_dutch = pad_list(explanations_dutch, target_length)
        explanations_english = pad_list(explanations_english, target_length)

        return explanations_dutch, explanations_english

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

        # TODO exact match??
        target_length = max(len(explanations_dutch), len(explanations_english))
        explanations_english = pad_list(explanations_english, target_length)
        explanations_dutch = pad_list(explanations_dutch, target_length)

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

        # TODO exact match??
        target_length = max(len(examples_english), len(examples_dutch))
        examples_english = pad_list(examples_english, target_length)
        examples_dutch = pad_list(examples_dutch, target_length)

        return examples_dutch, examples_english

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

            explanations = get_html_table(
                [explanations_dutch, explanations_english]
            ) + get_html_table([expressions, equivalents, translations])
            examples = get_html_table(
                [
                    examples_dutch + u_examples_dutch,
                    examples_english + u_examples_english,
                ]
            )
        else:
            explanations = get_html_table([explanations_dutch, explanations_english])
            examples = get_html_table([examples_dutch, examples_english])

        notefields = {
            "Dutch": dutch,
            "Misc": misc,
            "Explanations": '<b>explanations</b><br>' + explanations,
            "Examples": '<b>examples</b><br>' + examples,
        }
        return notefields


def generate_default_note(word):
    n = NoteDefault(word)
    return n.generate_notes()


def generate_simple_note(word):
    html = get_mwb_html(word)
    doc = lxml.html.fromstring(html.content)

    if ERR_STRING in doc.text_content():
        return None

    dutch = doc.xpath("//table[@border=0]/tr[1]/td[1]")[0].text_content()
    explanations = doc.xpath("//table[@border=0]/tr[1]/td[2]")[0].text_content()

    notefields = {"Dutch": dutch, "Explanations": explanations}
    return notefields
