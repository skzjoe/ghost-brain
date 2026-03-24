#!/usr/bin/env python3
import os
from xml.sax.saxutils import escape
from zipfile import ZipFile, ZIP_DEFLATED


def col_letter(n: int) -> str:
    out = ''
    while n:
        n, rem = divmod(n - 1, 26)
        out = chr(65 + rem) + out
    return out


def xml_cell(ref: str, value, style=0):
    if value is None:
        return f'<c r="{ref}" s="{style}"/>'
    if isinstance(value, bool):
        return f'<c r="{ref}" s="{style}" t="b"><v>{1 if value else 0}</v></c>'
    if isinstance(value, (int, float)):
        return f'<c r="{ref}" s="{style}"><v>{value}</v></c>'
    text = escape(str(value))
    return f'<c r="{ref}" s="{style}" t="inlineStr"><is><t>{text}</t></is></c>'


def infer_widths(rows, min_width=10, max_width=60):
    widths = {}
    for row in rows:
        for idx, value in enumerate(row, 1):
            size = len(str(value)) if value is not None else 0
            widths[idx] = max(widths.get(idx, min_width), min(max(size + 2, min_width), max_width))
    return widths


def sheet_xml(rows, col_widths=None, freeze='A2', auto_filter=True, header_style=1):
    col_widths = col_widths or infer_widths(rows)
    last_col = max((len(r) for r in rows), default=1)
    last_row = len(rows)
    parts = ['<?xml version="1.0" encoding="UTF-8" standalone="yes"?>']
    parts.append('<worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">')
    parts.append('<cols>')
    for idx, width in sorted(col_widths.items()):
        parts.append(f'<col min="{idx}" max="{idx}" width="{width}" customWidth="1"/>')
    parts.append('</cols>')
    parts.append('<sheetViews><sheetView workbookViewId="0">')
    if freeze:
        parts.append(f'<pane ySplit="1" topLeftCell="{freeze}" activePane="bottomLeft" state="frozen"/>')
    parts.append('</sheetView></sheetViews>')
    parts.append('<sheetFormatPr defaultRowHeight="18"/>')
    parts.append('<sheetData>')
    for r_idx, row in enumerate(rows, 1):
        parts.append(f'<row r="{r_idx}">')
        for c_idx, value in enumerate(row, 1):
            ref = f'{col_letter(c_idx)}{r_idx}'
            style = header_style if r_idx == 1 else 0
            parts.append(xml_cell(ref, value, style))
        parts.append('</row>')
    parts.append('</sheetData>')
    if auto_filter and rows:
        parts.append(f'<autoFilter ref="A1:{col_letter(last_col)}{last_row}"/>')
    parts.append('</worksheet>')
    return ''.join(parts)


def content_types_xml(sheet_count):
    overrides = []
    for i in range(1, sheet_count + 1):
        overrides.append(f'  <Override PartName="/xl/worksheets/sheet{i}.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml"/>')
    return """<?xml version=\"1.0\" encoding=\"UTF-8\" standalone=\"yes\"?>
<Types xmlns=\"http://schemas.openxmlformats.org/package/2006/content-types\">
  <Default Extension=\"rels\" ContentType=\"application/vnd.openxmlformats-package.relationships+xml\"/>
  <Default Extension=\"xml\" ContentType=\"application/xml\"/>
  <Override PartName=\"/xl/workbook.xml\" ContentType=\"application/vnd.openxmlformats-officedocument.spreadsheetml.sheet.main+xml\"/>
%s
  <Override PartName=\"/xl/styles.xml\" ContentType=\"application/vnd.openxmlformats-officedocument.spreadsheetml.styles+xml\"/>
  <Override PartName=\"/docProps/core.xml\" ContentType=\"application/vnd.openxmlformats-package.core-properties+xml\"/>
  <Override PartName=\"/docProps/app.xml\" ContentType=\"application/vnd.openxmlformats-officedocument.extended-properties+xml\"/>
</Types>""" % '\n'.join(overrides)


def root_rels_xml():
    return '''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
  <Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="xl/workbook.xml"/>
  <Relationship Id="rId2" Type="http://schemas.openxmlformats.org/package/2006/relationships/metadata/core-properties" Target="docProps/core.xml"/>
  <Relationship Id="rId3" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/extended-properties" Target="docProps/app.xml"/>
</Relationships>'''


def workbook_xml(sheet_names):
    body = []
    for i, name in enumerate(sheet_names, 1):
        body.append(f'    <sheet name="{escape(name)}" sheetId="{i}" r:id="rId{i}"/>')
    return """<?xml version=\"1.0\" encoding=\"UTF-8\" standalone=\"yes\"?>
<workbook xmlns=\"http://schemas.openxmlformats.org/spreadsheetml/2006/main\" xmlns:r=\"http://schemas.openxmlformats.org/officeDocument/2006/relationships\">
  <sheets>
%s
  </sheets>
</workbook>""" % '\n'.join(body)


def workbook_rels_xml(sheet_count):
    body = []
    for i in range(1, sheet_count + 1):
        body.append(f'  <Relationship Id="rId{i}" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet" Target="worksheets/sheet{i}.xml"/>')
    body.append(f'  <Relationship Id="rId{sheet_count + 1}" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/styles" Target="styles.xml"/>')
    return """<?xml version=\"1.0\" encoding=\"UTF-8\" standalone=\"yes\"?>
<Relationships xmlns=\"http://schemas.openxmlformats.org/package/2006/relationships\">
%s
</Relationships>""" % '\n'.join(body)


def styles_xml(header_fill='FF1F4E78'):
    return f'''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<styleSheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">
  <fonts count="2">
    <font><sz val="11"/><name val="Calibri"/></font>
    <font><b/><color rgb="FFFFFFFF"/><sz val="11"/><name val="Calibri"/></font>
  </fonts>
  <fills count="3">
    <fill><patternFill patternType="none"/></fill>
    <fill><patternFill patternType="gray125"/></fill>
    <fill><patternFill patternType="solid"><fgColor rgb="{header_fill}"/><bgColor indexed="64"/></patternFill></fill>
  </fills>
  <borders count="1"><border><left/><right/><top/><bottom/><diagonal/></border></borders>
  <cellStyleXfs count="1"><xf numFmtId="0" fontId="0" fillId="0" borderId="0"/></cellStyleXfs>
  <cellXfs count="2">
    <xf numFmtId="0" fontId="0" fillId="0" borderId="0" xfId="0"/>
    <xf numFmtId="0" fontId="1" fillId="2" borderId="0" xfId="0" applyFont="1" applyFill="1"><alignment horizontal="center" vertical="center" wrapText="1"/></xf>
  </cellXfs>
  <cellStyles count="1"><cellStyle name="Normal" xfId="0" builtinId="0"/></cellStyles>
</styleSheet>'''


def core_xml(title='Workbook', creator='Ghost'):
    return f'''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<cp:coreProperties xmlns:cp="http://schemas.openxmlformats.org/package/2006/metadata/core-properties" xmlns:dc="http://purl.org/dc/elements/1.1/" xmlns:dcterms="http://purl.org/dc/terms/" xmlns:dcmitype="http://purl.org/dc/dcmitype/" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
  <dc:creator>{escape(creator)}</dc:creator>
  <cp:lastModifiedBy>{escape(creator)}</cp:lastModifiedBy>
  <dc:title>{escape(title)}</dc:title>
</cp:coreProperties>'''


def app_xml(app='Ghost Excel Generator'):
    return f'''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Properties xmlns="http://schemas.openxmlformats.org/officeDocument/2006/extended-properties" xmlns:vt="http://schemas.openxmlformats.org/officeDocument/2006/docPropsVTypes">
  <Application>{escape(app)}</Application>
</Properties>'''


def write_xlsx(output_path, sheets, title='Workbook', creator='Ghost', header_fill='FF1F4E78'):
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    names = [s['name'] for s in sheets]
    with ZipFile(output_path, 'w', ZIP_DEFLATED) as zf:
        zf.writestr('[Content_Types].xml', content_types_xml(len(sheets)))
        zf.writestr('_rels/.rels', root_rels_xml())
        zf.writestr('xl/workbook.xml', workbook_xml(names))
        zf.writestr('xl/_rels/workbook.xml.rels', workbook_rels_xml(len(sheets)))
        zf.writestr('xl/styles.xml', styles_xml(header_fill=header_fill))
        for i, sheet in enumerate(sheets, 1):
            zf.writestr(f'xl/worksheets/sheet{i}.xml', sheet_xml(sheet['rows'], col_widths=sheet.get('widths'), freeze=sheet.get('freeze', 'A2'), auto_filter=sheet.get('auto_filter', True)))
        zf.writestr('docProps/core.xml', core_xml(title=title, creator=creator))
        zf.writestr('docProps/app.xml', app_xml())
