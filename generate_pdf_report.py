import subprocess
import os

# Markdown dosyasını PDF'e çevirmek için pandoc kullanıyoruz
markdown_file = "report.md"
pdf_output = "World_Population_Insights_Final_Report.pdf"

# Pandoc komutu
command = [
    "pandoc",
    markdown_file,
    "-o", pdf_output,
    "--pdf-engine=xelatex",
    "--variable=geometry:margin=1in",
    "--number-sections",
    "-V", "fontsize=11pt",
    "-V", "mainfont=DejaVu Sans",
    "--toc",
    "--toc-depth=3"
]

try:
    subprocess.run(command, check=True)
    print(f"✓ PDF raporu başarıyla oluşturuldu: {pdf_output}")
except FileNotFoundError:
    print("⚠ Pandoc yüklü değil. Lütfen şu komutu çalıştırın:")
    print("Ubuntu/Debian: sudo apt-get install pandoc texlive-latex-base texlive-fonts-recommended")
    print("macOS: brew install pandoc basictex")
    print("Windows: https://pandoc.org/installing.html")
except subprocess.CalledProcessError as e:
    print(f"✗ Hata: {e}")