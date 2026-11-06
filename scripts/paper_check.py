"""Paper QA check: refs, macros, figures, cites. Stdlib only."""
import re, os, sys

tex = open('paper/main.tex', encoding='utf-8').read()
bib = open('paper/refs.bib', encoding='utf-8').read() if os.path.exists('paper/refs.bib') else ''

errors = []

# 1. Collect defined macros from numbers.tex and main.tex
nums = {}
if os.path.exists('results/numbers.tex'):
    for line in open('results/numbers.tex', encoding='utf-8'):
        m = re.match(r'\\newcommand\{\\(\w+)\}\{([^}]+)\}', line.strip())
        if m:
            nums[m.group(1)] = m.group(2)

for line in tex.splitlines():
    m = re.match(r'\\newcommand\{\\(\w+)\}\{([^}]+)\}', line.strip())
    if m:
        nums[m.group(1)] = m.group(2)

# 2. Macros used as \macroname{} in paper
used_macros = set(re.findall(r'\\(\w+)\{\}', tex))
data_prefixes = ('sys','h','ablation','canary','test','total','posControl','probe')
for m in sorted(used_macros):
    if any(m.startswith(p) for p in data_prefixes):
        if m not in nums:
            errors.append(f'UNDEFINED MACRO: \\{m}{{}}')

# 3. \ref targets
labels = set(re.findall(r'\\label\{([^}]+)\}', tex))
refs = set(re.findall(r'\\ref\{([^}]+)\}', tex))
for r in sorted(refs - labels):
    errors.append(f'UNDEFINED REF: \\ref{{{r}}}')

# 4. \cite keys vs bib & \bibitem
bib_keys = set(re.findall(r'@\w+\{(\w+),', bib))
bibitem_keys = set(re.findall(r'\\bibitem\{([^}]+)\}', tex))
all_bib_keys = bib_keys.union(bibitem_keys)

raw_cites = re.findall(r'\\citep?\{([^}]+)\}', tex)
cite_keys = set()
for raw in raw_cites:
    for k in raw.split(','):
        k = k.strip()
        if k:
            cite_keys.add(k)
for c in sorted(cite_keys - all_bib_keys):
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

if errors:
    for e in errors:
        print('ERROR:', e)
    sys.exit(1)
else:
    print(f'paper_check: OK ({len(nums)} macros, {len(labels)} labels, {len(all_bib_keys)} bib entries, {len(figs)} figures)')
