"""WP60 - Build the submission package: Deliverables/ + Deliverables.zip (project root)

Run: .venv/Scripts/python.exe work/WP60_submission/build_package.py --name "Your Name" \
         [--streamlit URL] [--looker URL]
"""
import argparse
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent

ap = argparse.ArgumentParser()
ap.add_argument("--name", default="[Candidate name]")
ap.add_argument("--streamlit", default="*(link to be added)*")
ap.add_argument("--looker", default="*(link to be added)*")
a = ap.parse_args()

out = ROOT / "Deliverables"
if out.exists():
    shutil.rmtree(out)
out.mkdir(parents=True)

shutil.copy(ROOT / "outputs/Platzi_FPA_Executive_Summary.pdf", out / "01_Executive_Summary.pdf")
shutil.copy(ROOT / "outputs/Platzi_FPA_Model.xlsx", out / "02_Financial_Model.xlsx")
(out / "03_Dashboards.md").write_text(
    (HERE / "Dashboards_template.md").read_text(encoding="utf-8")
    .replace("{{STREAMLIT_URL}}", a.streamlit).replace("{{LOOKER_URL}}", a.looker), encoding="utf-8")
charts = out / "04_Charts"
charts.mkdir()
for f in sorted((ROOT / "outputs/charts").glob("*.png")):
    shutil.copy(f, charts / f.name)
shutil.copytree(ROOT / "sql", out / "05_SQL", ignore=shutil.ignore_patterns("__pycache__", "*.duckdb", "*.log"))
(out / "README.md").write_text(
    (HERE / "README_submission.md").read_text(encoding="utf-8").replace("{{NAME}}", a.name), encoding="utf-8")

zip_path = shutil.make_archive(str(out), "zip", root_dir=out.parent, base_dir=out.name)
files = [p for p in out.rglob("*") if p.is_file()]
print(f"{out.name}: {len(files)} files, zip {Path(zip_path).stat().st_size/1024:,.0f} KB -> {zip_path}")
