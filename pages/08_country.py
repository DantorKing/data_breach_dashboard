"""
pages/08_country.py
---------------------
Question this page answers: which countries have had the most data breaches?

IMPORTANT: the dataset has NO geographic column. Country is INFERRED from each
organisation's name (curated lookup) and from country keywords in the name
(e.g. "US Office of Personnel Management" -> United States, "Adidas" -> Germany).
Global companies and unidentifiable rows are lumped into "Global / Unknown".
Treat every country figure as an approximation, not an official statistic.
"""

import pandas as pd
import plotly.express as px
import streamlit as st

import utils

# ---------------------------------------------------------------------------
# Inferred country mapping (see module docstring for why this exists)
# ---------------------------------------------------------------------------

# Country name -> ISO3 code for the choropleth
COUNTRY_ISO3 = {
    "United States": "USA", "United Kingdom": "GBR", "Japan": "JPN",
    "Germany": "DEU", "France": "FRA", "Canada": "CAN", "India": "IND",
    "Australia": "AUS", "Israel": "ISR", "South Korea": "KOR", "Russia": "RUS",
    "China": "CHN", "Hong Kong": "HKG", "Sweden": "SWE", "Taiwan": "TWN",
    "Italy": "ITA", "Spain": "ESP", "Netherlands": "NLD", "Indonesia": "IDN",
    "Brazil": "BRA", "Norway": "NOR", "Finland": "FIN", "Turkey": "TUR",
    "Pakistan": "PAK", "Ireland": "IRL", "New Zealand": "NZL", "Greece": "GRC",
    "Hungary": "HUN", "Argentina": "ARG", "United Arab Emirates": "ARE",
    "Denmark": "DNK", "Switzerland": "CHE", "Belgium": "BEL", "Sri Lanka": "LKA",
    "Panama": "PAN", "Iraq": "IRQ", "Austria": "AUT", "Poland": "POL",
    "Singapore": "SGP", "Thailand": "THA", "Vietnam": "VNM", "Malaysia": "MYS",
    "Philippines": "PHL", "Iran": "IRN", "Saudi Arabia": "SAU", "Qatar": "QAT",
    "Kuwait": "KWT", "Egypt": "EGY", "Mexico": "MEX", "Chile": "CHL",
    "Costa Rica": "CRI", "Iceland": "ISL", "Luxembourg": "LUX", "Malta": "MLT",
    "Cyprus": "CYP", "Romania": "ROU", "Bulgaria": "BGR", "Serbia": "SRB",
    "Estonia": "EST", "South Africa": "ZAF", "Ukraine": "UKR", "Czechia": "CZE",
    "Portugal": "PRT", "Bangladesh": "BGD", "Nepal": "NPL", "Mongolia": "MNG",
    "Latvia": "LVA", "Lithuania": "LTU", "Slovakia": "SVK", "Croatia": "HRV",
    "Slovenia": "SVN", "Peru": "PER", "Colombia": "COL", "Venezuela": "VEN",
    "Uruguay": "URY", "Paraguay": "PRY", "Bolivia": "BOL", "Ecuador": "ECU",
    "Dominican Republic": "DOM", "Cuba": "CUB", "Jamaica": "JAM",
    "Trinidad and Tobago": "TTO", "Honduras": "HND", "Guatemala": "GTM",
    "El Salvador": "SLV", "Nicaragua": "NIC", "Morocco": "MAR", "Algeria": "DZA",
    "Tunisia": "TUN", "Libya": "LBY", "Sudan": "SDN", "Ethiopia": "ETH",
    "Kenya": "KEN", "Nigeria": "NGA", "Ghana": "GHA", "Tanzania": "TZA",
    "Uganda": "UGA", "Zimbabwe": "ZWE", "Zambia": "ZMB", "Mozambique": "MOZ",
    "Angola": "AGO", "Botswana": "BWA", "Namibia": "NAM", "Senegal": "SEN",
    "Mali": "MLI", "Cameroon": "CMR", "Ivory Coast": "CIV", "North Korea": "PRK",
    "Afghanistan": "AFG", "Yemen": "YEM", "Oman": "OMN", "Bahrain": "BHR",
    "Jordan": "JOR", "Lebanon": "LBN", "Syria": "SYR", "Myanmar": "MMR",
    "Cambodia": "KHM", "Laos": "LAO", "Kazakhstan": "KAZ", "Uzbekistan": "UZB",
    "Azerbaijan": "AZE", "Georgia": "GEO", "Armenia": "ARM", "Belarus": "BLR",
    "Moldova": "MDA", "Albania": "ALB", "North Macedonia": "MKD", "Bosnia and Herzegovina": "BIH",
    "Montenegro": "MNE", "Kosovo": "XKX", "Fiji": "FJI", "Papua New Guinea": "PNG",
}

# Country keywords embedded in organisation names -> country name
COUNTRY_KEYWORDS = {
    "UK": "United Kingdom", "British": "United Kingdom", "NHS": "United Kingdom",
    "US ": "United States", "U.S.": "United States", "American": "United States",
    "Texas": "United States", "California": "United States", "Florida": "United States",
    "Massachusetts": "United States", "South Carolina": "United States",
    "New York": "United States", "Washington State": "United States", "Baltimore": "United States",
    "Ohio": "United States", "Colorado": "United States", "Maine": "United States",
    "Oregon": "United States", "Virginia": "United States", "San Francisco": "United States",
    "Pennsylvania": "United States", "New York City": "United States", "IRS": "United States",
    "Medicare": "United States", "Medicaid": "United States",
    "Australian": "Australia", "Australia": "Australia", "Sydney": "Australia",
    "Canadian": "Canada", "Canada": "Canada", "Toronto": "Canada", "Nova Scotia": "Canada",
    "Helsinki": "Finland", "Finnish": "Finland", "Finland": "Finland", "Vastaamo": "Finland",
    "German": "Germany", "Germany": "Germany", "Berlin": "Germany", "Doner Kebab": "Germany",
    "France": "France", "French": "France", "Francaise": "France", "Paris": "France",
    "Japan": "Japan", "Japanese": "Japan", "Amagasaki": "Japan", "Tokyo": "Japan",
    "China": "China", "Chinese": "China", "Shanghai": "China",
    "Korean": "South Korea", "Korea": "South Korea", "Seoul": "South Korea",
    "India": "India", "Indian": "India", "Delhi": "India", "Mumbai": "India",
    "Turkey": "Turkey", "Turkish": "Turkey",
    "Brazil": "Brazil", "Brasil": "Brazil",
    "Russia": "Russia", "Russian": "Russia", "Moscow": "Russia", "VK": "Russia",
    "Netherlands": "Netherlands", "Dutch": "Netherlands",
    "Sweden": "Sweden", "Swedish": "Sweden",
    "Norway": "Norway", "Norwegian": "Norway",
    "Italy": "Italy", "Italian": "Italy", "Hacking Team": "Italy",
    "Spain": "Spain", "Spanish": "Spain",
    "Ireland": "Ireland", "Irish": "Ireland",
    "Greece": "Greece", "Greek": "Greece",
    "Switzerland": "Switzerland", "Swiss": "Switzerland",
    "Poland": "Poland", "Polish": "Poland",
    "Estonia": "Estonia", "Estonian": "Estonia",
    "Bulgaria": "Bulgaria", "Bulgarian": "Bulgaria",
    "Romania": "Romania", "Romanian": "Romania",
    "Serbia": "Serbia", "Serbian": "Serbia",
    "Belgium": "Belgium", "Belgian": "Belgium", "NMBS": "Belgium",
    "Singapore": "Singapore", "Singaporean": "Singapore", "SingHealth": "Singapore",
    "Hong Kong": "Hong Kong", "Thailand": "Thailand", "Thai": "Thailand",
    "Vietnam": "Vietnam", "Vietnamese": "Vietnam",
    "Malaysia": "Malaysia", "Malaysian": "Malaysia",
    "Indonesia": "Indonesia", "Indonesian": "Indonesia",
    "Philippines": "Philippines", "Philippine": "Philippines",
    "Pakistan": "Pakistan", "Pakistani": "Pakistan",
    "Iran": "Iran", "Iranian": "Iran", "Iraq": "Iraq",
    "Israel": "Israel", "Israeli": "Israel",
    "Syria": "Syria", "Syrian": "Syria",
    "Saudi": "Saudi Arabia", "Qatar": "Qatar", "Kuwait": "Kuwait",
    "UAE": "United Arab Emirates", "Dubai": "United Arab Emirates", "Emirates": "United Arab Emirates",
    "Egypt": "Egypt", "Mexico": "Mexico", "Mexican": "Mexico", "Chile": "Chile",
    "Panama": "Panama", "Costa Rica": "Costa Rica", "New Zealand": "New Zealand",
    "European Central Bank": "Germany", "NATO": "Belgium", "Contact tracing data": "United Kingdom",
}

# Curated organisation -> country. Only organisations whose home country is
# reasonably unambiguous are listed; everything else falls back to keywords or
# "Global / Unknown".
CURATED = {
    '"Apple"': "United States", "Apple": "United States", "23andMe": "United States",
    "500px": "Canada", "8fit": "Germany", "AOL": "United States", "AT&T": "United States",
    "Aadhaar": "India", "Accendo Insurance Co. ": "United States", "Acer": "Taiwan",
    "Activision": "United States", "Adidas": "Germany", "Adobe": "United States",
    "Adult Friend Finder": "United States", "Advocate Medical Group": "United States",
    "Affinity Health Plan, Inc.": "United States", "Aimware": "Germany",
    "Al.type": "Hong Kong", "Amazon": "United States", "Amazon Reviews": "United States",
    "Ameritrade Inc.": "United States", "Animoto": "United States",
    "Ankle & foot Center of Tampa Bay, Inc.": "United States", "Anthem ": "United States",
    "Apollo": "India", "Armor Games": "United States", "Artsy": "United States",
    "AshleyMadison.com": "Canada", "Atlassian": "Australia", "Auction.co.kr": "South Korea",
    "Automatic Data Processing": "United States", "AvMed, Inc.": "United States",
    "Avvo": "United States", "BBC": "United Kingdom", "BNY Mellon Shareowner Services": "United States",
    "Banner Health": "United States", "Bell": "Canada", "Betfair": "United Kingdom",
    "Bethesda Game Studios": "United States", "Blank Media Games": "United States",
    "Blizzard": "United States", "Blue Cross Blue Shield of Tennessee": "United States",
    "Blur": "United States", "BookMate": "India", "Boots Advantage Card": "United Kingdom",
    "Brazzers": "Canada", "Brewdog": "United Kingdom", "BriansClub": "United States",
    "Buchbinder Car Rentals": "Germany", "CDEK": "Russia", "CEX": "United Kingdom",
    "Call of Duty / Activision": "United States", "Canva": "Australia",
    "Capital One": "United States", "CarPhone Warehouse": "United Kingdom",
    "Cardsystems Solutions Inc. ": "United States", "Careem": "United Arab Emirates",
    "Carefirst": "United States", "Cartier ": "France", "Casio": "Japan",
    "Cathay Pacific Airways": "Hong Kong", "Cellebrite": "Israel", "Cencora": "United States",
    "Cense AI": "Israel", "Central Hudson Gas & Electric": "United States", "ChatGPT": "United States",
    "CheckFree Corporation": "United States", "Christie's": "United Kingdom",
    "Chtrbox": "India", "CircleCI": "United States", "Citigroup": "United States",
    "City and Hackney Teaching Primary Care Trust": "United Kingdom", "Click2Gov": "United States",
    "Clinton campaign": "United States", "ClixSense": "United States", "Clorox": "United States",
    "Cock.li": "Germany", "CoffeeMeetsBagel": "United States", "CoinSquare": "Canada",
    "Coinbase": "United States", "Coinmama": "Israel", "ColoCrossing": "United States",
    "Community Health Systems": "United States", "CommuteAir": "United States",
    "Compass Bank": "United States", "Cooler Master": "Taiwan", "Countrywide Financial Corp": "United States",
    "Coupang": "South Korea", "Court Ventures": "United States",
    "Crescent Health Inc., Walgreens": "United States", "D&B, Altegrity": "United States",
    "DaFont": "France", "Dai Nippon Printing": "Japan", "Dailymotion": "France",
    "DataCamp": "United States", "Deep Root Analytics": "United States", "Dell": "United States",
    "Dell ": "United States", "Delta Dental": "United States", "Desjardins Group": "Canada",
    "Digital Ocean": "United States", "Discord.io": "United States", "Disk Union": "Japan",
    "Disqus": "United States", "Dixons Carphone": "United Kingdom", "DoorDash": "United States",
    "Driving Standards Agency": "United Kingdom", "Drizly": "United States", "Dropbox": "United States",
    "Drupal": "Belgium", "Dubsmash": "Germany", "EasyJet": "United Kingdom", "EasyPark": "Sweden",
    "Ebay": "United States", "Educational Credit Management Corp": "United States",
    "Eisenhower Medical Center": "United States", "Emergency Healthcare Physicians, Ltd.": "United States",
    "Emory Healthcare": "United States", "Epik": "United States", "Episource ": "United States",
    "Epsilon": "United States", "Equifax": "United States", "Everbridge": "United States",
    "Evernote": "United States", "Experian / T-mobile": "United States", "Experian SA": "France",
    "EyeEm": "Germany", "Facebook": "United States", "Fidelity National Information Services": "United States",
    "Financial Business and Consumer Solutions": "United States", "Firebase": "United States",
    "Firstmac": "Australia", "FlexBooker": "United States", "Fling": "United States",
    "Formspring": "United States", "Fotolog": "United States", "Free": "France",
    "Friend Finder Network": "United States", "GEDmatch": "United States", "GMail": "United States",
    "GS Caltex": "South Korea", "Gab": "United States", "Gamigo": "Germany",
    "Gap Inc": "United States", "Gawker.com": "United States", "Ge.tt": "Denmark",
    "GiveSendGo": "United States", "Global Payments": "United States", "Go Daddy": "United States",
    "GoDaddy": "United States", "Google+": "United States", "GovPayNow.com": "United States",
    "Grindr": "United States", "Guntrader": "United Kingdom", "HCA": "United States",
    "HSE": "Ireland", "Hannaford Brothers Supermarket Chain": "United States", "HauteLook": "United States",
    "Have Fun Teaching": "United States", "Health Net ": "United States", "Health Net - IBM": "United States",
    "Heartland": "United States", "Helse Sør-Øst RHF": "Norway", "Heroku": "United States",
    "Hewlett Packard": "United States", "High Tail Hall": "United States", "Ho Mobile": "Italy",
    "Home Depot": "United States", "Houzz": "United States", "INL": "United States",
    "Imgur": "United States", "Instagram": "United States", "Internet Archive": "United States",
    "Interpark": "South Korea", "Invest Bank": "United Arab Emirates", "Ixigo": "India",
    "JD Sports": "United Kingdom", "JP Morgan Chase": "United States", "KDDI": "Japan",
    "KM.ru & Nival": "Russia", "KT Corp.": "South Korea", "Kaiser Permanente": "United States",
    "Kirkwood Community College": "United States", "Kodex": "Germany", "Krispy Kreme ": "United States",
    "Kromtech": "Russia", "LINE Pay": "Japan", "Last.fm": "United Kingdom", "LastPass": "United States",
    "Latitude Financial": "Australia", "Ledger": "France", "Lee Enterprises ": "United States",
    "LexisNexis": "United States", "Lincoln Medical & Mental Health Center": "United States",
    "LinkedIn": "United States", "LinkedIn, eHarmony, Last.fm": "United States", "Linkedin": "United States",
    "Linux Ubuntu forums": "United Kingdom", "Living Social": "United States", "LocalBlox": "United States",
    "Lynda.com": "United States", "MBM Company": "Israel", "MGM": "United States", "MGM Hotels": "United States",
    "MSI": "Taiwan", "MSpy": "Russia", "MacDonalds": "United States", "MacRumours.com": "United States",
    "Mail. ru": "Russia", "Mailchimp": "United States", "Marriott Hotels": "United States", "Marriott International": "United States",
    "Maximus": "United States", "Meet Mindful": "United States", "Memorial Healthcare System": "United States",
    "Microsoft": "United States", "Militarysingles.com": "United States", "Minecraft": "United States",
    "Monster.com": "United States", "Morgan Stanley Smith Barney": "United States",
    "Mossack Fonseca": "Panama", "Mount Olympus": "Greece", "Mozilla": "United States",
    "Mutuelle Generale de la Police": "France", "MyFitnessPal": "United States", "MyHeritage": "Israel",
    "MySpace": "United States", "NASDAQ": "United States", "Nametests": "Israel",
    "National Amusements": "United States", "National Public Data": "United States",
    "National Security Agency": "United States", "Neiman Marcus": "United States",
    "Nemours Foundation": "United States", "Network Solutions": "United States", "Newegg": "United States",
    "News Corp": "United States", "Nintendo": "Japan", "Nissan": "Japan", "Nvidia": "United States",
    "OPM": "United States", "OVH": "France", "Okta": "United States", "Omiai dating app": "Japan",
    "OmniVision": "United States", "Open Subtitles": "Germany", "Optus": "Australia",
    "Orbitz": "United States", "OxyData": "Israel", "Panda Restaurants": "United States",
    "Pandora Papers": "Panama", "Panerabread": "United States", "Park Mobile": "Russia",
    "PayAsUGym": "United Kingdom", "PayHere": "Sri Lanka", "PayPal ": "United States",
    "Peloton": "United States", "Petflow": "United States", "PharMerica": "United States",
    "Philadelphia Inquirer": "United States", "Plex": "United States", "PowerSchool": "United States",
    "Premera": "United States", "Quantas": "Australia", "Quest Diagnostics": "United States",
    "Quora": "United States", "RBS Worldpay": "United States", "Red Cross": "Switzerland",
    "Red Cross Blood Service": "Australia", "Reddit": "United States", "Restaurant Depot": "United States",
    "River City Media": "United States", "Robinhood": "United States", "Robinsons": "Singapore",
    "Roblox": "United States", "RockYou!": "United States", "Roll20": "United States",
    "RootsWeb": "United States", "Royal Enfield": "India", "SVR Tracking": "United States",
    "Saks and Lord & Taylor": "United States", "Sanrio": "Japan", "Santander": "Spain",
    "Sav-Rx": "United States", "Scribd": "United States", "Seacoast Radiology, PA": "United States",
    "Securus Technologies": "United States", "Sega": "Japan", "ShareThis": "United States",
    "Shein": "China", "Singing River": "United States", "Slack": "United States",
    "SnapChat": "United States", "Snapchat": "United States", "SolarWinds": "United States",
    "Sony": "Japan", "Sony Online Entertainment": "Japan", "Sony PSN": "Japan",
    "Sony Pictures": "United States", "SoundCloud": "Germany", "Spambot": "United States",
    "Spartanburg Regional Healthcare System": "United States", "Spectos": "Germany",
    "Spotify": "Sweden", "Stanford University": "United States", "Staples": "United States",
    "Star Alliance": "Germany", "Starbucks": "United States", "Steam": "United States",
    "Stratfor": "United States", "Stronghold Kingdoms": "United Kingdom", "Suprema": "South Korea",
    "Sutter Medical Foundation": "United States", "Syniverse": "United States",
    "T-Mobile": "United States", "T-Mobile ": "United States", "T-Mobile, Deutsche Telecom": "Germany",
    "T-mobile": "United States", "TD Ameritrade": "United States", "TIAA": "United States",
    "TIO Networks": "Canada", "TK / TJ Maxx": "United States", "TalkTalk": "United Kingdom",
    "Target": "United States", "Tea": "United States", "TehetségKapu": "Hungary",
    "Telegram ": "United Arab Emirates", "TerraCom & YourTel": "Canada", "Tesco Clubcard": "United Kingdom",
    "The Hospital Group": "United Kingdom", "The North Face": "United States",
    "The Post Millennial": "Canada", "Thermomix Recipe World Forum": "Germany", "Three": "United Kingdom",
    "Tianya": "China", "TicketFly": "United States", "Ticketmaster": "United States",
    "Topgolf Callaway": "United States", "Toyota": "Japan", "Travelio": "Indonesia",
    "Tricare": "United States", "Triple-S Salud, Inc.": "United States", "Tumblr": "United States",
    "Twitch": "United States", "Twitter": "United States", "UCLA Health": "United States",
    "UPS": "United States", "USG": "United States", "USPTO": "United States",
    "Ualabee": "Argentina", "Uber": "United States", "UbiSoft": "France", "Ubiquiti": "United States",
    "Ubuntu": "United Kingdom", "UnitedHealth ": "United States", "University of Delaware": "United States",
    "University of Miami": "United States", "University of Utah Hospitals & Clinics": "United States",
    "University of Wisconsin - Milwaukee": "United States", "Urban Massage": "United Kingdom",
    "VTech": "Hong Kong", "VW": "Germany", "VeriSource ": "United States", "Viacom": "United States",
    "ViewFines": "United Kingdom", "Virgin Media": "United Kingdom", "Vision Direct": "United Kingdom",
    "Vodafone": "United Kingdom", "Vårdguiden": "Sweden", "Washington Post": "United States",
    "Waterly": "Israel", "Wawa": "United States", "WebTPA": "United States", "Weebly": "United States",
    "Welltok": "United States", "Wendy's": "United States", "Whitepages": "United States",
    "WiFi Finder": "Canada", "Wiredbucks": "United States", "Wonga": "United Kingdom",
    "World Check": "United States", "Writerspace.com": "United States", "X (Twitter)": "United States",
    "Xfinity": "United States", "Yahoo": "United States", "Yahoo Voices": "United States",
    "Yale University": "United States", "YouNow": "United States", "Yum!": "United States",
    "Zappos": "United States", "Zhenhua": "China", "Zomato": "India", "Zoom": "United States",
    "db8151dd": "United States", "ssndob.ms": "United States", "uTorrent ": "United States",
    "visualisation here: https://informationisbeautiful.net/visualizations/worlds-biggest-data-breaches-hacks/\npink = new": "Global / Unknown",
    "Unknown": "Global / Unknown",
}

UNKNOWN_LABEL = "Global / Unknown"


def infer_country(name: str) -> str:
    """Infer a home country from an organisation name."""
    if name in CURATED:
        return CURATED[name]
    for keyword, country in COUNTRY_KEYWORDS.items():
        if keyword in name:
            return country
    return UNKNOWN_LABEL


utils.init_page("Country Analysis", icon="🌍")

st.title("🌍 Which countries have had the most attacks?")
st.caption(
    "Breaches attributed to a country by **inferring it from the organisation "
    "name** -- the dataset has no location field. Global firms and "
    "unidentifiable rows fall into 'Global / Unknown'. Treat these figures "
    "as **approximations**, not official statistics."
)

df = utils.load_data()
if df is None:
    st.error(
        "No dataset found in the `data/` folder. Drop a `.csv` or `.xlsx` "
        "file in there and rerun the app."
    )
    st.stop()

filtered = utils.render_sidebar_filters(df)

if filtered.empty:
    st.warning("No breaches match the current filters. Try widening them in the sidebar.")
    st.stop()

filtered = filtered.copy()
filtered["country"] = filtered["organisation"].apply(infer_country)
filtered["iso3"] = filtered["country"].map(COUNTRY_ISO3)

# --- Page-specific controls -------------------------------------------------
metric_choice = st.radio(
    "Measure",
    ["Number of breaches", "Total records lost"],
    horizontal=True,
    key="page8_metric",
)

value_col = "records_lost" if metric_choice == "Total records lost" else "breaches"
ylabel = "Records lost" if metric_choice == "Total records lost" else "Number of breaches"

country_stats = (
    filtered.groupby("country", as_index=False)
    .agg(
        breaches=("organisation", "count"),
        records_lost=("records_lost", "sum"),
    )
    .sort_values(value_col, ascending=False)
)
country_stats["iso3"] = country_stats["country"].map(COUNTRY_ISO3)

mapped = country_stats[country_stats["iso3"].notna() & (country_stats["country"] != UNKNOWN_LABEL)]
unmapped = country_stats[country_stats["country"] == UNKNOWN_LABEL]

# --- Chart 1: world map -----------------------------------------------------
st.subheader("Where do the breaches land?")
if mapped.empty:
    st.info("No mappable countries match the current filters.")
else:
    fig_map = px.choropleth(
        mapped,
        locations="iso3",
        color=value_col,
        hover_name="country",
        hover_data={"breaches": True, "records_lost": ":,.0f"},
        color_continuous_scale="Reds",
        labels={value_col: ylabel},
    )
    st.plotly_chart(fig_map, width='stretch')

# --- Chart 2: ranking bar ---------------------------------------------------
st.subheader(f"Top 15 countries by {metric_choice.lower()}")
top15 = country_stats.head(15)
fig_bar = px.bar(
    top15.sort_values(value_col),
    x=value_col,
    y="country",
    orientation="h",
    color=value_col,
    color_continuous_scale="Reds",
    hover_data={"breaches": True, "records_lost": ":,.0f"},
    labels={value_col: ylabel, "country": ""},
)
fig_bar.update_layout(coloraxis_showscale=False, yaxis_title="")
st.plotly_chart(fig_bar, width='stretch')

# --- Supporting KPIs & table -------------------------------------------------
col1, col2, col3 = st.columns(3)
col1.metric("Breaches in view", f"{len(filtered):,}")
col2.metric("Distinct countries", int(country_stats[country_stats["country"] != UNKNOWN_LABEL]["country"].nunique()))
col3.metric(
    "Global / Unknown share",
    f"{unmapped['breaches'].sum() / len(filtered) * 100:.1f}%"
    if len(filtered) else "—",
)

st.caption(
    f"**{mapped['breaches'].sum():,}** of **{len(filtered):,}** breaches in view "
    f"({mapped['breaches'].sum() / len(filtered) * 100:.0f}%) were attributed to a "
    "specific country via the inferred mapping."
)

with st.expander("See country breakdown"):
    display = country_stats.rename(
        columns={
            "country": "Country",
            "breaches": "Breaches",
            "records_lost": "Records lost",
        }
    )
    display["Records lost"] = display["Records lost"].map(utils.format_number)
    st.dataframe(display, width='stretch', hide_index=True)
