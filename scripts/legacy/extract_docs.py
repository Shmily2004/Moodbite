import pathlib
import re
import zipfile
import xml.etree.ElementTree as ET

root = pathlib.Path('.')
source_dir = root / 'docs' / 'original'
output_dir = root / 'docs' / 'extracted'
output_dir.mkdir(parents=True, exist_ok=True)

ns = {'w': 'http://schemas.openxmlformats.org/wordprocessingml/2006/main'}


def extract_text_from_docx(path: pathlib.Path) -> str:
    with zipfile.ZipFile(path) as z:
        xmldata = z.read('word/document.xml')
        rootxml = ET.fromstring(xmldata)

        paragraphs = []
        for paragraph in rootxml.findall('.//w:p', ns):
            texts = []
            for node in paragraph.findall('.//w:t', ns):
                if node.text:
                    texts.append(node.text)
            text = ''.join(texts)
            text = re.sub(r'\s+', ' ', text).strip()
            if text:
                paragraphs.append(text)

        return '\n\n'.join(paragraphs)


for path in sorted(source_dir.glob('*.docx')):
    content = extract_text_from_docx(path)
    output_path = output_dir / f'{path.stem}.md'
    output_path.write_text(f'# {path.stem}\n\n{content}\n', encoding='utf-8')
    print(f'Created {output_path}')
