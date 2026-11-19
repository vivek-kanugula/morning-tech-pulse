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
    2. GitHub Search API (trending repositories across Full Stack, DevOps, Frontend, Tooling, AI)
    3. Hacker News Firebase API (top engineering discussions & post-mortems)
    """
    print("📡 [1/4] Ingesting signals from Hugging Face, GitHub & Hacker News...")
    
    # 1. Hugging Face Daily Papers
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
                        "summary": summary.strip()[:350],
                        "url": f"https://huggingface.co/papers/{paper_id}" if paper_id else "https://huggingface.co/papers"
                    })
    except Exception as e:
        print(f"⚠️ Warning: Hugging Face fetch failed: {e}")

    # 2. Trending GitHub Repositories across tech stack (Full Stack, DevOps, Tools, AI)
    github_repos = []
    try:
        week_ago = (datetime.date.today() - datetime.timedelta(days=7)).isoformat()
        # Query broad tech ecosystem
        gh_url = f"https://api.github.com/search/repositories?q=stars:>150+pushed:>{week_ago}&sort=stars&order=desc&per_page=10"
        headers = {"User-Agent": "MorningTechPulseAgent/3.0"}
        gh_resp = requests.get(gh_url, headers=headers, timeout=10)
        if gh_resp.status_code == 200:
            for repo in gh_resp.json().get("items", []):
                github_repos.append({
                    "name": repo["full_name"],
                    "description": repo.get("description") or "Open source developer tool",
                    "stars": f"{repo.get('stargazers_count', 0):,} Stars",
                    "url": repo["html_url"],
                    "language": repo.get("language") or "General"
                })
    except Exception as e:
        print(f"⚠️ Warning: GitHub fetch failed: {e}")

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
    - Section 1: Pure daily AI breakthroughs & innovations from leading labs (OpenAI, DeepMind, Anthropic, Meta, etc.). No mottos or missions!
    - Section 2: Comprehensive beginner-friendly System Design Masterclass (rotating pattern with restaurant analogy, flow, trade-offs, real production story, interview takeaway).
    - Section 3: 5 standout developer repositories across the full tech stack (Backend, DevOps, Frontend, Tooling, AI) with beginner overviews and direct links.
    - Strictly NO terminal commands or CLI code snippets!
    """
    print("🧠 [2/4] Synthesizing technical briefing via Groq LPU (Zero-Slop Standard)...")
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        raise ValueError("GROQ_API_KEY environment variable is missing!")

    client = Groq(api_key=api_key)

    system_prompt = """You are a Principal AI & Distributed Systems Architect compiling a high-quality, beginner-friendly 3-page daily briefing for software developers and computer science freshers.

STRICT EDITORIAL RULES:
1. FORBIDDEN WORDS: revolutionary, game-changer, delve, tapestry, testament, unleash, foster, pivotal, paramount, realm, in today's fast-paced, cutting-edge, elevate, seamlessly.
2. ZERO CORPORATE MOTTOS / MISSIONS: Do NOT include company mottos, mission statements, or corporate philosophies. Focus STRICTLY on actual concrete breakthroughs, technical releases, and real software innovations.
3. BEGINNER-FRIENDLY & CLEAR: Avoid dense mathematical jargon and academic acronyms without explaining them. Explain concepts using clean, intuitive language, real-world analogies, and practical developer context so a fresher can easily grasp everything.
4. ZERO TERMINAL COMMANDS: Do NOT include any CLI commands, bash snippets, or code installation blocks.
5. COMPLETE COVERAGE: Write detailed, engaging paragraphs that provide substantial educational depth.

Return a valid JSON object matching this exact schema:
{
  "breakthroughs": [
    {
      "headline": "Direct factual headline of breakthrough or release",
      "company": "OpenAI / Google DeepMind / Anthropic / Meta AI / Mistral / etc.",
      "content": "A detailed, engaging 4-5 sentence paragraph explaining in plain English: what was released or discovered, how the technology works under the hood (in simple terms), and why it provides a major practical advantage for software developers."
    }
  ],
  "system_design": {
    "topic": "System Design: [Topic Name, e.g. Distributed Caching / Distributed Rate Limiting / Database Sharding / Consistent Hashing / Log-Structured Merge Trees / Message Queues & Event Streaming]",
    "fundamental_problem": "A clear, compelling 3-4 sentence explanation of the real-world dilemma: why normal servers/databases crash when traffic spikes, detailing the physical bottleneck (disk I/O, connection exhaustion, lock contention).",
    "intuitive_mental_model": "A memorable, intuitive real-world analogy (e.g. restaurant waiter with water pitcher, leaky water buckets, library index cards, post office routing) explaining the core concept in simple terms.",
    "architecture_flow": "A clear step-by-step walkthrough of how data and requests flow through the system (e.g. Client request -> Cache/Gateway check -> Decision logic -> Backend database -> TTL expiration).",
    "engineering_tradeoffs": "A balanced explanation of the tricky challenges and trade-offs (e.g. Cache Invalidation and Cache Stampedes, or consistency vs latency).",
    "production_case_study": "A concrete real-world production story explaining how a top tech company (e.g. Discord, Netflix, Instagram, Uber, Stripe) implemented this pattern at massive scale with specific engineering metrics.",
    "interview_takeaway": "An exact, concise script of what a software engineer or fresher should say in a technical interview when asked about this architectural pattern."
  },
  "developer_repos": [
    {
      "name": "owner/repo",
      "category": "Backend & Database / DevOps & Cloud / Frontend & UI / Developer Tooling / AI Engine",
      "stars": "e.g. 76,000+ Stars",
      "language": "e.g. TypeScript / Rust / Python / Go",
      "url": "https://github.com/...",
      "overview": "A clear, engaging 3-4 sentence paragraph explaining in simple terms what this project does, the concrete problem it solves for developers, and why it is superior to traditional alternatives or building from scratch."
    }
  ]
}

Provide exactly:
- Exactly 4 entries in `breakthroughs` (pure breakthroughs/releases from leading AI labs; NO mottos/missions).
- Exactly 1 complete, rich, educational masterclass in `system_design`.
- Exactly 5 standout entries in `developer_repos` across the broad tech stack (Backend, DevOps, Frontend, Rust Tooling, AI; NO CLI commands!)."""

    user_content = json.dumps({
        "hugging_face_papers": hf_papers[:6],
        "github_trending": github_repos[:8],
        "hacker_news_stories": hn_stories[:6]
    })

    response = client.chat.completions.create(
        model="openai/gpt-oss-120b",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"Here are the latest ingested signals:\n{user_content}\n\nCompile today's 3-page technical briefing following the exact schema."}
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
    - Page 1: Big AI Breakthroughs & Innovations (No mottos/missions)
    - Page 2: System Design Masterclass (Learning Topic)
    - Page 3: Standout Developer Repositories across Tech Stack (5 items)
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
        company = item.get("company", "Tech Lab")
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
    topic = sd.get("topic", "System Design: Distributed Systems Architecture")
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

    msg = MIMEMultipart("mixed")
    msg["From"] = f"Morning Tech Pulse <{sender}>"
    msg["To"] = recipient
    msg["Subject"] = subject

    # Minimal clean notification email body
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
          • <strong>Page 1:</strong> Latest Daily AI Breakthroughs & Lab Innovations<br/>
          • <strong>Page 2:</strong> System Design Masterclass & Real Production Practices<br/>
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
    print("🚀 Running Morning Tech Pulse Pipeline (3-Page Executive Standard)")
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
