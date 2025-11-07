# Ahrefs API Request Generator

Ett interaktivt verktyg för att skapa standardiserade Ahrefs API-förfrågningar utan att behöva komma ihåg alla parametrar och kolumnnamn.

## 🎯 Syfte

Istället för att behöva Ahrefs API-dokumentationen utantill, låter detta verktyg dig:
- Välja kolumner från en numrerad lista med beskrivningar
- Välja land från vanliga alternativ eller ange landskod
- Ange nyckelord och parametrar steg för steg
- Få färdiga curl-kommandon och Python-kod

## 🚀 Användning

### Kör scriptet:

```bash
python tools/ahrefs_request_generator.py
```

eller:

```bash
./tools/ahrefs_request_generator.py
```

### Interaktivt flöde:

**STEG 1: Välj kolumner**
- Se alla tillgängliga kolumner med beskrivningar
- Välj genom att ange nummer (t.ex: `1,2,3,5`)
- Eller använd snabbval:
  - `all` - alla kolumner
  - `basic` - grundläggande set (position, url, title, domain_rating, traffic)

**STEG 2: Välj land**
- Välj från vanliga länder (1-13)
- Eller ange landskod direkt (t.ex: `se`, `no`, `us`)

**STEG 3: Ange nyckelord**
- Skriv in det nyckelord du vill analysera

**STEG 4: Valfria parametrar**
- Antal top positioner att returnera
- Datum för SERP data
- Output-format (json, csv, xml, php)

**STEG 5: API Token**
- Valfritt: Inkludera din API token i output
- ⚠️ Spara INTE filen om du inkluderar token!

### Output

Scriptet genererar:
1. **Query parameters** - JSON-formaterat
2. **Full URL** - Redo att använda
3. **Curl-kommando** - Kopiera och kör direkt
4. **Python-kod** - Inkludera i ditt projekt

Du kan också spara allt till en JSON-fil för senare användning.

## 📊 Exempel på kolumner

### Gratis kolumner:
- `position` - Position i SERP
- `url` - URL för rankande sida
- `title` - Titel på rankande sida
- `type` - Typ av position
- `domain_rating` - Domain Rating (0-100)
- `url_rating` - URL Rating (0-100)
- `ahrefs_rank` - Ahrefs Rank
- `backlinks` - Totalt antal backlinks
- `keywords` - Antal keywords sidan rankar för

### Kolumner som kostar units:
- `refdomains` - Antal unika domäner (5 units)
- `traffic` - Estimerad trafik (10 units)
- `value` - Värde av trafik (10 units)
- `top_keyword` - Top keyword
- `top_keyword_volume` - Sökvolym (10 units)

## 💡 Tips

### Snabbt grundläggande query:
```
Steg 1: basic
Steg 2: se
Steg 3: digital marketing
Steg 4: [tryck enter för alla]
Steg 5: N
```

### Full analys:
```
Steg 1: all
Steg 2: us
Steg 3: seo tools
Steg 4: 10 [top positions]
Steg 5: y [inkludera token för direkt körning]
```

## 🔐 Säkerhet

- Scriptet varnar om att INTE spara filer med API token
- API tokens ska lagras som miljövariabler eller i `.env`-fil
- Använd tokens endast i säkra miljöer

## 🛠️ Integration med projektet

Genererad Python-kod kan användas direkt i:
- `backend/batch_processor.py`
- Custom scripts i `tools/`
- Notebook-exempel

Exempel:
```python
# Genererat av ahrefs_request_generator.py
import requests

url = "https://api.ahrefs.com/v3/serp-overview/serp-overview"
params = {
    "select": "position,url,title,domain_rating,traffic",
    "country": "se",
    "keyword": "digital marketing"
}
headers = {
    "Authorization": f"Bearer {os.getenv('AHREFS_API_TOKEN')}"
}

response = requests.get(url, params=params, headers=headers)
data = response.json()
```

## 📝 Sparade förfrågningar

När du sparar en förfrågan skapas en JSON-fil med:
- Tidsstämpel
- Endpoint-information
- Query parameters
- Färdiga kommandon

Användbart för:
- Dokumentation
- Återanvändning
- Delning med teamet
- Version control av API-queries

## 🌍 Stöd för länder

Scriptet stödjer alla Ahrefs-länder (170+):
- Vanliga länder visas först (SE, NO, DK, FI, US, GB, etc.)
- Alla ISO 3166-1 alpha-2 landskoder stöds
- Ange direkt eller välj från lista

## ⚡ Framtida utökningar

Möjliga tillägg:
- Stöd för fler Ahrefs endpoints
- Batch-generering för flera keywords
- Integration med configuration management
- API response validation
- Cost calculator för units
