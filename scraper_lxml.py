import re
import requests
import lxml.html
from itertools import chain


ERR_STRING = "We hebben geen vertalingen voor"
UITDRUKKING_DEEL = "deel van de uitdrukking"
PARENT_SELECTOR = "div"  # [@class="slider-wrap"]'


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


def get_note_default(word):
    html = get_mwb_html(word)
    html_content = html.content.decode("utf-8")
    start_idx = html_content.find("NL>EN")
    end_idx = html_content.find("Overige bronnen")
    doc = lxml.html.fromstring(html_content[start_idx:end_idx])
    # doc = lxml.html.fromstring(html.content)

    if ERR_STRING in doc.text_content():
        return None

    sections = doc.xpath(f'//{PARENT_SELECTOR}/h2[@class="inline"]')
    # combine multiple entries when one word have different parts of speech
    if len(sections) > 1:
        dutch = "; ".join(
            [" ".join(sec.text_content().split()[1:]) for sec in sections]
        )
    else:
        dutch = sections[0].text_content()

    part_of_speech = doc.xpath(
        f'//{PARENT_SELECTOR}/h2[@class="inline"]/parent::*/text()'
    )
    part_of_speech = [
        x.strip() for x in part_of_speech if (not x.isspace()) and (x.strip() != "-")
    ]
    part_of_speech = "; ".join(part_of_speech)

    # pronunciation and plurals (for nouns) / conjugations (for verbs)
    misc = [
        x.text_content()
        for x in doc.xpath(
            f'//{PARENT_SELECTOR}/h2[@class="inline"]/following-sibling::table[1]/tr'
        )
    ]
    misc = list({x.replace("\xa0", " ") for x in misc})
    misc.sort()
    misc = _join_with_br([part_of_speech] + misc)

    explanations_english = [
        x.text_content()
        for x in doc.xpath(
            f'//{PARENT_SELECTOR}/font[@style="color:navy;font-size:10pt"]'
        )
    ]
    # TODO if this is empty (eg for maling, use other sources)

    explanations_dutch = [
        x.text_content()
        for x in doc.xpath(
            f'//{PARENT_SELECTOR}/font[@style="color:navy;font-size:10pt"]/preceding-sibling::font[1]'
        )
        if not x.text_content()[:-1].isdigit()
    ]

    if (not explanations_english) and (not explanations_dutch):
        raise Exception
    if len(explanations_english) != len(explanations_dutch):
        raise Exception
    explanations = _get_html_table(explanations_dutch, explanations_english)

    examples_dutch = [
        x.text_content() for x in doc.xpath(f'//i/font[@style="color:#422526"]')
    ]
    examples_english = [
        x.text_content()
        for x in doc.xpath(f'//i/following-sibling::font[@style="color:navy"]')
    ]

    if (not examples_english) and (not examples_dutch):
        raise Exception
    if len(examples_english) != len(examples_dutch):
        raise Exception
    examples = _get_html_table(examples_dutch, examples_english)

    # TODO seperate uitdrukking

    notefields = {
        "Dutch": dutch,
        "Misc": misc,
        "Explanations": explanations,
        "Examples": examples,
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
