"""Encode a .drawio file as a viewer.diagrams.net #R URL (deflate-raw + base64), for previewing."""
import sys, zlib, base64, urllib.parse, re
xml = open(sys.argv[1], encoding="utf-8").read()
inner = re.search(r"<mxGraphModel.*</mxGraphModel>", xml, re.S).group(0)
q = urllib.parse.quote(inner, safe="~()*!.'")
c = zlib.compressobj(9, zlib.DEFLATED, -15); d = c.compress(q.encode()) + c.flush()
print("https://viewer.diagrams.net/?lightbox=1&nav=1#R" + urllib.parse.quote(base64.b64encode(d).decode(), safe=""))
