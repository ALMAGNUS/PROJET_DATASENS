# Fix RUF003: replace RIGHT SINGLE QUOTATION MARK (U+2019) with ASCII apostrophe
path = "src/e2/api/middleware/prometheus.py"
text = open(path, encoding="utf-8").read()
text = text.replace("\u2019", "'")
open(path, "w", encoding="utf-8").write(text)
print("OK")
