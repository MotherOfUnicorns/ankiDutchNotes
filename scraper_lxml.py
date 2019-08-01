import re
import requests
import lxml.html
from itertools import chain


ERR_STRING = 'We hebben geen vertalingen voor'


def get_mwb_html(word):
    url = f'https://www.mijnwoordenboek.nl/vertaal/nl/en/{word}'
    html = requests.get(url)
    return html

def get_note_default(word):
    html = get_mwb_html(word)
    doc = lxml.html.fromstring(html.content)
    
    if ERR_STRING in doc.text_content():
        return None

    sections = doc.xpath('//h2[@class="inline"]')
    if len(sections) > 1:
        dutch = '; '.join([' '.join(sec.text_content().split()[1:])
                           for sec in sections])
    else:
        dutch = sections[0].text_content()
    
    misc = [x.text_content() for x in doc.xpath('//tr/td[@class="smallcaps"]/..')]
    
    examples = [x.text_content() for x in chain.from_iterable(
        doc.xpath('//table[@cellspacing=0]'))]
    examples = [x for x in examples if x not in misc]
    
    explanations_english = [x.text_content() for x in doc.xpath(
        '//div[@class="slider-wrap"]/font[@style="color:navy;font-size:10pt"]/b')]
    explanations_dutch = [x.text_content() for x in doc.xpath(
        '//div[@class="slider-wrap"]/font[@style="color:#000;font-size:10pt"]/b')
        if not x.text_content()[:-1].isdigit()]
    
    def _join_with_br(l):
        return '<br>'.join(l)
    
    misc = _join_with_br([x.replace(u'\xa0', u' ') for x in misc])
    examples = _join_with_br(examples)
    explanations_english = _join_with_br(explanations_english)
    explanations_dutch = _join_with_br(explanations_dutch)

    explanations = explanations_dutch + '<hr>' + explanations_english

    notefields = {'Dutch': dutch,
                  'Misc': misc,
                  'Explanations': explanations,
                  'Examples': examples}
    return notefields


def get_note_simple(word):
    html = get_mwb_html(word)
    doc = lxml.html.fromstring(html.content)

    if ERR_STRING in doc.text_content():
        return None

    table = doc.xpath('//table[@border=0]/tr')
    dutch = table[0][0].text_content()
    explanations = table[0][1].text_content()

    notefields = {'Dutch': dutch,
                  'Explanations': explanations}
    return notefields



# 
# examples = '<br>'.join([x[0].text_content()
#                       for x in chain.from_iterable(table_contents)])
# 
# explanations = doc.xpath('//div[@class="slider-wrap"]/font/b')
# num_explanatons = int(len(explanations) / 3)
# explanations = '<br>'.join(
#     [' - '.join(
#         [x.text_content() for x in explanations[3 * ct: 3 * (ct + 1)]])
#      for ct in range(num_explanatons)])
# dutch_words = [x.text_content() for x in doc.xpath(
#                 '//h2/font[@style="font-family:times"]')]
# if len(dutch_words) > 1:
#     dutch_words = [word.split()[1:] for word in dutch_words]
# if not categories:
#     note = get_note_default('water')

