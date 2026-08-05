#!/usr/bin/env python3
"""Flatten the Claude Design .dc.html source into a self-contained static site.

The source is a Design Component: it renders client-side via support.js, which
pulls React off a CDN and expands <sc-for>/<sc-if>/{{ }} in the browser. This
script evaluates all of that ahead of time and emits plain HTML/CSS so the
deployed page has no scripts, no CDN dependency, and real content in view-source.
"""
import base64, html, pathlib

SRC = pathlib.Path(__file__).resolve().parent / "design-source"
OUT = pathlib.Path(__file__).resolve().parent.parent
OUT.mkdir(parents=True, exist_ok=True)

PHONE_DIGITS = "9374787022"
PHONE = "937-478-7022"
ADDR1 = "704 Hall Ave."
ADDR2 = "Dayton, OH 45404"
MAPS_Q = "704+Hall+Ave,+Dayton,+OH+45404"

LOGO_SRC = SRC / "uploads" / "pasted-1785939777393-0.png"
LOGO_W, LOGO_H = 640, 292
LOGO_QUALITY = 72

INVENTORY = [
    ("2015 Chevy Silverado 1500", "$18,500", "4WD · 112K mi · Crew Cab",        "truck"),
    ("2012 Ford F-150 XLT",       "$14,900", "4WD · 138K mi · New Brakes",      "truck"),
    ("2016 Dodge Charger R/T",    "$19,750", "5.7 HEMI · 96K mi · Clean Title", "car"),
    ("2014 Honda Accord EX-L",    "$11,400", "FWD · 104K mi · Leather",         "car"),
    ("2017 Ram 1500 Big Horn",    "$22,900", "4WD · 88K mi · Tow Package",      "truck"),
    ("2013 Jeep Grand Cherokee",  "$12,850", "4WD · 129K mi · New Tires",       "suv"),
]

TRUST = [
    ("INSPECTED BEFORE LISTED",
     "Every vehicle gets a full mechanical look-over in our own shop before it goes on the lot."),
    ("FINANCING AVAILABLE",
     "We work with local lenders and buy-here options. Call and we’ll tell you straight what you qualify for."),
    ("TRADE-INS WELCOME",
     "Bring what you’re driving now. We’ll appraise it on the spot and put the value toward your next one."),
    ("NO PRESSURE, NO GAMES",
     "Prices are the prices. Take a test drive, ask hard questions, bring your own mechanic."),
]

DESCRIPTION = ("Used truck and car sales just off I-75 in Dayton, Ohio. Every vehicle inspected "
               "before it's listed. Financing and trade-ins welcome. Call 937-478-7022.")
TITLE = "I-75 Truck & Car | Used Trucks & Cars in Dayton, OH"

# Vehicle silhouettes are side profiles on a shared 200x70 grid with a common
# ground line at y=51 and 12px wheels, so mixing body styles in one row keeps
# them on the same baseline at the same scale. The wheel arches are cut out of
# the body path and the wheels drawn as separate circles, which is what makes a
# wheel still read as a wheel at 24px.
VEHICLES = {
    "truck": (
        "M8 52 L8 34 Q8 29 13 28 L48 26 L61 9 Q63 6 68 6 L111 6 Q116 6 118 9 L127 26 "
        "L185 26 Q191 26 192 32 L192 52 L175 52 A15 15 0 0 0 145 52 L57 52 A15 15 0 0 0 27 52 Z",
        ((42, 52), (160, 52)),
    ),
    "car": (
        "M6 50 L6 40 Q6 34 14 32 L46 27 L66 11 Q70 8 77 8 L124 8 Q131 8 136 12 L160 28 "
        "L184 32 Q194 35 194 43 L194 50 L172 50 A15 15 0 0 0 142 50 L58 50 A15 15 0 0 0 28 50 Z",
        ((43, 50), (157, 50)),
    ),
    "suv": (
        "M8 51 L8 38 Q8 32 15 30 L44 27 L58 10 Q61 7 66 7 L150 7 Q157 7 160 11 L172 27 "
        "L184 31 Q192 34 192 42 L192 51 L174 51 A15 15 0 0 0 144 51 L56 51 A15 15 0 0 0 26 51 Z",
        ((41, 51), (159, 51)),
    ),
}

SPRITE = (
    '<svg xmlns="http://www.w3.org/2000/svg" style="display:none" aria-hidden="true">'
    + "".join(
        f'<symbol id="i-{k}" viewBox="0 0 200 70"><path d="{d}"/>'
        + "".join(f'<circle cx="{x}" cy="{y}" r="12"/>' for x, y in wheels)
        + "</symbol>"
        for k, (d, wheels) in VEHICLES.items()
    )
    + '<symbol id="i-shield" viewBox="0 0 100 100">'
    '<path d="M50 3.5C40 3.5 30 5.5 24 7.5 20 8.8 12 10 5.5 10c0 0 2 8 2 16v18.5C7.5 68 30 86.5 50 96.5 '
    '70 86.5 92.5 68 92.5 44.5V26c0-8 2-16 2-16C88 10 80 8.8 76 7.5 70 5.5 60 3.5 50 3.5Z" '
    'fill="#0d0d0d" stroke="#ffffff" stroke-width="7"/></symbol>'
    "</svg>"
)


# viewBox stays on the OUTER <svg>: <use> imports the symbol's geometry but not
# its aspect ratio, so without it `height:auto` falls back to the 150px default
# replaced-element height and every icon renders oversized.
def veh(kind, cls=""):
    return (f'<svg class="ic {cls}" viewBox="0 0 200 70" aria-hidden="true" focusable="false">'
            f'<use href="#i-{kind}"/></svg>')


def shield(num):
    return ('<svg class="ic shield" viewBox="0 0 100 100" aria-hidden="true" focusable="false">'
            f'<use href="#i-shield"/><text x="50" y="56" text-anchor="middle" '
            f'dominant-baseline="middle" fill="#fff">{num}</text></svg>')


FAVICON_SVG = (
    '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100">'
    '<rect width="100" height="100" fill="#0d0d0d"/>'
    '<path d="M50 3.5C40 3.5 30 5.5 24 7.5 20 8.8 12 10 5.5 10c0 0 2 8 2 16v18.5C7.5 68 30 86.5 50 96.5 '
    '70 86.5 92.5 68 92.5 44.5V26c0-8 2-16 2-16C88 10 80 8.8 76 7.5 70 5.5 60 3.5 50 3.5Z" '
    'fill="#0d0d0d" stroke="#fff" stroke-width="7"/>'
    '<text x="50" y="58" text-anchor="middle" fill="#fff" '
    'font-family="Arial Black, Arial, sans-serif" font-size="30" font-weight="bold">75</text></svg>'
)
FAVICON_URI = "data:image/svg+xml;base64," + base64.b64encode(FAVICON_SVG.encode()).decode()

CSS = """
*,*::before,*::after{box-sizing:border-box}
html{scroll-behavior:smooth}
body{margin:0;background:#0d0d0d;color:#e8e8e8;font-family:'Barlow',sans-serif;
 -webkit-font-smoothing:antialiased;min-width:320px;overflow-x:hidden}
h1,h2,h3{font-family:'Anton',sans-serif;font-weight:400;margin:0;transform:skewX(-8deg)}
.cond{font-family:'Barlow Condensed',sans-serif}
.ic{fill:#fff;height:auto;flex:none}
.shield{width:46px;height:50px;overflow:visible;fill:#0d0d0d}
.shield text{font-family:'Anton',sans-serif;font-size:34px;letter-spacing:1px}
:focus-visible{outline:3px solid #fff;outline-offset:3px}

.stripes{position:absolute;inset:0;pointer-events:none;background:repeating-linear-gradient(
 118deg,#fff 0,#fff 10px,transparent 10px,transparent 20px,#fff 20px,#fff 24px,transparent 24px,transparent 52px)}
.stripes.dark{background:repeating-linear-gradient(
 118deg,#000 0,#000 10px,transparent 10px,transparent 20px,#000 20px,#000 24px,transparent 24px,transparent 52px)}

.wrap{max-width:1120px;margin:0 auto;padding:clamp(44px,7vw,88px) 18px}

.topbar{background:#000;border-bottom:1px solid #262626;padding:9px 18px;display:flex;
 justify-content:space-between;align-items:center;gap:14px;flex-wrap:wrap;font-size:15px;
 letter-spacing:.07em;text-transform:uppercase;color:#8a8a8a}
.topbar a{color:#fff;text-decoration:none;font-weight:700;letter-spacing:.09em}
.topbar a:hover{color:#a3a3a3}

.hero{position:relative;overflow:hidden;border-bottom:1px solid #262626}
.hero .stripes{opacity:.06}
.hero-in{position:relative;max-width:1120px;margin:0 auto;
 padding:clamp(36px,7vw,84px) 18px clamp(40px,7vw,88px);display:flex;flex-direction:column;gap:18px}
.logo{width:clamp(230px,46vw,400px);height:auto;object-fit:contain;filter:grayscale(1) contrast(1.12)}
.eyebrow{display:inline-flex;align-items:center;gap:12px;font-weight:600;letter-spacing:.22em;
 text-transform:uppercase;color:#8a8a8a;font-size:14px}
.eyebrow::before{content:"";display:inline-block;width:30px;height:2px;background:#fff;flex:none}
.h1wrap{position:relative;align-self:stretch}
.h1bg{position:absolute;left:-40px;right:24%;top:6%;bottom:10%;background:#1c1c1c;transform:skewX(-8deg)}
h1{position:relative;padding:6px 0;font-size:clamp(42px,9.4vw,106px);line-height:.98;color:#fff;
 text-shadow:4px 5px 0 rgba(0,0,0,.75);text-wrap:balance}
.lede{margin:0;max-width:540px;font-size:clamp(16px,2.1vw,20px);line-height:1.55;color:#a3a3a3;text-wrap:pretty}
.cta-row{display:flex;gap:12px;flex-wrap:wrap;margin-top:6px}
.fleet{display:flex;align-items:flex-end;gap:24px;margin-top:10px;opacity:.5;flex-wrap:wrap}
.fleet .ic{width:clamp(96px,17vw,128px)}
.hazard{height:24px;opacity:.85;background:repeating-linear-gradient(
 118deg,#fff 0,#fff 9px,#0d0d0d 9px,#0d0d0d 18px,#fff 18px,#fff 22px,#0d0d0d 22px,#0d0d0d 46px)}

.btn{display:inline-flex;align-items:center;justify-content:center;text-decoration:none;
 font-family:'Barlow Condensed',sans-serif;font-weight:700;letter-spacing:.1em;
 text-transform:uppercase;min-height:48px}
.btn-solid{gap:10px;background:#fff;color:#0d0d0d;font-size:19px;padding:15px 28px}
.btn-solid:hover{background:#cfcfcf}
.btn-outline{color:#fff;font-size:19px;padding:15px 28px;border:2px solid #3d3d3d}
.btn-outline:hover{border-color:#fff}
.btn-ghost{margin-top:8px;align-self:stretch;border:2px solid #3d3d3d;color:#fff;font-size:16px;
 padding:12px 16px;min-height:46px}
.btn-ghost:hover{border-color:#fff;background:#fff;color:#0d0d0d}

.head{display:flex;align-items:center;gap:14px;margin:0 0 10px}
.head h2{font-size:clamp(30px,5.4vw,54px);color:#fff;line-height:1;text-shadow:3px 4px 0 rgba(0,0,0,.7)}
.sub{margin:0 0 30px;color:#8a8a8a;font-size:16px;max-width:540px;text-wrap:pretty}

.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(272px,1fr));gap:18px}
.card{background:#141414;border:1px solid #262626;display:flex;flex-direction:column}
.card:hover{border-color:#fff}
.shot{position:relative;width:100%;aspect-ratio:3/2;background:#101010;display:flex;
 flex-direction:column;align-items:center;justify-content:center;gap:10px;overflow:hidden}
.shot .stripes{opacity:.05}
.shot .i-ph{position:relative;width:84px;fill:#3d3d3d}
.shot span{position:relative;font-size:13px;letter-spacing:.16em;text-transform:uppercase;color:#6e6e6e}
.body{padding:18px 20px 20px;display:flex;flex-direction:column;gap:9px}
.row{display:flex;justify-content:space-between;align-items:baseline;gap:10px;flex-wrap:wrap}
.row h3{font-size:22px;color:#fff;line-height:1.1}
.price{font-family:'Anton',sans-serif;font-size:22px;color:#fff;line-height:1;border-bottom:3px solid #fff}
.specs{display:flex;align-items:center;gap:8px;font-size:14px;letter-spacing:.1em;
 text-transform:uppercase;color:#8a8a8a}
.specs .i-sm{width:24px;fill:#6e6e6e}
.note{margin:26px 0 0;color:#6e6e6e;font-size:15px;letter-spacing:.08em;text-transform:uppercase}

.divider{position:relative;height:96px;border-top:1px solid #262626;border-bottom:1px solid #262626;
 background:#000;overflow:hidden;display:flex;align-items:center}
.divider .stripes{opacity:.07}
.divider-row{position:relative;display:flex;align-items:flex-end;gap:46px;opacity:.32;padding:0 18px}
.divider-row .ic{width:76px}

.grid4{display:grid;grid-template-columns:repeat(auto-fit,minmax(250px,1fr));gap:18px}
.trust{position:relative;overflow:hidden;background:#141414;border:1px solid #262626;
 border-top:3px solid #fff;padding:24px 22px;display:flex;flex-direction:column;gap:10px}
.trust .i-bg{position:absolute;right:-14px;bottom:-8px;width:150px;opacity:.07}
.trust h3{position:relative;font-size:21px;color:#fff;line-height:1.15}
.trust p{position:relative;margin:0;color:#a3a3a3;font-size:15.5px;line-height:1.5;text-wrap:pretty}

.loc{background:#000;border-top:1px solid #262626;border-bottom:1px solid #262626}
.loc-grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(288px,1fr));gap:18px;align-items:stretch}
.col{display:flex;flex-direction:column;gap:18px}
.panel{background:#121212;border:1px solid #262626;padding:24px}
.label{font-family:'Barlow Condensed',sans-serif;font-weight:600;letter-spacing:.2em;
 text-transform:uppercase;font-size:13px;color:#8a8a8a;margin-bottom:10px}
.panel address{font-style:normal;font-size:19px;color:#fff;font-weight:600;line-height:1.4}
.dirs{display:inline-block;margin-top:12px;color:#fff;font-family:'Barlow Condensed',sans-serif;
 font-weight:700;letter-spacing:.1em;text-transform:uppercase;font-size:16px;text-decoration:none;
 border-bottom:2px solid #3d3d3d}
.dirs:hover{border-color:#fff}
.hours{display:flex;flex-direction:column;gap:8px;font-size:17px;color:#a3a3a3}
.hours div{display:flex;justify-content:space-between;gap:14px}
.hours b{color:#fff;font-weight:600}
.hours .off{color:#6e6e6e;font-weight:600}
.map{border:1px solid #262626;min-height:300px;background:#121212}
.map iframe{width:100%;height:100%;min-height:300px;border:0;display:block;
 filter:grayscale(1) invert(.92) contrast(.92)}

.contact{position:relative;overflow:hidden;background:#fff;color:#0d0d0d}
.contact .stripes{opacity:.07}
.contact-in{position:relative;max-width:1120px;margin:0 auto;padding:clamp(40px,6vw,72px) 18px;
 display:flex;flex-wrap:wrap;align-items:center;justify-content:space-between;gap:22px}
.contact h2{margin-bottom:8px;font-size:clamp(29px,5vw,50px);color:#0d0d0d;line-height:1}
.contact p{margin:0;color:#3d3d3d;font-size:16.5px}
.btn-dark{background:#0d0d0d;color:#fff;font-family:'Anton',sans-serif;
 font-size:clamp(24px,3.6vw,34px);letter-spacing:.03em;padding:17px 32px}
.btn-dark:hover{background:#262626}

footer{background:#000;padding:22px 18px 96px;text-align:center;font-size:13.5px;
 letter-spacing:.13em;text-transform:uppercase;color:#6e6e6e}

.sticky{position:fixed;left:0;right:0;bottom:0;z-index:50;gap:12px;background:#fff;color:#0d0d0d;
 font-size:18px;letter-spacing:.12em;padding:15px 16px;min-height:52px;border-top:3px solid #0d0d0d;
 box-shadow:0 -6px 18px rgba(0,0,0,.6)}
.sticky:hover{background:#cfcfcf}
.sticky .ic{width:30px;fill:#0d0d0d}

@media (prefers-reduced-motion:reduce){html{scroll-behavior:auto}}
"""


def esc(s):
    return html.escape(s, quote=False)


cards = "\n".join(f"""    <article class="card">
      <div class="shot"><div class="stripes"></div>{veh(k, 'i-ph')}<span class="cond">Photo coming soon</span></div>
      <div class="body">
        <div class="row"><h3>{esc(n)}</h3><span class="price">{esc(p)}</span></div>
        <div class="specs cond">{veh(k, 'i-sm')}<span>{esc(s)}</span></div>
        <a class="btn btn-ghost cond" href="tel:{PHONE_DIGITS}" aria-label="Call about the {html.escape(n, quote=True)}">Call About This One</a>
      </div>
    </article>""" for n, p, s, k in INVENTORY)

trust = "\n".join(f"""    <div class="trust">{veh('car', 'i-bg')}<h3>{esc(t)}</h3><p>{esc(b)}</p></div>"""
                  for t, b in TRUST)

_cycle = ["truck", "car", "suv"]
divider = "".join(veh(_cycle[i % 3]) for i in range(12))

doc = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{esc(TITLE)}</title>
<meta name="description" content="{html.escape(DESCRIPTION, quote=True)}">
<meta name="theme-color" content="#0d0d0d">
<link rel="icon" href="{FAVICON_URI}" type="image/svg+xml">
<meta property="og:type" content="website">
<meta property="og:title" content="{html.escape(TITLE, quote=True)}">
<meta property="og:description" content="{html.escape(DESCRIPTION, quote=True)}">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin="anonymous">
<link href="https://fonts.googleapis.com/css2?family=Anton&amp;family=Barlow:wght@400;500;600;700&amp;family=Barlow+Condensed:wght@500;600;700&amp;display=swap" rel="stylesheet">
<style>{CSS}</style>
<script type="application/ld+json">
{{"@context":"https://schema.org","@type":"AutoDealer","name":"I-75 Truck & Car LLC",
"telephone":"+1-937-478-7022",
"address":{{"@type":"PostalAddress","streetAddress":"{ADDR1}","addressLocality":"Dayton",
"addressRegion":"OH","postalCode":"45404","addressCountry":"US"}},
"openingHoursSpecification":[
{{"@type":"OpeningHoursSpecification","dayOfWeek":["Monday","Tuesday","Wednesday","Thursday","Friday"],"opens":"09:00","closes":"18:00"}},
{{"@type":"OpeningHoursSpecification","dayOfWeek":"Saturday","opens":"10:00","closes":"15:00"}}]}}
</script>
</head>
<body>
{SPRITE}

<div class="topbar cond">
  <span>{ADDR1}, {ADDR2}</span>
  <a href="tel:{PHONE_DIGITS}">{PHONE}</a>
</div>

<section id="top" class="hero">
  <div class="stripes"></div>
  <div class="hero-in">
    <img class="logo" src="logo.webp" width="{LOGO_W}" height="{LOGO_H}" fetchpriority="high" decoding="async"
         alt="I-75 Truck &amp; Car LLC &mdash; {ADDR1}, {ADDR2}, {PHONE}">
    <div class="eyebrow cond">Used Trucks &amp; Cars &middot; Dayton, Ohio</div>
    <div class="h1wrap">
      <div class="h1bg" aria-hidden="true"></div>
      <h1>TRUCKS &amp; CARS<br>WORTH DRIVING</h1>
    </div>
    <p class="lede">Straight-shooting used vehicle sales off I-75. Every truck and car on the lot is
      inspected before it&rsquo;s listed &mdash; no surprises, no runaround.</p>
    <div class="cta-row">
      <a class="btn btn-solid cond" href="tel:{PHONE_DIGITS}">Call Now &mdash; {PHONE}</a>
      <a class="btn btn-outline cond" href="#inventory">View Inventory</a>
    </div>
    <div class="fleet" aria-hidden="true">{veh('truck')}{veh('car')}{veh('suv')}</div>
  </div>
  <div class="hazard" aria-hidden="true"></div>
</section>

<section id="inventory" class="wrap">
  <div class="head">{shield('01')}<h2>FEATURED VEHICLES</h2></div>
  <p class="sub">Inventory changes weekly. Call about anything you see &mdash; or tell us what you&rsquo;re hunting for.</p>
  <div class="grid">
{cards}
  </div>
  <p class="note cond">Don&rsquo;t see it? We source trucks and cars on request &mdash; call and tell us the year, make and budget.</p>
</section>

<div class="divider" aria-hidden="true">
  <div class="stripes"></div>
  <div class="divider-row">{divider}</div>
</div>

<section id="why" class="wrap">
  <div class="head">{shield('02')}<h2>WHY BUY FROM US</h2></div>
  <p class="sub">Small lot, plain terms. You deal with the people who actually looked the vehicle over.</p>
  <div class="grid4">
{trust}
  </div>
</section>

<section id="location" class="loc">
  <div class="wrap">
    <div class="head">{shield('03')}<h2>VISIT THE LOT</h2></div>
    <p class="sub">Just off I-75 &mdash; that&rsquo;s the name.</p>
    <div class="loc-grid">
      <div class="col">
        <div class="panel">
          <div class="label">Address</div>
          <address>{ADDR1}<br>{ADDR2}</address>
          <a class="dirs" href="https://maps.google.com/?q={MAPS_Q}" target="_blank" rel="noopener">Get Directions &rarr;</a>
        </div>
        <div class="panel" style="flex:1">
          <div class="label">Hours</div>
          <div class="hours">
            <div><span>Mon&ndash;Fri</span><b>9:00 AM &ndash; 6:00 PM</b></div>
            <div><span>Saturday</span><b>10:00 AM &ndash; 3:00 PM</b></div>
            <div><span>Sunday</span><span class="off">By appointment</span></div>
          </div>
        </div>
      </div>
      <div class="map">
        <iframe title="Map to I-75 Truck &amp; Car, {ADDR1} {ADDR2}" loading="lazy"
          referrerpolicy="no-referrer-when-downgrade"
          src="https://www.google.com/maps?q={MAPS_Q}&amp;output=embed"></iframe>
      </div>
    </div>
  </div>
</section>

<section id="contact" class="contact">
  <div class="stripes dark"></div>
  <div class="contact-in">
    <div>
      <h2>READY TO DRIVE IT?</h2>
      <p>Call the lot and we&rsquo;ll have it pulled up front and warmed up.</p>
    </div>
    <a class="btn btn-dark" href="tel:{PHONE_DIGITS}">{PHONE}</a>
  </div>
</section>

<footer class="cond">
  &copy; 2026 I-75 Truck &amp; Car LLC &middot; {ADDR1}, {ADDR2} &middot; Used Truck &amp; Car Sales
</footer>

<a class="btn sticky cond" href="tel:{PHONE_DIGITS}">{veh('truck')}Call the Lot &mdash; {PHONE}</a>
</body>
</html>
"""

(OUT / "index.html").write_text(doc, encoding="utf-8")

from PIL import Image

_logo = Image.open(LOGO_SRC).convert("RGBA").resize((LOGO_W, LOGO_H), Image.LANCZOS)
# The hero applies filter: grayscale(1), so colour data is discarded at paint
# time anyway; storing it grayscale is smaller for an identical result.
_alpha = _logo.getchannel("A")
_logo = _logo.convert("L").convert("RGBA")
_logo.putalpha(_alpha)
_logo.save(OUT / "logo.webp", "WEBP", quality=LOGO_QUALITY, method=6)

print("index.html", len(doc), "bytes")
print("logo.webp ", (OUT / "logo.webp").stat().st_size, "bytes")
