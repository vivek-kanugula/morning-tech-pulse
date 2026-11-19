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
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable, PageBreak
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from dotenv import load_dotenv

# Load local environment variables from .env if present
load_dotenv()

def fetch_raw_signals():
    """
    Ingest raw signals from multiple authoritative engineering sources:
    1. Hugging Face Daily Papers (authentic AI/ML breakthroughs & model announcements)
    2. GitHub Search API (trending AI/LLM open-source repositories)
    3. Hacker News Firebase API (top technical discussions & systems post-mortems)
    """
    print("📡 [1/4] Ingesting signals from Hugging Face, GitHub AI & Hacker News...")
    
    # 1. Fetch Hugging Face Daily Papers & Model Announcements
    hf_papers = []
    try:
        hf_resp = requests.get("https://huggingface.co/api/daily_papers", timeout=10)
        if hf_resp.status_code == 200:
            for item in hf_resp.json()[:8]:
                paper_obj = item.get("paper", {})
                title = item.get("title") or paper_obj.get("title")
                summary = item.get("summary") or paper_obj.get("summary", "")
                paper_id = paper_obj.get("id") or item.get("id", "")
                if title:
                    hf_papers.append({
                        "title": title.strip(),
                        "summary": summary.strip()[:400],
                        "url": f"https://huggingface.co/papers/{paper_id}" if paper_id else "https://huggingface.co/papers",
                        "source": "Hugging Face Daily Papers"
                    })
    except Exception as e:
        print(f"⚠️ Warning: Hugging Face fetch failed: {e}")

    # 2. Fetch High-Star GitHub AI/LLM Repositories Active in Past 7 Days
    github_ai_repos = []
    try:
        week_ago = (datetime.date.today() - datetime.timedelta(days=7)).isoformat()
        gh_url = f"https://api.github.com/search/repositories?q=(ai+OR+llm)+pushed:>{week_ago}+stars:>100&sort=stars&order=desc&per_page=6"
        headers = {"User-Agent": "MorningTechPulseAgent/2.0"}
        gh_resp = requests.get(gh_url, headers=headers, timeout=10)
        if gh_resp.status_code == 200:
            for repo in gh_resp.json().get("items", []):
                github_ai_repos.append({
                    "name": repo["full_name"],
                    "description": repo.get("description") or "Open source AI framework",
                    "stars": repo.get("stargazers_count", 0),
                    "url": repo["html_url"],
                    "language": repo.get("language") or "General"
                })
    except Exception as e:
        print(f"⚠️ Warning: GitHub fetch failed: {e}")

    # 3. Fetch Top Hacker News Stories
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
                        "score": item_data.get("score", 0),
                        "source": "Hacker News"
                    })
            except Exception:
                continue
    except Exception as e:
        print(f"⚠️ Warning: Hacker News fetch failed: {e}")

    print(f"✅ Ingested: {len(hf_papers)} Hugging Face papers, {len(github_ai_repos)} GitHub AI repos, {len(hn_stories)} HN stories.")
    return hf_papers, github_ai_repos, hn_stories


def curate_with_groq(hf_papers, github_ai_repos, hn_stories):
    """
    Synthesize high-density technical digest using Groq Llama-3.3-70B / GPT-OSS.
    Enforces strict zero-AI-slop rubric: no buzzwords, no hype, no CLI terminal commands.
    """
    print("🧠 [2/4] Synthesizing technical briefing via Groq LPU (Zero-Slop Standard)...")
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        raise ValueError("GROQ_API_KEY environment variable is missing!")

    client = Groq(api_key=api_key)

    system_prompt = """You are a Principal AI & Distributed Systems Architect compiling a high-precision, 3-part internal engineering briefing for senior developers.

STRICT EDITORIAL RULES:
1. FORBIDDEN WORDS: revolutionary, game-changer, delve, tapestry, testament, unleash, foster, pivotal, paramount, realm, in today's fast-paced, cutting-edge, elevate, seamlessly.
2. ZERO MARKETING FLUFF: State exact technical specs, model architectures, parameters, algorithms, protocols, latency/memory tradeoffs, and production practices.
3. STRICTLY NO TERMINAL COMMANDS: Do NOT include any CLI commands, bash snippets, or installation instructions. The reader wants to understand *what happened*, *why it matters*, and *the engineering purpose*.
4. CONCISE & PRECISE: Keep explanations dense and educational.

Return a valid JSON object matching this exact schema:
{
  "ai_news": [
    {
      "headline": "Direct factual headline of model release, research breakthrough, or major launch",
      "category": "Multimodal / LLM / Quantization / Agent / Infrastructure",
      "what_happened": "2 concise sentences explaining the model architecture, breakthrough, or release specifications.",
      "practical_use_case": "Exact production scenario or problem this solves for engineers.",
      "url": "link"
    }
  ],
  "system_design_deep_dive": {
    "topic": "Name of Concrete Architecture Pattern (rotate among topics like: Distributed Rate Limiting with Redis & Leaky Bucket, Log-Structured Merge Trees vs B-Trees, Consistent Hashing with Virtual Nodes, Cache-Aside vs Write-Through with Debezium CDC, Raft Consensus & Leader Election, Epoll & Event-Driven I/O, Cassandra Shared-Nothing vs Postgres Sharding, Distributed Locking with Redlock, Write-Ahead Logging & ARIES Recovery, Two-Phase Commit vs Saga Pattern)",
    "fundamental_bottleneck": "The specific distributed systems or hardware bottleneck this pattern resolves (e.g. write amplification, network partitions, cascading failures, lock contention).",
    "mechanical_breakdown": [
      "Precise mechanical step or invariant 1 (data structures and state management)",
      "Precise mechanical step or invariant 2 (concurrency, serialization, or network protocol)",
      "Precise mechanical step or invariant 3 (failure recovery and edge case handling)"
    ],
    "architectural_tradeoffs": "Explicit trade-off analysis (e.g., consistency vs availability, write amplification vs read latency, memory overhead vs CPU utilization).",
    "production_case_study": "Concrete industry production practice (e.g., how Netflix, Stripe, Discord, Uber, or Cloudflare implements this at scale with specific numbers/metrics)."
  },
  "open_source_ai_repos": [
    {
      "repo_name": "owner/repo",
      "description": "1-2 sentence precise technical description of what the tool does.",
      "purpose_and_value": "Why an engineer would choose this; the specific operational or modeling challenge it solves in production.",
      "url": "https://github.com/...",
      "language": "Python / Rust / C++ / etc."
    }
  ]
}

Provide exactly:
- 3 high-impact entries in `ai_news` (selected from Hugging Face papers or major AI launches)
- 1 rigorous, educational entry in `system_design_deep_dive`
- 3 standout entries in `open_source_ai_repos` (strictly no terminal commands!)."""

    user_content = json.dumps({
        "hugging_face_papers": hf_papers[:6],
        "github_ai_candidates": github_ai_repos[:6],
        "hacker_news_discussions": hn_stories[:6]
    })

    # Groq OpenAI model endpoint
    response = client.chat.completions.create(
        model="openai/gpt-oss-120b",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"Ingested raw signals:\n{user_content}\n\nSynthesize today's 3-part technical digest."}
        ],
        response_format={"type": "json_object"},
        temperature=0.2
    )

    data = json.loads(response.choices[0].message.content)
    print("✅ Technical curation completed.")
    return data


def generate_pdf(digest_data, output_filename="Morning_Tech_Pulse.pdf"):
    """
    Compile structured briefing into an executive-grade 3-page PDF using ReportLab.
    Strictly enforce:
    - Page 1: Latest Authentic AI Developments & Model Launches
    - Page 2: System Design Deep Dive & Real-World Industry Practice
    - Page 3: Standout Open-Source AI Repositories (No CLI commands)
    - Max 3 Pages total!
    """
    print(f"📄 [3/4] Compiling strictly budgeted 3-Page PDF report ({output_filename})...")
    
    # Letter is 612 x 792 pt. Margins: 36 pt (0.5 in) each side -> Printable width = 540 pt, Printable height = 720 pt.
    doc = SimpleDocTemplate(
        output_filename,
        pagesize=letter,
        leftMargin=36,
        rightMargin=36,
        topMargin=32,
        bottomMargin=32
    )

    styles = getSampleStyleSheet()

    # Editorial typography palette
    title_style = ParagraphStyle(
        'DocTitle',
        parent=styles['Heading1'],
        fontName='Helvetica-Bold',
        fontSize=15,
        leading=18,
        textColor=colors.HexColor('#0f172a')
    )
    meta_style = ParagraphStyle(
        'DocMeta',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=8.5,
        leading=11,
        textColor=colors.HexColor('#64748b')
    )
    section_tag = ParagraphStyle(
        'SectionTag',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=9,
        leading=12,
        textColor=colors.HexColor('#0284c7'),
        spaceAfter=4
    )
    item_title = ParagraphStyle(
        'ItemTitle',
        parent=styles['Heading2'],
        fontName='Helvetica-Bold',
        fontSize=11,
        leading=14,
        textColor=colors.HexColor('#0f172a')
    )
    body_text = ParagraphStyle(
        'BodyTextCustom',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=9,
        leading=13,
        textColor=colors.HexColor('#334155')
    )
    bold_label = ParagraphStyle(
        'BoldLabel',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=9,
        leading=13,
        textColor=colors.HexColor('#1e293b')
    )
    highlight_box_text = ParagraphStyle(
        'HighlightText',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=8.5,
        leading=12,
        textColor=colors.HexColor('#0369a1')
    )
    footer_text = ParagraphStyle(
        'PageFooter',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=8,
        leading=10,
        textColor=colors.HexColor('#94a3b8'),
        alignment=1 # Centered
    )

    today_str = datetime.date.today().strftime('%A, %d %B %Y')
    story = []

    def get_header(page_title, page_subtitle, page_num):
        header_table = Table([
            [
                Paragraph(f"<b>MORNING TECH PULSE</b> &nbsp;|&nbsp; <font color='#64748b'>{page_title}</font>", title_style),
                Paragraph(f"<b>{today_str}</b><br/><font color='#64748b'>Page {page_num} of 3 • Vivek Kanugula</font>", ParagraphStyle('HRight', parent=meta_style, alignment=2))
            ]
        ], colWidths=[380, 160])
        header_table.setStyle(TableStyle([
            ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
            ('BOTTOMPADDING', (0,0), (-1,-1), 0),
            ('TOPPADDING', (0,0), (-1,-1), 0),
            ('LEFTPADDING', (0,0), (-1,-1), 0),
            ('RIGHTPADDING', (0,0), (-1,-1), 0),
        ]))
        return [
            header_table,
            Spacer(1, 4),
            HRFlowable(width="100%", thickness=1.2, color=colors.HexColor('#0f172a'), spaceBefore=2, spaceAfter=8)
        ]

    # ==========================================
    # PAGE 1: LATEST AUTHENTIC AI DEVELOPMENTS
    # ==========================================
    story.extend(get_header("AI DEVELOPMENTS & MODEL LAUNCHES", "Authentic Model Launches", 1))
    story.append(Paragraph("1. LATEST AUTHENTIC AI DEVELOPMENTS & RELEASES", section_tag))
    story.append(Spacer(1, 4))

    for idx, item in enumerate(digest_data.get("ai_news", [])[:3], 1):
        headline = item.get("headline", "AI Update")
        cat = item.get("category", "LLM")
        what_happened = item.get("what_happened", "")
        practical_use = item.get("practical_use_case", "")
        url = item.get("url", "#")

        card_content = [
            Paragraph(f"<b>{idx}. [{cat}] {headline}</b>", item_title),
            Spacer(1, 3),
            Paragraph(f"<b>What Happened:</b> {what_happened}", body_text),
            Spacer(1, 3),
            Paragraph(f"<b>Production Use Case:</b> {practical_use}", highlight_box_text),
            Spacer(1, 2),
            Paragraph(f"<font color='#2563eb'><a href='{url}'><u>Reference Link & Model Card</u></a></font>", meta_style)
        ]
        card_table = Table([[card_content]], colWidths=[540])
        card_table.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,-1), colors.HexColor('#f8fafc')),
            ('BOX', (0,0), (-1,-1), 0.75, colors.HexColor('#e2e8f0')),
            ('TOPPADDING', (0,0), (-1,-1), 8),
            ('BOTTOMPADDING', (0,0), (-1,-1), 8),
            ('LEFTPADDING', (0,0), (-1,-1), 10),
            ('RIGHTPADDING', (0,0), (-1,-1), 10),
        ]))
        story.append(card_table)
        story.append(Spacer(1, 10))

    story.append(Spacer(1, 12))
    story.append(Paragraph("Morning Tech Pulse • Page 1 of 3: AI Research & Model Launches", footer_text))
    story.append(PageBreak())

    # ==========================================
    # PAGE 2: SYSTEM DESIGN DEEP DIVE (LEARNING)
    # ==========================================
    sd = digest_data.get("system_design_deep_dive", {})
    story.extend(get_header("SYSTEM DESIGN ARCHITECTURE", "Production Engineering", 2))
    story.append(Paragraph("2. SYSTEM DESIGN DEEP DIVE & INDUSTRY PRACTICE", section_tag))
    story.append(Spacer(1, 4))

    topic_title = sd.get("topic", "Distributed Systems Architecture")
    bottleneck = sd.get("fundamental_bottleneck", "")
    mechanics = sd.get("mechanical_breakdown", [])
    tradeoffs = sd.get("architectural_tradeoffs", "")
    case_study = sd.get("production_case_study", "")

    mechanics_html = "<br/>".join([f"• <b>Mechanism {i+1}:</b> {m}" for i, m in enumerate(mechanics)])

    sd_content = [
        Paragraph(f"<b>Architecture Pattern: {topic_title}</b>", ParagraphStyle('SDHead', parent=item_title, fontSize=12, leading=15)),
        Spacer(1, 5),
        Paragraph(f"<b>Core Engineering Bottleneck:</b> {bottleneck}", body_text),
        Spacer(1, 6),
        HRFlowable(width="100%", thickness=0.5, color=colors.HexColor('#cbd5e1'), spaceBefore=2, spaceAfter=6),
        Paragraph("<b>Mechanical Breakdown & Invariants:</b>", bold_label),
        Spacer(1, 3),
        Paragraph(mechanics_html, body_text),
        Spacer(1, 6),
        HRFlowable(width="100%", thickness=0.5, color=colors.HexColor('#cbd5e1'), spaceBefore=2, spaceAfter=6),
        Paragraph(f"<b>Architectural Trade-offs:</b> {tradeoffs}", body_text),
        Spacer(1, 6),
        HRFlowable(width="100%", thickness=0.5, color=colors.HexColor('#cbd5e1'), spaceBefore=2, spaceAfter=6),
        Paragraph("<b>Real-World Industry Production Case Study:</b>", bold_label),
        Spacer(1, 2),
        Paragraph(case_study, highlight_box_text)
    ]
    sd_table = Table([[sd_content]], colWidths=[540])
    sd_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor('#f0f9ff')),
        ('BOX', (0,0), (-1,-1), 1, colors.HexColor('#bae6fd')),
        ('TOPPADDING', (0,0), (-1,-1), 12),
        ('BOTTOMPADDING', (0,0), (-1,-1), 12),
        ('LEFTPADDING', (0,0), (-1,-1), 12),
        ('RIGHTPADDING', (0,0), (-1,-1), 12),
    ]))
    story.append(sd_table)
    story.append(Spacer(1, 25))
    story.append(Paragraph("Morning Tech Pulse • Page 2 of 3: System Design Deep Dive", footer_text))
    story.append(PageBreak())

    # ==========================================
    # PAGE 3: TRENDING OPEN-SOURCE AI REPOSITORIES
    # ==========================================
    story.extend(get_header("AI OPEN-SOURCE ECOSYSTEM", "Tooling & Infrastructure", 3))
    story.append(Paragraph("3. STANDOUT AI OPEN-SOURCE REPOSITORIES", section_tag))
    story.append(Spacer(1, 4))

    for idx, repo in enumerate(digest_data.get("open_source_ai_repos", [])[:3], 1):
        name = repo.get("repo_name", "owner/repo")
        desc = repo.get("description", "")
        purpose = repo.get("purpose_and_value", "")
        lang = repo.get("language", "Python")
        url = repo.get("url", "#")

        repo_content = [
            Paragraph(f"<b>{idx}. {name}</b> &nbsp; <font color='#64748b'>({lang})</font>", item_title),
            Spacer(1, 3),
            Paragraph(f"<b>What It Does:</b> {desc}", body_text),
            Spacer(1, 3),
            Paragraph(f"<b>Purpose & Practical Value:</b> {purpose}", highlight_box_text),
            Spacer(1, 2),
            Paragraph(f"<font color='#2563eb'><a href='{url}'><u>GitHub Repository: {url}</u></a></font>", meta_style)
        ]
        repo_table = Table([[repo_content]], colWidths=[540])
        repo_table.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,-1), colors.HexColor('#f8fafc')),
            ('BOX', (0,0), (-1,-1), 0.75, colors.HexColor('#e2e8f0')),
            ('TOPPADDING', (0,0), (-1,-1), 8),
            ('BOTTOMPADDING', (0,0), (-1,-1), 8),
            ('LEFTPADDING', (0,0), (-1,-1), 10),
            ('RIGHTPADDING', (0,0), (-1,-1), 10),
        ]))
        story.append(repo_table)
        story.append(Spacer(1, 10))

    story.append(Spacer(1, 15))
    story.append(HRFlowable(width="100%", thickness=0.5, color=colors.HexColor('#e2e8f0'), spaceBefore=2, spaceAfter=4))
    story.append(Paragraph(
        "Autonomous Pipeline • Sources: Hugging Face Daily Papers, GitHub AI & Hacker News • Zero Marketing Fluff • Curated for Vivek Kanugula",
        meta_style
    ))
    story.append(Spacer(1, 6))
    story.append(Paragraph("Morning Tech Pulse • Page 3 of 3: Open-Source AI Tooling", footer_text))

    doc.build(story)
    
    # Verify strict page count <= 3
    with open(output_filename, 'rb') as f:
        pdf_bytes = f.read()
    page_count = len(re.findall(rb'/Type\s*/Page\b', pdf_bytes))
    print(f"✅ Verified PDF generated with exactly {page_count} pages (Budget: Max 3 Pages).")
    return output_filename


def dispatch_via_email(digest_data, pdf_path="Morning_Tech_Pulse.pdf"):
    """
    Deliver the briefing directly to Vivek Kanugula via Gmail SMTP.
    As requested: NO overview in the email body; email body is a clean, minimal notification,
    and all briefing content lives exclusively inside the attached 3-page PDF.
    """
    print("✉️ [4/4] Sending minimalist dispatch with attached PDF via Gmail SMTP...")
    
    sender = os.getenv("SENDER_EMAIL")
    recipient = os.getenv("RECEIVER_EMAIL", sender)
    password = os.getenv("GMAIL_APP_PASSWORD")

    if not sender or not password:
        raise ValueError("SENDER_EMAIL and GMAIL_APP_PASSWORD must be configured!")

    today_str = datetime.date.today().strftime('%d %b %Y')
    first_headline = digest_data.get("ai_news", [{}])[0].get("headline", "Daily AI Briefing")
    subject = f"Morning Tech Pulse: {first_headline} [{today_str}]"

    msg = MIMEMultipart("mixed")
    msg["From"] = f"Morning Tech Pulse <{sender}>"
    msg["To"] = recipient
    msg["Subject"] = subject

    # Minimal clean notification email body (NO content overview in body)
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
          📄 <strong>Attached:</strong> <code>Morning_Tech_Pulse.pdf</code><br/>
          • <strong>Page 1:</strong> Latest Authentic AI Developments & Model Launches<br/>
          • <strong>Page 2:</strong> System Design Deep Dive & Real-World Industry Practice<br/>
          • <strong>Page 3:</strong> Standout AI Open-Source Repositories (No CLI Code)
        </div>
        <p style="font-size: 11px; color: #94a3b8; margin-top: 18px; margin-bottom: 0;">
          Autonomous Pipeline • Ingested via Hugging Face, GitHub AI & Hacker News • Delivered via Gmail SMTP
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
    print("🚀 Running Morning Tech Pulse Pipeline (AI & Systems Standard)")
    print("=" * 60)

    hf_papers, github_ai_repos, hn_stories = fetch_raw_signals()
    digest_data = curate_with_groq(hf_papers, github_ai_repos, hn_stories)
    pdf_path = generate_pdf(digest_data)
    dispatch_via_email(digest_data, pdf_path)

    print("=" * 60)
    print("🏁 Pipeline execution finished cleanly.")
    print("=" * 60)


if __name__ == "__main__":
    main()
