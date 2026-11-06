import os
import shutil
import zipfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SUBMISSION_DIR = os.path.join(ROOT, "paper", "submission")
FIGURES_DIR = os.path.join(SUBMISSION_DIR, "figures")

os.makedirs(FIGURES_DIR, exist_ok=True)

# 1. Copy main.tex
shutil.copy2(os.path.join(ROOT, "paper", "main.tex"), os.path.join(SUBMISSION_DIR, "main.tex"))

# 2. Copy figures F1..F10 (PDF and PNG)
for i in range(1, 11):
    for ext in [".pdf", ".png"]:
        src = os.path.join(ROOT, "paper", "figures", f"F{i}{ext}")
        if os.path.exists(src):
            shutil.copy2(src, os.path.join(FIGURES_DIR, f"F{i}{ext}"))

# 3. Copy compiled main.pdf
if os.path.exists(os.path.join(ROOT, "paper", "main.pdf")):
    shutil.copy2(os.path.join(ROOT, "paper", "main.pdf"), os.path.join(SUBMISSION_DIR, "main.pdf"))

# 4. Create ConsensusProbe_submission.zip
zip_path = os.path.join(SUBMISSION_DIR, "ConsensusProbe_submission.zip")
with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
    zf.write(os.path.join(SUBMISSION_DIR, "main.tex"), arcname="main.tex")
    if os.path.exists(os.path.join(SUBMISSION_DIR, "main.pdf")):
        zf.write(os.path.join(SUBMISSION_DIR, "main.pdf"), arcname="main.pdf")
    for i in range(1, 11):
        for ext in [".pdf", ".png"]:
            fig_file = os.path.join(FIGURES_DIR, f"F{i}{ext}")
            if os.path.exists(fig_file):
                zf.write(fig_file, arcname=f"figures/F{i}{ext}")

print(f"Created submission directory: {SUBMISSION_DIR}")
print(f"Created zip archive: {zip_path} ({os.path.getsize(zip_path)} bytes)")
