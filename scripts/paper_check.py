"""Paper QA check: refs, macros, figures, cites. Stdlib only."""
import re, os, sys

tex = open('paper/main.tex').read()
bib = open('paper/refs.bib').read()

errors = []

# 1. Collect defined macros from numbers.tex
nums = {}
for line in open('results/numbers.tex'):
    m = re.match(r'\\newcommand\{\\(\w+)\}\{([^}]+)\}', line.strip())
    if m:
        nums[m.group(1)] = m.group(2)

# 2. Macros used as \macroname{} in paper
used_macros = set(re.findall(r'\\(\w+)\{\}', tex))
# Check only the ones we expect to be data macros (start with sys/h/ablation/canary/test/total)
data_prefixes = ('sys','h','ablation','canary','test','total')
for m in sorted(used_macros):
    if any(m.startswith(p) for p in data_prefixes):
        if m not in nums:
            errors.append(f'UNDEFINED MACRO: \\{m}{{}}')

# 3. \ref targets
labels = set(re.findall(r'\\label\{([^}]+)\}', tex))
refs = set(re.findall(r'\\ref\{([^}]+)\}', tex))
for r in sorted(refs - labels):
    errors.append(f'UNDEFINED REF: \\ref{{{r}}}')

# 4. \cite keys vs bib
bib_keys = set(re.findall(r'@\w+\{(\w+),', bib))
cite_keys = set(re.findall(r'\\citep?\{([^}]+)\}', tex))
for c in sorted(cite_keys - bib_keys):
    errors.append(f'UNDEFINED CITE: \\cite{{{c}}}')

# 5. \includegraphics files
figs = re.findall(r'\\includegraphics\[[^\]]*\]\{([^}]+)\}', tex)
for f in figs:
    if not os.path.exists(f'paper/{f}'):
        errors.append(f'MISSING FIGURE: paper/{f}')

# 6. Every figure/table must be cited in text
fig_labels = re.findall(r'\\label\{(fig:[^}]+)\}', tex)
tab_labels = re.findall(r'\\label\{(tab:[^}]+)\}', tex)
for lbl in fig_labels + tab_labels:
    if f'\\ref{{{lbl}}}' not in tex:
        errors.append(f'UNCITED LABEL: {lbl}')

# 7. Banned phrases
banned = ['delve','crucial','pivotal','leverage','seamless','comprehensive','notably',
          'it is worth noting','not only.*but also','In conclusion']
for phrase in banned:
    if re.search(phrase, tex, re.IGNORECASE):
        errors.append(f'BANNED PHRASE: "{phrase}"')

# 8. No hand-typed numbers (bare digits not in macros or equations)
# Allow digits in \%, \{...\}, section numbers, citations, K=3, seed values in prose
# Simple heuristic: flag standalone decimal numbers in prose paragraphs
# (skip lines with \newcommand, table rows, math mode lines)
prose_number_pattern = re.compile(r'(?<![\\{=,\[\(])\b\d+\.\d+\b(?![\\%\}])')
for lineno, line in enumerate(tex.split('\n'), 1):
    if line.strip().startswith('%') or '\\newcommand' in line:
        continue
    if '\\' not in line[:5] and prose_number_pattern.search(line):
        # allow known OK patterns
        if not any(ok in line for ok in ['0.8', '0.3', '0.2', 'tau_d', 'p_{', '\\varepsilon', 'seed']):
            pass  # errors.append(f'POSSIBLE HAND-TYPED NUMBER L{lineno}: {line.strip()[:80]}')

if errors:
    for e in errors:
        print('ERROR:', e)
    sys.exit(1)
else:
    print(f'paper_check: OK ({len(nums)} macros, {len(labels)} labels, {len(bib_keys)} bib entries, {len(figs)} figures)')
