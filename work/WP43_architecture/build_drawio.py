"""Builds Deliverables/06_Architecture.drawio: icon-based solution architecture (draw.io native stencils).
Preview: python drawio_url.py ../../Deliverables/06_Architecture.drawio -> open the printed viewer URL."""
from pathlib import Path
from xml.sax.saxutils import quoteattr

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "Deliverables" / "06_Architecture.drawio"

# layer colours: (group tint, icon/accent)
L = {
    "src": ("#F3F4F6", "#5F6B7A"),
    "dw": ("#EAF1FB", "#2F6DB5"),
    "out": ("#EAF6EE", "#2E8B57"),
    "loc": ("#F3EEFA", "#7B5EA7"),
    "cld": ("#FFF4E8", "#D9822B"),
    "aud": ("#FDEDEE", "#C0392B"),
}
cells = []


def group(id_, title, x, y, w, h, key):
    tint, acc = L[key]
    cells.append(
        f'<mxCell id="{id_}" value={quoteattr(title)} style="rounded=1;arcSize=6;html=1;fillColor={tint};strokeColor={acc};'
        f'strokeOpacity=35;verticalAlign=top;align=left;spacingLeft=12;spacingTop=6;fontSize=13;fontStyle=1;fontColor={acc};" '
        f'vertex="1" parent="1"><mxGeometry x="{x}" y="{y}" width="{w}" height="{h}" as="geometry"/></mxCell>')


def icon(id_, label, x, y, key, shape=None, image=None, size=56, sub=None):
    acc = L[key][1]
    text = f"<b>{label}</b>" + (f"<br><font color='#6B7280' style='font-size:10px'>{sub}</font>" if sub else "")
    look = f"image;image={image};" if image else f"shape={shape};fillColor={acc};strokeColor=none;"
    cells.append(
        f'<mxCell id="{id_}" value={quoteattr(text)} style="{look}html=1;aspect=fixed;verticalLabelPosition=bottom;'
        f'verticalAlign=top;labelBackgroundColor=none;fontSize=11;fontColor=#1F2937;spacingTop=2;" vertex="1" parent="1">'
        f'<mxGeometry x="{x}" y="{y}" width="{size}" height="{size}" as="geometry"/></mxCell>')


def edge(id_, s, t, label="", dashed=False, exit_=None, entry=None, pts=None):
    style = ("edgeStyle=orthogonalEdgeStyle;rounded=1;html=1;endArrow=blockThin;endFill=1;endSize=5;strokeWidth=1.5;"
             "strokeColor=#9CA3AF;fontSize=10;fontColor=#4B5563;labelBackgroundColor=#FFFFFF;")
    if dashed:
        style += "dashed=1;dashPattern=4 3;"
    if exit_:
        style += f"exitX={exit_[0]};exitY={exit_[1]};exitDx=0;exitDy=0;"
    if entry:
        style += f"entryX={entry[0]};entryY={entry[1]};entryDx=0;entryDy=0;"
    geo = '<mxGeometry relative="1" as="geometry">'
    if pts:
        geo += '<Array as="points">' + "".join(f'<mxPoint x="{a}" y="{b}"/>' for a, b in pts) + "</Array>"
    cells.append(f'<mxCell id="{id_}" value={quoteattr(label)} style="{style}" edge="1" parent="1" source="{s}" target="{t}">'
                 f"{geo}</mxGeometry></mxCell>")


# ---------- title ----------
cells.append('<mxCell id="title" value=' + quoteattr(
    "<b style='font-size:22px;color:#111827'>Platzi FP&amp;A: solution architecture</b><br>"
    "<span style='font-size:12px;color:#6B7280'>DuckDB for local development and tests · BigQuery as the cloud warehouse · "
    "outputs: financial model, executive summary and a live dashboard</span>")
    + ' style="text;html=1;align=left;verticalAlign=middle;" vertex="1" parent="1">'
    '<mxGeometry x="20" y="10" width="900" height="56" as="geometry"/></mxCell>')

# ---------- groups ----------
group("g1", "① Source data", 20, 80, 170, 560, "src")
group("g2", "② SQL model · DuckDB", 220, 80, 420, 560, "dw")
group("g3", "③ Outputs", 670, 80, 170, 560, "out")
group("g4", "④ Built with Python", 870, 80, 390, 230, "loc")
group("g5", "⑤ Cloud (free tiers)", 870, 330, 390, 310, "cld")
group("g6", "⑥ Audience", 1290, 80, 170, 560, "aud")

# ---------- ① sources ----------
icon("raw", "Raw CSVs", 77, 190, "src", shape="mxgraph.office.concepts.folder", sub="7 files · read-only")
icon("plan", "Metrics &amp; decisions", 77, 420, "src", shape="mxgraph.office.concepts.book_journal", sub="M-xx · D-xx · A-xx")

# ---------- ② SQL model ----------
icon("stg", "Staging", 262, 140, "dw", shape="mxgraph.office.databases.database", sub="7 models")
icon("int", "Intermediate", 262, 265, "dw", shape="mxgraph.office.databases.database", sub="periods · month spine")
icon("fct", "Facts", 262, 390, "dw", shape="mxgraph.office.databases.database", sub="MRR movements")
icon("marts", "Analysis marts", 262, 515, "dw", image="img/lib/azure2/databases/SQL_Database.svg", sub="36 tables")
icon("orch", "Pipeline", 482, 140, "dw", shape="mxgraph.office.concepts.settings", sub="one command")
icon("tests", "Data tests", 482, 265, "dw", shape="mxgraph.basic.tick", sub="31 / 31 pass")
icon("scen", "Scenario engine", 482, 390, "dw", shape="mxgraph.azure.code_file", sub="Base · Bull · Bear")

# ---------- ③ outputs ----------
icon("csv", "Marts export", 727, 265, "out", image="img/lib/azure2/general/Table.svg", sub="42 CSV tables")
icon("churn", "Churn alert", 727, 450, "out", shape="mxgraph.mscae.general.graph", sub="72 high-risk subs")

# ---------- ④ local ----------
icon("xlsx", "Financial model", 915, 150, "loc", image="img/lib/azure2/general/Workbooks.svg", sub="Excel · 46/46 checks")
icon("charts", "Charts", 1037, 150, "loc", image="img/lib/azure2/general/Cost_Analysis.svg", sub="4 PNG")
icon("summ", "Executive summary", 1159, 150, "loc", shape="mxgraph.office.concepts.document", sub="2-page PDF")

# ---------- ⑤ cloud ----------
icon("gh", "GitHub", 915, 395, "cld", shape="mxgraph.weblogos.github", sub="code &amp; data")
icon("st", "Streamlit app", 1159, 395, "cld", image="img/lib/azure2/general/Dashboard.svg", sub="5 tabs · filters")
icon("bq", "BigQuery", 915, 530, "cld", shape="mxgraph.gcp2.bigquery", sub="cloud warehouse · 49 tables")
icon("ls", "Q1–Q4 in BigQuery SQL", 1159, 530, "cld", shape="mxgraph.basic.tick", sub="242 / 242 match DuckDB")

# ---------- ⑥ audience ----------
icon("users", "CEO &amp; CFO", 1340, 310, "aud", shape="mxgraph.office.users.users", size=64,
     sub="PDF · Excel · dashboard")

# ---------- edges ----------
edge("e1", "raw", "stg", "load", exit_=(1, 0.5), entry=(0, 0.5))
edge("e2", "stg", "int", exit_=(0.5, 1), entry=(0.5, 0), pts=[])
edge("e3", "int", "fct")
edge("e4", "fct", "marts")
edge("e5", "orch", "stg", "runs", dashed=True, exit_=(0, 0.5), entry=(1, 0.5))
edge("e6", "tests", "int", "validate", dashed=True, exit_=(0, 0.5), entry=(1, 0.5))
edge("e7", "fct", "scen", "calibrate", exit_=(1, 0.5), entry=(0, 0.5))
edge("e8", "plan", "marts", "definitions", dashed=True, exit_=(1, 0.5), entry=(0, 0.5), pts=[(215, 448), (215, 543)])
edge("e9", "marts", "csv", exit_=(1, 0.5), entry=(0, 0.75), pts=[(655, 543), (655, 307)])
edge("e10", "scen", "csv", exit_=(1, 0.5), entry=(0, 0.5), pts=[(660, 418), (660, 293)])
edge("e11", "csv", "churn")
edge("e12", "csv", "g4", "build", exit_=(1, 0.25), entry=(0, 0.6), pts=[(855, 279), (855, 218)])
edge("e13", "xlsx", "charts", exit_=(1, 0.5), entry=(0, 0.5))
edge("e14", "charts", "summ", exit_=(1, 0.5), entry=(0, 0.5))
edge("e15", "csv", "gh", "git push", exit_=(1, 0.5), entry=(0, 0.5), pts=[(860, 293), (860, 423)])
edge("e16", "gh", "st", "auto-deploy", exit_=(1, 0.5), entry=(0, 0.5))
edge("e17", "csv", "bq", "bq load", exit_=(1, 0.75), entry=(0, 0.5), pts=[(850, 307), (850, 558)])
edge("e18", "bq", "ls", "native queries", exit_=(1, 0.5), entry=(0, 0.5))
edge("e19", "g4", "users", exit_=(1, 0.5), entry=(0, 0.25), pts=[(1275, 195), (1275, 326)])
edge("e20", "st", "users", exit_=(1, 0.5), entry=(0, 0.5))

# legend
cells.append('<mxCell id="legend" value=' + quoteattr(
    "<span style='color:#6B7280;font-size:10px'>━ data flow &nbsp;&nbsp; ┅ orchestration · validation · definitions</span>")
    + ' style="text;html=1;align=right;verticalAlign=middle;" vertex="1" parent="1">'
    '<mxGeometry x="1060" y="30" width="400" height="24" as="geometry"/></mxCell>')

xml = ('<mxfile host="app.diagrams.net"><diagram id="arch" name="Solution architecture">'
       '<mxGraphModel dx="1480" dy="660" grid="0" gridSize="10" guides="1" tooltips="1" connect="1" arrows="1" '
       'fold="1" page="1" pageScale="1" pageWidth="1480" pageHeight="660" background="#FFFFFF" math="0" shadow="0"><root>'
       '<mxCell id="0"/><mxCell id="1" parent="0"/>' + "".join(cells) + "</root></mxGraphModel></diagram></mxfile>")
OUT.write_text(xml, encoding="utf-8")
print("wrote", OUT, len(xml), "bytes")
