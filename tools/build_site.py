"""Bouwt de publieke containerpagina's uit de RigTrack containers.
Gebruik: python3 build_site.py containers.json OUTDIR
OUTDIR is de map van de website (de GitHub repository). Bestaande PDF's in
OUTDIR/c/<token>/certificaten/ blijven staan en worden op de pagina getoond.
"""
import json, os, sys, html, datetime, base64, shutil

SRC, OUT = sys.argv[1], sys.argv[2]
REPO = "Deco-subsea/rigging"
import re
def slug_of(c):
    if c.get("slug"): return c["slug"]
    m = re.search(r"([A-Z]{4})\s*(\d{6})\s*-?\s*(\d)", (c.get("naam") or "").upper())
    return (m.group(1) + m.group(2) + m.group(3)) if m else c["pub"]
HERE = os.path.dirname(os.path.abspath(__file__))
LOGO = "data:image/png;base64," + base64.b64encode(open(os.path.join(HERE, "logo.png"), "rb").read()).decode()
E = lambda s: html.escape(str(s if s is not None else ""))
TODAY = datetime.date.today()


def kg(v):
    if v in (None, ""):
        return "–"
    return f"{int(round(float(v))):,}".replace(",", ".") + " kg"


def dmy(s):
    if not s:
        return ""
    y, m, d = s[:10].split("-")
    return f"{d}/{m}/{y}"


def wll(w):
    if w in (None, ""):
        return "?"
    return str(w).replace(".", ",") + " t"


def keur(it):
    ed = it.get("ed") or ""
    if not ed:
        return ("off", "Geen keuring gekend / No inspection on file")
    e = datetime.date.fromisoformat(ed[:10])
    if e < TODAY:
        return ("bad", "Vervallen sinds / Expired " + dmy(ed))
    if (e - TODAY).days < 30:
        return ("warn", "Vervalt / Expires " + dmy(ed))
    return ("ok", "Geldig tot / Valid until " + dmy(ed))


CSS = """
:root{--navy:#0A2A5C;--blue:#1F6FB8;--sea:#2C9AD6;--ink:#14213A;--muted:#5F6B78;--line:#D6DEE9;--bg:#F3F6FA;--panel:#fff;
--ok:#1E6B3A;--okbg:#E2F2E8;--warn:#8F5C00;--warnbg:#FDF0D2;--bad:#B0242C;--badbg:#FBE3E4;--off:#5F6B78;--offbg:#ECEFF3}
@media (prefers-color-scheme:dark){:root{--ink:#E8EEF6;--muted:#9AA8BA;--line:#2A3A52;--bg:#0E1726;--panel:#15223A;--navy:#9CC3EE;
--okbg:#163A26;--ok:#7FD39C;--warnbg:#3D2E0E;--warn:#F2C46B;--badbg:#45161A;--bad:#F19AA0;--offbg:#23324A;--off:#B4C0D0}}
*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--ink);font:16px/1.45 -apple-system,Segoe UI,Roboto,Arial,sans-serif}
.wrap{max-width:680px;margin:0 auto;padding:16px 16px 40px;display:flex;flex-direction:column;gap:14px}
.hd{display:flex;align-items:center;gap:12px}.hd img{width:56px;height:56px;border-radius:12px;background:#fff;flex:none}
.hd small{color:var(--muted);font-size:13px}h1{margin:2px 0 0;font-size:26px;line-height:1.15;color:var(--navy)}
h2{margin:10px 0 0;font-size:14px;text-transform:uppercase;letter-spacing:.08em;color:var(--muted)}
.kv{display:grid;grid-template-columns:repeat(2,1fr);gap:8px}.kv div{background:var(--panel);border:1px solid var(--line);border-radius:12px;padding:10px 12px}
.kv small{display:block;color:var(--muted);font-size:11px;text-transform:uppercase;letter-spacing:.06em;font-weight:600}.kv b{font-size:18px;font-variant-numeric:tabular-nums}
.card{background:var(--panel);border:1px solid var(--line);border-radius:14px;padding:12px 14px;display:flex;flex-direction:column;gap:6px}
.t{display:flex;justify-content:space-between;align-items:center;gap:8px;flex-wrap:wrap}.t b{font-size:18px}
.meta{color:var(--muted);font-size:14px}
.chip{display:inline-block;font-size:12px;font-weight:700;border-radius:6px;padding:2px 8px}
.ok{background:var(--okbg);color:var(--ok)}.warn{background:var(--warnbg);color:var(--warn)}.bad{background:var(--badbg);color:var(--bad)}.off{background:var(--offbg);color:var(--off)}
a{color:var(--blue);font-weight:700}a.btn{display:block;text-align:center;text-decoration:none;background:var(--blue);color:#fff;border-radius:10px;padding:12px;font-size:16px}
.foot{color:var(--muted);font-size:13px;border-top:1px solid var(--line);padding-top:12px}
"""


def page(title, body):
    return f"""<!DOCTYPE html><html lang="nl"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<meta name="robots" content="noindex,nofollow"><title>{E(title)}</title><style>{CSS}</style></head><body><div class="wrap">{body}</div></body></html>"""


def item_card(it, role):
    c, t = keur(it)
    links = it.get("certs") or []
    lk = "".join(f'<a href="{E(u)}" target="_blank" rel="noopener">Certificaat en keuring / Certificate{(" (" + str(i + 1) + ")") if len(links) > 1 else ""}</a>' for i, u in enumerate(links))
    if not lk:
        lk = '<span class="meta">Certificaat op aanvraag / Certificate on request</span>'
    meta = " · ".join(x for x in [role, it.get("soort", ""), "WLL " + wll(it.get("w")), it.get("maat", ""), it.get("mk", ""),
                                   ("gekeurd / inspected " + dmy(it["kd"])) if it.get("kd") else ""] if x)
    return f'<div class="card"><div class="t"><b>{E(it["id"])}</b><span class="chip {c}">{E(t)}</span></div><div class="meta">{E(meta)}</div>{lk}</div>'


def build(c, outdir):
    slug = slug_of(c)
    d = os.path.join(outdir, "container", slug)
    old = os.path.join(outdir, "c", c["pub"])
    if c.get("pub") and slug != c["pub"]:
        os.makedirs(old, exist_ok=True)
        open(os.path.join(old, "index.html"), "w").write(f'<!DOCTYPE html><meta charset="utf-8"><meta http-equiv="refresh" content="0;url=../../container/{slug}/"><link rel="canonical" href="../../container/{slug}/"><a href="../../container/{slug}/">Ga naar de containerpagina</a>')
    cd = os.path.join(d, "certificaten")
    os.makedirs(cd, exist_ok=True)
    keep = os.path.join(cd, ".gitkeep")
    if not os.path.exists(keep):
        open(keep, "w").close()
    pdfs = sorted(f for f in os.listdir(cd) if f.lower().endswith(".pdf"))
    g = sorted(c.get("gew") or [], key=lambda x: x.get("d") or x.get("at") or "")
    last = g[-1] if g else None
    snap = c.get("snap") or {}
    kv = [("Type", c.get("type") or "–"), ("M.G.W.", kg(c.get("mgw"))), ("Tare", kg(c.get("tare"))), ("Payload", kg(c.get("pay"))),
          ("Gewogen / Weighed", (kg(last["kg"]) + " (" + dmy(last.get("d") or last.get("at")) + ")") if last else "–"),
          ("Inspectie / Inspection", dmy(c.get("kd")) or "–")]
    body = [f'<div class="hd"><img src="{LOGO}" alt="DECO Subsea"><div><small>DECO Subsea Services · container & rigging</small><h1>{E(c.get("naam"))}</h1></div></div>',
            '<div class="kv">' + "".join(f"<div><small>{E(a)}</small><b>{E(b)}</b></div>" for a, b in kv) + "</div>"]
    body.append("<h2>Certificaten container / Container certificates</h2>")
    inner = "".join(f'<a class="btn" href="certificaten/{E(f)}" target="_blank" rel="noopener">{E(os.path.splitext(f)[0])} (PDF)</a>' for f in pdfs) or '<div class="meta">Nog geen certificaat opgeladen / No certificate uploaded yet.</div>'
    body.append(f'<div id="certs" style="display:flex;flex-direction:column;gap:8px">{inner}</div>')
    for u in c.get("dtlinks") or []:
        body.append(f'<a href="{E(u)}" target="_blank" rel="noopener">Container in DigiTags (Vinçotte) / Container in DigiTags</a>')
    body.append(f"""<script>(function(){{var u="https://api.github.com/repos/{REPO}/contents/container/{slug}/certificaten";
fetch(u).then(function(r){{return r.ok?r.json():null}}).then(function(a){{if(!a||!a.length)return;var p=a.filter(function(f){{return /\\.pdf$/i.test(f.name)}});if(!p.length)return;
var box=document.getElementById("certs");box.innerHTML="";p.forEach(function(f){{var l=document.createElement("a");l.className="btn";l.href="certificaten/"+encodeURIComponent(f.name);l.target="_blank";l.rel="noopener";
l.textContent=f.name.replace(/\\.pdf$/i,"")+" (PDF)";box.appendChild(l);}});}}).catch(function(){{}});}})();</script>""")
    body.append("<h2>4 leg sling</h2>")
    body.append(item_card(snap["sling"], "Sling") if snap.get("sling") else '<div class="meta">Geen sling geregistreerd / No sling registered.</div>')
    sh = snap.get("sh") or []
    body.append(f"<h2>Shackles ({len(sh)})</h2>")
    body += [item_card(s, "Shackle") for s in sh] or ['<div class="meta">Geen shackles geregistreerd / No shackles registered.</div>']
    stand = dmy((snap.get("at") or c.get("at") or "")[:10])
    body.append(f'<div class="foot">Stand / Status: {E(stand)} · DECO Subsea N.V. · Peraltastraat 5, 8000 Brugge · +32 50 31 10 92 · <a href="https://www.deco-subsea.be">www.deco-subsea.be</a></div>')
    open(os.path.join(d, "index.html"), "w").write(page(c.get("naam") or "Container", "".join(body)))
    return d


data = json.load(open(SRC))
docs = [x.get("data", x) for x in (data if isinstance(data, list) else data.values())]
os.makedirs(OUT, exist_ok=True)
open(os.path.join(OUT, "index.html"), "w").write(page("DECO Subsea · rigging", f'<div class="hd"><img src="{LOGO}" alt="DECO Subsea"><div><small>DECO Subsea Services</small><h1>Container & rigging</h1></div></div><div class="meta">Scan de QR code op de container. / Scan the QR code on the container.</div>'))
open(os.path.join(OUT, ".nojekyll"), "w").close()
open(os.path.join(OUT, "robots.txt"), "w").write("User-agent: *\nDisallow: /\n")
n = 0
for c in docs:
    if c.get("pub"):
        build(c, OUT); n += 1
print("pagina's gemaakt:", n)
