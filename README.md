<h1 align="center">📺 TV File Search Bot</h1>

<p align="center">
  A Telegram bot for indexing and searching TV show & movie files.
  Built with Python + PostgreSQL, hosted on Railway.
</p>

---

## 👤 Developer

[![Contact Developer](https://img.shields.io/static/v1?label=Contact+Developer&message=On+Telegram&color=critical)](https://t.me/thediiii)

---

## 🌟 Features

- ✅ File indexing with title, season & episode tracking
- ✅ Fast file search with fuzzy matching
- ✅ PostgreSQL database (Railway hosted)
- ✅ User tracking & last active logging
- ✅ Admin broadcast to all users
- ✅ Deep-link search flow
- ✅ File stats & user stats
- ✅ Add / delete files from DB
- ✅ Pending search queue system

---

## 🗄️ Database Structure

| Table | Purpose |
|-------|---------|
| `files` | Stores indexed files with title, season, episode, file_id |
| `users` | Tracks all bot users and activity |
| `pending_search` | Handles deep-link search queue |

---

## ⚙️ Setup

### 1. Clone the repo
```bash
git clone https://github.com/digin-portfolio/YOUR_REPO_NAME
cd YOUR_REPO_NAME
```

### 2. Install dependencies
```bash
pip install psycopg2-binary python-telegram-bot
```

### 3. Set environment variables
```bash
DATABASE_URL=your_postgresql_url
BOT_TOKEN=your_telegram_bot_token
```

### 4. Initialize the database
```python
from database import init_db
init_db()
```

### 5. Deploy on Railway
- Add a **PostgreSQL** plugin on Railway
- Railway sets `DATABASE_URL` automatically
- Deploy and you're live ✅

---

## 📬 Contact

[![Telegram](https://img.shields.io/badge/Telegram-@thediiii-blue?style=flat&logo=telegram)](https://t.me/thediiii)

---

## ⚠️ Disclaimer

For educational purposes only.  
Use responsibly and respect platform rules.

---

## 📜 License

MIT License
