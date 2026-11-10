#!/usr/bin/env python3
"""
Render the profile README's cards as animated SVGs into cards/.

Design: "Three Worlds" (Paper, Ink, and Three World colors: BUILD blue, BRAND red, LEARN yellow;
Instrument Serif, Geist, Geist Mono), matched to the original clean white/paper aesthetic.

Every card is a standalone SVG displayed through <img>, utilizing inline CSS
animations, SMIL elements, and base64 embedded subset WOFF fonts.
Supports STATIC=1 mode for static screenshot rendering.
"""
import base64
import datetime
import json
import os
import re
from html import escape

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(HERE, "..")
DATA = os.path.join(ROOT, "data", "contributions.json")
OUT = os.path.join(ROOT, "cards")
FONTS = os.path.join(ROOT, "fonts")
PORTRAIT = os.path.join(ROOT, "ramraj-ascii.svg")

# Fallback portrait if ramraj-ascii.svg isn't ready
if not os.path.exists(PORTRAIT):
    PORTRAIT = os.path.join(ROOT, "source-prepped.png")

# ---- user profile details ---------------------------------------------------
USERNAME = "rathod-ramraj"
FULL_NAME_FIRST = "Rathod"
FULL_NAME_LAST = "Ramraj"
HEADLINE = "FULLSTACK DEVELOPER · NIT JALANDHAR"
TAGLINE = [
    "Crafting scalable web apps, high-performance backends,",
    "and cinematic user interfaces.",
]
SITE_URL = "rathodram.pages.dev"

# ---- brand tokens: clean paper theme ----------------------------------------
PAPER = "#f3f3f1"
PAPER_DEEP = "#e2e2de"
INK = "#111111"
INK_SOFT = "#3a3a3c"
MUTED = "#6e6e73"
RULE = "#dcdcd7"
TECH = "#2f55ff"      # BUILD Blue
STUDIO = "#ef3b2d"    # BRAND Red
LEARN = "#ffc81a"     # LEARN Yellow
W = 880  # full card width, GitHub's README column at 100%

SERIF = "'Instrument Serif', Georgia, serif"
SANS = "Geist, system-ui, -apple-system, sans-serif"
MONO = "'Geist Mono', ui-monospace, SFMono-Regular, Menlo, monospace"

FONT_FILES = {
    "serif": ("Instrument Serif", "normal", 400, "serif-400.woff"),
    "serif-i": ("Instrument Serif", "italic", 400, "serif-italic.woff"),
    "sans": ("Geist", "normal", 400, "geist-400.woff"),
    "sans-b": ("Geist", "normal", 600, "geist-600.woff"),
    "mono": ("Geist Mono", "normal", 400, "geistmono-400.woff"),
}

BASE_CSS = """
@keyframes rise{from{opacity:0;transform:translateY(16px)}to{opacity:1;transform:none}}
@keyframes fade{from{opacity:0}to{opacity:1}}
@keyframes grow{from{transform:scaleY(0)}to{transform:scaleY(1)}}
@keyframes pop{0%{opacity:0;transform:scale(.3)}70%{opacity:1;transform:scale(1.15)}100%{opacity:1;transform:none}}
@keyframes pulse{0%,100%{opacity:1}50%{opacity:.25}}
@keyframes nudge{0%,100%{transform:none}50%{transform:translateX(4px)}}
@keyframes nudgeup{0%,100%{transform:none}50%{transform:translate(3px,-3px)}}
.r{opacity:0;animation:rise .8s cubic-bezier(.2,.7,.2,1) both;transform-box:fill-box}
.f{opacity:0;animation:fade .9s ease-out both}
.g{transform-box:fill-box;transform-origin:bottom;transform:scaleY(0);animation:grow .8s cubic-bezier(.2,.7,.2,1) both}
.p{opacity:0;transform-box:fill-box;transform-origin:center;animation:pop .4s ease-out both}
.live{animation:pulse 1.6s ease-in-out infinite}
.n{transform-box:fill-box;animation:nudge 1.8s ease-in-out infinite}
.nu{transform-box:fill-box;animation:nudgeup 1.8s ease-in-out infinite}
@keyframes tilein{0%{opacity:0;transform:translateY(90px) scale(.6) rotate(-9deg)}55%{opacity:1;transform:translateY(-10px) scale(1.05) rotate(2deg)}75%{transform:translateY(3px) scale(.98) rotate(-.8deg)}90%{transform:translateY(-1px) scale(1.01) rotate(.2deg)}100%{opacity:1;transform:none}}
@keyframes slidein{from{opacity:0;transform:translateX(-26px)}to{opacity:1;transform:none}}
@keyframes arrowin{0%{opacity:0;transform:translateX(-30px)}60%{opacity:1;transform:translateX(6px)}100%{opacity:1;transform:none}}
@keyframes roll{from{transform:translateY(60px)}to{transform:none}}
@keyframes sheen{0%{transform:translateX(-260px) skewX(-20deg)}22%,100%{transform:translateX(420px) skewX(-20deg)}}
@keyframes ring{0%{opacity:.7;transform:scale(.2)}100%{opacity:0;transform:scale(2.4)}}
.ti{opacity:0;transform-box:fill-box;transform-origin:50% 60%;animation:tilein 1.1s cubic-bezier(.2,.8,.2,1) both}
.sl{opacity:0;transform-box:fill-box;animation:slidein .6s cubic-bezier(.2,.7,.2,1) both}
.ai{opacity:0;transform-box:fill-box;animation:arrowin .7s cubic-bezier(.2,.7,.2,1) both}
.ro{transform-box:fill-box;animation:roll .8s cubic-bezier(.15,.8,.2,1) both}
.sh{animation:sheen 5s ease-in-out infinite}
.rg{opacity:0;transform-box:fill-box;transform-origin:center;animation:ring 1s ease-out both}
@media (prefers-reduced-motion: reduce){
  .r,.f,.g,.p,.live,.n,.nu,.ti,.sl,.ai,.ro,.rg{animation:none!important;opacity:1!important;transform:none!important}
  .sh,.rg{display:none}
}
"""


def font_face(keys):
    out = []
    for k in keys:
        fam, style, weight, fn = FONT_FILES[k]
        path = os.path.join(FONTS, fn)
        if os.path.exists(path):
            b64 = base64.b64encode(open(path, "rb").read()).decode()
            out.append(
                f"@font-face{{font-family:'{fam}';font-style:{style};font-weight:{weight};"
                f"src:url(data:font/woff;base64,{b64}) format('woff')}}"
            )
    return "".join(out)


BOTTOM = 12       # bottom padding per row


def svg(w, h, body, fonts, label, extra_css="", left=0, right=0, bottom=BOTTOM):
    """Card of w x h drawn at x=left inside a transparent canvas, padded so rows tile exactly."""
    if left:
        body = f'<g transform="translate({left:.3f} 0)">{body}</g>'
    w_total, h_total = w + left + right, h + bottom
    css = font_face(fonts) + BASE_CSS + extra_css
    if os.environ.get("STATIC") == "1":
        css += (
            ".r,.f,.g,.p,.live,.n,.nu,.ti,.sl,.ai,.ro{animation:none!important;"
            "opacity:1!important;transform:none!important}.sh,.rg{display:none}"
        )
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{w_total:.3f}" height="{h_total}" '
        f'viewBox="0 0 {w_total:.3f} {h_total}" role="img" aria-label="{escape(label)}">'
        f'<title>{escape(label)}</title>'
        f"<style>{css}</style>{body}</svg>"
    )


def write(name, content):
    os.makedirs(OUT, exist_ok=True)
    path = os.path.join(OUT, name)
    with open(path, "w") as f:
        f.write(content)
    print(f"wrote cards/{name} ({len(content) // 1024} KB)")


def d(s):  # animation delay attribute
    return f'style="animation-delay:{s:.2f}s"'


def wrap(text, n):
    lines, line = [], ""
    for word in text.split():
        if line and len(line) + 1 + len(word) > n:
            lines.append(line)
            line = word
        else:
            line = f"{line} {word}".strip()
    return lines + [line] if line else lines


def text_lines(x, y, lines, lh, attrs):
    return "".join(
        f'<text x="{x}" y="{y + i * lh}" {attrs}>{escape(l)}</text>' for i, l in enumerate(lines)
    )


# ---- 1 · HERO CARD ----------------------------------------------------------
def hero():
    h = 360
    avatar_svg = ""
    photo_path = os.path.join(ROOT, "source-photo.png")

    # Optional avatar if SHOW_AVATAR=1 is requested
    if os.environ.get("SHOW_AVATAR") == "1" and os.path.exists(photo_path):
        try:
            b64_img = base64.b64encode(open(photo_path, "rb").read()).decode()
            avatar_svg = f"""
<g class="f" {d(0.3)}>
  <clipPath id="avatar-clip"><circle cx="730" cy="180" r="100"/></clipPath>
  <circle cx="730" cy="180" r="104" fill="{PAPER_DEEP}"/>
  <circle cx="730" cy="180" r="101" fill="{PAPER}" stroke="{RULE}" stroke-width="2"/>
  <image href="data:image/jpeg;base64,{b64_img}" x="630" y="80" width="200" height="200"
         clip-path="url(#avatar-clip)" preserveAspectRatio="xMidYMid slice"/>
</g>
"""
        except Exception as e:
            print(f"avatar notice: {e}")

    # Tech stack pills
    skills = ["React", "Next.js", "TypeScript", "Node.js", "Tailwind CSS", "MongoDB", "PostgreSQL"]
    skill_pills = []
    sx = 48
    for j, sk in enumerate(skills):
        pw = len(sk) * 8 + 18
        skill_pills.append(
            f'<g class="f" {d(0.65 + j * 0.04)}>'
            f'<rect x="{sx}" y="260" width="{pw}" height="28" rx="14" fill="{PAPER_DEEP}"/>'
            f'<text x="{sx + pw / 2}" y="278" font-family="{MONO}" font-size="11" fill="{INK_SOFT}" '
            f'text-anchor="middle">{escape(sk)}</text></g>'
        )
        sx += pw + 8

    body = f"""
<defs>
  <linearGradient id="shine" gradientUnits="userSpaceOnUse" x1="0" y1="0" x2="700" y2="0">
    <stop offset="0" stop-color="{INK}"/><stop offset=".40" stop-color="{INK}"/>
    <stop offset=".50" stop-color="{TECH}"/><stop offset=".60" stop-color="{INK}"/>
    <stop offset="1" stop-color="{INK}"/>
    <animateTransform attributeName="gradientTransform" type="translate" values="-700 0;700 0;700 0"
      keyTimes="0;.5;1" dur="7s" begin="1.4s" repeatCount="indefinite"/>
  </linearGradient>
</defs>
<rect width="{W}" height="{h}" rx="14" fill="{PAPER}"/>
<g class="f" {d(0)}>
  <rect class="live" x="48" y="44" width="8" height="8" rx="2" fill="{TECH}"/>
  <text x="66" y="52" font-family="{MONO}" font-size="12" letter-spacing="1.2" fill="{MUTED}">{HEADLINE}</text>
</g>
<text class="r" {d(0.15)} x="44" y="152" font-size="94" letter-spacing="-2.5" fill="url(#shine)"><tspan font-family="{SERIF}" font-style="normal" font-weight="400">{FULL_NAME_FIRST}</tspan> <tspan font-family="{SERIF}" font-style="italic" font-weight="400">{FULL_NAME_LAST}</tspan></text>
<g class="r" {d(0.40)}>
  {text_lines(48, 204, TAGLINE, 28, f'font-family="{SANS}" font-size="19" fill="{INK_SOFT}"')}
</g>
{''.join(skill_pills)}
<g class="f" {d(0.85)}>
  <text x="48" y="332" font-family="{MONO}" font-size="13" fill="{INK}">{SITE_URL}</text>
  <text class="nu" x="196" y="332" font-family="{MONO}" font-size="13" fill="{TECH}">&#8599;</text>
</g>
{avatar_svg}
"""
    write(
        "hero.svg",
        svg(
            W,
            h,
            body,
            ["serif", "serif-i", "sans", "mono"],
            f"{FULL_NAME_FIRST} {FULL_NAME_LAST}. {HEADLINE}. {' '.join(TAGLINE)}",
        ),
    )


# ---- 2 · THREE LINKED TILES (BUILD, EXPERIENCE/BRAND, LEARN/OSS) -------------
TILE_W, TILE_H = 880 / 3 - 8, 210  # 285.333 px wide, tiles seamlessly at 32.5% width


def count_up(num, word, x, y, attrs, begin, dur=1.1, frames=18):
    """Number counts up with SMIL <set> frames, works inside <img>."""
    m = re.match(r"([\d.]+)(.*)", num)
    if not m:
        tail = f' <tspan font-style="italic">{escape(word)}</tspan>'
        return f'<text x="{x}" y="{y}" {attrs}>{escape(num)}{tail}</text>'

    val, suf = float(m.group(1)), m.group(2)
    dec = len(m.group(1).split(".")[1]) if "." in m.group(1) else 0
    tail = f' <tspan font-style="italic">{escape(word)}</tspan>'

    if os.environ.get("STATIC") == "1":
        return f'<text x="{x}" y="{y}" {attrs}>{escape(num)}{tail}</text>'

    out = []
    for i in range(frames + 1):
        e = 1 - (1 - i / frames) ** 3
        txt = num if i == frames else f"{val * e:.{dec}f}{suf}"
        on = begin + dur * i / frames
        off = "" if i == frames else f'<set attributeName="opacity" to="0" begin="{begin + dur * (i + 1) / frames:.3f}s"/>'
        out.append(
            f'<text x="{x}" y="{y}" {attrs} opacity="0">{escape(txt)}{tail}'
            f'<set attributeName="opacity" to="1" begin="{on:.3f}s"/>{off}</text>'
        )
    return "".join(out)


def tile(name, label, color, on, num, word, blurb, delay, pos):
    lines = wrap(blurb, 34)
    blurb_svg = "".join(
        f'<text class="r" {d(delay + 0.75 + i * 0.1)} x="24" y="{150 + i * 20}" font-family="{SANS}" '
        f'font-size="14" fill="{on}" opacity=".92">{escape(l)}</text>'
        for i, l in enumerate(lines)
    )
    total_len = len(f"{num} {word}")
    fs = 26 if total_len > 15 else 36 if total_len > 9 else 44
    body = f"""
<defs>
  <clipPath id="card"><rect width="{TILE_W}" height="{TILE_H}" rx="14"/></clipPath>
  <clipPath id="slot"><rect x="0" y="62" width="{TILE_W}" height="62"/></clipPath>
  <linearGradient id="gl" x1="0" x2="1">
    <stop offset="0" stop-color="#fff" stop-opacity="0"/>
    <stop offset=".5" stop-color="#fff" stop-opacity=".35"/>
    <stop offset="1" stop-color="#fff" stop-opacity="0"/>
  </linearGradient>
</defs>
<g class="ti" {d(delay)}>
  <g clip-path="url(#card)">
    <rect width="{TILE_W}" height="{TILE_H}" fill="{color}"/>
    <circle class="rg" {d(delay + 0.5)} cx="{TILE_W - 40}" cy="{TILE_H - 40}" r="60" fill="none" stroke="{on}" stroke-opacity=".5" stroke-width="2"/>
    <rect class="sh" style="animation-delay:{delay + 1.4:.2f}s" x="0" y="-20" width="90" height="{TILE_H + 40}" fill="url(#gl)" transform="translate(-260 0)"/>
  </g>
  <text class="sl" {d(delay + 0.35)} x="24" y="38" font-family="{MONO}" font-size="12" letter-spacing="1.2" fill="{on}">{label}</text>
  <g class="ai" {d(delay + 0.5)}><text class="n" style="animation-delay:{delay + 1.3:.2f}s" x="250" y="38" font-family="{MONO}" font-size="14" fill="{on}">&#8594;</text></g>
  <g clip-path="url(#slot)"><g class="ro" {d(delay + 0.45)}>
    {count_up(num, word, 22, 112, f'font-family="{SERIF}" font-size="{fs}" fill="{on}"', delay + 0.45)}
  </g></g>
  {blurb_svg}
</g>
"""
    write(
        f"{name}.svg",
        svg(
            TILE_W,
            TILE_H,
            body,
            ["serif", "serif-i", "sans", "mono"],
            f"{label}: {num} {word}. {blurb}",
            left=4 * pos,
            right=8 - 4 * pos,
        ),
    )


# ---- 3 · ACTIVITY (MONTHLY BARS + STREAK STATS) -----------------------------
def activity(data):
    h = 340
    monthly = data.get("monthly", [])[-12:]
    best = max(monthly[:-1] or monthly, key=lambda m: m["total"])
    top = max(best["total"], 1)
    x0, x1, base, maxh, gap = 40, 600, 292, 140, 10
    bw = (x1 - x0 - gap * (len(monthly) - 1)) / len(monthly)
    bars = []
    for i, m in enumerate(monthly):
        partial = i == len(monthly) - 1
        is_best = m is best and m["total"] > 0
        bh = max(4, round(m["total"] / top * maxh))
        x = x0 + i * (bw + gap)
        fill = TECH if is_best else ("#c9c9c4" if partial else INK)
        label = datetime.date.fromisoformat(m["month"] + "-01").strftime("%b")
        bars.append(
            f'<rect class="g" style="animation-delay:{2.2 + i * 0.07:.2f}s" x="{x:.1f}" y="{base - bh}" '
            f'width="{bw:.1f}" height="{bh}" rx="4" fill="{fill}"><title>{label}: {m["total"]:,}</title></rect>'
            f'<text class="f" style="animation-delay:{2.2 + i * 0.07:.2f}s" x="{x + bw / 2:.1f}" y="{base + 22}" '
            f'text-anchor="middle" font-family="{MONO}" font-size="11" fill="{MUTED}">{label}</text>'
        )
        if is_best:
            bars.append(
                f'<text class="p" style="animation-delay:3.2s" x="{x + bw / 2:.1f}" y="{base - bh - 10}" '
                f'text-anchor="middle" font-family="{MONO}" font-size="11" fill="{TECH}">{m["total"]:,}</text>'
            )

    cs = data.get("current_streak", {}).get("length", 0)
    ls = data.get("longest_streak", {}).get("length", 0)
    streak_note = "current streak, and the longest" if cs >= ls and cs > 0 else f"current streak, longest {ls}"
    total_days = len(data.get("days", [])) or 365
    active_days = data.get("active_days", 0)
    best_day = data.get("best_day", {"count": 0})

    stats = [
        (f'{cs} <tspan font-style="italic">days</tspan>', streak_note),
        (f'{active_days}<tspan fill="#8e8e93"> / {total_days}</tspan>', "days with a commit"),
        (f'{best_day.get("count", 0)}', "on the busiest day"),
    ]
    side = []
    for i, (big, small) in enumerate(stats):
        y = 104 + i * 92
        side.append(
            f'<g class="r" {d(2.6 + i * 0.15)}>'
            f'<text x="650" y="{y}" font-family="{SERIF}" font-size="40" fill="{INK}">{big}</text>'
            f'<text x="650" y="{y + 24}" font-family="{SANS}" font-size="13" fill="{MUTED}">{small}</text></g>'
        )
        if i < 2:
            side.append(f'<rect class="f" {d(2.6)} x="650" y="{y + 44}" width="190" height="1" fill="{RULE}"/>')

    body = f"""
<rect width="{W}" height="{h}" rx="14" fill="{PAPER}"/>
<text class="f" {d(1.9)} x="40" y="58" font-family="{MONO}" font-size="12" letter-spacing="1" fill="{MUTED}">THE LAST 12 MONTHS ON GITHUB</text>
<text class="r" {d(2.0)} x="38" y="114" font-family="{SERIF}" font-size="52" fill="{INK}">{data.get("total_contributions", 0):,} <tspan font-style="italic">contributions</tspan></text>
{''.join(bars)}
{''.join(side)}
"""
    write(
        "activity.svg",
        svg(
            W,
            h,
            body,
            ["serif", "serif-i", "sans", "mono"],
            f'{data.get("total_contributions", 0):,} contributions in the last year, {cs}-day streak',
        ),
    )


# ---- 4 · FEATURED REPO CARDS ------------------------------------------------
REPO_W, REPO_H = 880 / 3 - 8, 176
REPOS = [
    (
        "watchflow",
        "Regional streaming directory discovery platform with automated link health verification bot.",
        "JavaScript",
        TECH,
    ),
    (
        "nezukoo",
        "Privacy-focused web push notification platform allowing websites to send instant browser alerts.",
        "TypeScript",
        STUDIO,
    ),
    (
        "portfolio-main",
        "Cinematic personal developer portfolio with modern animations, dark mode & live feeds.",
        "TypeScript",
        LEARN,
    ),
]


def repo_card(i, name, desc, lang, color, stars):
    delay = 4.6 + i * 0.12
    meta = f"{lang}  ·  ★ {stars}" if stars else f"{lang}  ·  live"
    body = f"""
<rect width="{REPO_W}" height="{REPO_H}" rx="14" fill="{PAPER}"/>
<g class="r" {d(delay)}>
  <rect x="24" y="30" width="8" height="8" rx="2" fill="{color}"/>
  <text x="40" y="39" font-family="{SANS}" font-weight="600" font-size="18" fill="{INK}">{escape(name)}</text>
  {text_lines(24, 72, wrap(desc, 34), 21, f'font-family="{SANS}" font-size="14" fill="{INK_SOFT}"')}
  <text x="24" y="{REPO_H - 24}" font-family="{MONO}" font-size="12" fill="{MUTED}">{escape(meta)}</text>
</g>
"""
    write(
        f"repo-{name}.svg",
        svg(
            REPO_W,
            REPO_H,
            body,
            ["sans", "sans-b", "mono"],
            f"{name}: {desc}",
            left=4 * i,
            right=8 - 4 * i,
        ),
    )


def section_title(text, italic, theme):
    fg = "#e6edf3" if theme == "dark" else INK
    body = (
        f'<text class="r" {d(4.4)} x="2" y="46" font-family="{SERIF}" font-size="34" fill="{fg}">{escape(text)} '
        f'<tspan font-style="italic">{escape(italic)}</tspan></text>'
    )
    write(f"title-coding-{theme}.svg", svg(W, 64, body, ["serif", "serif-i"], f"{text} {italic}", bottom=0))


# ---- 5 · BLUE CONTRIBUTION HEATMAP ------------------------------------------
BLUE = [PAPER_DEEP, "#c8d3ff", "#94a8ff", "#6280ff", TECH, "#1a3be0"]


def level_for(c):
    return 0 if c == 0 else 1 if c <= 5 else 2 if c <= 15 else 3 if c <= 30 else 4 if c <= 50 else 5


def heatmap(data):
    days = data.get("days", [])
    if not days:
        return

    first = datetime.date.fromisoformat(days[0]["date"])
    lead = (first.weekday() + 1) % 7  # sunday = 0
    cell, step, gx, gy = 12, 15, 44, 96
    cells, months, seen = [], [], set()

    for i, day in enumerate(days):
        k = i + lead
        col, row = divmod(k, 7)
        date = datetime.date.fromisoformat(day["date"])
        if date.day <= 7 and (date.year, date.month) not in seen and row == 0:
            seen.add((date.year, date.month))
            months.append((col, date.strftime("%b")))
        c = day["count"]
        delay = 1.0 + col * 0.03 + row * 0.02
        cells.append(
            f'<rect class="p" style="animation-delay:{delay:.2f}s" x="{gx + col * step}" y="{gy + row * step}" '
            f'width="{cell}" height="{cell}" rx="3" fill="{BLUE[level_for(c)]}">'
            f'<title>{day["date"]}: {c} contribution{"s" if c != 1 else ""}</title></rect>'
        )

    ncols = (len(days) + lead + 6) // 7
    right = gx + ncols * step - 3
    labels = "".join(
        f'<text x="{gx + col * step}" y="{gy + 7 * step + 16}" font-family="{MONO}" font-size="11" fill="{MUTED}">{m}</text>'
        for col, m in months
        if col < ncols - 12
    )
    legend_x = right - len(BLUE) * 14
    legend = "".join(
        f'<rect x="{legend_x + i * 14}" y="{gy + 7 * step + 6}" width="11" height="11" rx="2.5" fill="{c}"/>'
        for i, c in enumerate(BLUE)
    )
    h = gy + 7 * step + 44

    body = f"""
<rect width="{W}" height="{h}" rx="14" fill="{PAPER}"/>
<text class="r" {d(0.8)} x="42" y="62" font-family="{SERIF}" font-size="34" fill="{INK}">Every day, <tspan font-style="italic" fill="{TECH}">in blue</tspan></text>
<text class="f" {d(0.8)} x="{right}" y="60" text-anchor="end" font-family="{MONO}" font-size="12" letter-spacing="1" fill="{MUTED}">REFRESHED DAILY</text>
{''.join(cells)}
<g class="f" {d(2.4)}>{labels}
<text x="{legend_x - 8}" y="{gy + 7 * step + 16}" text-anchor="end" font-family="{MONO}" font-size="11" fill="{MUTED}">less</text>
{legend}
<text x="{legend_x + len(BLUE) * 14 + 2}" y="{gy + 7 * step + 16}" font-family="{MONO}" font-size="11" fill="{MUTED}">more</text></g>
"""
    write(
        "heatmap.svg",
        svg(
            W,
            h,
            body,
            ["serif", "serif-i", "mono"],
            f'Contribution graph: {data.get("total_contributions", 0):,} contributions in the last year',
        ),
    )


def repo_stars():
    stars = {}
    try:
        import requests

        for name, *_ in REPOS:
            r = requests.get(f"https://api.github.com/repos/{USERNAME}/{name}", timeout=5)
            if r.ok:
                stars[name] = r.json().get("stargazers_count", 0)
    except Exception as e:
        print(f"stars API unavailable ({e}); using defaults")
    return stars


if __name__ == "__main__":
    if not os.path.exists(DATA):
        print(f"Error: {DATA} not found. Run fetch_contributions.py first.")
        exit(1)

    data = json.load(open(DATA))

    # 1. Hero
    hero()

    # 2. Three Linked Tiles (BUILD, BRAND/EXPERIENCE, LEARN/OSS)
    tile(
        "build",
        "BUILD",
        TECH,
        "#ffffff",
        "5+",
        "web apps",
        "WatchFlow, Nezuko, OneFlix, Meme Adda, and more full-stack web platforms.",
        3.1,
        0,
    )
    tile(
        "brand",
        "EXPERIENCE",
        STUDIO,
        "#ffffff",
        "wprise.ai & C-DAC",
        "intern",
        "Software Developer Intern at wprise.ai and Cyber Security Intern at C-DAC Noida.",
        3.35,
        1,
    )
    tile(
        "learn",
        "OPEN SOURCE",
        LEARN,
        INK,
        "40+",
        "repos",
        "Active builder, open-source contributor, and daily problem solver.",
        3.6,
        2,
    )

    # 3. Monthly Activity Bars & Streak
    activity(data)

    # 4. Featured Repos
    stars = repo_stars()
    for i, (name, desc, lang, color) in enumerate(REPOS):
        repo_card(i, name, desc, lang, color, stars.get(name, 0))

    # 5. Section titles
    section_title("What I'm", "coding", "dark")
    section_title("What I'm", "coding", "light")

    # 6. Blue Heatmap
    heatmap(data)
