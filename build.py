#!/usr/bin/env python3
"""Grant Radar: builds a static site of open federal grants nonprofits can apply for, from the free Grants.gov search2 API."""
import json, urllib.request, datetime, html, os, re
API="https://api.grants.gov/v1/api/search2"
ELIG={"12":"501(c)(3) nonprofits","13":"Nonprofits without 501(c)(3)"}
PRO_URL=os.environ.get("PRO_URL","#pro")
def q(**kw):
    body={"rows":1000,"oppStatuses":"posted",**kw}
    r=urllib.request.Request(API,data=json.dumps(body).encode(),headers={"Content-Type":"application/json"})
    return json.load(urllib.request.urlopen(r,timeout=60))["data"]
grants={}
cats={}
for e in ELIG:
    d=q(eligibilities=e)
    for c in d.get("fundingCategories",[]): cats[c["value"]]=c["label"]
    for h in d["oppHits"]:
        g=grants.setdefault(h["id"],dict(h,elig=set(),cats=set())); g["elig"].add(e)
for e in ELIG:
    for code in list(cats):
        for h in q(eligibilities=e,fundingCategories=code)["oppHits"]:
            if h["id"] in grants: grants[h["id"]]["cats"].add(code)
today=datetime.date.today()
def pd(s):
    try: return datetime.datetime.strptime(s,"%m/%d/%Y").date()
    except: return None
for g in grants.values():
    g["close"]=pd(g.get("closeDate","")); g["open"]=pd(g.get("openDate",""))
    g["title"]=html.unescape(g["title"])
def slug(s): return re.sub(r"[^a-z0-9]+","-",s.lower()).strip("-")
CSS="""body{font-family:system-ui,sans-serif;max-width:960px;margin:auto;padding:16px;color:#1b2430}h1{color:#0b5d3b}a{color:#0b5d3b}
table{border-collapse:collapse;width:100%;font-size:14px}td,th{border-bottom:1px solid #ddd;padding:6px;text-align:left}
.cta{background:#0b5d3b;color:#fff;padding:16px;border-radius:8px;margin:16px 0}.cta a{color:#fff;font-weight:bold}.soon{color:#b00020;font-weight:bold}nav a{margin-right:8px;font-size:13px}"""
def row(g):
    c=g["close"]; days=(c-today).days if c else None
    cl=f'<span class="soon">{g["closeDate"]} ({days}d)</span>' if days is not None and days<=30 else (g.get("closeDate") or "Rolling/none listed")
    return f'<tr><td><a href="https://www.grants.gov/search-results-detail/{g["id"]}" rel="nofollow">{html.escape(g["title"])}</a><br><small>{html.escape(g["number"])}</small></td><td>{html.escape(g["agency"])}</td><td>{g.get("openDate","")}</td><td>{cl}</td></tr>'
def page(title,desc,items,fname,extra=""):
    items=sorted(items,key=lambda g:(g["close"] or datetime.date(2100,1,1)))
    nav=" ".join(f'<a href="{slug(l)}.html">{html.escape(l)}</a>' for _,l in sorted(cats.items(),key=lambda x:x[1]))
    cta=f'<div class="cta"><b>Grant Radar Pro, $29/month:</b> a Monday email with every new federal grant your nonprofit qualifies for, filtered to your focus areas, plus 14-day and 3-day deadline reminders. <a href="{PRO_URL}">Start Pro</a></div>'
    out=f'''<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{html.escape(title)}</title><meta name="description" content="{html.escape(desc)}"><style>{CSS}</style></head><body>
<h1>{html.escape(title)}</h1><p>{html.escape(desc)} Updated {today:%B %d, %Y} from Grants.gov. {len(items)} open opportunities.</p>{extra}{cta}
<nav><a href="index.html">All</a> <a href="closing-soon.html">Closing in 30 days</a> {nav}</nav>
<table><tr><th>Opportunity</th><th>Agency</th><th>Posted</th><th>Closes</th></tr>{"".join(row(g) for g in items)}</table>{cta}
<p><small>Data: Grants.gov public API. Not affiliated with the U.S. government. Always confirm eligibility on the official listing.</small></p></body></html>'''
    open(f"site/{fname}","w").write(out)
os.makedirs("site",exist_ok=True)
allg=list(grants.values())
page(f"Federal Grants for Nonprofits Open Now ({today:%B %Y})","Every open federal grant on Grants.gov that lists nonprofits as eligible, sorted by deadline.",allg,"index.html")
page(f"Federal Nonprofit Grants Closing in the Next 30 Days ({today:%B %Y})","Open federal grants for nonprofits with deadlines in the next 30 days.",[g for g in allg if g["close"] and 0<=(g["close"]-today).days<=30],"closing-soon.html")
for code,label in cats.items():
    page(f"{label} Grants for Nonprofits ({today:%B %Y})",f"Open federal {label.lower()} grants nonprofits can apply for, from Grants.gov.",[g for g in allg if code in g["cats"]],f"{slug(label)}.html")
urls=["index.html","closing-soon.html"]+[f"{slug(l)}.html" for l in cats.values()]
base="https://ur1313.github.io/grant-radar/"
open("site/sitemap.xml","w").write('<?xml version="1.0" encoding="UTF-8"?><urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">'+"".join(f"<url><loc>{base}{u}</loc><lastmod>{today}</lastmod></url>" for u in urls)+"</urlset>")
open("site/robots.txt","w").write(f"User-agent: *\nAllow: /\nSitemap: {base}sitemap.xml\n")
json.dump([{k:(sorted(v) if isinstance(v,set) else str(v) if isinstance(v,datetime.date) else v) for k,v in g.items()} for g in allg],open("site/grants.json","w"))
print(len(allg),"grants;",len(cats),"categories;",sum(1 for g in allg if g["close"] and 0<=(g["close"]-today).days<=30),"closing in 30d")
