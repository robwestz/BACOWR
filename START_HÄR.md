# 🚀 BACOWR Demo - START HÄR

**3 steg till en fungerande demo för cheferna:**

---

## Steg 1: Kör Setup-Scriptet

**Kopiera denna fil till din dator:**
- `SETUP_LOCAL_DEMO.py`

**Kör det:**

### I PyCharm:
1. Skapa nytt Python-projekt (kan vara tomt)
2. Dra `SETUP_LOCAL_DEMO.py` in i projektet
3. Högerklicka → "Run 'SETUP_LOCAL_DEMO'"

### I Terminal:
```bash
python SETUP_LOCAL_DEMO.py
```

**Vad gör det?**
- ✅ Klonar BACOWR till en LOKAL kopia (typ "BACOWR-demo" i din hemkatalog)
- ✅ Installerar alla Python-dependencies
- ✅ Skapar mock .env (funkar utan riktiga API keys)
- ✅ Testar att allt fungerar
- ✅ Skapar filen `RUN_DEMO_FOR_BOSSES.py` åt dig

**Tar ~5 minuter**

---

## Steg 2: Öppna i PyCharm

Setup-scriptet säger var projektet installerades, typ:
```
/Users/dittnamn/BACOWR-demo
```

**I PyCharm:**
1. File → Open
2. Välj den mappen
3. PyCharm hittar automatiskt virtual environment
4. Du ser alla filer i projektet

---

## Steg 3: Kör Demon för Cheferna

**När cheferna är där:**

1. Hitta filen `RUN_DEMO_FOR_BOSSES.py` i PyCharm
2. Högerklicka → "Run 'RUN_DEMO_FOR_BOSSES'"
3. Välj demo-typ i terminalen:
   - **1** = Snabb overview (5 min)
   - **2** = Interaktiv demo (15 min)
   - **3** = Kör tester (2 min)

**Det är allt!** 🎉

---

## 🎯 Vilken Demo Ska Jag Välja?

### Option 1: Snabb Overview (Rekommenderas för chefer!)
```
✅ Visar pipeline-arkitektur
✅ 8 QC-kriterier förklarade
✅ 3 bridge-typer (strong/pivot/wrapper)
✅ Cost & performance metrics
✅ Production readiness status
```
**Perfekt för:** 5-10 min presentation, snabb översikt

### Option 2: Interaktiv Demo
```
✅ Simulera job creation
✅ Utforska system status
✅ Se QC-kriterierna i detalj
✅ Kalkylera costs interaktivt
✅ Se API dokumentation
```
**Perfekt för:** Djupdykning, teknisk demo

### Option 3: Tester
```
✅ Kör alla 7 tester
✅ Visar att allt fungerar
✅ Teknisk trovärdighet
```
**Perfekt för:** Tekniska chefer, bevis att det funkar

---

## 🔑 Vill Du Använda Riktiga API Keys?

**Efter setup, redigera filen:**
```
BACOWR-demo/.env
```

**Ersätt "demo_key" med riktiga keys från:**
- Anthropic: https://console.anthropic.com/settings/keys
- OpenAI: https://platform.openai.com/api-keys
- SerpAPI: https://serpapi.com/manage-api-key

**Men för demon funkar det utan!** Mock data används automatiskt.

---

## ❓ Problem?

### "Python not found"
- Installera Python 3.8+: https://www.python.org/downloads/

### "Git not found"
- Installera Git: https://git-scm.com/downloads

### "Module not found"
- Kör setup-scriptet igen
- Eller: `pip install -r requirements.txt`

### "Script doesn't run"
- Kontrollera att du är i rätt mapp
- I PyCharm: Working directory ska vara projekt-roten

---

## 🎬 LYCKA TILL!

Du har nu:
- ✅ En lokal kopia (ingen risk att röra originalet)
- ✅ Allt installerat och fungerande
- ✅ EN fil att köra för cheferna: `RUN_DEMO_FOR_BOSSES.py`

**Det är så enkelt som det kan bli!** 🚀
