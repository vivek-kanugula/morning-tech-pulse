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

# Load local .env if available
load_dotenv()

def fetch_raw_signals():
    """Fetch live developer signals from Hacker News and GitHub APIs."""
    print("📡 [1/4] Fetching live data from Hacker News & GitHub APIs...")
    stories = []
    
    # 1. Fetch Top Hacker News Stories
    try:
        hn_top_ids = requests.get("https://hacker-news.firebaseio.com/v0/topstories.json", timeout=10).json()[:10]
        for item_id in hn_top_ids:
            try:
                item_data = requests.get(f"https://hacker-news.firebaseio.com/v0/item/{item_id}.json", timeout=5).json()
                if item_data and "title" in item_data and item_data.get("type") == "story":
                    stories.append({
                        "title": item_data["title"],
                        "url": item_data.get("url", f"https://news.ycombinator.com/item?id={item_id}"),
                        "score": item_data.get("score", 0),
                        "source": "Hacker News"
                    })
            except Exception:
                continue
    except Exception as e:
        print(f"⚠️ Warning: HN fetch failed: {e}")

    # 2. Fetch Trending GitHub Repositories
    github_repos = []
    try:
        week_ago = (datetime.date.today() - datetime.timedelta(days=7)).isoformat()
        gh_url = f"https://api.github.com/search/repositories?q=stars:>150+pushed:>{week_ago}&sort=stars&order=desc&per_page=5"
        headers = {"User-Agent": "MorningTechPulseAgent/1.0"}
        gh_resp = requests.get(gh_url, headers=headers, timeout=10).json()
        for repo in gh_resp.get("items", []):
            github_repos.append({
                "name": repo["full_name"],
                "description": repo.get("description") or "Open source tool",
                "stars": repo.get("stargazers_count", 0),
                "url": repo["html_url"],
                "language": repo.get("language") or "General"
            })
    except Exception as e:
        print(f"⚠️ Warning: GitHub fetch failed: {e}")

    print(f"✅ Collected {len(stories)} HN stories and {len(github_repos)} trending repositories.")
    return stories, github_repos


def curate_with_groq(stories, github_repos):
    """Call Groq Llama-3.3-70B to synthesize news, System Design card, GitHub gem, and terminal tip."""
    print("🧠 [2/4] Synthesizing intelligence with Groq Llama-3.3-70B...")
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        raise ValueError("GROQ_API_KEY environment variable is missing!")

    client = Groq(api_key=api_key)

    system_prompt = """You are a Senior Staff Software Engineer and System Architect preparing the daily 'Morning Tech Pulse' brief for ambitious engineers.
Your task is to produce a structured, high-signal technical digest. Filter out clickbait, crypto marketing, and generic announcements.

You must return a strictly valid JSON object with the following schema:
{
  "top_stories": [
    {
      "headline": "Clear, concise title",
      "summary": "2-sentence technical summary of what was released or changed.",
      "why_it_matters": "Architectural, performance, or developer workflow impact.",
      "category": "AI / Systems / Cloud / OpenSource",
      "url": "original link"
    }
  ],
  "github_gem": {
    "repo_name": "owner/repo",
    "description": "What it does in 1 punchy sentence.",
    "quickstart": "Terminal install or run command (e.g. pip install ... or docker run ...)",
    "practical_use": "Why an engineer should use this today.",
    "url": "https://github.com/..."
  },
  "system_design_card": {
    "topic": "Name of System Design Concept (e.g. Consistent Hashing, Bloom Filters, Raft Consensus, Write-Ahead Logs)",
    "core_problem": "The distributed systems problem it solves in 1 sentence.",
    "how_it_works": [
      "Key bullet 1 explaining the mechanism",
      "Key bullet 2 explaining trade-off (latency vs consistency, etc.)"
    ],
    "real_world_case": "How a company like Netflix, Discord, Uber, or Meta uses it."
  },
  "terminal_tip": {
    "command": "git or bash or docker 1-liner command",
    "explanation": "What it does and why it saves time."
  }
}
Select 3 top technical breakthroughs from the provided Hacker News stories, pick 1 top repo from the GitHub list for the gem, and provide a fresh System Design card and terminal power-tip."""

    user_content = json.dumps({
        "raw_stories": stories[:8],
        "github_candidates": github_repos
    })

    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_content}
        ],
        response_format={"type": "json_object"},
        temperature=0.2
    )

    data = json.loads(response.choices[0].message.content)
    print("✅ AI Curation complete.")
    return data


def generate_pdf(digest_data, output_filename="Morning_Tech_Pulse.pdf"):
    """Compile the curated content into an elegant, high-contrast PDF using ReportLab."""
    print(f"📄 [3/4] Generating PDF report ({output_filename})...")
    doc = SimpleDocTemplate(
        output_filename,
        pagesize=letter,
        leftMargin=36,
        rightMargin=36,
        topMargin=36,
        bottomMargin=36
    )

    styles = getSampleStyleSheet()

    # Custom styles
    title_style = ParagraphStyle(
        'DocTitle',
        parent=styles['Heading1'],
        fontName='Helvetica-Bold',
        fontSize=20,
        leading=24,
        textColor=colors.HexColor('#0f172a')
    )
    subtitle_style = ParagraphStyle(
        'DocSubtitle',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=10,
        leading=14,
        textColor=colors.HexColor('#2563eb')
    )
    meta_style = ParagraphStyle(
        'DocMeta',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=9,
        leading=12,
        textColor=colors.HexColor('#64748b')
    )
    section_h1 = ParagraphStyle(
        'SectionH1',
        parent=styles['Heading2'],
        fontName='Helvetica-Bold',
        fontSize=13,
        leading=16,
        textColor=colors.HexColor('#0f172a'),
        spaceBefore=10,
        spaceAfter=6
    )
    card_title = ParagraphStyle(
        'CardTitle',
        parent=styles['Heading3'],
        fontName='Helvetica-Bold',
        fontSize=11,
        leading=14,
        textColor=colors.HexColor('#1e293b')
    )
    body_text = ParagraphStyle(
        'BodyTextCustom',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=9.5,
        leading=13.5,
        textColor=colors.HexColor('#334155')
    )
    why_it_matters_text = ParagraphStyle(
        'WhyItMatters',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=9,
        leading=13,
        textColor=colors.HexColor('#1e40af')
    )
    code_text = ParagraphStyle(
        'CodeSnippet',
        parent=styles['Normal'],
        fontName='Courier-Bold',
        fontSize=9,
        leading=12,
        textColor=colors.HexColor('#0f172a')
    )

    story = []
    today_str = datetime.date.today().strftime('%A, %d %B %Y')

    # Header Banner Table
    header_data = [
        [
            Paragraph("⚡ MORNING TECH PULSE", title_style),
            Paragraph(f"<b>{today_str}</b><br/><font color='#64748b'>3-Min Executive Read</font>", ParagraphStyle('HRight', parent=meta_style, alignment=2))
        ]
    ]
    header_table = Table(header_data, colWidths=[360, 180])
    header_table.setStyle(TableStyle([
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('BOTTOMPADDING', (0,0), (-1,-1), 0),
        ('TOPPADDING', (0,0), (-1,-1), 0),
    ]))
    story.append(header_table)
    story.append(Spacer(1, 4))
    story.append(Paragraph("AUTONOMOUS DEVELOPER INTELLIGENCE & SYSTEM DESIGN BRIEFING", subtitle_style))
    story.append(Spacer(1, 8))
    story.append(HRFlowable(width="100%", thickness=1.5, color=colors.HexColor('#0f172a'), spaceBefore=2, spaceAfter=10))

    # SECTION 1: Top Engineering Breakthroughs
    story.append(Paragraph("📰 1. TOP ENGINEERING BREAKTHROUGHS", section_h1))
    for idx, item in enumerate(digest_data.get("top_stories", [])[:3], 1):
        cat = item.get("category", "Tech")
        headline = item.get("headline", "News Item")
        summary = item.get("summary", "")
        why = item.get("why_it_matters", "")
        url = item.get("url", "")

        story_block = [
            Paragraph(f"<b>{idx}. [{cat}] {headline}</b>", card_title),
            Spacer(1, 2),
            Paragraph(summary, body_text),
            Spacer(1, 2),
            Paragraph(f"💡 <b>Why It Matters:</b> {why} <font color='#2563eb'>(<a href='{url}'><u>Read Source</u></a>)</font>", why_it_matters_text),
            Spacer(1, 6)
        ]
        story.extend(story_block)

    story.append(HRFlowable(width="100%", thickness=0.5, color=colors.HexColor('#cbd5e1'), spaceBefore=6, spaceAfter=8))

    # SECTION 2: GitHub Open-Source Gem
    gem = digest_data.get("github_gem", {})
    if gem:
        story.append(Paragraph("🛠️ 2. GITHUB GEM OF THE DAY", section_h1))
        gem_content = [
            Paragraph(f"<b>Repo:</b> <font color='#2563eb'><b>{gem.get('repo_name')}</b></font> &nbsp;•&nbsp; <a href='{gem.get('url')}'><u>GitHub Link</u></a>", card_title),
            Spacer(1, 2),
            Paragraph(gem.get("description", ""), body_text),
            Spacer(1, 3),
            Paragraph(f"<b>Quickstart:</b> <font face='Courier'><code>{gem.get('quickstart', '')}</code></font>", body_text),
            Spacer(1, 2),
            Paragraph(f"<b>Why Use It:</b> {gem.get('practical_use', '')}", body_text),
        ]
        gem_table = Table([[gem_content]], colWidths=[540])
        gem_table.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,-1), colors.HexColor('#f8fafc')),
            ('BOX', (0,0), (-1,-1), 1, colors.HexColor('#e2e8f0')),
            ('TOPPADDING', (0,0), (-1,-1), 8),
            ('BOTTOMPADDING', (0,0), (-1,-1), 8),
            ('LEFTPADDING', (0,0), (-1,-1), 10),
            ('RIGHTPADDING', (0,0), (-1,-1), 10),
        ]))
        story.append(gem_table)
        story.append(Spacer(1, 8))

    story.append(HRFlowable(width="100%", thickness=0.5, color=colors.HexColor('#cbd5e1'), spaceBefore=4, spaceAfter=8))

    # SECTION 3: System Design Micro-Card
    sd = digest_data.get("system_design_card", {})
    if sd:
        story.append(Paragraph("🧠 3. SYSTEM DESIGN MICRO-CARD", section_h1))
        bullets_text = "<br/>".join([f"• {b}" for b in sd.get("how_it_works", [])])
        sd_content = [
            Paragraph(f"<b>Concept: {sd.get('topic', 'Distributed Architecture')}</b>", card_title),
            Spacer(1, 2),
            Paragraph(f"<b>The Problem:</b> {sd.get('core_problem', '')}", body_text),
            Spacer(1, 2),
            Paragraph(bullets_text, body_text),
            Spacer(1, 2),
            Paragraph(f"<b>🏢 Production Case Study:</b> {sd.get('real_world_case', '')}", why_it_matters_text),
        ]
        sd_table = Table([[sd_content]], colWidths=[540])
        sd_table.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,-1), colors.HexColor('#eff6ff')),
            ('BOX', (0,0), (-1,-1), 1, colors.HexColor('#bfdbfe')),
            ('TOPPADDING', (0,0), (-1,-1), 8),
            ('BOTTOMPADDING', (0,0), (-1,-1), 8),
            ('LEFTPADDING', (0,0), (-1,-1), 10),
            ('RIGHTPADDING', (0,0), (-1,-1), 10),
        ]))
        story.append(sd_table)
        story.append(Spacer(1, 8))

    # SECTION 4: Terminal Power-Tip
    tip = digest_data.get("terminal_tip", {})
    if tip:
        story.append(Paragraph("💡 4. TERMINAL & GIT POWER-TIP", section_h1))
        tip_content = [
            Paragraph(f"<b>Command:</b> <font color='#0f172a'><code>{tip.get('command', '')}</code></font>", code_text),
            Spacer(1, 2),
            Paragraph(f"<b>Usage:</b> {tip.get('explanation', '')}", body_text)
        ]
        tip_table = Table([[tip_content]], colWidths=[540])
        tip_table.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,-1), colors.HexColor('#f1f5f9')),
            ('BOX', (0,0), (-1,-1), 1, colors.HexColor('#cbd5e1')),
            ('TOPPADDING', (0,0), (-1,-1), 6),
            ('BOTTOMPADDING', (0,0), (-1,-1), 6),
            ('LEFTPADDING', (0,0), (-1,-1), 10),
            ('RIGHTPADDING', (0,0), (-1,-1), 10),
        ]))
        story.append(tip_table)
        story.append(Spacer(1, 10))

    # Footer
    story.append(HRFlowable(width="100%", thickness=0.5, color=colors.HexColor('#e2e8f0'), spaceBefore=4, spaceAfter=6))
    story.append(Paragraph(
        "⚡ Generated autonomously by <b>Morning Tech Pulse</b> • Powered by Groq Llama-3.3-70B • GitHub Actions CI/CD ($0 Compute Cost)",
        meta_style
    ))

    doc.build(story)
    print("✅ PDF generated successfully.")
    return output_filename


def build_email_html(digest_data):
    """Build clean, modern responsive HTML email body with high contrast cards."""
    today_str = datetime.date.today().strftime('%A, %d %B %Y')
    
    # Story cards
    cards_html = ""
    for item in digest_data.get("top_stories", [])[:3]:
        cat = item.get("category", "Tech")
        cards_html += f"""
        <div style="background-color: #ffffff; border: 1px solid #e2e8f0; border-radius: 8px; padding: 18px; margin-bottom: 16px;">
          <span style="display: inline-block; background-color: #eff6ff; color: #1d4ed8; font-size: 11px; font-weight: 700; text-transform: uppercase; padding: 3px 8px; border-radius: 4px; margin-bottom: 8px;">{cat}</span>
          <h2 style="margin: 0 0 8px 0; font-size: 17px; color: #0f172a; font-weight: 700;">
            <a href="{item.get('url', '#')}" style="color: #0f172a; text-decoration: none;">{item.get('headline')}</a>
          </h2>
          <p style="margin: 0 0 10px 0; font-size: 14px; color: #334155; line-height: 1.5;">{item.get('summary')}</p>
          <div style="background-color: #f8fafc; border-left: 3px solid #2563eb; padding: 8px 12px;">
            <p style="margin: 0; font-size: 13px; color: #1e3a8a; font-weight: 600;">💡 <strong>Why It Matters:</strong> {item.get('why_it_matters')}</p>
          </div>
        </div>
        """

    # GitHub Gem
    gem = digest_data.get("github_gem", {})
    gem_html = f"""
    <div style="background-color: #f8fafc; border: 1px solid #e2e8f0; border-radius: 8px; padding: 16px; margin-bottom: 16px;">
      <h3 style="margin: 0 0 6px 0; font-size: 14px; text-transform: uppercase; letter-spacing: 0.5px; color: #2563eb;">🛠️ GitHub Gem of the Day</h3>
      <p style="margin: 0 0 6px 0; font-size: 15px; font-weight: 700; color: #0f172a;">
        <a href="{gem.get('url', '#')}" style="color: #2563eb; text-decoration: none;">{gem.get('repo_name')}</a>
      </p>
      <p style="margin: 0 0 8px 0; font-size: 13px; color: #475569;">{gem.get('description')}</p>
      <div style="background-color: #0f172a; color: #38bdf8; font-family: monospace; padding: 6px 10px; border-radius: 4px; font-size: 12px; margin-bottom: 6px;">
        {gem.get('quickstart')}
      </div>
      <p style="margin: 0; font-size: 12px; color: #64748b;"><strong>Why Use It:</strong> {gem.get('practical_use')}</p>
    </div>
    """

    # System Design Card
    sd = digest_data.get("system_design_card", {})
    bullets = "".join([f"<li style='margin-bottom: 4px;'>{b}</li>" for b in sd.get("how_it_works", [])])
    sd_html = f"""
    <div style="background-color: #eff6ff; border: 1px solid #bfdbfe; border-radius: 8px; padding: 16px; margin-bottom: 16px;">
      <h3 style="margin: 0 0 6px 0; font-size: 14px; text-transform: uppercase; letter-spacing: 0.5px; color: #1d4ed8;">🧠 System Design Micro-Card</h3>
      <p style="margin: 0 0 6px 0; font-size: 15px; font-weight: 700; color: #1e3a8a;">{sd.get('topic')}</p>
      <p style="margin: 0 0 8px 0; font-size: 13px; color: #1e40af;"><strong>Problem:</strong> {sd.get('core_problem')}</p>
      <ul style="margin: 0 0 8px 0; padding-left: 20px; font-size: 13px; color: #1e293b;">
        {bullets}
      </ul>
      <p style="margin: 0; font-size: 12px; color: #1d4ed8;"><strong>🏢 Case Study:</strong> {sd.get('real_world_case')}</p>
    </div>
    """

    # Terminal Tip
    tip = digest_data.get("terminal_tip", {})
    tip_html = f"""
    <div style="background-color: #f1f5f9; border: 1px solid #cbd5e1; border-radius: 8px; padding: 14px; margin-bottom: 20px;">
      <h3 style="margin: 0 0 4px 0; font-size: 13px; text-transform: uppercase; letter-spacing: 0.5px; color: #475569;">💡 Terminal Power-Tip</h3>
      <code style="background-color: #0f172a; color: #a5f3fc; padding: 4px 8px; border-radius: 4px; font-size: 12px; font-weight: bold; display: inline-block; margin-bottom: 6px;">{tip.get('command')}</code>
      <p style="margin: 0; font-size: 13px; color: #334155;">{tip.get('explanation')}</p>
    </div>
    """

    full_html = f"""
    <!DOCTYPE html>
    <html>
    <head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1.0"></head>
    <body style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; background-color: #f3f4f6; margin: 0; padding: 20px;">
      <div style="max-width: 620px; margin: 0 auto; background-color: #ffffff; border-radius: 12px; overflow: hidden; border: 1px solid #e2e8f0; box-shadow: 0 4px 6px -1px rgba(0,0,0,0.05);">
        
        <!-- Header Banner -->
        <div style="background: linear-gradient(135deg, #0f172a 0%, #1e293b 100%); padding: 30px 24px; color: #ffffff;">
          <p style="margin: 0 0 6px 0; font-size: 11px; text-transform: uppercase; letter-spacing: 1.5px; color: #38bdf8;">⚡ Autonomous Developer Intelligence</p>
          <h1 style="margin: 0 0 6px 0; font-size: 24px; font-weight: 800; color: #ffffff;">Morning Tech Pulse</h1>
          <p style="margin: 0; font-size: 13px; color: #94a3b8;">{today_str} • 3-Min Executive Briefing</p>
        </div>

        <!-- Body Content -->
        <div style="padding: 24px; background-color: #f8fafc;">
          <h3 style="margin: 0 0 14px 0; font-size: 14px; text-transform: uppercase; letter-spacing: 0.5px; color: #64748b;">📰 Top Engineering Breakthroughs</h3>
          {cards_html}
          {gem_html}
          {sd_html}
          {tip_html}

          <!-- PDF Notice -->
          <div style="background-color: #fefce8; border: 1px solid #fef08a; border-radius: 8px; padding: 12px; text-align: center; margin-bottom: 16px;">
            <p style="margin: 0; font-size: 13px; color: #854d0e; font-weight: 600;">
              📎 <strong>Morning_Tech_Pulse.pdf</strong> is attached to this email for offline reading!
            </p>
          </div>

          <!-- Footer -->
          <div style="text-align: center; padding-top: 16px; border-top: 1px solid #e2e8f0; font-size: 11px; color: #64748b;">
            <p style="margin: 0 0 4px 0;">Curated autonomously by your <strong>Morning Tech Pulse Agent</strong>.</p>
            <p style="margin: 0;">Powered by <strong>Groq Llama-3.3-70B</strong> • GitHub Actions CI/CD ($0 Compute Cost)</p>
          </div>
        </div>

      </div>
    </body>
    </html>
    """
    return full_html


def dispatch_via_email(digest_data, pdf_path):
    """Send clean, responsive HTML briefing + PDF document attachment via Gmail SMTP."""
    print("📧 [4/4] Dispatching briefing & PDF via Email...")
    sender = os.getenv("SENDER_EMAIL")
    recipient = os.getenv("RECEIVER_EMAIL") or sender
    password = os.getenv("GMAIL_APP_PASSWORD")

    if not all([sender, password]):
        print("⚠️ Email credentials missing in environment variables.")
        print("Required: SENDER_EMAIL, GMAIL_APP_PASSWORD (and optionally RECEIVER_EMAIL)")
        return

    today_str = datetime.date.today().strftime('%d %b %Y')
    top_story = digest_data.get("top_stories", [{}])[0].get("headline", "Daily Briefing")
    subject = f"☕ Morning Tech Pulse: {top_story} [{today_str}]"

    # Create MIME message
    msg = MIMEMultipart("mixed")
    msg["From"] = f"Morning Tech Pulse <{sender}>"
    msg["To"] = recipient
    msg["Subject"] = subject

    # Attach HTML Body
    html_content = build_email_html(digest_data)
    msg.attach(MIMEText(html_content, "html", "utf-8"))

    # Attach PDF Document
    if os.path.exists(pdf_path):
        with open(pdf_path, "rb") as f:
            pdf_attachment = MIMEApplication(f.read(), _subtype="pdf")
            pdf_attachment.add_header('Content-Disposition', 'attachment', filename="Morning_Tech_Pulse.pdf")
            msg.attach(pdf_attachment)
            print("📎 PDF attached to email.")

    # Send via Gmail SMTP (SSL on port 465)
    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465, timeout=20) as server:
            # Remove any accidental spaces in app password
            clean_password = password.replace(" ", "")
            server.login(sender, clean_password)
            server.sendmail(sender, [recipient], msg.as_string())
        print(f"🎉 Email with attached PDF successfully delivered to {recipient}!")
    except Exception as e:
        print(f"❌ SMTP delivery failed: {e}")


def main():
    print("=" * 60)
    print("🚀 Morning Tech Pulse: Autonomous Daily Intelligence Agent")
    print("=" * 60)

    # Step 1: Collect Raw Signals
    stories, github_repos = fetch_raw_signals()

    # Step 2: Groq Llama-3.3-70B Synthesis
    digest_data = curate_with_groq(stories, github_repos)

    # Step 3: PDF Compilation
    pdf_path = generate_pdf(digest_data)

    # Step 4: Dispatch via Email with HTML + PDF Attachment
    dispatch_via_email(digest_data, pdf_path)

    print("=" * 60)
    print("🏁 Daily Run Completed Successfully!")
    print("=" * 60)

if __name__ == "__main__":
    main()
