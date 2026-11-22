import os
import re
import json
import datetime
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.application import MIMEApplication
import requests
from groq import Groq
from reportlab.lib.pagesizes import letter
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, HRFlowable, PageBreak
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_JUSTIFY, TA_LEFT, TA_RIGHT, TA_CENTER
from reportlab.lib import colors
from dotenv import load_dotenv

# Load local environment variables from .env
load_dotenv()

# ==========================================
# 31-DAY DETERMINISTIC SYSTEM DESIGN ROTATION
# Guarantees a different, non-repeating topic every single day of the month
# ==========================================
SYSTEM_DESIGN_CURRICULUM = [
    {
        "topic": "System Design: Distributed Caching & Invalidation Strategies",
        "focus": "Cache-Aside vs Write-Through vs Write-Behind, cache stampede (thundering herd) mitigation using probabilistic early expiration (XFetch) and distributed mutex locks",
        "case_study": "Meta (Facebook) scaling Memcached clusters to handle billions of requests per second"
    },
    {
        "topic": "System Design: Database Sharding & Horizontal Partitioning",
        "focus": "Range-based vs Hash-based sharding, shard key selection, rebalancing hot partitions, and cross-shard scatter-gather queries",
        "case_study": "Discord migrating billions of messages from MongoDB to Cassandra and ScyllaDB"
    },
    {
        "topic": "System Design: Log-Structured Merge (LSM) Trees & Write-Ahead Logs",
        "focus": "Sequential append-only write-ahead logs (WAL), in-memory MemTables, immutable SSTables, and background compaction vs traditional B-Tree random disk I/O",
        "case_study": "RocksDB and Apache Cassandra achieving massive write-heavy ingestion with low write amplification"
    },
    {
        "topic": "System Design: Consistent Hashing & Distributed Ring Topologies",
        "focus": "Virtual nodes, mapping hash keyspace to a circular ring, minimizing data re-mapping during cluster node joins/leaves, and fault tolerance",
        "case_study": "Amazon DynamoDB and Discord voice servers dynamically balancing state across clusters"
    },
    {
        "topic": "System Design: Event-Driven Architecture & Message Brokers",
        "focus": "Partitioned append-only commit logs, consumer group offset management, backpressure mechanisms, and at-least-once vs exactly-once semantics",
        "case_study": "LinkedIn ingesting and routing trillions of messages daily via Apache Kafka"
    },
    {
        "topic": "System Design: Distributed Rate Limiting & Token Bucket Algorithms",
        "focus": "Token bucket vs Leaky bucket vs Sliding Window Counters, atomicity in distributed memory using Redis Lua scripts, and client quota enforcement",
        "case_study": "Stripe and Cloudflare protecting financial APIs from thundering herds and malicious DDoS traffic"
    },
    {
        "topic": "System Design: Distributed Consensus & The Raft Protocol",
        "focus": "Leader election, randomized election timers, replicated state machine logs, and split-brain resolution through majority quorums (N/2 + 1)",
        "case_study": "etcd maintaining cluster-wide state consistency and service discovery for Kubernetes"
    },
    {
        "topic": "System Design: API Gateway & Circuit Breaking Patterns",
        "focus": "Cascading failure mitigation, three-state circuit breakers (Closed, Open, Half-Open), timeout budgets, and exponential backoff with jitter",
        "case_study": "Netflix preventing catastrophic cascade failures across microservices using Hystrix and Resilience4j"
    },
    {
        "topic": "System Design: CQRS & Event Sourcing Patterns",
        "focus": "Command Query Responsibility Segregation, immutable event streams as the single source of truth, and asynchronous materialized read projections",
        "case_study": "Uber ride dispatch and fare tracking systems scaling read and write paths independently"
    },
    {
        "topic": "System Design: Distributed Locks & The Redlock Algorithm",
        "focus": "Mutual exclusion across distributed processes, lease timeouts, clock drift hazards, and fencing tokens to prevent split-brain writes",
        "case_study": "Google Chubby lock service and Redis distributed lock implementations"
    },
    {
        "topic": "System Design: Bloom Filters & Count-Min Sketches for Stream Deduplication",
        "focus": "Probabilistic data structures, k independent hash functions, space efficiency with zero false negatives, and frequency estimation at high throughput",
        "case_study": "Google Chrome checking malicious URLs and Bigtable avoiding expensive disk reads for non-existent keys"
    },
    {
        "topic": "System Design: Vector Databases & Approximate Nearest Neighbors (ANN)",
        "focus": "High-dimensional embeddings, Hierarchical Navigable Small World (HNSW) graphs, Product Quantization, and cosine similarity indexing",
        "case_study": "Spotify music recommendation embeddings and Pinecone similarity search at scale"
    },
    {
        "topic": "System Design: Geo-Distributed Databases & Multi-Region Consistency",
        "focus": "Cross-region network latency, TrueTime synchronization, Raft consensus across availability zones, and active-active replication",
        "case_study": "CockroachDB and Google Cloud Spanner delivering globally consistent ACID transactions"
    },
    {
        "topic": "System Design: Reverse Proxies & HTTP/3 QUIC Edge Termination",
        "focus": "TCP Head-of-Line blocking mitigation, UDP-based QUIC multiplexing, TLS 1.3 0-RTT resumption, and Anycast routing",
        "case_study": "Cloudflare and Fastly edge networks accelerating global content delivery"
    },
    {
        "topic": "System Design: Distributed Tracing & OpenTelemetry Context Propagation",
        "focus": "Trace IDs, parent-child span trees, W3C TraceContext headers, async context loss, and adaptive tail-based sampling",
        "case_study": "Uber Jaeger and OpenTelemetry tracking millions of microservice spans in real time"
    },
    {
        "topic": "System Design: Database Connection Pooling & Thread-Per-Core Architectures",
        "focus": "Connection exhaustion, Epoll/kqueue non-blocking event loops, shared-nothing memory models, and avoiding OS thread context switching",
        "case_study": "PostgreSQL with PgBouncer vs ScyllaDB thread-per-core architecture handling massive concurrency"
    },
    {
        "topic": "System Design: Idempotency Keys & Safe API Retries",
        "focus": "At-least-once delivery duplicates, atomic unique constraint locking, cached response return on retry, and transactional outbox pattern",
        "case_study": "Stripe payment APIs ensuring customers are never double-charged during network timeouts"
    },
    {
        "topic": "System Design: Distributed Object Storage & Erasure Coding",
        "focus": "Reed-Solomon (M+N) parity encoding, bit-rot detection, overcoming multi-drive failures without full 3x replication overhead",
        "case_study": "AWS S3 and MinIO achieving 11 nines of durability with low storage multiplication"
    },
    {
        "topic": "System Design: WebSockets vs Server-Sent Events (SSE) vs Long-Polling",
        "focus": "Full-duplex TCP vs unidirectional HTTP streaming, keep-alive heartbeat pings, memory consumption per idle connection, and load balancer sticky sessions",
        "case_study": "Slack real-time messaging gateway and Figma multiplayer canvas synchronization"
    },
    {
        "topic": "System Design: Two-Phase Commit (2PC) vs The Saga Pattern",
        "focus": "Synchronous distributed transaction locks and coordinator single point of failure vs asynchronous choreograph/orchestrated compensating transactions",
        "case_study": "Uber and Amazon managing distributed order and fulfillment lifecycles across microservices"
    },
    {
        "topic": "System Design: B+ Tree Storage Engines vs Hash Indexes",
        "focus": "Disk block alignment, page splitting, range scan efficiency vs point lookup O(1) performance in relational storage engines",
        "case_study": "MySQL InnoDB B+ Tree indexing supporting high-concurrency transactional queries"
    },
    {
        "topic": "System Design: Content Delivery Networks (CDN) & Dynamic Origin Shielding",
        "focus": "Origin shielding, stale-while-revalidate caching headers, purge invalidation waves, and edge token verification",
        "case_study": "Netflix Open Connect appliance architecture delivering video streams close to end-users"
    },
    {
        "topic": "System Design: Search Engines & Inverted Index Architecture",
        "focus": "Text tokenization, posting lists, term frequency-inverse document frequency (TF-IDF), BM25 scoring, and distributed shards",
        "case_study": "Elasticsearch and Apache Lucene handling real-time search queries across terabytes of documents"
    },
    {
        "topic": "System Design: Service Mesh & Envoy Sidecar Data Planes",
        "focus": "Mutual TLS (mTLS) zero-trust identity, sidecar proxy routing, dynamic traffic splitting, and circuit breaking at the infrastructure layer",
        "case_study": "Lyft and Google Cloud service mesh architectures decoupling network policies from application code"
    },
    {
        "topic": "System Design: Zero-Downtime Database Schema Migrations",
        "focus": "Expand and Contract pattern, backward-compatible dual writing, shadow column backfills, and zero-lock DDL alterations",
        "case_study": "GitHub and Stripe executing live database schema migrations under continuous payment traffic"
    },
    {
        "topic": "System Design: Microservices vs Modular Monolith & Domain Boundaries",
        "focus": "Domain-Driven Design (DDD), bounded contexts, network hop overhead, distributed tracing complexity, and single-deployment velocity",
        "case_study": "Amazon Prime Video moving from serverless microservices to monolithic container clusters to cut compute costs by 90%"
    },
    {
        "topic": "System Design: Distributed Task Scheduling & Priority Delay Queues",
        "focus": "Dead-letter exchanges, exponential retry queues, worker heartbeating, distributed cron timers, and partition leases",
        "case_study": "Temporal and Celery orchestration engines executing mission-critical long-running workflows"
    },
    {
        "topic": "System Design: Load Balancing Algorithms: Least-Connections vs Peak EWMA",
        "focus": "Round-robin limitations, weighted least connections, Peak Exponentially Weighted Moving Average (EWMA), and Power of Two Random Choices",
        "case_study": "HAProxy and Twitter Finagle routing traffic with minimal latency variance"
    },
    {
        "topic": "System Design: Disaster Recovery & Chaos Engineering (RPO and RTO)",
        "focus": "Recovery Point Objective (RPO) vs Recovery Time Objective (RTO), warm standby vs active-active failover, and automated fault injection",
        "case_study": "Netflix Chaos Monkey deliberately terminating production instances to enforce resilient self-healing architectures"
    },
    {
        "topic": "System Design: Gossip Protocols & Decentralized Node Failure Detection",
        "focus": "Epidemic dissemination algorithms, Phi Accrual failure detection, heartbeat gossip rounds, and eventual cluster convergence",
        "case_study": "Apache Cassandra and HashiCorp Consul maintaining cluster state across thousands of nodes without a centralized master"
    },
    {
        "topic": "System Design: Read-Your-Own-Writes Consistency & Master-Replica Lag",
        "focus": "Asynchronous replication lag, sticky user sessions, reading from master on mutation, and causal consistency tracking via vector clocks",
        "case_study": "Meta (Instagram) ensuring immediate feed post visibility for authoring users despite global replica lag"
    }
]


def sanitize_text(text: str) -> str:
    """Normalize Unicode characters to ASCII safe equivalents to prevent ReportLab missing glyphs (black boxes)."""
    if not text:
        return ""
    replacements = {
        '\u2011': '-',   # non-breaking hyphen
        '\u2010': '-',   # hyphen
        '\u2012': '-',   # figure dash
        '\u2013': '-',   # en dash
        '\u2014': '--',  # em dash
        '\u2015': '--',  # horizontal bar
        '\u2018': "'",   # left single quote
        '\u2019': "'",   # right single quote
        '\u201a': "'",   # single low-9 quote
        '\u201b': "'",   # single high-reversed-9 quote
        '\u201c': '"',   # left double quote
        '\u201d': '"',   # right double quote
        '\u201e': '"',   # double low-9 quote
        '\u2026': '...', # ellipsis
        '\u00a0': ' ',   # non-breaking space
        '\u202f': ' ',   # narrow no-break space
        '\u200b': '',    # zero width space
        '\u2022': '*',   # bullet
        '\u25aa': '*',   # black small square
        '\u25fe': '*',   # black medium small square
        '\uf0a7': '*',
        '■': '-',
    }
    for k, v in replacements.items():
        text = text.replace(k, v)
    return text


def fetch_raw_signals():
    """
    Ingest raw signals across multiple authoritative tech and open-source sources:
    1. Hugging Face Daily Papers (authentic AI/ML breakthroughs & model announcements)
    2. GitHub Search API (authenticated query for high-star trending developer tools across Full Stack, DevOps, Systems, AI)
    3. Hacker News Firebase API (top engineering discussions & post-mortems)
    """
    print("📡 [1/4] Ingesting signals from Hugging Face, GitHub & Hacker News...")
    
    # 1. Hugging Face Daily Papers
    hf_papers = []
    try:
        hf_resp = requests.get("https://huggingface.co/api/daily_papers", timeout=10)
        if hf_resp.status_code == 200:
            for item in hf_resp.json()[:10]:
                paper_obj = item.get("paper", {})
                title = item.get("title") or paper_obj.get("title")
                summary = item.get("summary") or paper_obj.get("summary", "")
                paper_id = paper_obj.get("id") or item.get("id", "")
                if title:
                    hf_papers.append({
                        "title": title.strip(),
                        "summary": summary.strip()[:350],
                        "url": f"https://huggingface.co/papers/{paper_id}" if paper_id else "https://huggingface.co/papers"
                    })
    except Exception as e:
        print(f"⚠️ Warning: Hugging Face fetch failed: {e}")

    # 2. Trending GitHub Repositories across tech stack (Authenticated to prevent 403 Rate Limit)
    github_repos = []
    gh_token = os.getenv("GITHUB_TOKEN") or os.getenv("GH_TOKEN")
    gh_headers = {"User-Agent": "MorningTechPulseAgent/3.0"}
    if gh_token:
        gh_headers["Authorization"] = f"token {gh_token}"

    try:
        month_ago = (datetime.date.today() - datetime.timedelta(days=30)).isoformat()
        gh_url = f"https://api.github.com/search/repositories?q=created:>{month_ago}+stars:>80&sort=stars&order=desc&per_page=15"
        gh_resp = requests.get(gh_url, headers=gh_headers, timeout=10)
        if gh_resp.status_code == 200:
            for repo in gh_resp.json().get("items", []):
                github_repos.append({
                    "name": repo["full_name"],
                    "description": repo.get("description") or "Open source developer tool",
                    "stars": f"{repo.get('stargazers_count', 0):,} Stars",
                    "url": repo["html_url"],
                    "language": repo.get("language") or "General"
                })
        else:
            print(f"⚠️ Warning: Primary GitHub search returned status {gh_resp.status_code}")
    except Exception as e:
        print(f"⚠️ Warning: GitHub fetch failed: {e}")

    # Fallback to broad active repos query if primary search returned fewer than 5 items
    if len(github_repos) < 5:
        try:
            week_ago = (datetime.date.today() - datetime.timedelta(days=7)).isoformat()
            gh_url_fallback = f"https://api.github.com/search/repositories?q=pushed:>{week_ago}+stars:1000..50000&sort=updated&order=desc&per_page=12"
            gh_resp_fallback = requests.get(gh_url_fallback, headers=gh_headers, timeout=10)
            if gh_resp_fallback.status_code == 200:
                for repo in gh_resp_fallback.json().get("items", []):
                    github_repos.append({
                        "name": repo["full_name"],
                        "description": repo.get("description") or "Open source developer tool",
                        "stars": f"{repo.get('stargazers_count', 0):,} Stars",
                        "url": repo["html_url"],
                        "language": repo.get("language") or "General"
                    })
        except Exception as e:
            print(f"⚠️ Warning: Secondary GitHub search failed: {e}")

    # 3. Hacker News Top Stories
    hn_stories = []
    try:
        hn_top_ids = requests.get("https://hacker-news.firebaseio.com/v0/topstories.json", timeout=10).json()[:12]
        for item_id in hn_top_ids:
            try:
                item_data = requests.get(f"https://hacker-news.firebaseio.com/v0/item/{item_id}.json", timeout=5).json()
                if item_data and "title" in item_data and item_data.get("type") == "story":
                    hn_stories.append({
                        "title": item_data["title"],
                        "url": item_data.get("url", f"https://news.ycombinator.com/item?id={item_id}"),
                        "score": item_data.get("score", 0)
                    })
            except Exception:
                continue
    except Exception as e:
        print(f"⚠️ Warning: Hacker News fetch failed: {e}")

    print(f"✅ Ingested: {len(hf_papers)} HF papers, {len(github_repos)} GitHub repos, {len(hn_stories)} HN stories.")
    return hf_papers, github_repos, hn_stories


def curate_with_groq(hf_papers, github_repos, hn_stories):
    """
    Synthesize high-density technical digest using Groq LPU (GPT-OSS).
    Strict rules:
    - Section 1: 4 genuine daily AI/ML breakthroughs synthesized EXCLUSIVELY from today's live Hugging Face papers or Hacker News. No stale hallucinated releases (GPT-4 Turbo, Claude 3.5, etc.)!
    - Section 2: Deterministic daily System Design Masterclass rotated by day of year across 31 topics. No repeating!
    - Section 3: 5 standout developer repositories chosen EXCLUSIVELY from today's live ingested GitHub candidates.
    - Strictly NO terminal commands or CLI code snippets!
    """
    print("🧠 [2/4] Synthesizing technical briefing via Groq LPU (Zero-Slop Standard)...")
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        raise ValueError("GROQ_API_KEY environment variable is missing!")

    client = Groq(api_key=api_key)

    # Deterministic daily topic rotation based on day of year
    today = datetime.date.today()
    day_of_year = today.timetuple().tm_yday
    topic_idx = day_of_year % len(SYSTEM_DESIGN_CURRICULUM)
    today_topic = SYSTEM_DESIGN_CURRICULUM[topic_idx]
    print(f"🎯 Assigned Daily System Design Topic [{topic_idx + 1}/{len(SYSTEM_DESIGN_CURRICULUM)}]: {today_topic['topic']}")

    system_prompt = f"""You are a Principal AI & Distributed Systems Architect compiling a high-quality, beginner-friendly 3-page daily briefing for software developers and computer science freshers.

STRICT EDITORIAL RULES:
1. FORBIDDEN WORDS: revolutionary, game-changer, delve, tapestry, testament, unleash, foster, pivotal, paramount, realm, in today's fast-paced, cutting-edge, elevate, seamlessly.
2. ZERO STALE HALLUCINATIONS IN BREAKTHROUGHS:
   - You MUST extract the 4 breakthroughs EXCLUSIVELY from the provided 'hugging_face_papers' and 'hacker_news_stories' in the user prompt.
   - For each item, state the real paper/project title, authoring lab/institution or research domain (e.g. Computer Vision Lab, Autonomous Driving AI, Causal Inference Lab, Robotics), explain what was built in plain English, how it works under the hood (without academic jargon), and its concrete software engineering benefit.
   - STRICTLY FORBIDDEN: Do NOT write about old announcements like GPT-4 Turbo, Gemini 1.5 Pro, Claude 3.5 Sonnet, or LLaMA 3. The breakthroughs MUST reflect today's ingested papers!
3. MANDATORY SYSTEM DESIGN TOPIC FOR TODAY:
   - You MUST base today's entire Page 2 masterclass on: '{today_topic["topic"]}'.
   - Core focus: {today_topic["focus"]}.
   - Production case study: {today_topic["case_study"]}.
   - Do NOT pick any other topic!
4. STANDOUT DEVELOPER REPOSITORIES:
   - You MUST pick 5 repositories EXCLUSIVELY from the provided 'github_trending' candidates.
   - Use their exact repository name, stars, language, and URL.
   - Do NOT hallucinate popular static tools like prisma, next.js, or transformers unless they appear in the provided input data!
5. ZERO TERMINAL COMMANDS: Do NOT include any CLI commands, bash snippets, or code installation blocks.
6. COMPLETE COVERAGE: Write detailed, engaging paragraphs that provide substantial educational depth and fill the page budget.

Return a valid JSON object matching this exact schema:
{{
  "breakthroughs": [
    {{
      "headline": "Direct factual headline of paper or breakthrough",
      "company": "Research Lab / Institution / Organization",
      "content": "A detailed, engaging 4-5 sentence paragraph explaining in plain English: what was released or discovered, how the technology works under the hood (in simple terms), and why it provides a major practical advantage for software developers."
    }}
  ],
  "system_design": {{
    "topic": "{today_topic['topic']}",
    "fundamental_problem": "A clear, compelling 3-4 sentence explanation of the real-world dilemma: why normal servers/databases crash under load, detailing the physical bottleneck (disk I/O, network lock contention, split-brain, memory starvation).",
    "intuitive_mental_model": "A memorable, intuitive real-world analogy (e.g. restaurant waiter with water pitcher, parliamentary quorum voting, library index cards, post office routing) explaining the core concept in simple terms.",
    "architecture_flow": "A clear step-by-step walkthrough of how data and requests flow through the system.",
    "engineering_tradeoffs": "A balanced explanation of the tricky challenges and trade-offs (e.g. consistency vs latency, partition tolerance, memory footprint).",
    "production_case_study": "{today_topic['case_study']} - detailed explanation of how it was implemented at scale with specific engineering metrics.",
    "interview_takeaway": "An exact, concise script of what a software engineer or fresher should say in a technical interview when asked about this architectural pattern."
  }},
  "developer_repos": [
    {{
      "name": "owner/repo",
      "category": "Backend & Database / DevOps & Cloud / Frontend & UI / Developer Tooling / AI Engine",
      "stars": "e.g. 15,000+ Stars",
      "language": "e.g. TypeScript / Rust / Python / Go",
      "url": "https://github.com/...",
      "overview": "A clear, engaging 3-4 sentence paragraph explaining in simple terms what this project does, the concrete problem it solves for developers, and why it is superior to traditional alternatives or building from scratch."
    }}
  ]
}}

Provide exactly:
- Exactly 4 entries in `breakthroughs` (derived from today's papers).
- Exactly 1 complete masterclass on '{today_topic["topic"]}' in `system_design`.
- Exactly 5 standout entries in `developer_repos` (chosen from today's github_trending)."""

    user_content = json.dumps({
        "hugging_face_papers": hf_papers[:8],
        "github_trending": github_repos[:12],
        "hacker_news_stories": hn_stories[:8]
    })

    response = client.chat.completions.create(
        model="openai/gpt-oss-120b",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"Here are today's live ingested signals for {today.strftime('%d %B %Y')}:\n{user_content}\n\nCompile today's dynamic, zero-slop 3-page briefing following the exact schema."}
        ],
        response_format={"type": "json_object"},
        temperature=0.3
    )

    data = json.loads(response.choices[0].message.content)
    print("✅ Technical curation completed.")
    return data


def generate_pdf(digest_data, output_filename="Morning_Tech_Pulse.pdf"):
    """
    Compile structured briefing into an executive-grade 3-page PDF using ReportLab.
    - Page 1: Daily AI Breakthroughs & Lab Innovations (From live research papers)
    - Page 2: System Design Masterclass (Daily deterministic rotating topic)
    - Page 3: Standout Developer Repositories across Tech Stack (5 fresh repos)
    - Full justified text alignment, professional spacing, zero colored boxes, zero static footers.
    - Exactly 3 Pages total!
    """
    print(f"📄 [3/4] Compiling strictly budgeted 3-Page PDF report ({output_filename})...")
    
    # Printable area: 612 x 792 pt. Margins: 34 pt -> Width: 544 pt, Height: 736 pt
    doc = SimpleDocTemplate(
        output_filename,
        pagesize=letter,
        leftMargin=34,
        rightMargin=34,
        topMargin=26,
        bottomMargin=26
    )

    styles = getSampleStyleSheet()

    main_title = ParagraphStyle(
        'MainTitle',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=15,
        leading=18,
        textColor=colors.HexColor('#0f172a')
    )
    date_meta = ParagraphStyle(
        'DateMeta',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=8.5,
        leading=11,
        textColor=colors.HexColor('#64748b'),
        alignment=TA_RIGHT
    )
    article_title = ParagraphStyle(
        'ArticleTitle',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=10.5,
        leading=13.5,
        textColor=colors.HexColor('#0f172a'),
        spaceBefore=1,
        spaceAfter=1.5
    )
    topic_header = ParagraphStyle(
        'TopicHeader',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=12.5,
        leading=15.5,
        textColor=colors.HexColor('#0f172a'),
        spaceBefore=0,
        spaceAfter=3
    )
    section_subhead = ParagraphStyle(
        'SectionSubhead',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=9.2,
        leading=12.5,
        textColor=colors.HexColor('#0369a1'),
        spaceBefore=3,
        spaceAfter=1
    )
    body_justified = ParagraphStyle(
        'BodyJustified',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=8.8,
        leading=12.8,
        textColor=colors.HexColor('#334155'),
        alignment=TA_JUSTIFY,
        spaceAfter=2
    )

    today_str = datetime.date.today().strftime('%A, %d %B %Y')
    story = []

    # ==========================================
    # PAGE 1: LATEST BREAKTHROUGHS & INNOVATIONS
    # ==========================================
    story.append(Paragraph("<b>MORNING TECH PULSE</b>", main_title))
    story.append(Paragraph(f"{today_str}", date_meta))
    story.append(Spacer(1, 4))
    story.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor('#0f172a'), spaceBefore=2, spaceAfter=8))

    breakthroughs = digest_data.get("breakthroughs", [])[:4]
    for idx, item in enumerate(breakthroughs):
        headline = item.get("headline", "AI Innovation")
        company = item.get("company", "Research Lab")
        content = item.get("content", "")

        story.append(Paragraph(f"<b>{sanitize_text(headline)}</b> &nbsp;•&nbsp; <font color='#0284c7'><b>{sanitize_text(company)}</b></font>", article_title))
        story.append(Spacer(1, 2))
        story.append(Paragraph(sanitize_text(content), body_justified))
        story.append(Spacer(1, 4))
        if idx < len(breakthroughs) - 1:
            story.append(HRFlowable(width="100%", thickness=0.4, color=colors.HexColor('#e2e8f0'), spaceBefore=2, spaceAfter=5))

    story.append(PageBreak())

    # ==========================================
    # PAGE 2: SYSTEM DESIGN MASTERCLASS (FULL PAGE)
    # ==========================================
    sd = digest_data.get("system_design", {})
    topic = sd.get("topic", "System Design: Distributed Architecture")
    problem = sd.get("fundamental_problem", "")
    analogy = sd.get("intuitive_mental_model", "")
    flow = sd.get("architecture_flow", "")
    tradeoffs = sd.get("engineering_tradeoffs", "")
    case_study = sd.get("production_case_study", "")
    interview = sd.get("interview_takeaway", "")

    story.append(Paragraph(f"<b>{sanitize_text(topic)}</b>", topic_header))
    story.append(HRFlowable(width="100%", thickness=0.75, color=colors.HexColor('#0f172a'), spaceBefore=2, spaceAfter=8))

    story.append(Paragraph("The Fundamental Problem", section_subhead))
    story.append(Paragraph(sanitize_text(problem), body_justified))

    story.append(Paragraph("The Intuitive Mental Model", section_subhead))
    story.append(Paragraph(sanitize_text(analogy), body_justified))

    story.append(Paragraph("How the Architecture Operates Step-by-Step", section_subhead))
    story.append(Paragraph(sanitize_text(flow), body_justified))

    story.append(Paragraph("The Engineering Trade-Offs & Tricky Challenges", section_subhead))
    story.append(Paragraph(sanitize_text(tradeoffs), body_justified))

    story.append(Paragraph("Real-World Production Practice", section_subhead))
    story.append(Paragraph(sanitize_text(case_study), body_justified))

    story.append(Paragraph("Key Takeaway for Tech Interviews & Portfolio Projects", section_subhead))
    story.append(Paragraph(sanitize_text(interview), body_justified))

    story.append(PageBreak())

    # ==========================================
    # PAGE 3: STANDOUT DEVELOPER REPOSITORIES ACROSS TECH STACK
    # ==========================================
    story.append(Paragraph("<b>Standout Open-Source Repositories (Curated for Developers)</b>", topic_header))
    story.append(HRFlowable(width="100%", thickness=0.75, color=colors.HexColor('#0f172a'), spaceBefore=2, spaceAfter=8))

    repos = digest_data.get("developer_repos", [])[:5]
    for idx, r in enumerate(repos):
        name = r.get("name", "owner/repo")
        category = r.get("category", "Developer Tool")
        stars = r.get("stars", "")
        lang = r.get("language", "General")
        overview = r.get("overview", "")
        url = r.get("url", "https://github.com")

        story.append(Paragraph(
            f"<b>{sanitize_text(name)}</b> &nbsp;•&nbsp; <font color='#0284c7'><b>{sanitize_text(category)}</b></font> &nbsp;•&nbsp; <font color='#64748b'>{sanitize_text(stars)} ({sanitize_text(lang)})</font>",
            article_title
        ))
        story.append(Spacer(1, 1))
        story.append(Paragraph(sanitize_text(overview), body_justified))
        story.append(Spacer(1, 1))
        story.append(Paragraph(f"<font color='#2563eb'><a href='{url}'><u>GitHub Link: {url}</u></a></font>", body_justified))
        story.append(Spacer(1, 4))
        if idx < len(repos) - 1:
            story.append(HRFlowable(width="100%", thickness=0.4, color=colors.HexColor('#e2e8f0'), spaceBefore=2, spaceAfter=5))

    doc.build(story)
    
    # Verify strict page count <= 3
    with open(output_filename, 'rb') as f:
        pdf_bytes = f.read()
    page_count = len(re.findall(rb'/Type\s*/Page\b', pdf_bytes))
    print(f"✅ Verified PDF generated with exactly {page_count} pages (Budget: 3 Pages).")
    return output_filename


def dispatch_via_email(digest_data, pdf_path="Morning_Tech_Pulse.pdf"):
    """
    Deliver the briefing directly to Vivek Kanugula via Gmail SMTP.
    Clean minimalist notification body; all content lives inside the attached 3-page PDF.
    """
    print("✉️ [4/4] Sending minimalist dispatch with attached PDF via Gmail SMTP...")
    
    sender = os.getenv("SENDER_EMAIL")
    recipient = os.getenv("RECEIVER_EMAIL", sender)
    password = os.getenv("GMAIL_APP_PASSWORD")

    if not sender or not password:
        raise ValueError("SENDER_EMAIL and GMAIL_APP_PASSWORD must be configured!")

    today_str = datetime.date.today().strftime('%d %b %Y')
    first_headline = digest_data.get("breakthroughs", [{}])[0].get("headline", "Daily Technical Briefing")
    subject = f"Morning Tech Pulse: {first_headline} [{today_str}]"
    topic_name = digest_data.get("system_design", {}).get("topic", "System Design Masterclass")

    msg = MIMEMultipart("mixed")
    msg["From"] = f"Morning Tech Pulse <{sender}>"
    msg["To"] = recipient
    msg["Subject"] = subject

    # Minimal clean notification email body displaying today's dynamic topic
    html_notification = f"""
    <!DOCTYPE html>
    <html>
    <head><meta charset="utf-8"></head>
    <body style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; background-color: #f8fafc; color: #1e293b; padding: 24px; margin: 0;">
      <div style="max-width: 520px; margin: 0 auto; background-color: #ffffff; border: 1px solid #e2e8f0; border-radius: 8px; padding: 24px; box-shadow: 0 1px 3px rgba(0,0,0,0.05);">
        <h2 style="font-size: 18px; font-weight: 700; color: #0f172a; margin-top: 0; margin-bottom: 8px;">Morning Tech Pulse</h2>
        <p style="font-size: 14px; line-height: 1.5; color: #475569; margin-bottom: 16px;">
          Good morning Vivek. Your curated daily technical briefing for <strong>{today_str}</strong> is attached as a concise 3-page PDF.
        </p>
        <div style="background-color: #f1f5f9; border-left: 3px solid #0284c7; padding: 12px 14px; font-size: 13px; line-height: 1.5; color: #334155; border-radius: 0 4px 4px 0;">
          📄 <strong>Attached:</strong> <code>Morning_Tech_Pulse.pdf</code> (3-Page Executive PDF)<br/>
          • <strong>Page 1:</strong> Daily AI Breakthroughs ({sanitize_text(first_headline)[:45]}...)<br/>
          • <strong>Page 2:</strong> {sanitize_text(topic_name)}<br/>
          • <strong>Page 3:</strong> Standout Developer Repositories Across Full Tech Stack
        </div>
        <p style="font-size: 11px; color: #94a3b8; margin-top: 18px; margin-bottom: 0;">
          Autonomous Pipeline • Delivered via Gmail SMTP & GitHub Actions Cloud
        </p>
      </div>
    </body>
    </html>
    """
    msg.attach(MIMEText(html_notification, "html", "utf-8"))

    # Attach the 3-page PDF
    if os.path.exists(pdf_path):
        with open(pdf_path, "rb") as f:
            pdf_attachment = MIMEApplication(f.read(), _subtype="pdf")
            pdf_attachment.add_header('Content-Disposition', 'attachment', filename="Morning_Tech_Pulse.pdf")
            msg.attach(pdf_attachment)

    clean_password = password.replace(" ", "")
    with smtplib.SMTP_SSL("smtp.gmail.com", 465, timeout=20) as server:
        server.login(sender, clean_password)
        server.sendmail(sender, [recipient], msg.as_string())

    print(f"🎉 3-Page Executive PDF Briefing delivered successfully to {recipient}!")


def main():
    print("=" * 60)
    print("🚀 Running Morning Tech Pulse Pipeline (Dynamic 3-Page Standard)")
    print("=" * 60)

    hf_papers, github_repos, hn_stories = fetch_raw_signals()
    digest_data = curate_with_groq(hf_papers, github_repos, hn_stories)
    pdf_path = generate_pdf(digest_data)
    dispatch_via_email(digest_data, pdf_path)

    print("=" * 60)
    print("🏁 Pipeline execution finished cleanly.")
    print("=" * 60)


if __name__ == "__main__":
    main()
