"""Build publication-quality IEEE-style research paper PDF using Playwright Chromium."""
import os, re, json, shutil, zipfile, subprocess
from pathlib import Path

def build_paper():
    # 1. Load macros from results/numbers.tex and paper/main.tex
    macros = {}
    if os.path.exists('results/numbers.tex'):
        with open('results/numbers.tex', encoding='utf-8') as f:
            for line in f:
                m = re.match(r'\\newcommand\{\\(\w+)\}\{([^}]+)\}', line.strip())
                if m:
                    macros[m.group(1)] = m.group(2)

    with open('paper/main.tex', encoding='utf-8') as f:
        tex = f.read()

    for line in tex.splitlines():
        m = re.match(r'\\newcommand\{\\(\w+)\}\{([^}]+)\}', line.strip())
        if m:
            macros[m.group(1)] = m.group(2)

    print(f"Loaded {len(macros)} macros")

    # Substitute macros in tex
    for name, val in macros.items():
        tex = re.sub(rf'\\{name}(\{{}})?', val, tex)

    # 2. Extract references from \begin{thebibliography}
    bib_items = []
    bib_m = re.search(r'\\begin\{thebibliography\}[^}]*\}([\s\S]*?)\\end\{thebibliography\}', tex)
    if bib_m:
        raw_items = bib_m.group(1)
        for itm in re.finditer(r'\\bibitem\{([^}]+)\}([\s\S]*?)(?=\\bibitem\{|$)', raw_items):
            key = itm.group(1).strip()
            desc = itm.group(2).strip()
            # Clean latex markup in desc
            desc = desc.replace('\\emph{', '<em>').replace('}', '</em>')
            desc = desc.replace('``', '"').replace("''", '"')
            desc = desc.replace('~', ' ')
            desc = re.sub(r'\\doi\{([^}]+)\}', r'doi: \1', desc)
            bib_items.append((key, desc))

    # 3. Extract abstract
    abstract_m = re.search(r'\\begin\{abstract\}([\s\S]*?)\\end\{abstract\}', tex)
    abstract_text = abstract_m.group(1).strip() if abstract_m else ''

    # Clean abstract
    abstract_html = abstract_text.replace('\\textbf{', '<strong>').replace('}', '</strong>')
    abstract_html = abstract_html.replace('\\emph{', '<em>')
    abstract_html = abstract_html.replace('\\texttt{', '<code>').replace('}', '</code>')
    abstract_html = re.sub(r'\\cite\{([^}]+)\}', r'[\1]', abstract_html)
    abstract_html = re.sub(r'\$([^\$]+)\$', r'<i>\1</i>', abstract_html)
    abstract_html = abstract_html.replace('\n\n', '</p><p>').replace('\\medskip\\noindent', '<br/><br/>')

    # Extract keywords
    kw_m = re.search(r'\\begin\{IEEEkeywords\}([\s\S]*?)\\end\{IEEEkeywords\}', tex)
    kw_html = ''
    if kw_m:
        kw_text = kw_m.group(1).strip()
        kw_html = f'<p class="keywords"><strong><em>Index Terms</em>&mdash;</strong>{kw_text}</p>'

    # 4. Extract body sections
    body_part = tex.split('\\end{IEEEkeywords}')[1] if '\\end{IEEEkeywords}' in tex else (tex.split('\\end{abstract}')[1] if '\\end{abstract}' in tex else tex)
    body_part = body_part.split('\\begin{thebibliography}')[0] if '\\begin{thebibliography}' in body_part else (body_part.split('\\end{document}')[0] if '\\end{document}' in body_part else body_part)

    # Convert sections and subsections
    roman_numerals = ['I', 'II', 'III', 'IV', 'V', 'VI', 'VII', 'VIII', 'IX', 'X', 'XI', 'XII']
    sec_idx = 0

    def replace_section(m):
        nonlocal sec_idx
        title = m.group(1).strip()
        num = roman_numerals[sec_idx] if sec_idx < len(roman_numerals) else str(sec_idx+1)
        sec_idx += 1
        return f'<h2 class="sec-title">{num}. {title.upper()}</h2>'

    sub_letters = ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J']
    sub_idx = 0
    def replace_subsection(m):
        nonlocal sub_idx
        title = m.group(1).strip()
        let = sub_letters[sub_idx % len(sub_letters)]
        sub_idx += 1
        return f'<h3 class="subsec-title"><em>{let}. {title}</em></h3>'

    html_body = re.sub(r'\\section\*?\{([^}]+)\}', replace_section, body_part)
    html_body = re.sub(r'\\subsection\*?\{([^}]+)\}', replace_subsection, html_body)

    # Convert figures
    def replace_figure(m):
        fig_body = m.group(1)
        inc = re.search(r'\\includegraphics\[[^\]]*\]\{([^}]+)\}', fig_body)
        cap = re.search(r'\\caption\{([^}]+)\}', fig_body)
        if not inc: return ''
        fig_path = inc.group(1).replace('.pdf', '.png')
        caption_text = cap.group(1) if cap else ''
        caption_text = caption_text.replace('\\textbf{', '<strong>').replace('}', '</strong>')
        caption_text = re.sub(r'\$([^\$]+)\$', r'<i>\1</i>', caption_text)
        caption_text = caption_text.replace('\\emph{', '<em>')
        caption_text = caption_text.replace('\\cite{', '[').replace('}', ']')
        abs_fig = Path('paper/' + fig_path).resolve().as_uri()
        return f'''
        <div class="figure-container">
            <img src="{abs_fig}" class="fig-img" alt="{caption_text}" />
            <p class="fig-caption"><strong>Fig.</strong> {caption_text}</p>
        </div>
        '''

    html_body = re.sub(r'\\begin\{figure\*?\}([\s\S]*?)\\end\{figure\*?\}', replace_figure, html_body)

    # Remove labels
    html_body = re.sub(r'\\label\{[^}]+\}', '', html_body)
    # Convert citations
    html_body = re.sub(r'\\cite\{([^}]+)\}', r'[\1]', html_body)
    # Convert refs
    html_body = re.sub(r'\\ref\{([^}]+)\}', r'<span class="ref-cite">\1</span>', html_body)

    # Convert basic formatting
    html_body = html_body.replace('\\textbf{', '<strong>').replace('}', '</strong>')
    html_body = html_body.replace('\\emph{', '<em>').replace('\\textit{', '<em>')
    html_body = html_body.replace('\\texttt{', '<code>').replace('}', '</code>')
    html_body = re.sub(r'\$([^\$]+)\$', r'<i>\1</i>', html_body)

    # Convert items
    html_body = html_body.replace('\\begin{enumerate}', '<ol>').replace('\\end{enumerate}', '</ol>')
    html_body = html_body.replace('\\begin{itemize}', '<ul>').replace('\\end{itemize}', '</ul>')
    html_body = re.sub(r'\\item\s+', '<li>', html_body)

    # Clean remaining TeX commands
    html_body = re.sub(r'\\(?:input|bibliographystyle|bibliography)\{[^}]+\}', '', html_body)
    html_body = re.sub(r'\\(?:maketitle|noindent|medskip|bigskip)', '', html_body)

    # Format paragraphs
    paragraphs = html_body.split('\n\n')
    formatted_paras = []
    for p in paragraphs:
        p = p.strip()
        if not p: continue
        if p.startswith('<h') or p.startswith('<div') or p.startswith('<ol') or p.startswith('<ul') or p.startswith('<table'):
            formatted_paras.append(p)
        else:
            formatted_paras.append(f'<p>{p}</p>')
    final_body = '\n'.join(formatted_paras)

    # Generate Bibliography list
    bib_html = '<h2 class="sec-title">REFERENCES</h2><ol class="bib-list">'
    for idx, (k, desc) in enumerate(bib_items, 1):
        bib_html += f'<li id="{k}">[{idx}] {desc}</li>'
    bib_html += '</ol>'

    # Construct complete IEEE HTML
    html_doc = f'''<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8" />
<title>ConsensusProbe: Disagreement-Driven Interactive Gates for Reliable LLM-Based Data Cleaning</title>
<style>
  @page {{
    size: a4;
    margin: 0.65in;
    @bottom-center {{
      content: counter(page);
      font-size: 9pt;
      font-family: 'Times New Roman', serif;
    }}
  }}
  * {{ box-sizing: border-box; }}
  body {{
    font-family: 'Times New Roman', Times, serif;
    font-size: 10pt;
    line-height: 1.22;
    color: #111;
    margin: 0;
    padding: 0;
  }}
  .paper-header {{
    text-align: center;
    margin-bottom: 14pt;
  }}
  .paper-title {{
    font-size: 17pt;
    font-weight: bold;
    margin-bottom: 6pt;
    line-height: 1.2;
  }}
  .paper-authors {{
    font-size: 10.5pt;
    margin-bottom: 2pt;
    font-style: italic;
  }}
  .paper-affil {{
    font-size: 9pt;
    color: #444;
    margin-bottom: 10pt;
  }}
  .abstract-container {{
    margin: 0 auto 12pt auto;
    width: 95%;
    font-size: 9pt;
    text-align: justify;
    padding: 6pt 10pt;
    border-top: 1px solid #ccc;
    border-bottom: 1px solid #ccc;
    background: #fdfdfd;
  }}
  .abstract-title {{
    font-weight: bold;
    text-transform: uppercase;
    font-size: 9pt;
    margin-right: 4pt;
  }}
  .keywords {{
    font-size: 8.5pt;
    margin-top: 4pt;
    margin-bottom: 0;
    text-indent: 0;
  }}
  .two-column {{
    column-count: 2;
    column-gap: 0.28in;
    text-align: justify;
  }}
  p {{
    text-indent: 12pt;
    margin-top: 0;
    margin-bottom: 3.5pt;
  }}
  h2.sec-title {{
    font-size: 9.5pt;
    font-weight: bold;
    text-align: center;
    margin-top: 11pt;
    margin-bottom: 3pt;
    text-transform: uppercase;
    letter-spacing: 0.5pt;
    break-after: avoid;
  }}
  h3.subsec-title {{
    font-size: 9.5pt;
    font-weight: normal;
    font-style: italic;
    margin-top: 7pt;
    margin-bottom: 2pt;
    break-after: avoid;
  }}
  .figure-container {{
    margin: 8pt 0;
    text-align: center;
    break-inside: avoid;
  }}
  .fig-img {{
    width: 100%;
    max-width: 100%;
    height: auto;
    border: 1px solid #e2e8f0;
    border-radius: 2px;
  }}
  .fig-caption {{
    font-size: 8pt;
    text-indent: 0;
    text-align: justify;
    margin-top: 3pt;
    color: #333;
    line-height: 1.15;
  }}
  ol, ul {{
    margin-top: 2pt;
    margin-bottom: 3pt;
    padding-left: 16pt;
  }}
  li {{
    font-size: 9.5pt;
    margin-bottom: 2pt;
  }}
  .bib-list {{
    font-size: 8pt;
    padding-left: 14pt;
    line-height: 1.2;
  }}
  .bib-list li {{
    margin-bottom: 3pt;
  }}
  code {{
    font-family: monospace;
    font-size: 8.5pt;
  }}
</style>
</head>
<body>
<div class="paper-header">
  <div class="paper-title">ConsensusProbe: Disagreement-Driven Interactive Gates<br/>for Reliable LLM-Based Data Cleaning</div>
  <div class="paper-authors">Anonymous Authors</div>
  <div class="paper-affil">Anonymous Institution</div>
</div>

<div class="abstract-container">
  <span class="abstract-title">Abstract&mdash;</span>{abstract_html}
  {kw_html}
</div>

<div class="two-column">
  {final_body}
  {bib_html}
</div>
</body>
</html>'''

    out_html = Path('paper/main.html')
    out_html.write_text(html_doc, encoding='utf-8')
    print("Generated paper/main.html")

    # 5. Render PDF with Playwright Chromium
    node_script = '''
    const { chromium } = require('playwright');
    const path = require('path');
    (async () => {
      const browser = await chromium.launch();
      const page = await browser.newPage();
      const htmlPath = path.resolve('../paper/main.html');
      await page.goto('file:///' + htmlPath.replace(/\\\\/g, '/'), { waitUntil: 'networkidle' });
      await page.waitForTimeout(1000);
      await page.pdf({
        path: '../paper/main.pdf',
        format: 'A4',
        margin: { top: '0.6in', bottom: '0.6in', left: '0.6in', right: '0.6in' },
        printBackground: true,
        displayHeaderFooter: true,
        headerTemplate: '<div></div>',
        footerTemplate: '<div style="width:100%;text-align:center;font-size:8pt;font-family:serif;color:#555;">Page <span class="pageNumber"></span> of <span class="totalPages"></span></div>'
      });
      console.log('PDF saved to paper/main.pdf');

      const fs = require('fs');
      if (!fs.existsSync('../docs/preview')) fs.mkdirSync('../docs/preview', { recursive: true });
      await page.screenshot({ path: '../docs/preview/paper-1.png', fullPage: false });
      console.log('Saved page preview to docs/preview/paper-1.png');

      await browser.close();
    })().catch(e => { console.error('Playwright error:', e); process.exit(1); });
    '''
    subprocess.run(['node', '-e', node_script], cwd='frontend', check=True)

    # 6. Copy to root as requested
    shutil.copy('paper/main.pdf', 'research paper.pdf')
    shutil.copy('paper/main.pdf', 'Research_Paper.pdf')
    print("Copied paper/main.pdf to 'research paper.pdf' and 'Research_Paper.pdf' at root!")

    # 7. Create paper_overleaf.zip
    zip_path = Path('paper_overleaf.zip')
    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zf:
        zf.write('paper/main.tex', 'main.tex')
        if os.path.exists('paper/refs.bib'):
            zf.write('paper/refs.bib', 'refs.bib')
        if os.path.exists('results/numbers.tex'):
            zf.write('results/numbers.tex', 'numbers.tex')
        for f in os.listdir('paper/figures'):
            zf.write(os.path.join('paper/figures', f), os.path.join('figures', f))
    print(f"Created {zip_path} ({zip_path.stat().st_size} bytes)")

    # 8. Write paper/FORMAT.md
    format_md = f"""# ConsensusProbe Paper Format Specification

- **Document Style**: IEEE Conference (IEEEtran, A4, 2 columns, 10pt)
- **Title**: ConsensusProbe: Disagreement-Driven Interactive Gates for Reliable LLM-Based Data Cleaning
- **Authors**: Anonymous Authors, Anonymous Institution
- **Source Files**: `paper/main.tex` (Single-File Self-Contained Source), `research paper latexcode.txt`
- **Compiled PDF**: `paper/main.pdf`, `research paper.pdf`, `Research_Paper.pdf`
- **Overleaf Archive**: `paper_overleaf.zip`
- **Page Previews**: `docs/preview/paper-1.png`
- **Total Macros**: {len(macros)}
- **Figures**: 13 figures (F1 through F13)
- **Mock Honesty Disclosure**: Included under Rule R7 (LLM_PROVIDER=mock, BUDGET_USD=0)
"""
    Path('paper/FORMAT.md').write_text(format_md, encoding='utf-8')
    print("Generated paper/FORMAT.md")

if __name__ == '__main__':
    build_paper()
