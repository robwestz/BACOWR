#!/usr/bin/env python3
"""
Ahrefs API Request Generator
Interaktivt verktyg för att skapa standardiserade Ahrefs API-förfrågningar
"""

import json
import sys
from typing import List, Optional
from datetime import datetime

# Tillgängliga kolumner med beskrivningar
AVAILABLE_COLUMNS = {
    "position": "Position i SERP",
    "url": "URL för rankande sida",
    "title": "Titel på rankande sida",
    "type": "Typ av position (organic, paid, SERP feature)",
    "domain_rating": "Domain Rating (0-100)",
    "url_rating": "URL Rating (0-100)",
    "ahrefs_rank": "Ahrefs Rank",
    "backlinks": "Totalt antal backlinks",
    "refdomains": "Antal unika domäner som länkar (kostar 5 units)",
    "keywords": "Antal keywords sidan rankar för",
    "traffic": "Estimerad månatlig organisk trafik (kostar 10 units)",
    "value": "Estimerat värde av trafiken i USD cents (kostar 10 units)",
    "top_keyword": "Keyword som ger mest trafik",
    "top_keyword_volume": "Sökvolym för top keyword (kostar 10 units)",
    "update_date": "Datum när SERP checkades"
}

# Vanliga länder (utökad lista)
COMMON_COUNTRIES = {
    "se": "Sverige",
    "no": "Norge",
    "dk": "Danmark",
    "fi": "Finland",
    "us": "USA",
    "gb": "Storbritannien",
    "de": "Tyskland",
    "fr": "Frankrike",
    "es": "Spanien",
    "it": "Italien",
    "nl": "Nederländerna",
    "ca": "Kanada",
    "au": "Australien"
}

# Alla länder från API spec
ALL_COUNTRIES = [
    "ad", "ae", "af", "ag", "ai", "al", "am", "ao", "ar", "as", "at", "au", "aw", "az",
    "ba", "bb", "bd", "be", "bf", "bg", "bh", "bi", "bj", "bn", "bo", "br", "bs", "bt", "bw", "by", "bz",
    "ca", "cd", "cf", "cg", "ch", "ci", "ck", "cl", "cm", "cn", "co", "cr", "cu", "cv", "cy", "cz",
    "de", "dj", "dk", "dm", "do", "dz",
    "ec", "ee", "eg", "es", "et",
    "fi", "fj", "fm", "fo", "fr",
    "ga", "gb", "gd", "ge", "gf", "gg", "gh", "gi", "gl", "gm", "gn", "gp", "gq", "gr", "gt", "gu", "gy",
    "hk", "hn", "hr", "ht", "hu",
    "id", "ie", "il", "im", "in", "iq", "is", "it",
    "je", "jm", "jo", "jp",
    "ke", "kg", "kh", "ki", "kn", "kr", "kw", "ky", "kz",
    "la", "lb", "lc", "li", "lk", "ls", "lt", "lu", "lv", "ly",
    "ma", "mc", "md", "me", "mg", "mk", "ml", "mm", "mn", "mq", "mr", "ms", "mt", "mu", "mv", "mw", "mx", "my", "mz",
    "na", "nc", "ne", "ng", "ni", "nl", "no", "np", "nr", "nu", "nz",
    "om",
    "pa", "pe", "pf", "pg", "ph", "pk", "pl", "pn", "pr", "ps", "pt", "py",
    "qa",
    "re", "ro", "rs", "ru", "rw",
    "sa", "sb", "sc", "se", "sg", "sh", "si", "sk", "sl", "sm", "sn", "so", "sr", "st", "sv",
    "td", "tg", "th", "tj", "tk", "tl", "tm", "tn", "to", "tr", "tt", "tw", "tz",
    "ua", "ug", "us", "uy", "uz",
    "vc", "ve", "vg", "vi", "vn", "vu",
    "ws",
    "ye", "yt",
    "za", "zm", "zw"
]

OUTPUT_FORMATS = ["json", "csv", "xml", "php"]


def print_header(text: str):
    """Skriv ut en formaterad header"""
    print(f"\n{'='*60}")
    print(f"  {text}")
    print(f"{'='*60}\n")


def print_section(text: str):
    """Skriv ut en sektion"""
    print(f"\n{text}")
    print("-" * 60)


def select_columns() -> List[str]:
    """Låt användaren välja kolumner"""
    print_section("STEG 1: Välj kolumner")

    print("\nTillgängliga kolumner:")
    columns_list = list(AVAILABLE_COLUMNS.items())
    for idx, (col, desc) in enumerate(columns_list, 1):
        print(f"  {idx:2d}. {col:20s} - {desc}")

    print("\nOBS! Vissa kolumner kostar extra units (se beskrivning)")
    print("\nAnge ditt val:")
    print("  - Skriv nummer separerade med komma (t.ex: 1,2,3,5)")
    print("  - Eller skriv 'all' för alla kolumner")
    print("  - Eller skriv 'basic' för grundläggande set (position, url, title, domain_rating, traffic)")

    while True:
        choice = input("\nDitt val: ").strip().lower()

        if choice == 'all':
            return list(AVAILABLE_COLUMNS.keys())

        if choice == 'basic':
            return ['position', 'url', 'title', 'domain_rating', 'traffic']

        try:
            indices = [int(x.strip()) for x in choice.split(',')]
            selected = [columns_list[i-1][0] for i in indices if 1 <= i <= len(columns_list)]

            if selected:
                print(f"\nValda kolumner: {', '.join(selected)}")
                return selected
            else:
                print("❌ Ogiltiga nummer. Försök igen.")
        except (ValueError, IndexError):
            print("❌ Ogiltigt format. Använd nummer separerade med komma (t.ex: 1,2,3)")


def select_country() -> str:
    """Låt användaren välja land"""
    print_section("STEG 2: Välj land")

    print("\nVanliga länder:")
    common_list = list(COMMON_COUNTRIES.items())
    for idx, (code, name) in enumerate(common_list, 1):
        print(f"  {idx:2d}. {code.upper()} - {name}")

    print("\nAnge ditt val:")
    print("  - Skriv nummer för vanligt land")
    print("  - Eller skriv landskod direkt (t.ex: 'se', 'us', 'de')")

    while True:
        choice = input("\nDitt val: ").strip().lower()

        # Försök som nummer först
        try:
            idx = int(choice)
            if 1 <= idx <= len(common_list):
                country_code = common_list[idx-1][0]
                country_name = common_list[idx-1][1]
                print(f"✓ Valt land: {country_name} ({country_code.upper()})")
                return country_code
        except ValueError:
            pass

        # Annars tolka som landskod
        if choice in ALL_COUNTRIES:
            country_name = COMMON_COUNTRIES.get(choice, choice.upper())
            print(f"✓ Valt land: {country_name} ({choice.upper()})")
            return choice

        print(f"❌ Ogiltig landskod. Måste vara en av: {', '.join(ALL_COUNTRIES[:20])}...")


def get_keyword() -> str:
    """Få nyckelord från användaren"""
    print_section("STEG 3: Ange nyckelord")

    while True:
        keyword = input("\nSkriv in nyckelordet att analysera: ").strip()
        if keyword:
            print(f"✓ Nyckelord: {keyword}")
            return keyword
        print("❌ Nyckelord får inte vara tomt.")


def get_optional_params() -> dict:
    """Få valfria parametrar"""
    print_section("STEG 4: Valfria parametrar (tryck Enter för att hoppa över)")

    params = {}

    # Top positions
    top_pos = input("\nAntal top positioner att returnera (default: alla): ").strip()
    if top_pos:
        try:
            params['top_positions'] = int(top_pos)
            print(f"✓ Top positions: {params['top_positions']}")
        except ValueError:
            print("❌ Ogiltigt nummer, använder default")

    # Date
    print("\nDatum för SERP data (format: YYYY-MM-DD eller YYYY-MM-DDThh:mm:ss)")
    date = input("Datum (default: senaste): ").strip()
    if date:
        try:
            # Validera datumet
            if 'T' in date:
                datetime.fromisoformat(date)
            else:
                datetime.strptime(date, '%Y-%m-%d')
                date = f"{date}T00:00:00"
            params['date'] = date
            print(f"✓ Datum: {params['date']}")
        except ValueError:
            print("❌ Ogiltigt datumformat, använder default")

    # Output format
    print(f"\nOutput-format: {', '.join(OUTPUT_FORMATS)}")
    output = input("Format (default: json): ").strip().lower()
    if output and output in OUTPUT_FORMATS:
        params['output'] = output
        print(f"✓ Format: {params['output']}")

    return params


def generate_request(columns: List[str], country: str, keyword: str,
                    optional_params: dict, api_token: Optional[str] = None) -> dict:
    """Generera API-förfrågan"""

    # Bygg query parameters
    query_params = {
        'select': ','.join(columns),
        'country': country,
        'keyword': keyword,
        **optional_params
    }

    # Bygg URL
    base_url = "https://api.ahrefs.com/v3/serp-overview/serp-overview"
    query_string = '&'.join([f"{k}={v}" for k, v in query_params.items()])
    full_url = f"{base_url}?{query_string}"

    # Bygg curl-kommando
    curl_command = f'curl -X GET "{full_url}"'
    if api_token:
        curl_command += f' -H "Authorization: Bearer {api_token}"'
    else:
        curl_command += ' -H "Authorization: Bearer YOUR_API_TOKEN"'

    # Python requests exempel
    python_code = f'''import requests

url = "{base_url}"
params = {json.dumps(query_params, indent=4)}
headers = {{
    "Authorization": "Bearer {'YOUR_API_TOKEN' if not api_token else api_token}"
}}

response = requests.get(url, params=params, headers=headers)
data = response.json()
print(data)
'''

    return {
        'url': full_url,
        'method': 'GET',
        'query_params': query_params,
        'curl_command': curl_command,
        'python_code': python_code
    }


def save_to_file(request_data: dict, filename: str):
    """Spara request till fil"""
    output = {
        'generated_at': datetime.now().isoformat(),
        'endpoint': 'SERP Overview',
        'request': request_data
    }

    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(output, f, indent=2, ensure_ascii=False)

    print(f"✓ Sparat till: {filename}")


def main():
    """Huvudfunktion"""
    print_header("🔍 Ahrefs API Request Generator - SERP Overview")

    print("Detta verktyg hjälper dig att skapa standardiserade Ahrefs API-förfrågningar")
    print("utan att behöva komma ihåg alla parametrar!\n")

    # Samla in data
    columns = select_columns()
    country = select_country()
    keyword = get_keyword()
    optional_params = get_optional_params()

    # Fråga om API token (valfritt)
    print_section("STEG 5: API Token (valfritt)")
    print("\nVill du inkludera din API token i output?")
    print("OBS! Spara INTE filen om du inkluderar token!")
    include_token = input("Inkludera token? (y/N): ").strip().lower() == 'y'

    api_token = None
    if include_token:
        api_token = input("Ange API token: ").strip()

    # Generera request
    print_section("Genererar API-förfrågan...")
    request_data = generate_request(columns, country, keyword, optional_params, api_token)

    # Visa resultat
    print_header("✨ Genererad API-förfrågan")

    print("\n📋 QUERY PARAMETERS:")
    print(json.dumps(request_data['query_params'], indent=2))

    print("\n\n🌐 FULL URL:")
    print(request_data['url'])

    print("\n\n💻 CURL KOMMANDO:")
    print(request_data['curl_command'])

    print("\n\n🐍 PYTHON KOD:")
    print(request_data['python_code'])

    # Fråga om att spara
    print_section("Vill du spara denna förfrågan?")
    save = input("Spara till fil? (y/N): ").strip().lower() == 'y'

    if save:
        filename = input("Filnamn (default: ahrefs_request.json): ").strip()
        if not filename:
            filename = "ahrefs_request.json"
        if not filename.endswith('.json'):
            filename += '.json'

        save_to_file(request_data, filename)

    print_header("✅ Klart!")
    print("\nTips: Du kan nu kopiera curl-kommandot eller Python-koden")
    print("      och använda den direkt i ditt projekt!\n")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n❌ Avbrutet av användaren")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ Ett fel uppstod: {e}")
        sys.exit(1)
