# backend/pipeline/constants.py
# All constant data used across the pipeline:
# 1. GDELT_COLUMNS         — column names for GDELT CSV files (no header row)
# 2. CAMEO_LOOKUP          — event code → human readable label
# 3. STRATEGIC_COUNTRY_CODES — which countries to keep when filtering GDELT
# 4. STRATEGIC_GEO_CODES   — same but for geo fields (different format in GDELT)
# 5. CANONICAL_ENTITIES    — entity resolution dictionary (name → Wikidata ID)
# 6. SOURCE_CLASSIFICATION — domain → {country, media type} for USP 1


# ─── 1. GDELT COLUMN NAMES ───────────────────────────────────────
# GDELT CSV files have no header row.
# pandas needs this list to know what to call each of the 60 columns.

GDELT_COLUMNS = [
    'GLOBALEVENTID', 'SQLDATE', 'MonthYear', 'Year', 'FractionDate',
    'Actor1Code', 'Actor1Name', 'Actor1CountryCode', 'Actor1KnownGroupCode',
    'Actor1EthnicCode', 'Actor1Religion1Code', 'Actor1Religion2Code',
    'Actor1Type1Code', 'Actor1Type2Code', 'Actor1Type3Code',
    'Actor2Code', 'Actor2Name', 'Actor2CountryCode', 'Actor2KnownGroupCode',
    'Actor2EthnicCode', 'Actor2Religion1Code', 'Actor2Religion2Code',
    'Actor2Type1Code', 'Actor2Type2Code', 'Actor2Type3Code',
    'IsRootEvent', 'EventCode', 'EventBaseCode', 'EventRootCode',
    'QuadClass', 'GoldsteinScale', 'NumMentions', 'NumSources',
    'NumArticles', 'AvgTone', 'Actor1Geo_Type', 'Actor1Geo_FullName',
    'Actor1Geo_CountryCode', 'Actor1Geo_ADM1Code', 'Actor1Geo_Lat',
    'Actor1Geo_Long', 'Actor1Geo_FeatureID', 'Actor2Geo_Type',
    'Actor2Geo_FullName', 'Actor2Geo_CountryCode', 'Actor2Geo_ADM1Code',
    'Actor2Geo_Lat', 'Actor2Geo_Long', 'Actor2Geo_FeatureID',
    'ActionGeo_Type', 'ActionGeo_FullName', 'ActionGeo_CountryCode',
    'ActionGeo_ADM1Code', 'ActionGeo_Lat', 'ActionGeo_Long',
    'ActionGeo_FeatureID', 'DATEADDED', 'SOURCEURL'
]


# ─── 2. CAMEO EVENT CODES ────────────────────────────────────────
# Maps GDELT's numeric event codes to human readable labels.
# Full reference: https://parusanalytics.com/eventdata/cameo.dir/CAMEO.Manual.1.1b3.pdf
# Used in pipeline/nlp.py and pipeline/orchestrator.py

CAMEO_LOOKUP = {
    # Public statements
    "010": "Make public statement",
    "011": "Decline to comment",
    "012": "Make pessimistic comment",
    "013": "Make optimistic comment",
    "014": "Consider policy option",
    "015": "Acknowledge",
    "016": "Deny responsibility",
    "017": "Engage in symbolic act",
    "018": "Appeal for action",
    "019": "Express accord",
    # Appeal
    "020": "Appeal for cooperation",
    "021": "Appeal for material cooperation",
    "022": "Appeal for humanitarian aid",
    "023": "Appeal for economic aid",
    "024": "Appeal for military cooperation",
    "025": "Appeal for diplomatic cooperation",
    "028": "Appeal for political reform",
    # Intent to cooperate
    "030": "Express intent to cooperate",
    "031": "Express intent for material cooperation",
    "036": "Express intent to cooperate",
    "038": "Express intent for political reform",
    # Consult
    "040": "Consult",
    "041": "Discuss by phone",
    "042": "Make official visit",
    "043": "Host a visit",
    "044": "Meet at third location",
    "045": "Mediate",
    "046": "Engage in negotiation",
    # Diplomatic cooperation
    "050": "Engage in diplomatic cooperation",
    "051": "Express support for leader",
    "052": "Praise or endorse",
    "053": "Express support for policy",
    "054": "Express support for social cause",
    "055": "Grant diplomatic recognition",
    "056": "Apologise",
    "057": "Sign formal agreement",
    "058": "Settle legal dispute",
    # Material cooperation
    "060": "Engage in material cooperation",
    "061": "Cooperate economically",
    "062": "Cooperate militarily",
    "063": "Engage in joint military exercises",
    "064": "Share intelligence",
    # Aid
    "070": "Provide aid",
    "071": "Provide economic aid",
    "072": "Provide military aid",
    "073": "Provide humanitarian aid",
    "074": "Provide military protection",
    "075": "Grant asylum",
    # Yield
    "080": "Yield",
    "081": "Ease administrative sanctions",
    "082": "Ease economic sanctions",
    "083": "Ease military sanctions",
    "084": "Return territorial control",
    "085": "Return human remains",
    "086": "Ease political dissent",
    # Investigate
    "090": "Investigate",
    "091": "Investigate crime",
    "092": "Investigate military action",
    "093": "Investigate war crimes",
    # Demand
    "100": "Demand",
    "101": "Demand political reform",
    "102": "Demand leadership change",
    "103": "Demand rights",
    "104": "Demand material cooperation",
    "105": "Demand diplomatic cooperation",
    "106": "Demand humanitarian aid",
    "107": "Demand economic aid",
    "108": "Demand military action",
    # Disapprove
    "110": "Disapprove",
    "111": "Criticize or denounce",
    "112": "Accuse of wrongdoing",
    "113": "Accuse of military action",
    "114": "Accuse of human rights violations",
    "115": "Accuse of political dissent",
    "116": "Accuse of corruption",
    # Reject
    "120": "Reject",
    "121": "Reject proposal",
    "122": "Refuse to cooperate",
    "123": "Reject UN resolution",
    "124": "Refuse to allow",
    "125": "Reject accusation",
    "126": "Reject peace process",
    "127": "Reject request for material aid",
    # Threaten
    "130": "Threaten",
    "131": "Threaten with military force",
    "132": "Threaten with sanctions",
    "133": "Issue ultimatum",
    "134": "Threaten with administrative action",
    "135": "Threaten with political action",
    "136": "Threaten with embargo",
    "138": "Threaten with military attack",
    # Protest
    "140": "Protest",
    "141": "Demonstrate",
    "142": "Conduct hunger strike",
    "143": "Conduct strike or boycott",
    "144": "Obstruct passage",
    "145": "Engage in political dissent",
    # Impose restrictions
    "150": "Impose restrictions",
    "151": "Impose embargo",
    "152": "Impose sanctions",
    "153": "Halt negotiations",
    "154": "Halt mediation",
    "155": "Expel organisation",
    "156": "Impose administrative sanctions",
    # Coerce
    "160": "Coerce",
    "161": "Arrest or detain",
    "162": "Expel or deport",
    "163": "Seize property",
    "164": "Conduct hunger strike",
    "165": "Conduct strike or boycott",
    "166": "Impose blockade",
    "168": "Use tactical force",
    # Assault
    "170": "Assault",
    "171": "Use conventional military force",
    "172": "Use unconventional violence",
    "173": "Kill",
    "174": "Wound or injure",
    "175": "Abduct, kidnap, take hostage",
    "176": "Torture",
    "180": "Use unconventional mass violence",
    "181": "Abduct, hijack, take hostage",
    "182": "Conduct suicide bombing",
    "183": "Conduct car bombing",
    "186": "Conduct biological, chemical attack",
    "190": "Use unconventional violence",
    "193": "Carry out suicide bombing",
    "194": "Carry out vehicle bombing",
    "195": "Conduct cyber attack",
    # Military force
    "200": "Use conventional military force",
    "201": "Conduct air strike",
    "202": "Conduct naval blockade",
    "203": "Occupy territory",
    "204": "Engage in border conflict",
    "205": "Engage in naval battle",
    "206": "Violate ceasefire",
}


# ─── 3. STRATEGIC COUNTRY CODES ──────────────────────────────────
# Actor country codes to keep when filtering GDELT rows.
# If Actor1CountryCode or Actor2CountryCode is in this list, keep the row.
# These are GDELT's 3-letter ISO codes.

STRATEGIC_COUNTRY_CODES = [
    'IND',  # India — always keep
    'CHN',  # China — primary threat
    'PAK',  # Pakistan — primary threat
    'USA',  # United States — primary partner
    'RUS',  # Russia — arms supplier, strategic partner
    'BGD',  # Bangladesh — direct neighbour
    'NPL',  # Nepal — buffer state
    'LKA',  # Sri Lanka — Indian Ocean
    'MDV',  # Maldives — Indian Ocean chokepoint
    'AFG',  # Afghanistan — terrorism, instability
    'MMR',  # Myanmar — insurgency spillover
    'BTN',  # Bhutan — buffer state, China border
    'IRN',  # Iran — CPEC context, energy
    'SAU',  # Saudi Arabia — energy security
    'ARE',  # UAE — Indian diaspora, trade
    'ISR',  # Israel — defence cooperation
    'JPN',  # Japan — QUAD member
    'AUS',  # Australia — QUAD member
]


# ─── 4. STRATEGIC GEO CODES ──────────────────────────────────────
# Same countries but using GDELT's 2-letter geo codes.
# Used to filter on ActionGeo_CountryCode, Actor1Geo_CountryCode etc.
# These are different from the 3-letter actor codes above.

STRATEGIC_GEO_CODES = [
    'IN',   # India
    'CH',   # China
    'PK',   # Pakistan
    'US',   # United States
    'RS',   # Russia
    'BG',   # Bangladesh
    'NP',   # Nepal
    'CE',   # Sri Lanka
    'MV',   # Maldives
    'AF',   # Afghanistan
    'BM',   # Myanmar
    'BT',   # Bhutan
    'IR',   # Iran
    'SA',   # Saudi Arabia
    'AE',   # UAE
    'IS',   # Israel
    'JA',   # Japan
    'AS',   # Australia
]


# ─── 5. CANONICAL ENTITY DICTIONARY ─────────────────────────────
# Used by pipeline/resolution.py for entity resolution.
# Maps canonical names → Wikidata IDs and aliases.
#
# HOW TO ADD NEW ENTITIES:
# 1. Go to wikidata.org and search the entity name
# 2. Copy the Q-number from the URL (e.g. Q668 for India)
# 3. Add an entry below with all known aliases
#
# The more aliases you add, the better entity resolution works.
# This is the one file your domain analyst should expand.

CANONICAL_ENTITIES = {

    # ── INDIAN LEADERS ───────────────────────────────────────────
    "Narendra Modi": {
        "wikidata_id": "Q1058580",
        "type": "PERSON",
        "role": "Prime Minister of India",
        "country": "India",
        "aliases": [
            "Modi", "PM Modi", "Indian PM", "Modi ji",
            "Shri Modi", "NaMo", "Narendra Damodardas Modi"
        ]
    },
    "S. Jaishankar": {
        "wikidata_id": "Q7394088",
        "type": "PERSON",
        "role": "External Affairs Minister of India",
        "country": "India",
        "aliases": [
            "Jaishankar", "EAM Jaishankar", "S Jaishankar",
            "Subrahmanyam Jaishankar", "Dr Jaishankar", "MEA Jaishankar"
        ]
    },
    "Rajnath Singh": {
        "wikidata_id": "Q552218",
        "type": "PERSON",
        "role": "Defence Minister of India",
        "country": "India",
        "aliases": [
            "Rajnath", "Defence Minister Singh", "Rajnath Singh"
        ]
    },
    "Amit Shah": {
        "wikidata_id": "Q18590784",
        "type": "PERSON",
        "role": "Home Minister of India",
        "country": "India",
        "aliases": [
            "Amit Shah", "Home Minister Shah", "Union Home Minister"
        ]
    },
    "Anil Chauhan": {
        "wikidata_id": "Q116946174",
        "type": "PERSON",
        "role": "Chief of Defence Staff India",
        "country": "India",
        "aliases": [
            "General Chauhan", "CDS Chauhan", "Chief of Defence Staff",
            "CDS Anil Chauhan"
        ]
    },
    "Manoj Pande": {
        "wikidata_id": "Q113661553",
        "type": "PERSON",
        "role": "Chief of Army Staff India",
        "country": "India",
        "aliases": [
            "General Manoj Pande", "Army Chief Pande",
            "Chief of Army Staff", "COAS Pande"
        ]
    },
    "R.Hari Kumar": {
        "wikidata_id": "Q113661560",
        "type": "PERSON",
        "role": "Chief of Naval Staff India",
        "country": "India",
        "aliases": [
            "Admiral Hari Kumar", "CNS Hari Kumar", "Chief of Naval Staff"
        ]
    },
    "V.R. Chaudhari": {
        "wikidata_id": "Q113661558",
        "type": "PERSON",
        "role": "Chief of Air Staff India",
        "country": "India",
        "aliases": [
            "Air Chief Marshal Chaudhari", "CAS Chaudhari",
            "Chief of Air Staff", "VR Chaudhari"
        ]
    },

    # ── CHINESE LEADERS ──────────────────────────────────────────
    "Xi Jinping": {
        "wikidata_id": "Q6255",
        "type": "PERSON",
        "role": "President of China",
        "country": "China",
        "aliases": [
            "Xi", "President Xi", "Chinese President",
            "General Secretary Xi", "Chairman Xi"
        ]
    },
    "Li Qiang": {
        "wikidata_id": "Q714530",
        "type": "PERSON",
        "role": "Premier of China",
        "country": "China",
        "aliases": [
            "Premier Li", "Li Qiang", "Chinese Premier"
        ]
    },
    "Wang Yi": {
        "wikidata_id": "Q200180",
        "type": "PERSON",
        "role": "Foreign Minister of China",
        "country": "China",
        "aliases": [
            "Wang Yi", "Chinese Foreign Minister", "FM Wang Yi"
        ]
    },

    # ── PAKISTANI LEADERS ────────────────────────────────────────
    "Shehbaz Sharif": {
        "wikidata_id": "Q432694",
        "type": "PERSON",
        "role": "Prime Minister of Pakistan",
        "country": "Pakistan",
        "aliases": [
            "Shahbaz Sharif", "Shehbaz", "Pakistani PM",
            "PM Sharif", "PM Shehbaz"
        ]
    },
    "Asim Munir": {
        "wikidata_id": "Q116433474",
        "type": "PERSON",
        "role": "Chief of Army Staff Pakistan",
        "country": "Pakistan",
        "aliases": [
            "General Asim Munir", "COAS Munir", "Pakistan Army Chief",
            "General Munir"
        ]
    },
    "Ishaq Dar": {
        "wikidata_id": "Q3149057",
        "type": "PERSON",
        "role": "Foreign Minister of Pakistan",
        "country": "Pakistan",
        "aliases": [
            "Ishaq Dar", "Pakistani FM", "FM Dar"
        ]
    },

    # ── US LEADERS ───────────────────────────────────────────────
    "Joe Biden": {
        "wikidata_id": "Q6279",
        "type": "PERSON",
        "role": "President of United States",
        "country": "United States",
        "aliases": [
            "Biden", "President Biden", "US President Biden"
        ]
    },
    "Antony Blinken": {
        "wikidata_id": "Q2811028",
        "type": "PERSON",
        "role": "US Secretary of State",
        "country": "United States",
        "aliases": [
            "Blinken", "Secretary Blinken", "US Secretary of State",
            "Antony Blinken"
        ]
    },
    "Lloyd Austin": {
        "wikidata_id": "Q6660249",
        "type": "PERSON",
        "role": "US Secretary of Defense",
        "country": "United States",
        "aliases": [
            "Austin", "Secretary Austin", "Defense Secretary Austin",
            "Lloyd Austin"
        ]
    },

    # ── RUSSIAN LEADERS ──────────────────────────────────────────
    "Vladimir Putin": {
        "wikidata_id": "Q7747",
        "type": "PERSON",
        "role": "President of Russia",
        "country": "Russia",
        "aliases": [
            "Putin", "President Putin", "Russian President"
        ]
    },
    "Sergei Lavrov": {
        "wikidata_id": "Q183903",
        "type": "PERSON",
        "role": "Foreign Minister of Russia",
        "country": "Russia",
        "aliases": [
            "Lavrov", "Russian FM", "Foreign Minister Lavrov"
        ]
    },

    # ── COUNTRIES ────────────────────────────────────────────────
    "India": {
        "wikidata_id": "Q668",
        "type": "COUNTRY",
        "aliases": [
            "Republic of India", "Bharat", "Indian government",
            "New Delhi", "GOI", "Government of India"
        ]
    },
    "China": {
        "wikidata_id": "Q148",
        "type": "COUNTRY",
        "aliases": [
            "People's Republic of China", "PRC", "Beijing",
            "Chinese government", "PROC"
        ]
    },
    "Pakistan": {
        "wikidata_id": "Q843",
        "type": "COUNTRY",
        "aliases": [
            "Islamic Republic of Pakistan", "Islamabad",
            "Pakistani government", "GOP"
        ]
    },
    "United States": {
        "wikidata_id": "Q30",
        "type": "COUNTRY",
        "aliases": [
            "USA", "US", "America", "Washington", "Washington DC",
            "White House", "State Department", "Pentagon"
        ]
    },
    "Russia": {
        "wikidata_id": "Q159",
        "type": "COUNTRY",
        "aliases": [
            "Russian Federation", "Moscow", "Kremlin",
            "Russian government"
        ]
    },
    "Bangladesh": {
        "wikidata_id": "Q902",
        "type": "COUNTRY",
        "aliases": [
            "People's Republic of Bangladesh", "Dhaka",
            "Bangladeshi government"
        ]
    },
    "Nepal": {
        "wikidata_id": "Q837",
        "type": "COUNTRY",
        "aliases": ["Federal Democratic Republic of Nepal", "Kathmandu"]
    },
    "Sri Lanka": {
        "wikidata_id": "Q854",
        "type": "COUNTRY",
        "aliases": [
            "Democratic Socialist Republic of Sri Lanka", "Colombo",
            "Ceylon"
        ]
    },
    "Maldives": {
        "wikidata_id": "Q826",
        "type": "COUNTRY",
        "aliases": ["Republic of Maldives", "Male", "Maldivian government"]
    },
    "Afghanistan": {
        "wikidata_id": "Q889",
        "type": "COUNTRY",
        "aliases": ["Islamic Emirate of Afghanistan", "Kabul", "Taliban"]
    },
    "Myanmar": {
        "wikidata_id": "Q836",
        "type": "COUNTRY",
        "aliases": ["Burma", "Republic of the Union of Myanmar", "Naypyidaw"]
    },
    "Iran": {
        "wikidata_id": "Q794",
        "type": "COUNTRY",
        "aliases": [
            "Islamic Republic of Iran", "Tehran", "Persia",
            "Iranian government"
        ]
    },

    # ── MILITARY ORGANISATIONS ───────────────────────────────────
    "People's Liberation Army": {
        "wikidata_id": "Q8733",
        "type": "ORGANIZATION",
        "aliases": [
            "PLA", "Chinese Army", "Chinese military",
            "PLA Army", "PLAA", "Chinese Armed Forces"
        ]
    },
    "Indian Army": {
        "wikidata_id": "Q188822",
        "type": "ORGANIZATION",
        "aliases": [
            "Indian Armed Forces", "Indian military",
            "Indian troops", "Indian soldiers"
        ]
    },
    "Pakistani Army": {
        "wikidata_id": "Q182609",
        "type": "ORGANIZATION",
        "aliases": [
            "Pakistan Army", "Pakistani military",
            "Pakistan Armed Forces", "ISI"
        ]
    },
    "Inter-Services Intelligence": {
        "wikidata_id": "Q1266645",
        "type": "ORGANIZATION",
        "aliases": ["ISI", "Pakistani intelligence", "Pakistan ISI"]
    },

    # ── MULTILATERAL ORGANISATIONS ───────────────────────────────
    "SCO": {
        "wikidata_id": "Q842490",
        "type": "ORGANIZATION",
        "full_name": "Shanghai Cooperation Organisation",
        "aliases": [
            "Shanghai Cooperation Organization",
            "Shanghai Cooperation Organisation",
            "SCO summit"
        ]
    },
    "QUAD": {
        "wikidata_id": "Q7268213",
        "type": "ORGANIZATION",
        "full_name": "Quadrilateral Security Dialogue",
        "aliases": [
            "Quadrilateral Security Dialogue", "QUAD alliance",
            "Quad summit", "Indo-Pacific Quad"
        ]
    },
    "BRICS": {
        "wikidata_id": "Q48268",
        "type": "ORGANIZATION",
        "aliases": [
            "BRIC", "BRICS nations", "BRICS summit",
            "BRICS bloc"
        ]
    },
    "United Nations": {
        "wikidata_id": "Q1065",
        "type": "ORGANIZATION",
        "aliases": [
            "UN", "UN Security Council", "UNSC",
            "UN General Assembly", "UNGA", "United Nations Security Council"
        ]
    },
    "NATO": {
        "wikidata_id": "Q7184",
        "type": "ORGANIZATION",
        "aliases": [
            "North Atlantic Treaty Organization",
            "North Atlantic Alliance", "NATO alliance"
        ]
    },
    "IMF": {
        "wikidata_id": "Q3392857",
        "type": "ORGANIZATION",
        "aliases": [
            "International Monetary Fund",
            "IMF loan", "IMF bailout"
        ]
    },

    # ── KEY LOCATIONS ────────────────────────────────────────────
    "Line of Actual Control": {
        "wikidata_id": "Q1066344",
        "type": "LOCATION",
        "aliases": [
            "LAC", "Actual Control Line",
            "Indo-Chinese border", "China-India border"
        ]
    },
    "Depsang Plains": {
        "wikidata_id": "Q1247899",
        "type": "LOCATION",
        "aliases": [
            "Depsang", "Depsang Valley", "Depsang bulge",
            "Depsang Plains area"
        ]
    },
    "Galwan Valley": {
        "wikidata_id": "Q6482987",
        "type": "LOCATION",
        "aliases": [
            "Galwan", "Galwan river", "Galwan clash site",
            "Galwan sector"
        ]
    },
    "Aksai Chin": {
        "wikidata_id": "Q190434",
        "type": "LOCATION",
        "aliases": [
            "Aksai Chin region", "Aksai Chin plateau"
        ]
    },
    "Arunachal Pradesh": {
        "wikidata_id": "Q1162",
        "type": "LOCATION",
        "aliases": [
            "Arunachal", "South Tibet",
            "Zangnan", "Northeast India"
        ]
    },
    "Kashmir": {
        "wikidata_id": "Q43473",
        "type": "LOCATION",
        "aliases": [
            "Jammu and Kashmir", "J&K", "Kashmir Valley",
            "PoK", "Pakistan-occupied Kashmir",
            "Azad Kashmir"
        ]
    },
    "South China Sea": {
        "wikidata_id": "Q34480",
        "type": "LOCATION",
        "aliases": [
            "SCS", "South China Sea dispute",
            "disputed waters South China Sea"
        ]
    },
    "Indian Ocean": {
        "wikidata_id": "Q1247",
        "type": "LOCATION",
        "aliases": [
            "IOR", "Indian Ocean Region",
            "Indo-Pacific", "Indian Ocean waters"
        ]
    },
    "Hambantota": {
        "wikidata_id": "Q205662",
        "type": "LOCATION",
        "aliases": [
            "Hambantota port", "Hambantota Sri Lanka",
            "Chinese port Sri Lanka"
        ]
    },
    "Gwadar": {
        "wikidata_id": "Q170176",
        "type": "LOCATION",
        "aliases": [
            "Gwadar port", "Gwadar Pakistan",
            "CPEC port", "Chinese port Pakistan"
        ]
    },

    # ── STRATEGIC PROGRAMMES AND INITIATIVES ─────────────────────
    "CPEC": {
        "wikidata_id": "Q18608389",
        "type": "ORGANIZATION",
        "full_name": "China-Pakistan Economic Corridor",
        "aliases": [
            "China Pakistan Economic Corridor",
            "CPEC project", "Belt and Road Pakistan"
        ]
    },
    "Belt and Road Initiative": {
        "wikidata_id": "Q19875622",
        "type": "ORGANIZATION",
        "aliases": [
            "BRI", "One Belt One Road", "OBOR",
            "Silk Road Economic Belt", "New Silk Road"
        ]
    },
}


# ─── 6. SOURCE CLASSIFICATION ────────────────────────────────────
# Maps news source domain → country of origin and media type.
# Used by api/usp_analysis.py for Narrative Warfare Detection (USP 1).
# "state" = government controlled outlet
# "independent" = privately owned outlet

SOURCE_CLASSIFICATION = {
    # Chinese state media
    "xinhuanet.com":       {"country": "CHN", "type": "state"},
    "globaltimes.cn":      {"country": "CHN", "type": "state"},
    "chinadaily.com.cn":   {"country": "CHN", "type": "state"},
    "cgtn.com":            {"country": "CHN", "type": "state"},
    "peopledaily.com.cn":  {"country": "CHN", "type": "state"},
    "china.org.cn":        {"country": "CHN", "type": "state"},

    # Pakistani media
    "radio.gov.pk":        {"country": "PAK", "type": "state"},
    "app.com.pk":          {"country": "PAK", "type": "state"},
    "pid.gov.pk":          {"country": "PAK", "type": "state"},
    "dawn.com":            {"country": "PAK", "type": "independent"},
    "geo.tv":              {"country": "PAK", "type": "independent"},
    "thenews.com.pk":      {"country": "PAK", "type": "independent"},
    "arynews.tv":          {"country": "PAK", "type": "independent"},
    "tribune.com.pk":      {"country": "PAK", "type": "independent"},

    # Indian media
    "timesofindia.com":    {"country": "IND", "type": "independent"},
    "thehindu.com":        {"country": "IND", "type": "independent"},
    "ndtv.com":            {"country": "IND", "type": "independent"},
    "hindustantimes.com":  {"country": "IND", "type": "independent"},
    "indianexpress.com":   {"country": "IND", "type": "independent"},
    "theprint.in":         {"country": "IND", "type": "independent"},
    "thewire.in":          {"country": "IND", "type": "independent"},
    "firstpost.com":       {"country": "IND", "type": "independent"},
    "news18.com":          {"country": "IND", "type": "independent"},
    "ani.com":             {"country": "IND", "type": "independent"},
    "pib.gov.in":          {"country": "IND", "type": "state"},
    "mea.gov.in":          {"country": "IND", "type": "state"},
    "pmo.gov.in":          {"country": "IND", "type": "state"},

    # Russian state media
    "rt.com":              {"country": "RUS", "type": "state"},
    "tass.com":            {"country": "RUS", "type": "state"},
    "tass.ru":             {"country": "RUS", "type": "state"},
    "sputniknews.com":     {"country": "RUS", "type": "state"},
    "interfax.com":        {"country": "RUS", "type": "independent"},

    # Bangladeshi media
    "thedailystar.net":    {"country": "BGD", "type": "independent"},
    "prothomalo.com":      {"country": "BGD", "type": "independent"},
    "dhakatribune.com":    {"country": "BGD", "type": "independent"},
    "bss.gov.bd":          {"country": "BGD", "type": "state"},

    # Sri Lankan media
    "dailymirror.lk":      {"country": "LKA", "type": "independent"},
    "sundaytimes.lk":      {"country": "LKA", "type": "independent"},
    "news.lk":             {"country": "LKA", "type": "state"},

    # US/Western media
    "reuters.com":         {"country": "INT", "type": "independent"},
    "apnews.com":          {"country": "INT", "type": "independent"},
    "bbc.com":             {"country": "GBR", "type": "independent"},
    "bbc.co.uk":           {"country": "GBR", "type": "independent"},
    "theguardian.com":     {"country": "GBR", "type": "independent"},
    "france24.com":        {"country": "FRA", "type": "state"},
    "dw.com":              {"country": "DEU", "type": "state"},
    "aljazeera.com":       {"country": "QAT", "type": "state"},
    "bloomberg.com":       {"country": "INT", "type": "independent"},
    "nytimes.com":         {"country": "INT", "type": "independent"},
    "washingtonpost.com":  {"country": "INT", "type": "independent"},
    "foreignpolicy.com":   {"country": "INT", "type": "independent"},
    "thediplomat.com":      {"country": "INT", "type": "independent"},
    "eastasiaforum.org":   {"country": "INT", "type": "independent"},
}


def classify_source(url: str) -> dict:
    """
    Returns {country, type} for a given source URL.
    Checks if any known domain appears in the URL string.
    Falls back to unknown if domain not in dictionary.

    Used by api/usp_analysis.py — USP 1 Narrative Warfare Detection.
    """
    if not url:
        return {"country": "UNK", "type": "unknown"}

    for domain, info in SOURCE_CLASSIFICATION.items():
        if domain in url:
            return info

    return {"country": "UNK", "type": "unknown"}