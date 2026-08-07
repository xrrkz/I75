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
    'fill="none" stroke="#ffffff" stroke-width="6"/></symbol>'
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
    '<rect width="100" height="100" fill="#0a0a0a"/>'
    '<path d="M50 3.5C40 3.5 30 5.5 24 7.5 20 8.8 12 10 5.5 10c0 0 2 8 2 16v18.5C7.5 68 30 86.5 50 96.5 '
    '70 86.5 92.5 68 92.5 44.5V26c0-8 2-16 2-16C88 10 80 8.8 76 7.5 70 5.5 60 3.5 50 3.5Z" '
    'fill="#0d0d0d" stroke="#fff" stroke-width="7"/>'
    '<text x="50" y="58" text-anchor="middle" fill="#fff" '
    'font-family="Arial Black, Arial, sans-serif" font-size="30" font-weight="bold">75</text></svg>'
)
FAVICON_URI = "data:image/svg+xml;base64," + base64.b64encode(FAVICON_SVG.encode()).decode()

CSS = """
/* ---- Metric-matched fallbacks -----------------------------------------
   Anton sets far narrower than Arial, Barlow Condensed narrower still. Left
   unadjusted the fallback draws the headline much wider, it wraps to a
   different number of lines, and the whole page relaid out when the webfont
   swapped in. size-adjust scales the fallback to the same advance so the line
   count matches either way; the ascent/descent overrides keep the line box the
   same height at that new scale.

   The percentages are calibrated on the strings long enough to decide a line
   break, not on an average over the alphabet. Anton's letters run ~69% of
   Arial's advance while its digits run ~89%; averaging the two leaves the
   headline ~15% too wide, which at 320px overflows the column and wraps to
   four lines. Short numeric runs like prices never wrap, so letting them pull
   the average only mis-sizes the copy that does.

   local() only -- these download nothing. Liberation Sans is metric-identical
   to Arial and Helvetica is metric-compatible, so one set of numbers covers
   Windows, macOS and most Linux. Where none resolve the face fails and the
   stack falls through to sans-serif, i.e. exactly today's behaviour. */
@font-face{font-family:'Anton Fb';src:local('Arial'),local('Helvetica'),local('Liberation Sans');
 size-adjust:69.34%;ascent-override:202.53%;descent-override:47.46%;line-gap-override:0%}
@font-face{font-family:'Barlow Fb';src:local('Arial'),local('Helvetica'),local('Liberation Sans');
 size-adjust:96.79%;ascent-override:114.89%;descent-override:25.73%;line-gap-override:0%}
@font-face{font-family:'BarlowC Fb';src:local('Arial'),local('Helvetica'),local('Liberation Sans');
 size-adjust:66.62%;ascent-override:161.37%;descent-override:41.13%;line-gap-override:0%}

*,*::before,*::after{box-sizing:border-box}
html{scroll-behavior:smooth}
body{margin:0;background:#0a0a0a;color:#d6d6d6;font-family:'Barlow','Barlow Fb',sans-serif;
 -webkit-font-smoothing:antialiased;min-width:320px;overflow-x:hidden}
h1,h2,h3{font-family:'Anton','Anton Fb',sans-serif;font-weight:400;margin:0}
/* The skew is the one bit of motorsport italic kept on type. Shallower than a
   real oblique so it reads as lean rather than as a novelty. */
h1,h2,h3{transform:skewX(-6deg)}
.cond{font-family:'Barlow Condensed','BarlowC Fb',sans-serif}
.ic{fill:#fff;height:auto;flex:none}
/* Timing-board numerals: figures line up column-wise in prices and hours. */
.num{font-variant-numeric:tabular-nums}
:focus-visible{outline:2px solid #fff;outline-offset:3px}

/* Two racing motifs carry the whole page, each used sparingly:
   .road   a lane of highway closing the hero.
   .stripe the paired racing stripe, as a section and card marker.
   The old diagonal hazard texture is gone — it ran behind five separate
   sections and was doing most of the visual shouting. */

/* Highway lane markings rather than a chequered flag. The lot is named for the
   interstate, so the road is the more specific image -- and a dashed centre
   line sliding past is legible motion, where a 14px chequerboard was really
   just texture. Dashes are a repeating gradient on a pseudo-element that
   overhangs both edges, so translating it by exactly one period loops with no
   visible seam. */
.road{position:relative;height:34px;overflow:hidden;background:#111;
 border-top:1px solid #1a1a1a;border-bottom:1px solid #1a1a1a}
.road .lane{position:absolute;left:-140px;right:-140px;top:50%;height:2px;margin-top:-1px;opacity:.6;
 background:repeating-linear-gradient(90deg,#fff 0,#fff 44px,transparent 44px,transparent 110px)}
/* Fades the lane into the page edges so it reads as passing through rather
   than starting and stopping at the viewport. */
.road::after{content:"";position:absolute;inset:0;pointer-events:none;
 background:linear-gradient(90deg,#0a0a0a,transparent 14%,transparent 86%,#0a0a0a)}
.stripe{display:inline-block;width:32px;height:8px;flex:none;
 background:linear-gradient(#fff 0,#fff 3px,transparent 3px,transparent 5px,#fff 5px,#fff 8px)}

.wrap{max-width:1080px;margin:0 auto;padding:clamp(48px,7vw,88px) 20px}
/* The silhouette divider that used to sit between these sections is gone;
   a hairline frames the whitespace so the gap reads as spacing, not a void. */
#why{border-top:1px solid #1a1a1a}

.topbar{border-bottom:1px solid #1a1a1a;padding:12px 20px;display:flex;
 justify-content:space-between;align-items:center;gap:14px;flex-wrap:wrap;font-size:12px;
 letter-spacing:.2em;text-transform:uppercase;color:#6a6a6a}
/* Padding cancelled by an equal negative margin: the tap target grows to ~32px
   without moving the number, which at 12px type would otherwise be a 14px-tall
   target on the one action this page exists to drive. */
.topbar a{color:#fff;text-decoration:none;display:inline-block;padding:9px 4px;margin:-9px -4px}
.topbar a:hover{color:#9a9a9a}

.hero{border-bottom:1px solid #1a1a1a}
.hero-in{max-width:1080px;margin:0 auto;
 padding:clamp(44px,8vw,96px) 20px clamp(48px,8vw,100px);
 display:flex;flex-direction:column;align-items:flex-start;gap:22px}
/* Typographic lockup in place of the logo photo: the highway shield already
   carries the "75", so the wordmark only has to say the rest. Keeps the
   business identified at the top of the page without a raster image. */
.brand{display:flex;align-items:center;gap:12px}
.brand .shield{width:38px;height:42px}
.brand-name{font-family:'Anton','Anton Fb',sans-serif;font-size:clamp(19px,2.4vw,24px);
 letter-spacing:.03em;color:#fff;transform:skewX(-6deg)}
.eyebrow{display:inline-flex;align-items:center;gap:14px;font-weight:600;letter-spacing:.26em;
 text-transform:uppercase;color:#7a7a7a;font-size:12px}
h1{font-size:clamp(44px,9vw,104px);line-height:.95;color:#fff;text-wrap:balance}
.lede{margin:0;max-width:500px;font-size:clamp(16px,2vw,19px);line-height:1.6;color:#8a8a8a;text-wrap:pretty}
.cta-row{display:flex;gap:14px;flex-wrap:wrap;margin-top:4px}

.btn{display:inline-flex;align-items:center;justify-content:center;text-decoration:none;
 font-family:'Barlow Condensed','BarlowC Fb',sans-serif;font-weight:700;letter-spacing:.16em;
 text-transform:uppercase;min-height:48px;transition:background .15s,border-color .15s,color .15s}
.btn-solid{background:#fff;color:#0a0a0a;font-size:16px;padding:14px 26px}
.btn-solid:hover{background:#c4c4c4}
.btn-outline{color:#fff;font-size:16px;padding:14px 26px;border:1px solid #333}
.btn-outline:hover{border-color:#fff}
.btn-ghost{margin-top:10px;align-self:stretch;border:1px solid #262626;color:#fff;font-size:13px;
 padding:12px 16px;min-height:46px}
.btn-ghost:hover{border-color:#fff;background:#fff;color:#0a0a0a}

.head{display:flex;align-items:center;gap:16px;margin:0 0 14px}
.head h2{font-size:clamp(28px,4.6vw,46px);color:#fff;line-height:1}
.shield{width:36px;height:40px;overflow:visible;fill:none}
.shield text{font-family:'Anton','Anton Fb',sans-serif;font-size:36px;letter-spacing:1px}
.sub{margin:0 0 40px;color:#6e6e6e;font-size:15.5px;max-width:520px;line-height:1.6;text-wrap:pretty}

/* Hairline grids: the 1px gap over a light background paints the rules, so
   cards need no borders of their own and nothing doubles up at the seams. */
.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(264px,1fr));
 gap:1px;background:#1a1a1a;border:1px solid #1a1a1a}
.card{background:#0a0a0a;display:flex;flex-direction:column;transition:background .15s}
.card:hover{background:#101010}
/* Empty photo slot: flat, with hairline corner marks so it reads as a frame
   waiting for a photo rather than an image that failed to load. */
.shot{position:relative;width:100%;aspect-ratio:16/10;background:#0e0e0e;display:flex;
 flex-direction:column;align-items:center;justify-content:center;gap:10px}
.shot .i-ph{width:92px;fill:#333}
.shot span{font-size:10.5px;letter-spacing:.26em;text-transform:uppercase;color:#5a5a5a}
/* Scoped under .shot deliberately: the corner marks are <span>s, so a bare
   .mk rule would lose to `.shot span` above and they would stay in the flex
   flow instead of pinning to the corners. */
.shot .mk{position:absolute;width:13px;height:13px;border:1px solid #282828}
.shot .mk.tl{top:12px;left:12px;border-right:0;border-bottom:0}
.shot .mk.tr{top:12px;right:12px;border-left:0;border-bottom:0}
.shot .mk.bl{bottom:12px;left:12px;border-right:0;border-top:0}
.shot .mk.rb{bottom:12px;right:12px;border-left:0;border-top:0}
.body{padding:20px;display:flex;flex-direction:column;gap:10px}
.row{display:flex;justify-content:space-between;align-items:baseline;gap:12px;flex-wrap:wrap}
.row h3{font-size:19px;color:#fff;line-height:1.15}
.price{font-family:'Anton','Anton Fb',sans-serif;font-size:19px;color:#fff;line-height:1}
.specs{font-size:11.5px;letter-spacing:.2em;text-transform:uppercase;color:#6a6a6a}
.note{margin:32px 0 0;color:#6e6e6e;font-size:12px;letter-spacing:.2em;text-transform:uppercase}

.grid4{display:grid;grid-template-columns:repeat(auto-fit,minmax(240px,1fr));
 gap:1px;background:#1a1a1a;border:1px solid #1a1a1a}
.trust{background:#0a0a0a;padding:26px 24px;display:flex;flex-direction:column;gap:12px}
.trust h3{font-size:17px;color:#fff;line-height:1.25}
.trust p{margin:0;color:#7a7a7a;font-size:14.5px;line-height:1.6;text-wrap:pretty}

.loc{border-top:1px solid #1a1a1a;border-bottom:1px solid #1a1a1a}
.loc-grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(280px,1fr));
 gap:1px;background:#1a1a1a;border:1px solid #1a1a1a}
.col{display:flex;flex-direction:column;gap:1px;background:#1a1a1a}
.panel{background:#0a0a0a;padding:26px 24px}
.label{font-family:'Barlow Condensed','BarlowC Fb',sans-serif;font-weight:600;letter-spacing:.24em;
 text-transform:uppercase;font-size:11px;color:#5a5a5a;margin-bottom:12px}
.panel address{font-style:normal;font-size:17px;color:#fff;font-weight:500;line-height:1.5}
.dirs{display:inline-block;margin-top:8px;padding:6px 0;color:#fff;font-family:'Barlow Condensed','BarlowC Fb',sans-serif;
 font-weight:700;letter-spacing:.16em;text-transform:uppercase;font-size:13px;text-decoration:none;
 border-bottom:1px solid #333}
.dirs:hover{border-color:#fff}
.hours{display:flex;flex-direction:column;gap:10px;font-size:15px;color:#8a8a8a}
.hours div{display:flex;justify-content:space-between;gap:14px}
.hours b{color:#fff;font-weight:500}
.hours .off{color:#5a5a5a;font-weight:500}
.map{background:#0e0e0e;min-height:300px}
.map iframe{width:100%;height:100%;min-height:300px;border:0;display:block;
 filter:grayscale(1) invert(.92) contrast(.92)}

.contact{background:#fff;color:#0a0a0a}
.contact-in{max-width:1080px;margin:0 auto;padding:clamp(44px,6vw,76px) 20px;
 display:flex;flex-wrap:wrap;align-items:center;justify-content:space-between;gap:24px}
.contact h2{margin-bottom:10px;font-size:clamp(26px,4.4vw,44px);color:#0a0a0a;line-height:1}
.contact p{margin:0;color:#555;font-size:15.5px}
.btn-dark{background:#0a0a0a;color:#fff;font-family:'Anton','Anton Fb',sans-serif;
 font-size:clamp(22px,3.2vw,30px);letter-spacing:.04em;padding:16px 30px}
.btn-dark:hover{background:#262626}

footer{border-top:1px solid #1a1a1a;padding:26px 20px 96px;text-align:center;font-size:11px;
 letter-spacing:.22em;text-transform:uppercase;color:#5c5c5c}

.sticky{position:fixed;left:0;right:0;bottom:0;z-index:50;background:#fff;color:#0a0a0a;
 font-size:14px;letter-spacing:.2em;padding:14px 16px;min-height:50px}
.sticky:hover{background:#c4c4c4}

/* ---- Load-in sequence -------------------------------------------------
   Hero only: it is what is on screen at load, and animating the sections
   below would spend the motion where nobody is looking.

   Every element animates from a hidden `from` state held by
   animation-fill-mode:both, which is what produces the stagger without a
   separate initial rule. That also means these keyframes are the ONLY thing
   hiding anything -- if the stylesheet fails to load, the markup renders
   plain and fully visible rather than blank.

   Only opacity/transform/clip-path animate, so nothing here reflows and the
   sequence contributes no layout shift. */
@keyframes riseIn{from{opacity:0;transform:translateY(14px)}to{opacity:1;transform:none}}
@keyframes slideIn{from{opacity:0;transform:translateX(-38px)}to{opacity:1;transform:none}}
@keyframes fadeIn{from{opacity:0}to{opacity:1}}
@keyframes growX{from{transform:scaleX(0)}to{transform:scaleX(1)}}
/* A wipe, not a scaleX: scaling would stretch the checker squares on the way
   in. clip-path reveals the pattern at its true size. */
@keyframes wipeX{from{clip-path:inset(0 100% 0 0)}to{clip-path:inset(0 0 0 0)}}
@keyframes riseUp{from{transform:translateY(100%)}to{transform:none}}

.topbar{animation:fadeIn .45s ease both}
.brand{animation:riseIn .55s cubic-bezier(.16,.84,.3,1) .05s both}
.eyebrow{animation:riseIn .5s cubic-bezier(.16,.84,.3,1) .18s both}
/* Scoped to the hero: the trust cards reuse .stripe far below the fold. */
.eyebrow .stripe{transform-origin:left;animation:growX .45s cubic-bezier(.16,.84,.3,1) .40s both}
/* Per-line stagger, so the two lines arrive like a car passing. The spans
   carry the motion because the h1 itself owns the -6deg skew -- animating
   transform on the parent would overwrite it. */
h1 span{display:block;animation:slideIn .6s cubic-bezier(.16,.84,.3,1) both}
h1 span:nth-child(1){animation-delay:.26s}
h1 span:nth-child(2){animation-delay:.36s}
.lede{animation:riseIn .55s cubic-bezier(.16,.84,.3,1) .52s both}
/* Animation on the base rule, delay alone on the nth-child -- same shape as
   `h1 span` above. Putting the shorthand on `:nth-child()` would raise its
   specificity above the reduced-motion reset below, which would leave these
   buttons animating (and starting from opacity 0) for exactly the users who
   asked for no motion. */
.cta-row .btn{animation:riseIn .45s cubic-bezier(.16,.84,.3,1) both}
.cta-row .btn:nth-child(1){animation-delay:.62s}
.cta-row .btn:nth-child(2){animation-delay:.70s}
/* The strip wipes in with the rest of the hero; the dashes inside it run on
   their own element so the two never contend for the same property. One
   period is 110px, so that is exactly how far the lane travels per cycle. */
@keyframes lane{from{transform:translateX(0)}to{transform:translateX(-110px)}}
.road{animation:wipeX .6s cubic-bezier(.3,.7,.4,1) .80s both}
.road .lane{animation:lane 1.9s linear 1.4s infinite}
.sticky{animation:riseUp .5s cubic-bezier(.16,.84,.3,1) .95s both}

/* ---- Interaction ------------------------------------------------------
   Gated behind hover:hover so a touch device never gets stuck in a hover
   state it cannot leave. Transitions only, so anything interrupted midway
   reverses cleanly. */
@media (hover:hover){
 /* The lift uses `translate`, not `transform`. These elements already carry a
    keyframe animation that sets transform with fill:both -- the scroll reveal
    here, the load-in on the buttons -- and an animated value beats a plain
    declaration in the cascade, so a `transform` hover would silently never
    apply. `translate` is a separate property, so the two compose. */
 .card{transition:background .18s ease,translate .18s cubic-bezier(.16,.84,.3,1)}
 .card:hover{translate:0 -3px}
 .shot .i-ph{transition:fill .25s ease,transform .35s cubic-bezier(.16,.84,.3,1)}
 .card:hover .i-ph{fill:#555;transform:translateX(5px)}
 /* The corner marks pull outward on hover like a viewfinder locking on.
    Transform rather than inset so it stays off the layout path. */
 .shot .mk{transition:border-color .2s ease,transform .3s cubic-bezier(.16,.84,.3,1)}
 .card:hover .mk{border-color:#4a4a4a}
 .card:hover .mk.tl{transform:translate(-4px,-4px)}
 .card:hover .mk.tr{transform:translate(4px,-4px)}
 .card:hover .mk.bl{transform:translate(-4px,4px)}
 .card:hover .mk.rb{transform:translate(4px,4px)}
 .btn-solid:hover,.btn-dark:hover{translate:0 -2px}
 .btn-solid,.btn-dark{transition:background .15s ease,translate .18s cubic-bezier(.16,.84,.3,1)}
}
/* Speed line: a raked streak crossing the button on hover. Runs as an
   animation rather than a transition so it replays on every hover instead of
   sliding back on mouse-out. The streak is a pseudo-element clipped by the
   button, so it costs no layout and cannot escape the shape. */
@keyframes sweep{
 0%{opacity:0;transform:translateX(0) skewX(-18deg)}
 12%{opacity:1}
 100%{opacity:0;transform:translateX(460%) skewX(-18deg)}}
.btn{position:relative;overflow:hidden}
.btn::before{content:"";position:absolute;top:-30%;bottom:-30%;left:-55%;width:38%;
 opacity:0;pointer-events:none;transform:translateX(0) skewX(-18deg)}
/* Streak colour follows the surface it crosses, not the variant name: white
   over the dark buttons, dark over the light ones. .btn-ghost inverts to a
   white background exactly when it is hovered, so it takes the dark streak. */
.btn-outline::before,.btn-dark::before{
 background:linear-gradient(90deg,transparent,rgba(255,255,255,.55),transparent)}
.btn-solid::before,.btn-ghost::before,.sticky::before{
 background:linear-gradient(90deg,transparent,rgba(0,0,0,.24),transparent)}
@media (hover:hover){
 .btn:hover::before{animation:sweep .62s cubic-bezier(.3,.6,.4,1)}
 /* Also fire it when a card hover lights up its call button, so the streak
    tracks the same intent the arrow does. */
 .card:hover .btn-ghost::before{animation:sweep .62s cubic-bezier(.3,.6,.4,1)}
}
/* Throttle blip: the press dips the button. Declared after the hover lifts so
   it wins at equal specificity while the pointer is still down. */
.btn:active{translate:0 1px}

/* The arrow is always in flow and only opacity/transform change, so revealing
   it cannot reflow the button or shift the card. */
.btn-ghost::after,.btn-solid::after,.btn-dark::after{content:"\\2192";margin-left:9px;
 opacity:0;transform:translateX(-5px);transition:opacity .2s ease,transform .25s cubic-bezier(.16,.84,.3,1)}
.card:hover .btn-ghost::after,.btn-ghost:hover::after,.btn-ghost:focus-visible::after,
.btn-solid:hover::after,.btn-solid:focus-visible::after,
.btn-dark:hover::after,.btn-dark:focus-visible::after{opacity:1;transform:none}
/* Underline drawn on hover, over the resting hairline. */
.dirs{background-image:linear-gradient(#fff,#fff);background-repeat:no-repeat;
 background-position:0 100%;background-size:0 1px;transition:background-size .3s cubic-bezier(.16,.84,.3,1)}
.dirs:hover,.dirs:focus-visible{background-size:100% 1px}

/* ---- Scroll reveal ----------------------------------------------------
   Scroll-driven, so each block animates when it actually arrives rather than
   playing unseen at load. @supports keeps it opt-in: browsers without
   animation-timeline get no rule at all and render everything visible, which
   is why the guard wraps the whole block rather than just the timeline. */
@supports (animation-timeline:view()){
 @media (prefers-reduced-motion:no-preference){
  .card,.trust,.panel,.map,.wrap>.head,.wrap>.sub,.loc .head,.loc .sub{
   animation:riseIn linear both;animation-timeline:view();animation-range:entry 0% entry 55%}
  /* Column offset turns a row arriving together into a diagonal sweep. */
  .grid .card:nth-child(3n+2),.grid4 .trust:nth-child(4n+2){animation-range:entry 6% entry 61%}
  .grid .card:nth-child(3n+3),.grid4 .trust:nth-child(4n+3){animation-range:entry 12% entry 67%}
  .grid4 .trust:nth-child(4n+4){animation-range:entry 18% entry 73%}
 }
}

@media (prefers-reduced-motion:reduce){
 html{scroll-behavior:auto}
 /* No motion at all rather than faster motion: with the animations off each
    element sits at its resting state, which is the visible one. */
 .topbar,.brand,.eyebrow,.eyebrow .stripe,h1 span,.lede,.cta-row .btn,.road,.road .lane,.sticky{
  animation:none}
 /* The speed line and the press dip are motion too. */
 .btn:hover::before,.card:hover .btn-ghost::before{animation:none}
 .btn:active{translate:none}
 /* Transitions too: a hover lift is still motion. */
 .card,.shot .i-ph,.shot .mk,.btn-solid,.btn-dark,.dirs,
 .btn-ghost::after,.btn-solid::after,.btn-dark::after{transition:none}
 .card:hover,.btn-solid:hover,.btn-dark:hover{translate:none}
}
"""


def esc(s):
    return html.escape(s, quote=False)


cards = "\n".join(f"""    <article class="card">
      <div class="shot"><span class="mk tl"></span><span class="mk tr"></span><span class="mk bl"></span><span class="mk rb"></span>{veh(k, 'i-ph')}<span class="cond">Photo coming soon</span></div>
      <div class="body">
        <div class="row"><h3>{esc(n)}</h3><span class="price num">{esc(p)}</span></div>
        <div class="specs cond num">{esc(s)}</div>
        <a class="btn btn-ghost cond" href="tel:{PHONE_DIGITS}" aria-label="Call about the {html.escape(n, quote=True)}">Call About This One</a>
      </div>
    </article>""" for n, p, s, k in INVENTORY)

trust = "\n".join(f"""    <div class="trust"><span class="stripe" aria-hidden="true"></span><h3>{esc(t)}</h3><p>{esc(b)}</p></div>"""
                  for t, b in TRUST)

doc = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{esc(TITLE)}</title>
<meta name="description" content="{html.escape(DESCRIPTION, quote=True)}">
<meta name="theme-color" content="#0a0a0a">
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
  <div class="hero-in">
    <div class="brand">{shield('75')}<span class="brand-name">I-75 Truck &amp; Car</span></div>
    <div class="eyebrow cond"><span class="stripe" aria-hidden="true"></span>Used Trucks &amp; Cars &middot; Dayton, Ohio</div>
    <h1><span>TRUCKS &amp; CARS</span> <span>WORTH DRIVING</span></h1>  <!-- the space between the spans is deliberate: with display:block it is
       discarded, but if the stylesheet never loads the spans fall back to
       inline and it keeps the two lines from running together. -->
    <p class="lede">Straight-shooting used vehicle sales off I-75. Every truck and car on the lot is
      inspected before it&rsquo;s listed &mdash; no surprises, no runaround.</p>
    <div class="cta-row">
      <a class="btn btn-solid cond" href="tel:{PHONE_DIGITS}">Call Now &mdash; {PHONE}</a>
      <a class="btn btn-outline cond" href="#inventory">View Inventory</a>
    </div>
  </div>
  <div class="road" aria-hidden="true"><div class="lane"></div></div>
</section>

<section id="inventory" class="wrap">
  <div class="head">{shield('01')}<h2>FEATURED VEHICLES</h2></div>
  <p class="sub">Inventory changes weekly. Call about anything you see &mdash; or tell us what you&rsquo;re hunting for.</p>
  <div class="grid">
{cards}
  </div>
  <p class="note cond">Don&rsquo;t see it? We source trucks and cars on request &mdash; call and tell us the year, make and budget.</p>
</section>

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
          <div class="hours num">
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
  <div class="contact-in">
    <div>
      <h2>READY TO DRIVE IT?</h2>
      <p>Call the lot and we&rsquo;ll have it pulled up front and warmed up.</p>
    </div>
    <a class="btn btn-dark num" href="tel:{PHONE_DIGITS}">{PHONE}</a>
  </div>
</section>

<footer class="cond">
  &copy; 2026 I-75 Truck &amp; Car LLC &middot; {ADDR1}, {ADDR2} &middot; Used Truck &amp; Car Sales
</footer>

<a class="btn sticky cond" href="tel:{PHONE_DIGITS}">Call the Lot &mdash; {PHONE}</a>
</body>
</html>
"""

(OUT / "index.html").write_text(doc, encoding="utf-8")


print("index.html", len(doc), "bytes")
