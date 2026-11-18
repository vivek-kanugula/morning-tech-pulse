import os
import json
import datetime
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.application import MIMEApplication
import requests
from groq import Groq
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from dotenv import load_dotenv

# Load local .env
load_dotenv()

def fetch_raw_signals():
    """Fetch raw signals from Hacker News and GitHub APIs."""
    print("📡 [1/4] Pulling top stories from Hacker News & trending GitHub repositories...")
    stories = []
    
    # 1. Fetch Top Hacker News Stories
    try:
        hn_top_ids = requests.get("https://hacker-news.firebaseio.com/v0/topstories.json", timeout=10).json()[:12]
        for item_id in hn_top_ids:
            try:
                item_data = requests.get(f"https://hacker-news.firebaseio.com/v0/item/{item_id}.json", timeout=5).json()
                if item_data and "title" in item_data and item_data.get("type") == "story":
                    stories.append({
                        "title": item_data["title"],
                        "url": item_data.get("url", f"https://news.ycombinator.com/item?id={item_id}"),
                        "score": item_data.get("score", 0),
                        "comments_count": item_data.get("descendants", 0)
                    })
            except Exception:
                continue
    except Exception as e:
        print(f"⚠️ Warning: HN fetch failed: {e}")

    # 2. Fetch High-Star GitHub Repositories Active in Past 7 Days
    github_repos = []
    try:
        week_ago = (datetime.date.today() - datetime.timedelta(days=7)).isoformat()
        gh_url = f"https://api.github.com/search/repositories?q=stars:>200+pushed:>{week_ago}&sort=stars&order=desc&per_page=6"
        headers = {"User-Agent": "TechBriefingAgent/1.0"}
        gh_resp = requests.get(gh_url, headers=headers, timeout=10).json()
        for repo in gh_resp.get("items", []):
            github_repos.append({
                "name": repo["full_name"],
                "description": repo.get("description") or "Open source library",
                "stars": repo.get("stargazers_count", 0),
                "url": repo["html_url"],
                "language": repo.get("language") or "General"
            })
    except Exception as e:
        print(f"⚠️ Warning: GitHub fetch failed: {e}")

    print(f"✅ Ingested {len(stories)} HN stories and {len(github_repos)} GitHub repositories.")
    return stories, github_repos


def curate_with_groq(stories, github_repos):
    """
    Synthesize high-density technical digest using Groq Llama-3.3-70B.
    Enforces strict zero-AI-slop rubric: no buzzwords, no hype, only technical facts and trade-offs.
    """
    print("🧠 [2/4] Synthesizing technical briefing via Groq Llama-3.3-70B (Zero-Slop Filter)...")
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        raise ValueError("GROQ_API_KEY environment variable is missing!")

    client = Groq(api_key=api_key)

    system_prompt = """You are a Principal Infrastructure & Systems Architect writing an internal engineering brief for senior engineers at a top tech company.
STRICT STYLE RULES:
- FORBIDDEN WORDS: revolutionary, game-changer, delve, tapestry, testament, unleash, foster, pivotal, paramount, realm, in today's fast-paced, cutting-edge, elevate.
- ZERO MARKETING HYPE: Do not say 'this tool empowers developers'. State exact technical functions, protocols, performance metrics, benchmarks, or memory/CPU tradeoffs.
- Write with brutal conciseness and technical precision. Assume the reader is a veteran backend/systems developer.

Return a valid JSON object matching this schema:
{
  "top_stories": [
    {
      "headline": "Direct factual headline without exclamation marks",
      "summary": "2 sentences explaining the technical implementation or change.",
      "architectural_impact": "Direct analysis of latency, memory, concurrency, or infrastructure trade-offs.",
      "category": "Systems / AI / Databases / Cloud / Networking",
      "url": "original source link"
    }
  ],
  "github_gem": {
    "repo_name": "owner/repo",
    "description": "Concrete technical description (e.g. 'Lock-free concurrent hashmap in Rust with SIMD lookup').",
    "quickstart": "Exact terminal installation or run command",
    "technical_utility": "Concrete scenario where an engineer would choose this over standard alternatives.",
    "url": "https://github.com/..."
  },
  "system_design_card": {
    "topic": "Name of Concrete Architecture Pattern (e.g. Log-Structured Merge Trees, Consistent Hashing Rings, Epoll vs Select, Raft Consensus, Distributed Locks)",
    "core_problem": "The fundamental distributed or operating system bottleneck it addresses.",
    "mechanism_breakdown": [
      "Precise mechanical step 1 (data structure or protocol behavior)",
      "Precise mechanical step 2 (concurrency or consistency trade-off)"
    ],
    "production_case_study": "Concrete production example (e.g. 'Discord replaced Cassandra with ScyllaDB, dropping p99 read latency from 40ms to 2ms due to Scylla's thread-per-core shared-nothing architecture in C++')."
  },
  "terminal_power_tip": {
    "command": "Practical Unix/Git/Docker command",
    "use_case": "Specific scenario where this saves debugging time (e.g. inspecting socket buffers, tracking memory leaks, diffing branches)."
  }
}

Select 3 top technical breakthroughs from the raw stories, 1 standout repository from the GitHub candidates, and formulate a rigorous System Design breakdown."""

    user_content = json.dumps({
        "raw_stories": stories[:8],
        "github_candidates": github_repos
    })

    response = client.chat.completions.create(
        model="openai/gpt-oss-120b",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_content}
        ],
        response_format={"type": "json_object"},
        temperature=0.1
    )

    data = json.loads(response.choices[0].message.content)
    print("✅ Technical curation completed.")
    return data


def generate_pdf(digest_data, output_filename="Morning_Tech_Pulse.pdf"):
    """Compile structured briefing into an executive-grade PDF using ReportLab."""
    print(f"📄 [3/4] Compiling PDF report ({output_filename})...")
    doc = SimpleDocTemplate(
        output_filename,
        pagesize=letter,
        leftMargin=36,
        rightMargin=36,
        topMargin=36,
        bottomMargin=36
    )

    styles = getSampleStyleSheet()

    # Editorial typography palette
    title_style = ParagraphStyle(
        'DocTitle',
        parent=styles['Heading1'],
        fontName='Helvetica-Bold',
        fontSize=18,
        leading=22,
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
    section_h1 = ParagraphStyle(
        'SectionH1',
        parent=styles['Heading2'],
        fontName='Helvetica-Bold',
        fontSize=11,
        leading=14,
        textColor=colors.HexColor('#0f172a'),
        spaceBefore=10,
        spaceAfter=5
    )
    card_title = ParagraphStyle(
        'CardTitle',
        parent=styles['Heading3'],
        fontName='Helvetica-Bold',
        fontSize=10,
        leading=13,
        textColor=colors.HexColor('#1e293b')
    )
    body_text = ParagraphStyle(
        'BodyTextCustom',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=9,
        leading=12.5,
        textColor=colors.HexColor('#334155')
    )
    impact_text = ParagraphStyle(
        'ImpactText',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=8.5,
        leading=12,
        textColor=colors.HexColor('#1e40af')
    )
    code_text = ParagraphStyle(
        'CodeSnippet',
        parent=styles['Normal'],
        fontName='Courier-Bold',
        fontSize=8.5,
        leading=11,
        textColor=colors.HexColor('#0f172a')
    )

    story = []
    today_str = datetime.date.today().strftime('%A, %d %B %Y')

    # Header Table
    header_data = [
        [
            Paragraph("<b>TECH PULSE</b> &nbsp;|&nbsp; <font color='#64748b'>ENGINEERING EXECUTIVE BRIEFING</font>", title_style),
            Paragraph(f"<b>{today_str}</b><br/><font color='#64748b'>Curated for Vivek Kanugula</font>", ParagraphStyle('HRight', parent=meta_style, alignment=2))
        ]
    ]
    header_table = Table(header_data, colWidths=[380, 160])
    header_table.setStyle(TableStyle([
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('BOTTOMPADDING', (0,0), (-1,-1), 0),
        ('TOPPADDING', (0,0), (-1,-1), 0),
    ]))
    story.append(header_table)
    story.append(Spacer(1, 6))
    story.append(HRFlowable(width="100%", thickness=1.5, color=colors.HexColor('#0f172a'), spaceBefore=2, spaceAfter=8))

    # SECTION 1: Top Engineering Breakthroughs
    story.append(Paragraph("1. CORE TECHNICAL DEVELOPMENTS", section_h1))
    for idx, item in enumerate(digest_data.get("top_stories", [])[:3], 1):
        cat = item.get("category", "Engineering")
        headline = item.get("headline", "Technical Update")
        summary = item.get("summary", "")
        impact = item.get("architectural_impact", "")
        url = item.get("url", "")

        story_block = [
            Paragraph(f"<b>{idx}. [{cat}] {headline}</b>", card_title),
            Spacer(1, 1),
            Paragraph(summary, body_text),
            Spacer(1, 2),
            Paragraph(f"⚙️ <b>Architectural Impact:</b> {impact} <font color='#2563eb'>(<a href='{url}'><u>Source</u></a>)</font>", impact_text),
            Spacer(1, 5)
        ]
        story.extend(story_block)

    story.append(HRFlowable(width="100%", thickness=0.5, color=colors.HexColor('#cbd5e1'), spaceBefore=4, spaceAfter=6))

    # SECTION 2: GitHub Open-Source Gem
    gem = digest_data.get("github_gem", {})
    if gem:
        story.append(Paragraph("2. OPEN-SOURCE TOOLING SPOTLIGHT", section_h1))
        gem_content = [
            Paragraph(f"<b>Repository:</b> <font color='#2563eb'><b>{gem.get('repo_name')}</b></font> &nbsp;•&nbsp; <a href='{gem.get('url')}'><u>Source Code</u></a>", card_title),
            Spacer(1, 2),
            Paragraph(gem.get("description", ""), body_text),
            Spacer(1, 2),
            Paragraph(f"<b>Quickstart:</b> <font face='Courier'><code>{gem.get('quickstart', '')}</code></font>", body_text),
            Spacer(1, 2),
            Paragraph(f"<b>Technical Utility:</b> {gem.get('technical_utility', '')}", body_text),
        ]
        gem_table = Table([[gem_content]], colWidths=[540])
        gem_table.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,-1), colors.HexColor('#f8fafc')),
            ('BOX', (0,0), (-1,-1), 1, colors.HexColor('#e2e8f0')),
            ('TOPPADDING', (0,0), (-1,-1), 6),
            ('BOTTOMPADDING', (0,0), (-1,-1), 6),
            ('LEFTPADDING', (0,0), (-1,-1), 8),
            ('RIGHTPADDING', (0,0), (-1,-1), 8),
        ]))
        story.append(gem_table)
        story.append(Spacer(1, 6))

    story.append(HRFlowable(width="100%", thickness=0.5, color=colors.HexColor('#cbd5e1'), spaceBefore=2, spaceAfter=6))

    # SECTION 3: System Design Deep-Dive
    sd = digest_data.get("system_design_card", {})
    if sd:
        story.append(Paragraph("3. SYSTEM DESIGN ARCHITECTURE CARD", section_h1))
        bullets_text = "<br/>".join([f"• {b}" for b in sd.get("mechanism_breakdown", [])])
        sd_content = [
            Paragraph(f"<b>Pattern: {sd.get('topic', 'Distributed Architecture')}</b>", card_title),
            Spacer(1, 2),
            Paragraph(f"<b>Bottleneck:</b> {sd.get('core_problem', '')}", body_text),
            Spacer(1, 2),
            Paragraph(bullets_text, body_text),
            Spacer(1, 2),
            Paragraph(f"<b>Production Case Study:</b> {sd.get('production_case_study', '')}", impact_text),
        ]
        sd_table = Table([[sd_content]], colWidths=[540])
        sd_table.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,-1), colors.HexColor('#f0f9ff')),
            ('BOX', (0,0), (-1,-1), 1, colors.HexColor('#bae6fd')),
            ('TOPPADDING', (0,0), (-1,-1), 6),
            ('BOTTOMPADDING', (0,0), (-1,-1), 6),
            ('LEFTPADDING', (0,0), (-1,-1), 8),
            ('RIGHTPADDING', (0,0), (-1,-1), 8),
        ]))
        story.append(sd_table)
        story.append(Spacer(1, 6))

    # SECTION 4: Terminal Power-Tip
    tip = digest_data.get("terminal_power_tip", {})
    if tip:
        story.append(Paragraph("4. SYSTEMS & DEBUGGING RECIPE", section_h1))
        tip_content = [
            Paragraph(f"<b>Command:</b> <font color='#0f172a'><code>{tip.get('command', '')}</code></font>", code_text),
            Spacer(1, 2),
            Paragraph(f"<b>Use Case:</b> {tip.get('use_case', '')}", body_text)
        ]
        tip_table = Table([[tip_content]], colWidths=[540])
        tip_table.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,-1), colors.HexColor('#f8fafc')),
            ('BOX', (0,0), (-1,-1), 1, colors.HexColor('#e2e8f0')),
            ('TOPPADDING', (0,0), (-1,-1), 5),
            ('BOTTOMPADDING', (0,0), (-1,-1), 5),
            ('LEFTPADDING', (0,0), (-1,-1), 8),
            ('RIGHTPADDING', (0,0), (-1,-1), 8),
        ]))
        story.append(tip_table)
        story.append(Spacer(1, 8))

    # Footer
    story.append(HRFlowable(width="100%", thickness=0.5, color=colors.HexColor('#e2e8f0'), spaceBefore=2, spaceAfter=4))
    story.append(Paragraph(
        "Autonomous Pipeline • Ingested via Hacker News & GitHub APIs • Curated by Groq Llama-3.3-70B • Distributed via Gmail SMTP",
        meta_style
    ))

    doc.build(story)
    print("✅ PDF generated successfully.")
    return output_filename


def build_email_html(digest_data):
    """Render clean, editorial HTML email body without flashy AI slop."""
    today_str = datetime.date.today().strftime('%A, %d %B %Y')
    
    # Story items
    stories_html = ""
    for item in digest_data.get("top_stories", [])[:3]:
        cat = item.get("category", "Engineering")
        stories_html += f"""
        <div style="background-color: #ffffff; border: 1px solid #e5e7eb; border-radius: 6px; padding: 16px; margin-bottom: 14px;">
          <div style="font-size: 10px; font-weight: 700; text-transform: uppercase; letter-spacing: 0.5px; color: #475569; margin-bottom: 6px;">{cat}</div>
          <div style="font-size: 16px; font-weight: 700; color: #0f172a; margin-bottom: 6px; line-height: 1.3;">
            <a href="{item.get('url', '#')}" style="color: #0f172a; text-decoration: none;">{item.get('headline')}</a>
          </div>
          <div style="font-size: 13.5px; color: #334155; line-height: 1.5; margin-bottom: 10px;">{item.get('summary')}</div>
          <div style="background-color: #f8fafc; border-left: 3px solid #0284c7; padding: 8px 12px; font-size: 12.5px; color: #0369a1; font-weight: 600; line-height: 1.4;">
            ⚙️ <strong>Architectural Impact:</strong> {item.get('architectural_impact')}
          </div>
        </div>
        """

    # GitHub Gem
    gem = digest_data.get("github_gem", {})
    gem_html = f"""
    <div style="background-color: #f8fafc; border: 1px solid #e2e8f0; border-radius: 6px; padding: 14px; margin-bottom: 14px;">
      <div style="font-size: 11px; font-weight: 700; text-transform: uppercase; color: #475569; margin-bottom: 4px;">🛠️ Open-Source Tooling Spotlight</div>
      <div style="font-size: 15px; font-weight: 700; color: #0f172a; margin-bottom: 4px;">
        <a href="{gem.get('url', '#')}" style="color: #0284c7; text-decoration: none;">{gem.get('repo_name')}</a>
      </div>
      <div style="font-size: 13px; color: #475569; margin-bottom: 8px;">{gem.get('description')}</div>
      <div style="background-color: #0f172a; color: #38bdf8; font-family: ui-monospace, Menlo, monospace; padding: 6px 10px; border-radius: 4px; font-size: 12px; margin-bottom: 6px;">
        {gem.get('quickstart')}
      </div>
      <div style="font-size: 12px; color: #64748b;"><strong>Technical Utility:</strong> {gem.get('technical_utility')}</div>
    </div>
    """

    # System Design Card
    sd = digest_data.get("system_design_card", {})
    bullets = "".join([f"<li style='margin-bottom: 3px;'>{b}</li>" for b in sd.get("mechanism_breakdown", [])])
    sd_html = f"""
    <div style="background-color: #f0f9ff; border: 1px solid #bae6fd; border-radius: 6px; padding: 14px; margin-bottom: 14px;">
      <div style="font-size: 11px; font-weight: 700; text-transform: uppercase; color: #0284c7; margin-bottom: 4px;">🧠 System Design Architecture Card</div>
      <div style="font-size: 15px; font-weight: 700; color: #0369a1; margin-bottom: 4px;">{sd.get('topic')}</div>
      <div style="font-size: 13px; color: #075985; margin-bottom: 6px;"><strong>Core Bottleneck:</strong> {sd.get('core_problem')}</div>
      <ul style="margin: 0 0 6px 0; padding-left: 18px; font-size: 12.5px; color: #0f172a; line-height: 1.4;">
        {bullets}
      </ul>
      <div style="font-size: 12px; color: #0369a1; font-weight: 600;"><strong>Production Case Study:</strong> {sd.get('production_case_study')}</div>
    </div>
    """

    # Terminal Tip
    tip = digest_data.get("terminal_power_tip", {})
    tip_html = f"""
    <div style="background-color: #f8fafc; border: 1px solid #e2e8f0; border-radius: 6px; padding: 12px; margin-bottom: 16px;">
      <div style="font-size: 11px; font-weight: 700; text-transform: uppercase; color: #475569; margin-bottom: 4px;">⚡ Systems & Debugging Recipe</div>
      <code style="background-color: #0f172a; color: #38bdf8; font-family: ui-monospace, Menlo, monospace; padding: 3px 6px; border-radius: 4px; font-size: 12px; display: inline-block; margin-bottom: 4px;">{tip.get('command')}</code>
      <div style="font-size: 12.5px; color: #334155;">{tip.get('use_case')}</div>
    </div>
    """

    full_html = f"""
    <!DOCTYPE html>
    <html>
    <head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1.0"></head>
    <body style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; background-color: #f3f4f6; margin: 0; padding: 18px;">
      <div style="max-width: 600px; margin: 0 auto; background-color: #ffffff; border-radius: 8px; overflow: hidden; border: 1px solid #e5e7eb;">
        
        <!-- Header -->
        <div style="background-color: #0f172a; padding: 24px 20px; color: #ffffff;">
          <div style="font-size: 10px; font-weight: 700; text-transform: uppercase; letter-spacing: 1.5px; color: #94a3b8; margin-bottom: 4px;">ENGINEERING EXECUTIVE BRIEFING</div>
          <div style="font-size: 20px; font-weight: 800; color: #ffffff; margin-bottom: 4px;">Morning Tech Pulse</div>
          <div style="font-size: 12px; color: #cbd5e1;">{today_str} • Prepared for Vivek Kanugula</div>
        </div>

        <!-- Content -->
        <div style="padding: 20px; background-color: #fafafa;">
          <div style="font-size: 11px; font-weight: 700; text-transform: uppercase; letter-spacing: 0.5px; color: #64748b; margin-bottom: 12px;">1. Core Technical Developments</div>
          {stories_html}
          {gem_html}
          {sd_html}
          {tip_html}

          <!-- PDF Notice -->
          <div style="background-color: #f1f5f9; border: 1px solid #cbd5e1; border-radius: 6px; padding: 10px 14px; text-align: center; margin-bottom: 14px;">
            <div style="font-size: 12.5px; color: #334155; font-weight: 600;">
              📎 <strong>Morning_Tech_Pulse.pdf</strong> is attached to this email for offline reading.
            </div>
          </div>

          <!-- Footer -->
          <div style="text-align: center; padding-top: 12px; border-top: 1px solid #e5e7eb; font-size: 11px; color: #94a3b8;">
            Curated autonomously via Groq Llama-3.3-70B • Zero compute cost
          </div>
        </div>

      </div>
    </body>
    </html>
    """
    return full_html


def dispatch_via_email(digest_data, pdf_path):
    """Deliver briefing + PDF document attachment via Gmail SMTP."""
    print("📧 [4/4] Delivering briefing and PDF via Gmail SMTP...")
    sender = os.getenv("SENDER_EMAIL")
    recipient = os.getenv("RECEIVER_EMAIL") or sender
    password = os.getenv("GMAIL_APP_PASSWORD")

    if not all([sender, password]):
        raise ValueError("SENDER_EMAIL and GMAIL_APP_PASSWORD must be configured!")

    today_str = datetime.date.today().strftime('%d %b %Y')
    first_topic = digest_data.get("top_stories", [{}])[0].get("headline", "Daily Briefing")
    subject = f"Morning Tech Pulse: {first_topic} [{today_str}]"

    msg = MIMEMultipart("mixed")
    msg["From"] = f"Morning Tech Pulse <{sender}>"
    msg["To"] = recipient
    msg["Subject"] = subject

    # Attach HTML
    html_content = build_email_html(digest_data)
    msg.attach(MIMEText(html_content, "html", "utf-8"))

    # Attach PDF
    if os.path.exists(pdf_path):
        with open(pdf_path, "rb") as f:
            pdf_attachment = MIMEApplication(f.read(), _subtype="pdf")
            pdf_attachment.add_header('Content-Disposition', 'attachment', filename="Morning_Tech_Pulse.pdf")
            msg.attach(pdf_attachment)

    clean_password = password.replace(" ", "")
    with smtplib.SMTP_SSL("smtp.gmail.com", 465, timeout=20) as server:
        server.login(sender, clean_password)
        server.sendmail(sender, [recipient], msg.as_string())

    print(f"🎉 Executive briefing with attached PDF delivered successfully to {recipient}!")


def main():
    print("=" * 60)
    print("🚀 Running Morning Tech Pulse Pipeline (Zero-Slop Standard)")
    print("=" * 60)

    stories, github_repos = fetch_raw_signals()
    digest_data = curate_with_groq(stories, github_repos)
    pdf_path = generate_pdf(digest_data)
    dispatch_via_email(digest_data, pdf_path)

    print("=" * 60)
    print("🏁 Pipeline execution finished cleanly.")
    print("=" * 60)

if __name__ == "__main__":
    main()
