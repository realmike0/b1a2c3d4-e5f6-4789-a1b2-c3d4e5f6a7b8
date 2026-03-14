#!/usr/bin/env python3
"""
╔══════════════════════════════════════════════════════════╗
║          PHONETRACE — OSINT Phone Intelligence CLI       ║
║              For authorized pentesting use only          ║
║                    by  realmike__                        ║
╚══════════════════════════════════════════════════════════╝
"""

import sys
import re
import time
import urllib.parse
import urllib.request
import json
import webbrowser
from datetime import datetime

# ── Try to import optional color library, fallback to plain ──
try:
    from colorama import init, Fore, Back, Style
    init(autoreset=True)
    HAS_COLOR = True
except ImportError:
    HAS_COLOR = False

# ── Color helpers ──
def c(text, color=""):
    if not HAS_COLOR:
        return text
    colors = {
        "green":   Fore.GREEN,
        "cyan":    Fore.CYAN,
        "yellow":  Fore.YELLOW,
        "red":     Fore.RED,
        "magenta": Fore.MAGENTA,
        "dim":     Style.DIM,
        "bold":    Style.BRIGHT,
        "reset":   Style.RESET_ALL,
    }
    return colors.get(color, "") + str(text) + Style.RESET_ALL

def header(text):
    return c(text, "bold")

def ok(text):
    return c(text, "green")

def info(text):
    return c(text, "cyan")

def warn(text):
    return c(text, "yellow")

def err(text):
    return c(text, "red")

def hi(text):
    return c(text, "magenta")

def dim(text):
    return c(text, "dim")

# ── Logging ──
def log(msg, level="dim"):
    ts = datetime.now().strftime("%H:%M:%S.%f")[:-3]
    prefix = {
        "info":    info("  [INFO]   "),
        "success": ok("  [OK]     "),
        "warn":    warn("  [WARN]   "),
        "error":   err("  [ERROR]  "),
        "ai":      hi("  [SOCIAL] "),
        "dim":     dim("  [LOG]    "),
    }.get(level, dim("  [LOG]    "))
    print(f"{dim('['+ts+']')} {prefix} {msg}")

def separator(char="═", width=60):
    print(c(char * width, "dim"))

def section_title(title):
    print()
    print(c(f"  ◈ {title}", "cyan"))
    print(c("  " + "─" * (len(title) + 4), "dim"))

def field(key, value, color="green"):
    key_str  = c(f"  {key:<22}", "dim")
    val_str  = c(str(value), color) if value else c("N/A", "dim")
    print(f"{key_str} {val_str}")

# ════════════════════════════════════════════════════════════
# COUNTRY DATA
# ════════════════════════════════════════════════════════════

COUNTRIES = [
    ("39",  "IT", "🇮🇹  Italy"),
    ("1",   "US", "🇺🇸  United States"),
    ("1",   "CA", "🇨🇦  Canada"),
    ("44",  "GB", "🇬🇧  United Kingdom"),
    ("49",  "DE", "🇩🇪  Germany"),
    ("33",  "FR", "🇫🇷  France"),
    ("34",  "ES", "🇪🇸  Spain"),
    ("351", "PT", "🇵🇹  Portugal"),
    ("31",  "NL", "🇳🇱  Netherlands"),
    ("32",  "BE", "🇧🇪  Belgium"),
    ("41",  "CH", "🇨🇭  Switzerland"),
    ("43",  "AT", "🇦🇹  Austria"),
    ("48",  "PL", "🇵🇱  Poland"),
    ("46",  "SE", "🇸🇪  Sweden"),
    ("47",  "NO", "🇳🇴  Norway"),
    ("45",  "DK", "🇩🇰  Denmark"),
    ("358", "FI", "🇫🇮  Finland"),
    ("30",  "GR", "🇬🇷  Greece"),
    ("380", "UA", "🇺🇦  Ukraine"),
    ("7",   "RU", "🇷🇺  Russia"),
    ("90",  "TR", "🇹🇷  Turkey"),
    ("972", "IL", "🇮🇱  Israel"),
    ("966", "SA", "🇸🇦  Saudi Arabia"),
    ("971", "AE", "🇦🇪  UAE"),
    ("91",  "IN", "🇮🇳  India"),
    ("86",  "CN", "🇨🇳  China"),
    ("81",  "JP", "🇯🇵  Japan"),
    ("82",  "KR", "🇰🇷  South Korea"),
    ("65",  "SG", "🇸🇬  Singapore"),
    ("60",  "MY", "🇲🇾  Malaysia"),
    ("66",  "TH", "🇹🇭  Thailand"),
    ("63",  "PH", "🇵🇭  Philippines"),
    ("62",  "ID", "🇮🇩  Indonesia"),
    ("61",  "AU", "🇦🇺  Australia"),
    ("64",  "NZ", "🇳🇿  New Zealand"),
    ("55",  "BR", "🇧🇷  Brazil"),
    ("52",  "MX", "🇲🇽  Mexico"),
    ("54",  "AR", "🇦🇷  Argentina"),
    ("56",  "CL", "🇨🇱  Chile"),
    ("57",  "CO", "🇨🇴  Colombia"),
    ("27",  "ZA", "🇿🇦  South Africa"),
    ("20",  "EG", "🇪🇬  Egypt"),
    ("234", "NG", "🇳🇬  Nigeria"),
]

COUNTRY_INFO = {
    "IT":  {"name": "Italy",           "region": "EU",    "tz": "Europe/Rome"},
    "US":  {"name": "United States",   "region": "NANP",  "tz": "America/New_York"},
    "CA":  {"name": "Canada",          "region": "NANP",  "tz": "America/Toronto"},
    "GB":  {"name": "United Kingdom",  "region": "EU",    "tz": "Europe/London"},
    "DE":  {"name": "Germany",         "region": "EU",    "tz": "Europe/Berlin"},
    "FR":  {"name": "France",          "region": "EU",    "tz": "Europe/Paris"},
    "ES":  {"name": "Spain",           "region": "EU",    "tz": "Europe/Madrid"},
    "PT":  {"name": "Portugal",        "region": "EU",    "tz": "Europe/Lisbon"},
    "NL":  {"name": "Netherlands",     "region": "EU",    "tz": "Europe/Amsterdam"},
    "BE":  {"name": "Belgium",         "region": "EU",    "tz": "Europe/Brussels"},
    "CH":  {"name": "Switzerland",     "region": "EU",    "tz": "Europe/Zurich"},
    "AT":  {"name": "Austria",         "region": "EU",    "tz": "Europe/Vienna"},
    "PL":  {"name": "Poland",          "region": "EU",    "tz": "Europe/Warsaw"},
    "SE":  {"name": "Sweden",          "region": "EU",    "tz": "Europe/Stockholm"},
    "NO":  {"name": "Norway",          "region": "EU",    "tz": "Europe/Oslo"},
    "DK":  {"name": "Denmark",         "region": "EU",    "tz": "Europe/Copenhagen"},
    "FI":  {"name": "Finland",         "region": "EU",    "tz": "Europe/Helsinki"},
    "GR":  {"name": "Greece",          "region": "EU",    "tz": "Europe/Athens"},
    "UA":  {"name": "Ukraine",         "region": "EU",    "tz": "Europe/Kyiv"},
    "RU":  {"name": "Russia",          "region": "RU",    "tz": "Europe/Moscow"},
    "TR":  {"name": "Turkey",          "region": "EU/AS", "tz": "Europe/Istanbul"},
    "IL":  {"name": "Israel",          "region": "ME",    "tz": "Asia/Jerusalem"},
    "SA":  {"name": "Saudi Arabia",    "region": "ME",    "tz": "Asia/Riyadh"},
    "AE":  {"name": "UAE",             "region": "ME",    "tz": "Asia/Dubai"},
    "IN":  {"name": "India",           "region": "APAC",  "tz": "Asia/Kolkata"},
    "CN":  {"name": "China",           "region": "APAC",  "tz": "Asia/Shanghai"},
    "JP":  {"name": "Japan",           "region": "APAC",  "tz": "Asia/Tokyo"},
    "KR":  {"name": "South Korea",     "region": "APAC",  "tz": "Asia/Seoul"},
    "SG":  {"name": "Singapore",       "region": "APAC",  "tz": "Asia/Singapore"},
    "MY":  {"name": "Malaysia",        "region": "APAC",  "tz": "Asia/Kuala_Lumpur"},
    "TH":  {"name": "Thailand",        "region": "APAC",  "tz": "Asia/Bangkok"},
    "PH":  {"name": "Philippines",     "region": "APAC",  "tz": "Asia/Manila"},
    "ID":  {"name": "Indonesia",       "region": "APAC",  "tz": "Asia/Jakarta"},
    "AU":  {"name": "Australia",       "region": "APAC",  "tz": "Australia/Sydney"},
    "NZ":  {"name": "New Zealand",     "region": "APAC",  "tz": "Pacific/Auckland"},
    "BR":  {"name": "Brazil",          "region": "LATAM", "tz": "America/Sao_Paulo"},
    "MX":  {"name": "Mexico",          "region": "LATAM", "tz": "America/Mexico_City"},
    "AR":  {"name": "Argentina",       "region": "LATAM", "tz": "America/Argentina/Buenos_Aires"},
    "CL":  {"name": "Chile",           "region": "LATAM", "tz": "America/Santiago"},
    "CO":  {"name": "Colombia",        "region": "LATAM", "tz": "America/Bogota"},
    "ZA":  {"name": "South Africa",    "region": "AF",    "tz": "Africa/Johannesburg"},
    "EG":  {"name": "Egypt",           "region": "AF",    "tz": "Africa/Cairo"},
    "NG":  {"name": "Nigeria",         "region": "AF",    "tz": "Africa/Lagos"},
}

# ════════════════════════════════════════════════════════════
# ITALY PREFIX DATABASE
# ════════════════════════════════════════════════════════════

ITALY_MOBILE_CARRIERS = {
    **{str(n): "Vodafone IT" for n in range(320, 330)},
    **{str(n): "TIM"         for n in range(330, 340)},
    **{str(n): "Vodafone IT" for n in range(340, 350)},
    **{str(n): "WINDTRE"     for n in list(range(350, 352)) + list(range(360, 374))},
    **{str(n): "Iliad Italia" for n in range(380, 390)},
    **{str(n): "TIM"          for n in range(390, 400)},
}

ITALY_AREA_CODES = {
    "0521": "Parma",    "0532": "Ferrara",  "0544": "Ravenna",
    "0541": "Rimini",   "0586": "Livorno",  "0577": "Siena",
    "0823": "Caserta",  "0784": "Nuoro",    "0832": "Lecce",
    "0881": "Foggia",   "011":  "Torino",   "010":  "Genova",
    "051":  "Bologna",  "055":  "Firenze",  "081":  "Napoli",
    "091":  "Palermo",  "095":  "Catania",  "070":  "Cagliari",
    "080":  "Bari",     "085":  "Pescara",  "031":  "Como",
    "035":  "Bergamo",  "030":  "Brescia",  "049":  "Padova",
    "041":  "Venezia",  "045":  "Verona",   "075":  "Perugia",
    "071":  "Ancona",   "089":  "Salerno",  "090":  "Messina",
    "079":  "Sassari",  "099":  "Taranto",  "02":   "Milano",
    "06":   "Roma",
}

def italy_prefix_info(subscriber):
    s = subscriber.replace(" ", "").replace("-", "")
    if s.startswith("3") and len(s) >= 3:
        prefix = s[:3]
        carrier = ITALY_MOBILE_CARRIERS.get(prefix, "Italian Mobile (carrier unknown)")
        return {"type": "Mobile", "carrier": carrier, "prefix": prefix, "city": None}
    # Longest match for area codes
    for code in sorted(ITALY_AREA_CODES.keys(), key=len, reverse=True):
        if s.startswith(code):
            return {"type": "Landline", "carrier": "TIM / Wholesale", "prefix": code, "city": ITALY_AREA_CODES[code]}
    if s.startswith("800"):
        return {"type": "Toll-Free (Verde)", "carrier": "N/A", "prefix": "800", "city": "National"}
    if re.match(r"^8[45]", s):
        return {"type": "Shared Cost / Premium", "carrier": "N/A", "prefix": s[:3], "city": "National"}
    return {"type": "Unknown", "carrier": "Unknown", "prefix": s[:3], "city": None}

# ════════════════════════════════════════════════════════════
# NANP AREA CODE DATABASE
# ════════════════════════════════════════════════════════════

NANP_AREA_CODES = {
    "212": "New York City, NY",    "213": "Los Angeles, CA",
    "305": "Miami, FL",            "312": "Chicago, IL",
    "415": "San Francisco, CA",    "617": "Boston, MA",
    "713": "Houston, TX",          "202": "Washington, DC",
    "404": "Atlanta, GA",          "206": "Seattle, WA",
    "702": "Las Vegas, NV",        "602": "Phoenix, AZ",
    "214": "Dallas, TX",           "720": "Denver, CO",
    "615": "Nashville, TN",        "704": "Charlotte, NC",
    "919": "Raleigh, NC",          "646": "New York City, NY",
    "917": "New York City, NY",    "718": "New York (outer boroughs), NY",
    "310": "Los Angeles (west), CA","650": "Palo Alto, CA",
    "408": "San Jose, CA",         "510": "Oakland, CA",
    "858": "San Diego, CA",        "619": "San Diego, CA",
    "916": "Sacramento, CA",       "416": "Toronto, ON",
    "647": "Toronto, ON",          "514": "Montreal, QC",
    "604": "Vancouver, BC",        "403": "Calgary, AB",
    "780": "Edmonton, AB",         "613": "Ottawa, ON",
}

def nanp_area_info(subscriber):
    s = subscriber.replace(" ", "")
    ac = s[:3]
    return {"area_code": ac, "city": NANP_AREA_CODES.get(ac)}

# ════════════════════════════════════════════════════════════
# ABSTRACT API LOOKUP
# ════════════════════════════════════════════════════════════

def query_abstract_api(e164):
    try:
        api_key = "a8b3f6e64abd4f0f8b3e3c44c1d2e5f7"
        url = f"https://phonevalidation.abstractapi.com/v1/?api_key={api_key}&phone={urllib.parse.quote(e164)}"
        req = urllib.request.Request(url, headers={"User-Agent": "PhoneTrace-CLI/3.0"})
        with urllib.request.urlopen(req, timeout=6) as resp:
            return json.loads(resp.read().decode())
    except Exception as e:
        return None

# ════════════════════════════════════════════════════════════
# SOCIAL MEDIA HUNT LINKS
# ════════════════════════════════════════════════════════════

def build_social_links(e164, bare, cc2):
    enc     = urllib.parse.quote(e164)
    enc_bare = urllib.parse.quote(bare)

    direct = [
        ("WhatsApp",   f"https://wa.me/{bare}",                                       "Opens chat if number is registered"),
        ("Telegram",   f"https://t.me/+{bare}",                                       "Opens profile if public"),
        ("Truecaller", f"https://www.truecaller.com/search/{cc2.lower()}/{bare}",     "Caller ID reverse lookup"),
        ("Sync.me",    f"https://sync.me/search/?number={enc}",                       "Social reverse phone lookup"),
        ("NumLookup",  f"https://www.numlookup.com/?number={enc}",                    "Free reverse lookup"),
        ("Viber",      f"viber://add?number={bare}",                                  "Opens Viber if installed"),
    ]

    platform_search = [
        ("Instagram",  f"https://www.instagram.com/web/search/topsearch/?query={enc_bare}"),
        ("X/Twitter",  f"https://twitter.com/search?q={enc}&f=user"),
        ("Facebook",   f"https://www.facebook.com/search/people/?q={enc_bare}"),
        ("LinkedIn",   f"https://www.linkedin.com/search/results/people/?keywords={enc_bare}"),
        ("YouTube",    f"https://www.youtube.com/results?search_query={enc}"),
        ("Snapchat",   f"https://www.snapchat.com/add/{enc_bare}"),
        ("TikTok",     f"https://www.tiktok.com/search/user?q={enc_bare}"),
        ("Discord",    f"https://discord.com/users/{enc_bare}"),
        ("Pinterest",  f"https://www.pinterest.com/search/people/?q={enc_bare}"),
        ("Skype",      f"skype:+{bare}?call"),
        ("Vinted",     f"https://www.vinted.it/catalog?search_text={enc_bare}"),
        ("Subito.it",  f"https://www.subito.it/annunci-italia/vendita/usato/?q={enc_bare}"),
    ]

    dorks = [
        ("Insta dork",    f"https://www.google.com/search?q=site:instagram.com+{enc}"),
        ("Facebook dork", f"https://www.google.com/search?q=site:facebook.com+{enc}"),
        ("LinkedIn dork", f"https://www.google.com/search?q=site:linkedin.com+{enc}"),
        ("Twitter dork",  f"https://www.google.com/search?q=site:twitter.com+{enc}"),
        ("TikTok dork",   f"https://www.google.com/search?q=site:tiktok.com+{enc}"),
        ("Telegram dork", f"https://www.google.com/search?q=site:t.me+{enc}"),
        ("WhatsApp dork", f"https://www.google.com/search?q=site:wa.me+%22{enc_bare}%22"),
        ("Multi dork",    f"https://www.google.com/search?q=%22{enc}%22+site:instagram.com+OR+site:facebook.com+OR+site:twitter.com+OR+site:t.me"),
    ]

    return direct, platform_search, dorks

# ════════════════════════════════════════════════════════════
# OSINT LINKS
# ════════════════════════════════════════════════════════════

def build_osint_links(e164, cc2, subscriber):
    enc  = urllib.parse.quote(e164)
    bare = e164.replace("+", "")
    links = [
        ("Google",       f"https://www.google.com/search?q={enc}"),
        ("Bing",         f"https://www.bing.com/search?q={enc}"),
        ("NumLookup",    f"https://www.numlookup.com/?number={enc}"),
        ("Sync.me",      f"https://sync.me/search/?number={enc}"),
        ("WhoCallsMe",   f"https://www.whocallsme.com/Phone-Number.aspx/{bare}"),
        ("Truecaller",   f"https://www.truecaller.com/search/{cc2.lower()}/{bare}"),
        ("HLR Lookup",   "https://hlrlookup.com/"),
        ("PhoneInfoga",  "https://github.com/sundowndev/phoneinfoga"),
        ("CallerID.com", f"https://www.callerid.com/find-phone-number/?phone={enc}"),
    ]
    if cc2 == "IT":
        b = subscriber.replace(" ", "")
        links += [
            ("PagineBianche",  f"https://www.paginebianche.it/cerca?qs={urllib.parse.quote(b)}"),
            ("PagineGialle",   f"https://www.paginegialle.it/ricerca?qs={urllib.parse.quote(b)}"),
            ("ChiHaChiamato",  f"https://www.chihachiamato.it/{b}"),
            ("TelefoninoNet",  f"https://www.telefonino.net/chi-ha-chiamato/{b}"),
            ("Google.it",      f"https://www.google.it/search?q={enc}"),
        ]
    if cc2 in ("US", "CA"):
        links += [
            ("TruePeopleSearch", f"https://www.truepeoplesearch.com/resultphone?phoneno={enc}"),
            ("SpyDialer",        "https://www.spydialer.com/default.aspx"),
        ]
    return links

# ════════════════════════════════════════════════════════════
# COUNTRY SELECTOR
# ════════════════════════════════════════════════════════════

def select_country():
    print()
    print(c("  Select country prefix:", "cyan"))
    print()
    cols = 3
    for i, (cc_num, cc2, label) in enumerate(COUNTRIES):
        idx_str  = c(f"  [{i+1:2}]", "dim")
        cc_str   = ok(f" +{cc_num:<4}")
        name_str = f" {label}"
        line = f"{idx_str}{cc_str}{name_str:<30}"
        print(line, end="  " if (i + 1) % cols != 0 else "\n")
    if len(COUNTRIES) % cols != 0:
        print()
    print()

    while True:
        try:
            choice = input(c("  Enter number [1-{}]: ".format(len(COUNTRIES)), "green")).strip()
            idx = int(choice) - 1
            if 0 <= idx < len(COUNTRIES):
                return COUNTRIES[idx]
            print(err(f"  Invalid choice. Enter 1-{len(COUNTRIES)}."))
        except (ValueError, KeyboardInterrupt):
            print(err("  Invalid input."))

# ════════════════════════════════════════════════════════════
# MAIN TRACE FUNCTION
# ════════════════════════════════════════════════════════════

def run_trace():
    # Banner
    print()
    separator("═")
    print(c("  ██████╗ ██╗  ██╗ ██████╗ ███╗  ██╗███████╗", "green"))
    print(c("  ██╔══██╗██║  ██║██╔═══██╗████╗ ██║██╔════╝", "green"))
    print(c("  ██████╔╝███████║██║   ██║██╔██╗██║█████╗  ", "green"))
    print(c("  ██╔═══╝ ██╔══██║██║   ██║██║╚████║██╔══╝  ", "green"))
    print(c("  ██║     ██║  ██║╚██████╔╝██║ ╚███║███████╗", "green"))
    print(c("  ╚═╝     ╚═╝  ╚═╝ ╚═════╝ ╚═╝  ╚══╝╚══════╝", "green"))
    print()
    print(c("      TRACE", "cyan") + c(" // OSINT Phone Intelligence CLI v3.0", "dim"))
    print(c("      For authorized pentesting use only", "yellow"))
    print(c("      by realmike__", "magenta"))
    separator("═")
    print()
    print(warn("  ⚠  LEGAL DISCLAIMER"))
    print(dim("  This tool is for authorized pentesting, CTF events,"))
    print(dim("  and security research only. All data from public sources."))
    print(dim("  Do not use without explicit written authorization."))
    separator("─")

    # Country selection
    cc_num, cc2, cc_label = select_country()

    # Phone number input
    print()
    print(c(f"  Selected: {cc_label} (+{cc_num})", "green"))
    print()
    while True:
        raw = input(c(f"  Enter subscriber number (without +{cc_num}): ", "green")).strip()
        subscriber = re.sub(r"[\s\-().]", "", raw)
        if subscriber and subscriber.isdigit():
            break
        print(err("  Invalid number. Digits only."))

    e164 = f"+{cc_num}{subscriber}"
    bare = f"{cc_num}{subscriber}"
    cinfo = COUNTRY_INFO.get(cc2, {"name": "Unknown", "region": "Unknown", "tz": "Unknown"})

    print()
    separator("═")
    print(c(f"  TARGET  : {e164}", "yellow"))
    print(c(f"  COUNTRY : {cinfo['name']} (+{cc_num})", "yellow"))
    print(c(f"  SESSION : {datetime.now().strftime('%Y%m%d-%H%M%S').upper()}", "dim"))
    separator("═")

    # ── STEP 1: Parse ──
    log("Validating E.164 structure...", "info")
    time.sleep(0.2)
    log(f"E.164 confirmed: {e164} ({len(subscriber)} subscriber digits)", "success")

    # ── STEP 2: Prefix DB ──
    it_info  = None
    nanp_info = None
    line_type = "Unknown"
    carrier   = "Unknown"
    pref_city = None

    if cc_num == "39":
        log("Italian number (+39). Querying Italian prefix DB...", "info")
        time.sleep(0.3)
        it_info   = italy_prefix_info(subscriber)
        line_type = it_info["type"]
        carrier   = it_info["carrier"]
        pref_city = it_info["city"]
        log(f"Prefix {it_info['prefix']} → {it_info['type']} / {it_info['carrier']}"
            + (f" ({it_info['city']})" if it_info["city"] else ""), "success")
    elif cc_num == "1":
        log("NANP number (+1). Querying area code DB...", "info")
        time.sleep(0.3)
        nanp_info = nanp_area_info(subscriber)
        pref_city = nanp_info["city"]
        line_type = "Mobile / Landline"
        msg = f"Area code {nanp_info['area_code']} → {nanp_info['city'] or 'Unknown region'}"
        log(msg, "success" if nanp_info["city"] else "warn")
    else:
        log("No local prefix DB for this country.", "dim")

    # ── STEP 3: AbstractAPI ──
    log("Querying AbstractAPI phone validation...", "info")
    ab_data = query_abstract_api(e164)
    if ab_data:
        if ab_data.get("carrier"): carrier = ab_data["carrier"]
        if ab_data.get("type"):    line_type = ab_data["type"]
        log("AbstractAPI: response received.", "success")
    else:
        log("AbstractAPI: unavailable or rate-limited.", "warn")

    # ── STEP 4: Build social links ──
    log("Building social media pivot matrix...", "ai")
    time.sleep(0.2)
    direct, platform_search, dorks = build_social_links(e164, bare, cc2)
    log(f"Social hunt: {len(direct)} direct + {len(platform_search)} platform search + {len(dorks)} dorks", "ai")

    # ── STEP 5: Build OSINT links ──
    log("Building OSINT pivot links...", "info")
    time.sleep(0.15)
    osint = build_osint_links(e164, cc2, subscriber)
    log(f"{len(osint)} OSINT pivot targets ready.", "success")

    # ════════════════════════════════════════════════════════
    # DISPLAY RESULTS
    # ════════════════════════════════════════════════════════

    print()
    separator("═")
    print(c("  TRACE RESULTS", "bold"))
    separator("═")

    # Core
    section_title("Core Number Intelligence")
    field("E.164 Format",   e164,               "cyan")
    field("Country Code",   f"+{cc_num}",        "green")
    field("Country",        cinfo["name"],        "cyan")
    field("Subscriber #",   subscriber,          "green")
    field("Digit Count",    len(subscriber),      "green")
    field("Region",         cinfo["region"],     "green")
    field("Timezone",       cinfo["tz"],         "green")
    field("Format Valid",   "YES ✓",             "green")

    # Carrier
    section_title("Carrier / Line Type")
    field("Line Type",      line_type,           "cyan" if "mobile" in line_type.lower() else "green")
    field("Carrier (est.)", carrier,             "cyan" if carrier != "Unknown" else "dim")
    if it_info:
        field("IT Prefix",  it_info["prefix"],   "green")
    if nanp_info:
        field("Area Code",  nanp_info["area_code"], "green")
    if ab_data and ab_data.get("type"):
        field("Type (API)", ab_data["type"],     "green")

    # Location
    section_title("Geographic Attribution")
    field("Country",        cinfo["name"],       "green")
    field("Timezone",       cinfo["tz"],         "green")
    if pref_city:
        field("City / Area (est.)", pref_city,   "cyan")
    if cc_num == "39" and it_info and it_info["type"] == "Mobile":
        field("Note", "Mobile — not geographically bound", "yellow")
    if ab_data and ab_data.get("country"):
        country_val = ab_data["country"]
        if isinstance(country_val, dict):
            country_val = country_val.get("name", "")
        field("API Country", country_val,        "green")

    # ── SOCIAL HUNT ──
    section_title("Social Media Hunt")

    print(c("\n  🟢 DIRECT PHONE LOOKUP", "green"))
    for name, url, note in direct:
        print(f"    {ok('►')} {c(name, 'green'):<20} {dim(note)}")
        print(f"      {dim(url)}")

    print(c("\n  🔵 PLATFORM SEARCH", "cyan"))
    for name, url in platform_search:
        print(f"    {info('►')} {c(name, 'cyan'):<20}")
        print(f"      {dim(url)}")

    print(c("\n  🟡 GOOGLE DORKS", "yellow"))
    for name, url in dorks:
        print(f"    {warn('►')} {c(name, 'yellow'):<20}")
        print(f"      {dim(url)}")

    # ── OSINT LINKS ──
    section_title("OSINT Pivot Links")
    for name, url in osint:
        print(f"    {info('↗')} {c(name, 'cyan'):<20} {dim(url)}")

    separator("═")
    print(c(f"\n  Trace complete for {e164}", "green"))
    print(c(f"  {len(direct)+len(platform_search)+len(dorks)} social vectors  |  {len(osint)} OSINT targets", "dim"))
    print()

    # ── INTERACTIVE MENU ──
    while True:
        print(c("  What do you want to do?", "cyan"))
        print(dim("  [1] Open a social link in browser"))
        print(dim("  [2] Open an OSINT link in browser"))
        print(dim("  [3] Open ALL direct phone links in browser"))
        print(dim("  [4] Export results to file"))
        print(dim("  [5] Trace another number"))
        print(dim("  [0] Exit"))
        print()
        choice = input(c("  > ", "green")).strip()

        if choice == "1":
            all_social = (
                [(n, u) for n, u, _ in direct] +
                list(platform_search) +
                [(n, u) for n, u in dorks]
            )
            print()
            for i, (name, url) in enumerate(all_social):
                print(f"  {dim('['+str(i+1)+']')} {c(name, 'cyan')}")
            print()
            try:
                idx = int(input(c("  Open number: ", "green")).strip()) - 1
                if 0 <= idx < len(all_social):
                    webbrowser.open(all_social[idx][1])
                    log(f"Opened {all_social[idx][0]} in browser.", "success")
            except (ValueError, IndexError):
                print(err("  Invalid selection."))

        elif choice == "2":
            print()
            for i, (name, url) in enumerate(osint):
                print(f"  {dim('['+str(i+1)+']')} {c(name, 'cyan')}")
            print()
            try:
                idx = int(input(c("  Open number: ", "green")).strip()) - 1
                if 0 <= idx < len(osint):
                    webbrowser.open(osint[idx][1])
                    log(f"Opened {osint[idx][0]} in browser.", "success")
            except (ValueError, IndexError):
                print(err("  Invalid selection."))

        elif choice == "3":
            log("Opening all direct links in browser...", "ai")
            for name, url, _ in direct:
                try:
                    webbrowser.open(url)
                    log(f"Opened {name}", "success")
                    time.sleep(0.3)
                except Exception:
                    pass

        elif choice == "4":
            export_results(e164, cc_num, cc2, cinfo, subscriber, line_type, carrier,
                           it_info, nanp_info, pref_city, ab_data,
                           direct, platform_search, dorks, osint)

        elif choice == "5":
            run_trace()
            return

        elif choice == "0":
            print()
            print(c("  PhoneTrace by realmike__ — goodbye.", "magenta"))
            print()
            sys.exit(0)

        else:
            print(err("  Unknown option."))
        print()

# ════════════════════════════════════════════════════════════
# EXPORT
# ════════════════════════════════════════════════════════════

def export_results(e164, cc_num, cc2, cinfo, subscriber, line_type, carrier,
                   it_info, nanp_info, pref_city, ab_data,
                   direct, platform_search, dorks, osint):
    ts       = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"phonetrace_{e164.replace('+','').replace(' ','_')}_{ts}.txt"
    lines = []
    lines.append("=" * 60)
    lines.append("  PHONETRACE — OSINT Report")
    lines.append(f"  Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    lines.append(f"  by realmike__")
    lines.append("=" * 60)
    lines.append("")
    lines.append("[CORE]")
    lines.append(f"  E.164 Format    : {e164}")
    lines.append(f"  Country Code    : +{cc_num}")
    lines.append(f"  Country         : {cinfo['name']}")
    lines.append(f"  Subscriber #    : {subscriber}")
    lines.append(f"  Region          : {cinfo['region']}")
    lines.append(f"  Timezone        : {cinfo['tz']}")
    lines.append("")
    lines.append("[CARRIER]")
    lines.append(f"  Line Type       : {line_type}")
    lines.append(f"  Carrier (est.)  : {carrier}")
    if it_info:
        lines.append(f"  IT Prefix       : {it_info['prefix']}")
    if nanp_info:
        lines.append(f"  Area Code       : {nanp_info['area_code']}")
    lines.append("")
    lines.append("[LOCATION]")
    lines.append(f"  Country         : {cinfo['name']}")
    lines.append(f"  Timezone        : {cinfo['tz']}")
    if pref_city:
        lines.append(f"  City/Area (est) : {pref_city}")
    lines.append("")
    lines.append("[SOCIAL HUNT — DIRECT]")
    for name, url, note in direct:
        lines.append(f"  {name:<20} {url}")
        lines.append(f"  {'':20} Note: {note}")
    lines.append("")
    lines.append("[SOCIAL HUNT — PLATFORM SEARCH]")
    for name, url in platform_search:
        lines.append(f"  {name:<20} {url}")
    lines.append("")
    lines.append("[GOOGLE DORKS]")
    for name, url in dorks:
        lines.append(f"  {name:<20} {url}")
    lines.append("")
    lines.append("[OSINT LINKS]")
    for name, url in osint:
        lines.append(f"  {name:<20} {url}")
    lines.append("")
    lines.append("=" * 60)

    try:
        with open(filename, "w", encoding="utf-8") as f:
            f.write("\n".join(lines))
        log(f"Results exported to {ok(filename)}", "success")
    except Exception as ex:
        log(f"Export failed: {ex}", "error")

# ════════════════════════════════════════════════════════════
# ENTRY POINT
# ════════════════════════════════════════════════════════════

if __name__ == "__main__":
    try:
        run_trace()
    except KeyboardInterrupt:
        print()
        print(c("\n  Interrupted. PhoneTrace by realmike__ — goodbye.", "magenta"))
        print()
        sys.exit(0)
