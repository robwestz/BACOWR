# 🚀 BACOWR Demo - Snabbstart

## Klart på 2 minuter!

### 1. Förbered (första gången)

```bash
python setup_demo.py
```

Detta installerar allt och skapar konfigurationsfiler.

**OBS!** Efter setup, öppna `api/.env` och lägg till din Anthropic API-nyckel:
```env
ANTHROPIC_API_KEY=sk-ant-api03-din-nyckel-här
```

### 2. Kör demo

```bash
python start_demo.py
```

Öppnar automatiskt:
- **API**: http://localhost:8000
- **Swagger docs**: http://localhost:8000/docs
- **Frontend**: http://localhost:3000

### 3. Testa!

1. Öppna **http://localhost:3000**
2. Klicka på "Quick Start"
3. Fyll i:
   - Publisher: `aftonbladet.se`
   - Target: `https://sv.wikipedia.org/wiki/Artificiell_intelligens`
   - Anchor: `läs mer om AI`
4. Klicka "Generate"
5. Vänta ~30 sekunder
6. Se din genererade artikel! 🎉

### Stoppa

Tryck `Ctrl+C` i terminalen.

---

## I PyCharm

### Första gången:

1. Högerklicka på `setup_demo.py`
2. Välj "Run 'setup_demo'"
3. Vänta tills klart

### Varje gång du vill testa:

1. Högerklicka på `start_demo.py`
2. Välj "Run 'start_demo'"
3. Öppna http://localhost:3000 i browser

---

## Felsökning

**"No module named 'fastapi'"**
→ Kör `setup_demo.py` igen

**"npm: command not found"**
→ Installera Node.js: https://nodejs.org/

**"Port 8000 already in use"**
→ Stoppa andra processer på port 8000

**"Database locked"**
→ Radera `api/bacowr.db` och kör igen

---

## Vad händer?

- **setup_demo.py**: Installerar dependencies, skapar .env-filer med dina API-nycklar
- **start_demo.py**: Startar både backend (FastAPI) och frontend (Next.js) samtidigt

---

**Allt är förberett! Bara kör och testa! 🚀**
