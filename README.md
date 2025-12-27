# 🧠 QueryMind  
**Natural Language → SQL Desktop Application (Offline, Local LLMs)**

QueryMind is a Windows desktop application that allows users to **query SQL databases using natural language**.  
It uses **local LLMs via Ollama** to convert user prompts into SQL queries, executes them on the connected database, and displays results in a **chat-style interface**.

> 🔐 Fully offline • No cloud APIs • Secure & private

---

## 🚀 Features

- 🧠 Natural Language → SQL conversion using local LLMs
- 💬 Chat-based UI (WhatsApp-style conversation)
- ⚙️ Settings tab for:
  - Database configuration (host, port, username, password, DB name)
  - Local model selection (Gemma, LLaMA, etc.)
- 🔌 Supports SQL databases (PostgreSQL / MySQL)
- 🖥️ Packaged as a standalone Windows executable
- 🔐 Runs completely offline

---

## 🖼️ Application Preview

_Add screenshots here_

- Chat Tab – Query & results view  
- Settings Tab – Database & model configuration

---

## 📦 Download

➡️ **Windows Executable (.exe)**  
Available in **GitHub Releases**:

👉 https://github.com/ritesh2004/QueryMind/releases/tag/version1.0.0

- Version: **v1.0.0**
- Size: ~60 MB
- No Python installation required

---

## 🛠 System Requirements

- **OS:** Windows 10 / 11 (64-bit)
- **Ollama:** Installed & added to PATH  
  👉 https://ollama.com
- **Databases Supported:** PostgreSQL, MySQL

---

## ⚙️ How It Works

1. User enters a natural language query  
   _Example: “Show the last 10 orders”_
2. Selected local LLM converts the query into SQL
3. SQL is executed on the connected database
4. Results are shown in a chat-style interface

---

## 🧠 Model Selection Suggestions (IMPORTANT)

Choosing the **right LLM model** is critical for accurate SQL generation.

### ✅ Recommended Models

These models are **tested and known to work well** for Natural Language → SQL tasks:

- **gemma3:1b / gemma3:2b**
- **llama3 / llama3.1**
- **mistral**
- **qwen2.5**

These models:
- Understand structured query patterns
- Generate valid and executable SQL
- Perform well even with schema-based prompts

### ❌ Models NOT Recommended

- **functiongemma**

⚠️ **Why not FunctionGemma?**
- It is designed for **function calling**, not text-to-SQL
- It does **not reliably generate SQL queries**
- Output is often incomplete or non-executable

> ❗ If you select `functiongemma`, SQL generation may fail or produce invalid queries.

### 🎯 Recommendation

For best results:
- Start with **`gemma3:1b`** (fast & lightweight)
- Use **LLaMA 3** or **Mistral** for better accuracy on complex queries

---

## 📁 Project Structure

```

querymind/
│
├── app.py          # Main application entry point
├── agent.py        # LLM agent & prompt handling
├── dbManager.py    # Database connection & execution
├── logo.ico        # icon
├── settings.json   # User config (auto-generated in AppData)
└── README.md

````

---

## 🔐 Security & Privacy

- No data is sent to external servers
- All LLM inference happens locally
- Database credentials are stored locally in user AppData
- No telemetry or tracking

---

## ⚠️ Known Limitations

- First launch may take a few seconds (model initialization)
- Limited to SQL databases in this version
- Windows SmartScreen warning may appear (app not code-signed)

---

## 🔮 Roadmap

- 📜 Query history & export
- 📊 Result visualization
- 🌐 More database engines
- 🎨 UI/UX improvements

---

## 🧪 Development Setup (Optional)

To run from source:

```bash
pip install -r requirements.txt
python app.py
````

Ensure Ollama is installed and running.

---

# 📦 Release Notes

## 🏷 QueryMind v1.0.0 — Initial Stable Release

### ✨ Highlights

* First public stable release
* Fully offline Natural Language → SQL execution
* Local LLM support via Ollama
* Chat-based UI with settings panel
* Standalone Windows executable

### 📦 Assets

* `QueryMind-v1.0.0.exe` (~60 MB)

### ⚠️ Notes

* Windows may show SmartScreen warning (unsigned app)
* Ollama must be installed separately

### 🔮 Upcoming

* Improved SQL accuracy using schema context
* Query history
* Multi-database support

---

## 📜 License

MIT License

---

## 🙌 Author

**Ritesh Pramanik**
Electronics & Software Engineer

🔗 Portfolio: <your-portfolio-link>
🔗 LinkedIn: <your-linkedin-link>

---

## ⭐ Feedback & Contributions

Feedback, bug reports, and feature suggestions are welcome.
Feel free to open an issue or submit a pull request.