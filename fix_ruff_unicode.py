# One-off script: replace ambiguous Unicode with ASCII for Ruff RUF001/RUF003
import pathlib

base = pathlib.Path(__file__).resolve().parent
for path in ["src/streamlit/app.py", "src/e2/api/middleware/prometheus.py"]:
    p = base / path
    if not p.exists():
        continue
    t = p.read_text(encoding="utf-8")
    t = t.replace("\u2019", "'")   # RIGHT SINGLE QUOTATION MARK -> ASCII
    t = t.replace("\u2013", "-")   # EN DASH
    t = t.replace("\u2014", "-")   # EM DASH
    t = t.replace("\u2011", "-")   # NON-BREAKING HYPHEN
    t = t.replace("\u2192", "->")  # RIGHTWARDS ARROW
    p.write_text(t, encoding="utf-8")
    print("Fixed:", path)
