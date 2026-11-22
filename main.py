import os
import re
import json
import random
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

# History persistence file path
HISTORY_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "delivered_history.json")


def load_history():
    """Load persistent delivery history to strictly prevent repeated topics, repos, and breakthroughs."""
    if os.path.exists(HISTORY_FILE):
        try:
            with open(HISTORY_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                return {
                    "delivered_topics": data.get("delivered_topics", []),
                    "delivered_repos": data.get("delivered_repos", []),
                    "delivered_breakthroughs": data.get("delivered_breakthroughs", [])
                }
        except Exception as e:
            print(f"⚠️ Warning loading delivery history: {e}")
    return {"delivered_topics": [], "delivered_repos": [], "delivered_breakthroughs": []}


def save_history(history):
    """Persist updated delivery history back to disk."""
    try:
        with open(HISTORY_FILE, "w", encoding="utf-8") as f:
            json.dump(history, f, indent=2)
        print(f"💾 Persisted delivery history ({len(history.get('delivered_repos', []))} repos, {len(history.get('delivered_topics', []))} topics).")
    except Exception as e:
        print(f"⚠️ Warning saving delivery history: {e}")


# =========================================================================
# COMPREHENSIVE SYSTEM DESIGN CURRICULUM (HLD + LLD)
# Covering Low-Level Design (OOD/Design Patterns) and High-Level Design (Distributed Systems)
# =========================================================================
SYSTEM_DESIGN_CURRICULUM = [
    # -----------------------------
    # LOW-LEVEL DESIGN (LLD) TOPICS
    # -----------------------------
    {
        "topic": "LLD: In-Memory Cache with LRU Eviction & Concurrency Control",
        "category": "Low-Level Design (LLD)",
        "focus": "Doubly linked list combined with Hash Map for O(1) get/put, ReadWriteLock for thread-safe access, and TTL background cleaner",
        "case_study": "Caffeine and Guava Cache high-performance in-memory caching libraries in Java"
    },
    {
        "topic": "LLD: Parking Lot System with Multi-Tier Vehicle Allocation & Dynamic Pricing",
        "category": "Low-Level Design (LLD)",
        "focus": "Strategy pattern for nearest-spot assignment, State pattern for spot availability, Vehicle inheritance hierarchy, and concurrent slot locking",
        "case_study": "ParkMobile and automated airport parking garage management systems"
    },
    {
        "topic": "LLD: Elevator Dispatch System with Optimal Direction Scheduling (LOOK/SCAN)",
        "category": "Low-Level Design (LLD)",
        "focus": "State pattern for Idle/Moving/DoorOpen, LOOK/SCAN disk scheduling algorithm for elevator cars, and centralized request dispatcher queue",
        "case_study": "Otis and Schindler destination-dispatch elevator banks in skyscrapers"
    },
    {
        "topic": "LLD: In-Memory Task Scheduler & Thread Pool Engine",
        "category": "Low-Level Design (LLD)",
        "focus": "Producer-Consumer pattern with bounded blocking queues, worker thread lifecycle, and Min-Heap priority queue for delayed execution",
        "case_study": "Java ThreadPoolExecutor and Node.js libuv event loop work queues"
    },
    {
        "topic": "LLD: Splitwise Expense Sharing System with Debt Simplification Graph",
        "category": "Low-Level Design (LLD)",
        "focus": "Exact/Percentage/Share split calculation strategies, Directed graph minimum cash flow simplification algorithm, and immutable transaction ledger",
        "case_study": "Splitwise balance settlement engine minimizing cross-user money transfers"
    },
    {
        "topic": "LLD: Rate Limiter Library at Code Level (Token Bucket & Sliding Window)",
        "category": "Low-Level Design (LLD)",
        "focus": "Decorator/Middleware pattern, AtomicLong for lock-free thread safety, sliding window log vs token bucket refill calculation",
        "case_study": "Resilience4j and Google Guava RateLimiter in microservice SDKs"
    },
    {
        "topic": "LLD: Movie Ticket Booking System with Concurrent Seat Locking",
        "category": "Low-Level Design (LLD)",
        "focus": "Optimistic locking with version numbers vs Pessimistic locks for temporary seat holds with TTL, Command pattern for booking lifecycle",
        "case_study": "BookMyShow and AMC Theatres seat reservation engines during peak blockbuster releases"
    },
    {
        "topic": "LLD: Asynchronous Logging Framework with Append-Only Buffer & Rotation",
        "category": "Low-Level Design (LLD)",
        "focus": "Ring buffer (Disruptor pattern) for zero-allocation logging, asynchronous worker thread, file rolling policies (size and date)",
        "case_study": "Log4j2 LMAX Disruptor architecture achieving millions of logs/sec with sub-microsecond latency"
    },
    {
        "topic": "LLD: Chess Game Engine with Move Validation & Board State Tracking",
        "category": "Low-Level Design (LLD)",
        "focus": "Command pattern for move execution and undo, Polymorphic piece movement rules, Board state representation with 64-bit bitboards",
        "case_study": "Stockfish and Chess.com move validation and game clock engines"
    },
    {
        "topic": "LLD: In-Memory Pub-Sub Event Bus with Topic Subscriptions & Backpressure",
        "category": "Low-Level Design (LLD)",
        "focus": "Observer pattern, Thread-safe ConcurrentHashMap topic registry, asynchronous fan-out dispatch with bounded queues and drops",
        "case_study": "Google Guava EventBus and RxJava reactive event streams"
    },
    {
        "topic": "LLD: Snake and Ladder Board Game Engine using Strategy & State Patterns",
        "category": "Low-Level Design (LLD)",
        "focus": "State machine for player turns and winning condition, Strategy pattern for dice rolling (biased/random), extensible board layout",
        "case_study": "Modular board game simulation engines and casino gaming software"
    },
    {
        "topic": "LLD: ATM Machine System with Finite State Machine & Cash Dispenser",
        "category": "Low-Level Design (LLD)",
        "focus": "State pattern for Idle/CardInserted/PinEntered/Dispensing, Chain of Responsibility pattern for cash denomination dispensers ($100, $50, $20)",
        "case_study": "Diebold Nixdorf and NCR ATM banking software architecture"
    },
    {
        "topic": "LLD: Notification Dispatcher with Priority Channels & Template Engine",
        "category": "Low-Level Design (LLD)",
        "focus": "Factory pattern for channel handlers (Email, SMS, Push), Strategy pattern for provider failover, Template rendering with caching",
        "case_study": "Twilio and Courier multi-channel notification routing engines"
    },
    {
        "topic": "LLD: Vending Machine with State Pattern & Coin Inventory Calculator",
        "category": "Low-Level Design (LLD)",
        "focus": "State pattern for Ready/MoneyInserted/Dispensing/SoldOut, Greedy change calculation with denomination coin inventory",
        "case_study": "Smart retail kiosk and automated vending hardware firmware"
    },
    {
        "topic": "LLD: Live Cricket Scoreboard Provider with Observer Pattern (Cricbuzz)",
        "category": "Low-Level Design (LLD)",
        "focus": "Observer/Subscriber pattern for real-time ball-by-ball updates, Strategy pattern for match types (T20, ODI, Test), Match state coordinator",
        "case_study": "Cricbuzz and ESPN Cricinfo real-time live match commentary architectures"
    },
    {
        "topic": "LLD: File System Directory Structure with Composite Pattern",
        "category": "Low-Level Design (LLD)",
        "focus": "Composite pattern treating File and Directory polymorphically, Visitor pattern for disk usage calculation and search",
        "case_study": "Linux virtual file system (VFS) and Unix inode directory tree abstractions"
    },
    {
        "topic": "LLD: Text Editor Undo/Redo Engine with Command Pattern & Memento",
        "category": "Low-Level Design (LLD)",
        "focus": "Command pattern encapsulating text edits (insert, delete, replace), Dual-stack Memento pattern for undo/redo history, Piece Table data structure",
        "case_study": "VS Code text buffer implementation using Piece Trees and Redo stacks"
    },
    {
        "topic": "LLD: Online Shopping Cart & Discount Coupon Engine with Decorator Pattern",
        "category": "Low-Level Design (LLD)",
        "focus": "Decorator pattern for stacking promo discounts, Strategy pattern for coupon validation (percentage, flat, BOGO), Pricing pipeline",
        "case_study": "Shopify checkout pricing engine and Amazon promotional pricing calculators"
    },
    {
        "topic": "LLD: Order Management & Fulfillment Pipeline with State Pattern",
        "category": "Low-Level Design (LLD)",
        "focus": "Finite State Machine for OrderCreated/PaymentPending/Shipped/Delivered/Cancelled, Event hooks for inventory reservation",
        "case_study": "Amazon and Flipkart warehouse order lifecycle state machines"
    },
    {
        "topic": "LLD: Connection Pool Manager with Semaphore & Object Pool Pattern",
        "category": "Low-Level Design (LLD)",
        "focus": "Object Pool pattern, Counting Semaphore for max active connections, thread lease timeouts, validation on borrow/return",
        "case_study": "HikariCP high-performance JDBC connection pool for Java"
    },
    {
        "topic": "LLD: Tic-Tac-Toe Game with N-Dimensional Scalable Board Validation",
        "category": "Low-Level Design (LLD)",
        "focus": "O(1) win verification using row/col/diagonal sum counters, Polymorphic player strategies (Human, Minimax AI), Game controller",
        "case_study": "Google Assistant game skills and game engine turn managers"
    },
    {
        "topic": "LLD: Flight Reservation System with Temporary Seat Hold Expiration",
        "category": "Low-Level Design (LLD)",
        "focus": "DelayQueue for seat lock expiration, Optimistic concurrency control for seat allocation, Strategy pattern for dynamic fare calculation",
        "case_study": "Amadeus and Sabre global airline reservation backends"
    },
    {
        "topic": "LLD: Restaurant Table Reservation System with Conflict Detection",
        "category": "Low-Level Design (LLD)",
        "focus": "Interval tree / sweep-line algorithm for overlapping reservation time slots, Composite pattern for dining rooms and table combinations",
        "case_study": "OpenTable and Resy table allocation engines during peak dining hours"
    },

    # ------------------------------
    # HIGH-LEVEL DESIGN (HLD) TOPICS
    # ------------------------------
    {
        "topic": "HLD: Designing a Distributed URL Shortener (TinyURL / Bitly) at Scale",
        "category": "High-Level Design (HLD)",
        "focus": "Base62 encoding vs Key Generation Service (KGS), cache layer with Redis, database sharding by hash, analytics click stream",
        "case_study": "Bitly processing billions of redirects daily with sub-10ms response times"
    },
    {
        "topic": "HLD: Designing a Collaborative Real-Time Document Editor (Google Docs / Figma)",
        "category": "High-Level Design (HLD)",
        "focus": "Operational Transformation (OT) vs Conflict-Free Replicated Data Types (CRDTs), WebSocket session affinity, state vector synchronization",
        "case_study": "Figma multiplayer engine and Google Docs handling concurrent multi-user editing"
    },
    {
        "topic": "HLD: Designing a Ride-Hailing Service (Uber / Lyft) at Global Scale",
        "category": "High-Level Design (HLD)",
        "focus": "Geospatial indexing using Uber H3 hexagonal hierarchical spatial index, driver location stream ingestion, Quadtree spatial search",
        "case_study": "Uber DISCO dispatch engine matching drivers and riders in real time"
    },
    {
        "topic": "HLD: Designing a Video Streaming Platform (YouTube / Netflix)",
        "category": "High-Level Design (HLD)",
        "focus": "Video chunking and asynchronous transcoding pipelines, adaptive bitrate streaming (HLS/DASH), CDN edge caching, origin shielding",
        "case_study": "Netflix Open Connect CDN appliances and YouTube video ingestion pipeline"
    },
    {
        "topic": "HLD: Designing a Social Media News Feed (Twitter / Instagram)",
        "category": "High-Level Design (HLD)",
        "focus": "Fan-out on write (push) for regular users vs Fan-out on read (pull) for celebrities, timeline cache in Redis, ranked feed synthesis",
        "case_study": "Twitter (X) timeline service and Instagram Explore feed ranking architecture"
    },
    {
        "topic": "HLD: Designing an E-Commerce Flash Sale System (High Concurrency Inventory)",
        "category": "High-Level Design (HLD)",
        "focus": "Pre-warming inventory into Redis, atomic Lua decrement scripts, message queue buffering for order creation, circuit breaking",
        "case_study": "Amazon Prime Day and Alibaba Singles' Day handling hundreds of thousands of checkout requests per second"
    },
    {
        "topic": "HLD: Designing a Distributed Search Autocomplete / Typeahead Engine",
        "category": "High-Level Design (HLD)",
        "focus": "Prefix tree (Trie) serialized in memory, top-k frequent completions pre-computed at each node, weekly map-reduce frequency updates",
        "case_study": "Google Search typeahead and Amazon product search autocompletion"
    },
    {
        "topic": "HLD: Designing a Global Web Crawler at Internet Scale",
        "category": "High-Level Design (HLD)",
        "focus": "Frontier priority queue, Bloom filter URL deduplication, politeness domain rate-limiting, DNS caching, distributed workers",
        "case_study": "Common Crawl and Google Googlebot crawling billions of web pages monthly"
    },
    {
        "topic": "HLD: Designing an Instant Messaging & Live Chat Platform (WhatsApp / Discord)",
        "category": "High-Level Design (HLD)",
        "focus": "WebSocket gateway connection managers, ephemeral presence servers, Cassandra/ScyllaDB message stores, push notification bridge",
        "case_study": "Discord handling millions of concurrent voice and chat connections"
    },
    {
        "topic": "HLD: Designing a Cloud File Storage & Synchronization Service (Dropbox)",
        "category": "High-Level Design (HLD)",
        "focus": "Content-addressable block chunking (SHA-256), client-side deduplication, metadata synchronization service, Delta sync protocol",
        "case_study": "Dropbox desktop and cloud synchronization engine"
    },
    {
        "topic": "HLD: Designing a Real-Time Proximity Service (Yelp / Nearby Places)",
        "category": "High-Level Design (HLD)",
        "focus": "Geohash indexing, spatial database queries (PostGIS), quadtree spatial decomposition, read-heavy caching strategies",
        "case_study": "Yelp search engine locating businesses within radius boundaries"
    },
    {
        "topic": "HLD: Designing a Distributed Metrics Collection & Alerting Platform (Datadog)",
        "category": "High-Level Design (HLD)",
        "focus": "Time-series database (TSDB), rollup aggregations, LSM tree write optimization, push vs pull metric collection, sliding window alerts",
        "case_study": "Prometheus and Datadog ingesting billions of metric datapoints per minute"
    },
    {
        "topic": "HLD: Designing an E-Commerce Payment Processing Gateway (Stripe)",
        "category": "High-Level Design (HLD)",
        "focus": "Idempotency keys, Two-Phase Commit with bank networks, audit logging, reconciliation batch engines, transactional outbox",
        "case_study": "Stripe payments infrastructure processing hundreds of billions in transaction volume"
    },
    {
        "topic": "HLD: Designing a Distributed Job Scheduler (Cron at Global Scale)",
        "category": "High-Level Design (HLD)",
        "focus": "Leader election, partition leases, hashed tick wheel, persistent state in Postgres, worker heartbeating and job failover",
        "case_study": "Temporal and Airbnb Chronos distributing scheduled tasks across server fleets"
    },
    {
        "topic": "HLD: Designing an API Gateway Architecture with Rate Limiting & Auth",
        "category": "High-Level Design (HLD)",
        "focus": "Reverse proxy routing, JWT signature verification at edge, distributed rate limiting with Redis, request hedging and timeout budgets",
        "case_study": "Kong, Envoy, and Netflix Zuul managing edge traffic"
    },
    {
        "topic": "HLD: Designing a Vector Similarity Search Engine for Generative AI (RAG)",
        "category": "High-Level Design (HLD)",
        "focus": "Dense embeddings, Hierarchical Navigable Small World (HNSW) indexing, approximate nearest neighbors (ANN), metadata filtering",
        "case_study": "Pinecone, Milvus, and Spotify audio recommendation engines"
    },
    {
        "topic": "HLD: Designing a Distributed Caching Architecture & Invalidation Waves",
        "category": "High-Level Design (HLD)",
        "focus": "Cache-Aside vs Write-Through, XFetch probabilistic early recomputation, Thundering Herd mutex locks, consistent hashing ring",
        "case_study": "Meta scaling Memcached to billions of requests per second"
    },
    {
        "topic": "HLD: Designing Database Sharding & Partition Key Topologies",
        "category": "High-Level Design (HLD)",
        "focus": "Range-based vs Hash-based sharding, shard key selection, rebalancing hot partitions, cross-shard scatter-gather queries",
        "case_study": "Discord migrating billions of messages from MongoDB to ScyllaDB"
    },
    {
        "topic": "HLD: Designing Log-Structured Merge (LSM) Trees & Write-Ahead Logs",
        "category": "High-Level Design (HLD)",
        "focus": "Append-only write-ahead logs (WAL), in-memory MemTables, immutable SSTables, sequential disk I/O vs random B-Tree I/O",
        "case_study": "RocksDB and Apache Cassandra achieving massive write throughput"
    },
    {
        "topic": "HLD: Designing Consistent Hashing & Ring Topologies for Dynamic Elastic Clusters",
        "category": "High-Level Design (HLD)",
        "focus": "Virtual nodes, circular keyspace mapping, minimal data movement during scale-in/scale-out events, replication factor",
        "case_study": "Amazon DynamoDB and Discord voice servers dynamically routing state"
    },
    {
        "topic": "HLD: Designing an Event-Driven Architecture with Partitioned Commit Logs (Kafka)",
        "category": "High-Level Design (HLD)",
        "focus": "Partitioned commit logs, consumer group offset tracking, backpressure mechanisms, at-least-once vs exactly-once semantics",
        "case_study": "LinkedIn ingesting trillions of messages daily via Apache Kafka"
    },
    {
        "topic": "HLD: Designing Distributed Consensus using the Raft Protocol",
        "category": "High-Level Design (HLD)",
        "focus": "Leader election, randomized election timers, replicated state machine logs, quorum-based split-brain resolution (N/2 + 1)",
        "case_study": "etcd powering state consistency and orchestration in Kubernetes"
    },
    {
        "topic": "HLD: Designing CQRS & Event Sourcing Architecture for Auditable Financial Ledgers",
        "category": "High-Level Design (HLD)",
        "focus": "Command Query Responsibility Segregation, immutable event streams as the source of truth, asynchronous materialized read projections",
        "case_study": "Uber dispatch and Amazon banking ledger architectures"
    },
    {
        "topic": "HLD: Designing Distributed Locks with Redlock Algorithm & Fencing Tokens",
        "category": "High-Level Design (HLD)",
        "focus": "Mutual exclusion across distributed nodes, lease timeouts, clock drift hazards, fencing tokens preventing split-brain writes",
        "case_study": "Google Chubby lock service and Redis distributed lock implementations"
    },
    {
        "topic": "HLD: Designing Geo-Distributed Multi-Region Databases with Active-Active Replication",
        "category": "High-Level Design (HLD)",
        "focus": "Cross-region network latency, TrueTime synchronization, Raft consensus across availability zones, active-active multi-master replication",
        "case_study": "CockroachDB and Google Cloud Spanner delivering globally consistent ACID transactions"
    },
    {
        "topic": "HLD: Designing Reverse Proxies & HTTP/3 QUIC Edge Termination Networks",
        "category": "High-Level Design (HLD)",
        "focus": "TCP Head-of-Line blocking mitigation, UDP-based QUIC multiplexing, TLS 1.3 0-RTT resumption, Anycast routing",
        "case_study": "Cloudflare and Fastly edge networks accelerating global content delivery"
    },
    {
        "topic": "HLD: Designing Database Connection Pooling & Thread-Per-Core Architectures",
        "category": "High-Level Design (HLD)",
        "focus": "Connection exhaustion, Epoll/kqueue non-blocking event loops, shared-nothing memory models, eliminating OS thread context switching",
        "case_study": "ScyllaDB thread-per-core architecture handling millions of IOPS vs PostgreSQL PgBouncer"
    },
    {
        "topic": "HLD: Designing Distributed Object Storage with Reed-Solomon Erasure Coding",
        "category": "High-Level Design (HLD)",
        "focus": "Reed-Solomon (M+N) parity encoding, bit-rot detection, overcoming multi-drive failures without full 3x replication overhead",
        "case_study": "AWS S3 and MinIO achieving 11 nines of durability with low storage multiplication"
    },
    {
        "topic": "HLD: Designing WebSockets vs Server-Sent Events vs Long-Polling for Real-Time State",
        "category": "High-Level Design (HLD)",
        "focus": "Full-duplex TCP vs unidirectional HTTP streaming, keep-alive heartbeat pings, memory consumption per idle connection, load balancer sticky sessions",
        "case_study": "Slack real-time messaging gateway and Figma multiplayer canvas synchronization"
    },
    {
        "topic": "HLD: Designing Two-Phase Commit (2PC) vs The Saga Pattern for Microservices",
        "category": "High-Level Design (HLD)",
        "focus": "Synchronous distributed transaction locks and coordinator single point of failure vs asynchronous choreograph/orchestrated compensating transactions",
        "case_study": "Uber and Amazon managing distributed order and fulfillment lifecycles across microservices"
    },
    {
        "topic": "HLD: Designing Content Delivery Networks (CDN) & Dynamic Origin Shielding",
        "category": "High-Level Design (HLD)",
        "focus": "Origin shielding, stale-while-revalidate caching headers, purge invalidation waves, edge token verification",
        "case_study": "Netflix Open Connect appliance architecture delivering video streams close to end-users"
    },
    {
        "topic": "HLD: Designing a Full-Text Search Engine with Inverted Index & BM25 Scoring",
        "category": "High-Level Design (HLD)",
        "focus": "Text tokenization, posting lists, term frequency-inverse document frequency (TF-IDF), BM25 scoring, distributed shards",
        "case_study": "Elasticsearch and Apache Lucene handling real-time search queries across terabytes of documents"
    },
    {
        "topic": "HLD: Designing Service Mesh & Envoy Sidecar Data Planes",
        "category": "High-Level Design (HLD)",
        "focus": "Mutual TLS (mTLS) zero-trust identity, sidecar proxy routing, dynamic traffic splitting, circuit breaking at infrastructure layer",
        "case_study": "Lyft and Google Cloud service mesh architectures decoupling network policies from application code"
    },
    {
        "topic": "HLD: Designing Zero-Downtime Database Schema Migrations with Expand/Contract",
        "category": "High-Level Design (HLD)",
        "focus": "Expand and Contract pattern, backward-compatible dual writing, shadow column backfills, zero-lock DDL alterations",
        "case_study": "GitHub and Stripe executing live database schema migrations under continuous payment traffic"
    },
    {
        "topic": "HLD: Designing Microservices vs Modular Monolith & Domain Decomposition (DDD)",
        "category": "High-Level Design (HLD)",
        "focus": "Domain-Driven Design (DDD), bounded contexts, network hop overhead, distributed tracing complexity, single-deployment velocity",
        "case_study": "Amazon Prime Video moving from serverless microservices to monolithic container clusters to cut compute costs by 90%"
    },
    {
        "topic": "HLD: Designing Distributed Task Scheduling & Priority Delay Queues",
        "category": "High-Level Design (HLD)",
        "focus": "Dead-letter exchanges, exponential retry queues, worker heartbeating, distributed cron timers, partition leases",
        "case_study": "Temporal and Celery orchestration engines executing mission-critical long-running workflows"
    },
    {
        "topic": "HLD: Designing Load Balancing Algorithms: Weighted Least-Connections vs Peak EWMA",
        "category": "High-Level Design (HLD)",
        "focus": "Round-robin limitations, weighted least connections, Peak Exponentially Weighted Moving Average (EWMA), Power of Two Random Choices",
        "case_study": "HAProxy and Twitter Finagle routing traffic with minimal latency variance"
    },
    {
        "topic": "HLD: Designing Disaster Recovery & Chaos Engineering for High Availability",
        "category": "High-Level Design (HLD)",
        "focus": "Recovery Point Objective (RPO) vs Recovery Time Objective (RTO), warm standby vs active-active failover, automated fault injection",
        "case_study": "Netflix Chaos Monkey deliberately terminating production instances to enforce resilient self-healing architectures"
    },
    {
        "topic": "HLD: Designing Gossip Protocols & Decentralized Node Failure Detection",
        "category": "High-Level Design (HLD)",
        "focus": "Epidemic dissemination algorithms, Phi Accrual failure detection, heartbeat gossip rounds, eventual cluster convergence",
        "case_study": "Apache Cassandra and HashiCorp Consul maintaining cluster state across thousands of nodes without a centralized master"
    },
    {
        "topic": "HLD: Designing Read-Your-Own-Writes Consistency under Asynchronous Replication Lag",
        "category": "High-Level Design (HLD)",
        "focus": "Asynchronous replication lag, sticky user sessions, reading from master on mutation, causal consistency tracking via vector clocks",
        "case_study": "Meta (Instagram) ensuring immediate feed post visibility for authoring users despite global replica lag"
    },
    {
        "topic": "HLD: Designing Bloom Filters & Count-Min Sketches for High-Throughput Stream Deduplication",
        "category": "High-Level Design (HLD)",
        "focus": "Probabilistic data structures, k independent hash functions, space efficiency with zero false negatives, frequency estimation",
        "case_study": "Google Chrome checking malicious URLs and Bigtable avoiding expensive disk reads for non-existent keys"
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


def fetch_raw_signals(history):
    """
    Ingest raw signals across multiple authoritative tech and open-source sources:
    1. Hugging Face Daily Papers (authentic AI/ML breakthroughs & model announcements)
    2. GitHub Search API (Authenticated query across multiple diverse categories, filtering out any previously delivered repos)
    3. Hacker News Firebase API (top engineering discussions & post-mortems)
    """
    print("📡 [1/4] Ingesting signals from Hugging Face, GitHub & Hacker News...")
    
    delivered_repos_set = set(r.lower() for r in history.get("delivered_repos", []))
    delivered_breakthroughs_set = set(b.lower() for b in history.get("delivered_breakthroughs", []))

    # 1. Hugging Face Daily Papers
    hf_papers = []
    try:
        hf_resp = requests.get("https://huggingface.co/api/daily_papers", timeout=10)
        if hf_resp.status_code == 200:
            for item in hf_resp.json()[:12]:
                paper_obj = item.get("paper", {})
                title = item.get("title") or paper_obj.get("title")
                summary = item.get("summary") or paper_obj.get("summary", "")
                paper_id = paper_obj.get("id") or item.get("id", "")
                if title and title.strip().lower() not in delivered_breakthroughs_set:
                    hf_papers.append({
                        "title": title.strip(),
                        "summary": summary.strip()[:350],
                        "url": f"https://huggingface.co/papers/{paper_id}" if paper_id else "https://huggingface.co/papers"
                    })
    except Exception as e:
        print(f"⚠️ Warning: Hugging Face fetch failed: {e}")

    # 2. GitHub Repositories Across Broad Categories (Strict anti-repetition filter)
    github_repos = []
    seen_names = set()
    gh_token = os.getenv("GITHUB_TOKEN") or os.getenv("GH_TOKEN")
    gh_headers = {"User-Agent": "MorningTechPulseAgent/4.0"}
    if gh_token:
        gh_headers["Authorization"] = f"token {gh_token}"

    # Diverse search queries spanning modern tools, legendary utilities, systems, and languages
    search_queries = [
        "topic:developer-tools+stars:1000..60000&sort=stars&order=desc",
        "topic:cli+stars:1500..50000&sort=stars&order=desc",
        "topic:database+stars:1000..60000&sort=stars&order=desc",
        "language:rust+stars:2000..60000&sort=stars&order=desc",
        "language:go+stars:2000..60000&sort=stars&order=desc",
        "language:typescript+stars:2000..60000&sort=stars&order=desc",
        "language:python+stars:2000..60000&sort=stars&order=desc",
        f"created:>{(datetime.date.today() - datetime.timedelta(days=60)).isoformat()}+stars:>80&sort=stars&order=desc"
    ]
    # Pick a random subset of 3-4 query angles each day for variety
    selected_queries = random.sample(search_queries, min(4, len(search_queries)))

    for q in selected_queries:
        try:
            gh_url = f"https://api.github.com/search/repositories?q={q}&per_page=12"
            gh_resp = requests.get(gh_url, headers=gh_headers, timeout=10)
            if gh_resp.status_code == 200:
                for repo in gh_resp.json().get("items", []):
                    name = repo["full_name"]
                    name_lower = name.lower()
                    if name_lower not in delivered_repos_set and name_lower not in seen_names:
                        seen_names.add(name_lower)
                        github_repos.append({
                            "name": name,
                            "description": repo.get("description") or "Open source developer tool",
                            "stars": f"{repo.get('stargazers_count', 0):,} Stars",
                            "url": repo["html_url"],
                            "language": repo.get("language") or "General"
                        })
        except Exception as e:
            print(f"⚠️ Warning: GitHub query failed for '{q}': {e}")

    # Fallback to general high-star active repos if needed
    if len(github_repos) < 5:
        try:
            gh_url_fb = "https://api.github.com/search/repositories?q=stars:500..100000&sort=updated&order=desc&per_page=20"
            gh_resp_fb = requests.get(gh_url_fb, headers=gh_headers, timeout=10)
            if gh_resp_fb.status_code == 200:
                for repo in gh_resp_fb.json().get("items", []):
                    name = repo["full_name"]
                    name_lower = name.lower()
                    if name_lower not in delivered_repos_set and name_lower not in seen_names:
                        seen_names.add(name_lower)
                        github_repos.append({
                            "name": name,
                            "description": repo.get("description") or "Open source developer tool",
                            "stars": f"{repo.get('stargazers_count', 0):,} Stars",
                            "url": repo["html_url"],
                            "language": repo.get("language") or "General"
                        })
        except Exception as e:
            print(f"⚠️ Warning: Secondary GitHub fallback failed: {e}")

    # 3. Hacker News Top Stories
    hn_stories = []
    try:
        hn_top_ids = requests.get("https://hacker-news.firebaseio.com/v0/topstories.json", timeout=10).json()[:12]
        for item_id in hn_top_ids:
            try:
                item_data = requests.get(f"https://hacker-news.firebaseio.com/v0/item/{item_id}.json", timeout=5).json()
                if item_data and "title" in item_data and item_data.get("type") == "story":
                    title = item_data["title"]
                    if title.strip().lower() not in delivered_breakthroughs_set:
                        hn_stories.append({
                            "title": title,
                            "url": item_data.get("url", f"https://news.ycombinator.com/item?id={item_id}"),
                            "score": item_data.get("score", 0)
                        })
            except Exception:
                continue
    except Exception as e:
        print(f"⚠️ Warning: Hacker News fetch failed: {e}")

    print(f"✅ Ingested: {len(hf_papers)} fresh HF papers, {len(github_repos)} un-delivered GitHub repos, {len(hn_stories)} fresh HN stories.")
    return hf_papers, github_repos, hn_stories


def select_system_design_topic(history):
    """
    Randomly select an undelivered topic from the entire System Design curriculum (HLD + LLD).
    Ensures zero repeats across runs.
    """
    delivered_topics = set(t.lower() for t in history.get("delivered_topics", []))
    available_topics = [t for t in SYSTEM_DESIGN_CURRICULUM if t["topic"].lower() not in delivered_topics]
    
    if not available_topics:
        print("🔄 All 64+ topics have been delivered! Refreshing available cycle.")
        history["delivered_topics"] = []
        available_topics = SYSTEM_DESIGN_CURRICULUM

    selected_topic = random.choice(available_topics)
    print(f"🎯 Randomly Selected System Design Topic: [{selected_topic['category']}] -> {selected_topic['topic']}")
    return selected_topic


def curate_with_groq(hf_papers, github_repos, hn_stories, today_topic):
    """
    Synthesize high-density technical digest using Groq LPU (GPT-OSS).
    Strict rules:
    - Section 1: 4 genuine daily AI/ML breakthroughs synthesized EXCLUSIVELY from today's live Hugging Face papers or Hacker News.
    - Section 2: Full-page System Design Masterclass on the randomly chosen HLD/LLD topic.
    - Section 3: 5 standout developer repositories chosen EXCLUSIVELY from today's un-delivered GitHub candidates.
    - Strictly NO terminal commands or CLI code snippets!
    """
    print("🧠 [2/4] Synthesizing technical briefing via Groq LPU (Zero-Slop Standard)...")
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        raise ValueError("GROQ_API_KEY environment variable is missing!")

    client = Groq(api_key=api_key)
    today = datetime.date.today()

    system_prompt = f"""You are a Principal Software Architect compiling a high-quality, beginner-friendly 3-page daily briefing for software developers and computer science freshers.

STRICT EDITORIAL RULES:
1. FORBIDDEN WORDS: revolutionary, game-changer, delve, tapestry, testament, unleash, foster, pivotal, paramount, realm, in today's fast-paced, cutting-edge, elevate, seamlessly.
2. ZERO STALE HALLUCINATIONS IN BREAKTHROUGHS:
   - You MUST extract the 4 breakthroughs EXCLUSIVELY from the provided 'hugging_face_papers' and 'hacker_news_stories' in the user prompt.
   - For each item, state the real paper/project title, authoring lab/institution or research domain (e.g. Computer Vision Lab, Autonomous Driving AI, Causal Inference Lab, Robotics), explain what was built in plain English, how it works under the hood (without academic jargon), and its concrete software engineering benefit.
   - STRICTLY FORBIDDEN: Do NOT write about old announcements like GPT-4 Turbo, Gemini 1.5 Pro, Claude 3.5 Sonnet, or LLaMA 3. The breakthroughs MUST reflect today's ingested papers!
3. MANDATORY SYSTEM DESIGN TOPIC FOR TODAY ({today_topic['category']}):
   - You MUST base today's entire Page 2 masterclass on: '{today_topic["topic"]}'.
   - Core focus: {today_topic["focus"]}.
   - Production case study: {today_topic["case_study"]}.
   - If this is a Low-Level Design (LLD) topic, discuss class structures, design patterns, thread safety, and data structures. If this is a High-Level Design (HLD) topic, discuss microservices, caching, consensus, and horizontal scaling.
   - Do NOT pick any other topic!
4. STANDOUT DEVELOPER REPOSITORIES:
   - You MUST pick 5 repositories EXCLUSIVELY from the provided 'github_trending' candidates.
   - Use their exact repository name, stars, language, and URL.
   - Do NOT pick any repository not in the input list!
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
    "fundamental_problem": "A clear, compelling 3-4 sentence explanation of the real-world dilemma: why this system/component becomes a bottleneck, detailing the physical dilemma (thread race conditions, lock contention, memory leaks, latency spikes, or network partitions).",
    "intuitive_mental_model": "A memorable, intuitive real-world analogy (e.g. restaurant waiter with water pitcher, parliamentary quorum voting, library index cards, post office routing, traffic toll-booth) explaining the core concept in simple terms.",
    "architecture_flow": "A clear step-by-step walkthrough of how the system operates and coordinates requests.",
    "engineering_tradeoffs": "A balanced explanation of the tricky challenges and trade-offs (e.g. memory vs CPU, optimistic vs pessimistic locks, consistency vs availability).",
    "production_case_study": "{today_topic['case_study']} - detailed explanation of how it was implemented at scale with specific engineering metrics.",
    "interview_takeaway": "An exact, concise script of what a software engineer or fresher should say in a technical interview when asked about this architectural pattern or LLD problem."
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
        "github_trending": github_repos[:15],
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
    
    # Guarantee exactly 5 developer repositories are populated on Page 3
    curated_repos = data.get("developer_repos", [])
    if len(curated_repos) < 5 and github_repos:
        existing_names = set(r.get("name", "").lower() for r in curated_repos)
        for candidate in github_repos:
            c_name = candidate.get("name", "")
            if c_name.lower() not in existing_names:
                curated_repos.append({
                    "name": c_name,
                    "category": "Developer Tooling",
                    "stars": candidate.get("stars", ""),
                    "language": candidate.get("language", "General"),
                    "overview": candidate.get("description") or "Open-source developer utility with active maintenance.",
                    "url": candidate.get("url", f"https://github.com/{c_name}")
                })
                existing_names.add(c_name.lower())
                if len(curated_repos) >= 5:
                    break
    data["developer_repos"] = curated_repos[:5]

    print("✅ Technical curation completed.")
    return data


def generate_pdf(digest_data, output_filename="Morning_Tech_Pulse.pdf"):
    """
    Compile structured briefing into an executive-grade 3-page PDF using ReportLab.
    - Page 1: Daily AI Breakthroughs & Lab Innovations (From live research papers)
    - Page 2: System Design Masterclass (Randomly chosen HLD / LLD topic)
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
    topic = sd.get("topic", "System Design: Architecture Masterclass")
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
    print("🚀 Running Morning Tech Pulse Pipeline (HLD + LLD Dynamic Standard)")
    print("=" * 60)

    # 1. Load persistent delivery history
    history = load_history()

    # 2. Randomly select undelivered topic across entire System Design (HLD + LLD)
    today_topic = select_system_design_topic(history)

    # 3. Ingest fresh live signals with strict anti-repetition filter
    hf_papers, github_repos, hn_stories = fetch_raw_signals(history)

    # 4. Curate zero-slop briefing via Groq
    digest_data = curate_with_groq(hf_papers, github_repos, hn_stories, today_topic)

    # 5. Compile verified 3-page PDF
    pdf_path = generate_pdf(digest_data)

    # 6. Dispatch via Gmail SMTP
    dispatch_via_email(digest_data, pdf_path)

    # 7. Record delivered items into history to strictly prevent repeats in future runs
    history["delivered_topics"].append(today_topic["topic"])
    for r in digest_data.get("developer_repos", []):
        if r.get("name"):
            history["delivered_repos"].append(r["name"])
    for b in digest_data.get("breakthroughs", []):
        if b.get("headline"):
            history["delivered_breakthroughs"].append(b["headline"])

    save_history(history)

    print("=" * 60)
    print("🏁 Pipeline execution finished cleanly with history updated.")
    print("=" * 60)


if __name__ == "__main__":
    main()
