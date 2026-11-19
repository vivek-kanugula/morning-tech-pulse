# ⚡ Morning Tech Pulse: Autonomous AI & System Design Intelligence Agent

> An autonomous cloud-native intelligence agent that ingests real-time AI and systems signals across **Hugging Face Daily Papers**, **GitHub Search API**, and **Hacker News**, curates executive technical briefings using **Groq LPUs**, compiles a strictly formatted **3-page executive PDF**, and dispatches it directly to your email inbox every morning at **$0 compute cost**.

---

## 🏗️ Architecture & Daily Pipeline

```mermaid
flowchart LR
    Cron[GitHub Actions Cron / 07:30 AM IST] --> Ingest[Multi-Source Ingestion Engine:\nHugging Face + GitHub AI + Hacker News]
    Ingest --> Groq[Groq LPU Synthesis:\nZero-Slop Architectural Rubric]
    Groq --> Engine[ReportLab Engine:\nStrict 3-Page Executive PDF]
    Engine --> Dispatch[Gmail SMTP SSL Dispatcher:\nMinimalist Notification + PDF Attachment]
    Dispatch --> Inbox[📥 Vivek's Inbox:\nDelivered at 07:30 AM IST Daily]
```

---

## 📄 3-Page Executive PDF Structure

The generated PDF is strictly budgeted to **3 pages** with clean editorial typography and zero marketing fluff:

| Page | Section | Focus & Engineering Content |
| :--- | :--- | :--- |
| **Page 1** | **Latest Authentic AI Developments** | Curated model releases, new weight drops, and research breakthroughs from Hugging Face & AI research labs. Explains *what happened* and the *exact production use case* for engineers. |
| **Page 2** | **System Design Deep Dive (Learning)** | A rotating fundamental architectural pattern (e.g. *Deterministic Sharded LSM-Trees*, *Consistent Hashing*, *Raft Consensus*, *Distributed Rate Limiting*, *Cache-Aside with CDC*). Explains the *core bottleneck*, *3 mechanical invariants*, *architectural trade-offs*, and *real-world industry production case studies* (Netflix, Stripe, Discord, Uber). |
| **Page 3** | **Standout AI Open-Source Repositories** | High-utility trending AI repositories. Highlights *what it does* and its *engineering purpose & practical value* (strictly without terminal commands or code clutter). |

---

## 📂 Repository Artifacts

1. **`daily_tech_pulse_n8n.json`**: Complete, importable 9-node visual **n8n workflow**. Drag and drop into any n8n instance (Desktop or Cloud) to view and edit the visual graph.
2. **`main.py`**: Headless Python automation engine that executes the multi-source crawler, Groq LLM synthesis, ReportLab 3-page PDF compiler, and Gmail SMTP dispatcher in 15 seconds flat.
3. **`.github/workflows/daily_briefing.yml`**: GitHub Actions scheduler running daily at `07:30 AM IST` (`02:00 UTC`) and supporting 1-click manual trigger (`workflow_dispatch`).

---

## 💰 Zero-Cost ($0) Stack

* **Inference**: Groq Cloud API (`openai/gpt-oss-120b` / `llama-3.3-70b`) — Free tier.
* **Signals**: Hugging Face Daily Papers API & GitHub Public REST API — Free.
* **Delivery**: Gmail SMTP (SSL Port 465) — Free.
* **Execution**: GitHub Actions CI/CD (2,000 free minutes/month) — Free.
* **PDF Engine**: Python ReportLab — Free & Open Source.

---

## 🧪 Testing Your Workflow

1. In your GitHub repository, click on the **Actions** tab.
2. Select **"Daily Morning Tech Pulse Cloud Dispatcher"** from the left sidebar.
3. Click the **"Run workflow"** button.
4. Watch the runner complete in ~20 seconds; check your inbox for `Morning_Tech_Pulse.pdf`!

---

## 📄 Resume Bullet Points

Add this directly to your CV under **Projects**:

* *"Architected an autonomous AI Intelligence & Systems Learning pipeline leveraging **Groq LPU Inference**, **Hugging Face Research APIs**, and **GitHub Actions** running on a 24/7 cron schedule at **$0 compute cost**."*
* *"Engineered a multi-source data ingestion engine synthesizing signals across **Hugging Face Daily Papers**, **GitHub Trending AI**, and **Hacker News**, enforcing rigid JSON schema constraints to eliminate marketing buzzwords and extract production use cases."*
* *"Developed an automated document generation engine with **ReportLab** producing strict 3-page executive PDFs covering **AI model releases**, **distributed system design case studies (Netflix, Stripe, Discord)**, and **open-source tooling audits**, distributed via **Gmail SMTP**."*
