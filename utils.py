def join_with_br(l):
    return "<br>".join(l)


def _get_table_row_bgcolor(ct):
    if ct % 2 == 0:
        return "#FFFFFF"
    else:
        return "#FFF8DC"


def get_html_table(list_of_columnes):
    col_width = 100 // len(list_of_columnes)
    rows = [f'</td> <td width="{col_width}%">'.join(x) for x in zip(*list_of_columnes)]
    rows = [f'<td width="{col_width}%"> {r} </td>' for r in rows]
    columns = [
        f'<tr bgcolor="{_get_table_row_bgcolor(ct)}">{row}</tr>'
        for ct, row in enumerate(rows)
    ]
    columns = " ".join(columns)
    return f'<table align="left">{columns}</table>'


def pad_list(input_list, target_length):
    input_length = len(input_list)
    assert target_length >= input_length, "target length should be longer than input"

    if input_length == target_length:
        return input_list

    return input_list + [""] * (target_length - input_length)


class NoExplanationException(Exception):
    pass


class NoExampleException(Exception):
    pass
