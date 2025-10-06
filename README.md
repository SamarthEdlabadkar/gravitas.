# 🧠 Gravitas

**Gravitas** is a full-stack web application for **interactive knowledge exploration** — combining **AI-powered data processing** with a **dynamic, D3.js-driven knowledge graph interface**.
It enables users to visualize relationships between research publications, datasets, and concepts, transforming static text into insightful visual connections.

---

## 🚀 Features

### 🔍 Intelligent Backend

* **Data Extraction & Categorization:** Uses `PubMed` and `Open Science Data` APIs for sourcing and organizing research data.
* **Vectorization & Semantic Search:** Employs custom vectorizers (`vectorizer_pubmed.py`, `vectorizer_osd.py`) for embedding and similarity computation.
* **Automated Summarization:** Generates concise summaries of search results and documents.
* **API-driven Architecture:** Flask backend (`app.py`) handles requests and integrates all processing pipelines.

### 🌐 Interactive Frontend

* **Dynamic Graph Visualization:** Built using **D3.js** and **TypeScript + React**, enabling real-time, animated network exploration.
* **Modern UI Library:** 50+ reusable components (accordion, chart, dialog, slider, etc.) for consistent design and responsiveness.
* **Multi-Page App:** Includes pages for network visualization, knowledge graph, and error handling.
* **Fast Development with Vite:** Optimized build and live-reload experience for front-end developers.

---

## 🧩 Tech Stack

| Layer               | Technology                               |
| ------------------- | ---------------------------------------- |
| **Frontend**        | React, TypeScript, Vite, D3.js           |
| **Backend**         | Python, Groq (Gen AI), Flask             |
| **APIs**            | PubMed API, Open Science Data API        |
| **Styling/UI**      | Tailwind / ShadCN (from `ui` components) |
| **Data Processing** | Ollama (Gen AI), transformers            |
| **Build & Tooling** | Node.js, ESLint, TSConfig                |

---

## 📂 Project Structure

```
gravitas/
├── client/              # Frontend (React + TypeScript + Vite)
│   ├── src/
│   │   ├── components/  # Reusable UI + graph components
│   │   ├── pages/       # Page-level React components
│   │   ├── hooks/       # Custom React hooks
│   │   └── lib/         # Utilities
│   ├── public/          # Static assets
│   ├── package.json
│   └── vite.config.ts
│
└── server/              # Backend (Flask)
    ├── app.py           # Main entry point
    ├── scripts/         # APIs, vectorizers, categorization scripts
    ├── requirements.txt
    ├── searchTest.json  # Sample search results
    └── summaryTest.json # Sample summaries
```

---

## ⚙️ Setup & Installation

### 1️⃣ Clone the Repository

```bash
git clone https://github.com/kee5625/gravitas.git
cd gravitas
```

### 2️⃣ Backend Setup

```bash
cd server
python -m venv venv
source venv/bin/activate  # (Windows: venv\Scripts\activate)
pip install -r requirements.txt
python app.py
```

The backend will start on `http://127.0.0.1:5000`.

### 3️⃣ Frontend Setup

```bash
cd ../client
npm install
npm run dev
```

The frontend will start on `http://localhost:5173`.

---

## 🧠 Usage

1. Run both backend and frontend servers.
2. Open the app in your browser.
3. Enter a query (e.g., “Space Biology” or “Cancer Genomics”).
4. Explore the interactive **Knowledge Graph** and **Network** visualizations generated from live research data.
5. Hover over nodes for relationships, summaries, and metadata.

---

## 🧑‍💻 Contributing

Contributions are welcome!

1. Fork this repository
2. Create a feature branch
3. Submit a pull request

Please ensure:

* Code follows ESLint / TypeScript standards.
* Python scripts are PEP8 compliant.

---

## 🗺️ Roadmap

* [ ] Add caching for repeated queries
* [ ] Deploy to a cloud environment (AWS / Render)
* [ ] Integrate user accounts and history
* [ ] Add support for additional data APIs

---

## 📜 License

This project is licensed under the **MIT License**.
Feel free to use, modify, and distribute with attribution.

---

## 🙏 Acknowledgements

* [PubMed API](https://www.ncbi.nlm.nih.gov/home/develop/api/)
* [Open Science Data API](https://osd.allofus.nih.gov/)
* [D3.js](https://d3js.org/)
* [Vite](https://vitejs.dev/)
* [ShadCN/UI](https://ui.shadcn.com/)

