import os
import fitz # PyMuPDF

def generate_n8n_canvas_image(output_png_path):
    width = 1680
    height = 940

    nodes = {
        "schedule": {"x": 120, "y": 380, "title": "Daily Schedule", "sub": "07:30 AM Trigger", "icon": "clock", "color": "#0ea5e9"},
        "hn_ids": {"x": 420, "y": 270, "title": "Fetch HN Top IDs", "sub": "HTTP Request", "icon": "globe", "color": "#f97316"},
        "slice_ids": {"x": 700, "y": 270, "title": "Slice Top 8 Stories", "sub": "Code Node", "icon": "code", "color": "#8b5cf6"},
        "details": {"x": 980, "y": 270, "title": "Get Story Details", "sub": "HTTP Request", "icon": "globe", "color": "#f97316"},
        "gh_trending": {"x": 420, "y": 510, "title": "Fetch GitHub AI Repos", "sub": "Search API", "icon": "github", "color": "#10b981"},
        "aggregate": {"x": 1260, "y": 380, "title": "Aggregate Signals", "sub": "Signal Formatter", "icon": "merge", "color": "#6366f1"},
        "groq": {"x": 1260, "y": 640, "title": "Groq LPU Synthesis", "sub": "Zero-Slop AI Engine", "icon": "brain", "color": "#ec4899"},
        "email_body": {"x": 980, "y": 640, "title": "Build Notification", "sub": "HTML Formatter", "icon": "code", "color": "#8b5cf6"},
        "gmail": {"x": 700, "y": 640, "title": "Send Executive Brief", "sub": "Gmail SMTP Port 465", "icon": "mail", "color": "#ef4444"}
    }

    connections = [
        ("schedule", "hn_ids"),
        ("schedule", "gh_trending"),
        ("hn_ids", "slice_ids"),
        ("slice_ids", "details"),
        ("details", "aggregate"),
        ("gh_trending", "aggregate"),
        ("aggregate", "groq"),
        ("groq", "email_body"),
        ("email_body", "gmail")
    ]

    card_w = 210
    card_h = 76

    btn_x = int(width / 2 - 95)
    btn_y = height - 60

    svg_parts = []
    svg_parts.append(f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}" width="{width}" height="{height}">
    <defs>
      <!-- Shadow filter for node cards -->
      <filter id="cardShadow" x="-10%" y="-15%" width="125%" height="135%" filterUnits="userSpaceOnUse">
        <feDropShadow dx="0" dy="4" stdDeviation="6" flood-color="#0f172a" flood-opacity="0.08"/>
      </filter>
      <filter id="btnShadow" x="-15%" y="-20%" width="130%" height="150%" filterUnits="userSpaceOnUse">
        <feDropShadow dx="0" dy="3" stdDeviation="5" flood-color="#0f172a" flood-opacity="0.18"/>
      </filter>
    </defs>

    <!-- Browser Background -->
    <rect width="{width}" height="{height}" fill="#f8fafc"/>

    <!-- Browser Chrome Header Bar -->
    <rect width="{width}" height="44" fill="#ffffff" stroke="#e2e8f0" stroke-width="1"/>
    <circle cx="28" cy="22" r="6" fill="#ff5f56"/>
    <circle cx="48" cy="22" r="6" fill="#ffbd2e"/>
    <circle cx="68" cy="22" r="6" fill="#27c93f"/>

    <!-- Browser URL Bar -->
    <rect x="480" y="8" width="720" height="28" rx="6" fill="#f1f5f9" stroke="#e2e8f0" stroke-width="1"/>
    <text x="840" y="26" font-family="-apple-system, BlinkMacSystemFont, Segoe UI, Roboto, sans-serif" font-size="12" fill="#64748b" text-anchor="middle">http://localhost:5678/workflow/morning-tech-pulse-agent</text>

    <!-- n8n Workspace Top Bar -->
    <rect y="44" width="{width}" height="48" fill="#ffffff" stroke="#e2e8f0" stroke-width="1"/>
    <text x="28" y="74" font-family="-apple-system, BlinkMacSystemFont, Segoe UI, Roboto, sans-serif" font-size="13" font-weight="600" fill="#0f172a">Workflows</text>
    <text x="100" y="74" font-family="-apple-system, BlinkMacSystemFont, Segoe UI, Roboto, sans-serif" font-size="13" fill="#94a3b8">/</text>
    <text x="116" y="74" font-family="-apple-system, BlinkMacSystemFont, Segoe UI, Roboto, sans-serif" font-size="13" font-weight="700" fill="#0284c7">Daily Morning Tech Pulse &amp; System Design Agent</text>

    <!-- Active status badge -->
    <rect x="520" y="58" width="72" height="20" rx="10" fill="#dcfce7"/>
    <circle cx="532" cy="68" r="3.5" fill="#16a34a"/>
    <text x="543" y="72" font-family="-apple-system, BlinkMacSystemFont, Segoe UI, Roboto, sans-serif" font-size="10.5" font-weight="700" fill="#15803d">ACTIVE</text>

    <!-- Editor / Executions Tabs -->
    <rect x="750" y="54" width="180" height="28" rx="6" fill="#f1f5f9"/>
    <rect x="752" y="56" width="86" height="24" rx="5" fill="#ffffff"/>
    <text x="795" y="72" font-family="-apple-system, BlinkMacSystemFont, Segoe UI, Roboto, sans-serif" font-size="11.5" font-weight="600" fill="#0f172a" text-anchor="middle">Editor</text>
    <text x="882" y="72" font-family="-apple-system, BlinkMacSystemFont, Segoe UI, Roboto, sans-serif" font-size="11.5" font-weight="500" fill="#64748b" text-anchor="middle">Executions</text>

    <!-- Test workflow button -->
    <rect x="{width - 150}" y="54" width="124" height="28" rx="6" fill="#ff6d5a"/>
    <text x="{width - 88}" y="72" font-family="-apple-system, BlinkMacSystemFont, Segoe UI, Roboto, sans-serif" font-size="11.5" font-weight="700" fill="#ffffff" text-anchor="middle">Test Workflow</text>

    <!-- Canvas Dot Grid Background -->
    <rect y="92" width="{width}" height="{height - 92}" fill="#f8fafc"/>
''')

    # Add discrete dot grid via direct circles (PyMuPDF safe)
    dots_svg = []
    for gx in range(30, width - 20, 32):
        for gy in range(120, height - 20, 32):
            dots_svg.append(f'<circle cx="{gx}" cy="{gy}" r="1.5" fill="#cbd5e1" opacity="0.6"/>')
    svg_parts.append("".join(dots_svg))

    # Connecting wires (smooth bezier curves)
    for src_id, dst_id in connections:
        src = nodes[src_id]
        dst = nodes[dst_id]
        
        x1 = src["x"] + card_w
        y1 = src["y"] + card_h / 2
        x2 = dst["x"]
        y2 = dst["y"] + card_h / 2

        if x2 < x1:
            if src_id == "aggregate" and dst_id == "groq":
                d = f"M {x1} {y1} C {x1 + 90} {y1}, {dst['x'] + card_w + 90} {y2}, {dst['x'] + card_w} {y2}"
            else:
                x1_left = src["x"]
                x2_right = dst["x"] + card_w
                d = f"M {x1_left} {y1} C {x1_left - 70} {y1}, {x2_right + 70} {y2}, {x2_right} {y2}"
        else:
            dx = max(70, (x2 - x1) * 0.48)
            d = f"M {x1} {y1} C {x1 + dx} {y1}, {x2 - dx} {y2}, {x2} {y2}"

        svg_parts.append(f'''
        <path d="{d}" fill="none" stroke="#94a3b8" stroke-width="2.5" stroke-linecap="round"/>
        ''')

    # Draw Node Cards
    for node_id, n in nodes.items():
        x = n["x"]
        y = n["y"]
        color = n["color"]
        title = n["title"]
        sub = n["sub"]
        icon_type = n["icon"]

        icon_content = ""
        if icon_type == "clock":
            icon_content = '<circle cx="21" cy="21" r="10" fill="none" stroke="#ffffff" stroke-width="2"/><path d="M 21 16 L 21 21 L 25 23" fill="none" stroke="#ffffff" stroke-width="2" stroke-linecap="round"/>'
        elif icon_type == "globe":
            icon_content = '<circle cx="21" cy="21" r="10" fill="none" stroke="#ffffff" stroke-width="1.8"/><ellipse cx="21" cy="21" rx="5" ry="10" fill="none" stroke="#ffffff" stroke-width="1.8"/><line x1="11" y1="21" x2="31" y2="21" stroke="#ffffff" stroke-width="1.8"/>'
        elif icon_type == "code":
            icon_content = '<path d="M 17 16 L 12 21 L 17 26 M 25 16 L 30 21 L 25 26" fill="none" stroke="#ffffff" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>'
        elif icon_type == "github":
            icon_content = '<path d="M 21 12 A 9 9 0 0 0 18 29.5 C 18.5 29.6 18.7 29.3 18.7 29 L 18.7 27 C 16 27.5 15.5 25.8 15.5 25.8 C 15 24.6 14.3 24.3 14.3 24.3 C 13.5 23.7 14.4 23.7 14.4 23.7 C 15.3 23.8 15.8 24.6 15.8 24.6 C 16.6 26 18 25.6 18.5 25.4 C 18.6 24.8 18.8 24.4 19.1 24.1 C 17 23.9 14.7 23 14.7 19.3 C 14.7 18.2 15.1 17.4 15.7 16.7 C 15.6 16.5 15.3 15.4 15.8 14 C 15.8 14 16.7 13.7 18.7 15.1 C 19.5 14.9 20.4 14.8 21.3 14.8 C 22.2 14.8 23.1 14.9 23.9 15.1 C 25.9 13.7 26.8 14 26.8 14 C 27.3 15.4 27 16.5 26.9 16.7 C 27.5 17.4 27.9 18.2 27.9 19.3 C 27.9 23 25.6 23.9 23.5 24.1 C 23.8 24.4 24.1 25 24.1 26 L 24.1 29 C 24.1 29.3 24.3 29.6 24.8 29.5 A 9 9 0 0 0 21 12 Z" fill="#ffffff"/>'
        elif icon_type == "merge":
            icon_content = '<circle cx="16" cy="16" r="3" fill="#ffffff"/><circle cx="16" cy="26" r="3" fill="#ffffff"/><circle cx="26" cy="21" r="3" fill="#ffffff"/><path d="M 16 16 L 22 21 M 16 26 L 22 21" stroke="#ffffff" stroke-width="2"/>'
        elif icon_type == "brain":
            icon_content = '<path d="M 16 17 C 14 17 12 19 12 21 C 12 23 13.5 24.5 15 25 L 15 27 C 13.5 27 12 26 12 26 M 26 17 C 28 17 30 19 30 21 C 30 23 28.5 24.5 27 25 L 27 27 C 28.5 27 30 26 30 26 M 21 14 C 18 14 16 16 16 19 L 16 26 L 21 28 L 26 26 L 26 19 C 26 16 24 14 21 14 Z" fill="none" stroke="#ffffff" stroke-width="1.8"/>'
        elif icon_type == "mail":
            icon_content = '<rect x="11" y="14" width="20" height="14" rx="2" fill="none" stroke="#ffffff" stroke-width="1.8"/><path d="M 11 15 L 21 22 L 31 15" fill="none" stroke="#ffffff" stroke-width="1.8" stroke-linecap="round"/>'

        svg_parts.append(f'''
        <!-- Card: {title} -->
        <g id="node_{node_id}">
          <rect x="{x}" y="{y}" width="{card_w}" height="{card_h}" rx="8" fill="#ffffff" stroke="#e2e8f0" stroke-width="1.2" filter="url(#cardShadow)"/>
          
          <!-- Colored Icon Container -->
          <rect x="{x + 12}" y="{y + 17}" width="42" height="42" rx="7" fill="{color}"/>
          <g transform="translate({x + 12}, {y + 17})">
            {icon_content}
          </g>

          <!-- Text Labels -->
          <text x="{x + 64}" y="{y + 35}" font-family="-apple-system, BlinkMacSystemFont, Segoe UI, Roboto, sans-serif" font-size="12" font-weight="700" fill="#0f172a">{title}</text>
          <text x="{x + 64}" y="{y + 51}" font-family="-apple-system, BlinkMacSystemFont, Segoe UI, Roboto, sans-serif" font-size="10.5" font-weight="500" fill="#64748b">{sub}</text>

          <!-- Connection Handles -->
          <circle cx="{x}" cy="{y + card_h/2}" r="5" fill="#ffffff" stroke="#94a3b8" stroke-width="2"/>
          <circle cx="{x + card_w}" cy="{y + card_h/2}" r="5" fill="#0284c7" stroke="#ffffff" stroke-width="1.5"/>
        </g>
        ''')

    # Floating Bottom Controls (Execute button & Canvas controls)
    svg_parts.append(f'''
    <!-- Bottom Execute Button -->
    <g transform="translate({btn_x}, {btn_y})" filter="url(#btnShadow)">
      <rect width="190" height="42" rx="21" fill="#0f172a"/>
      <polygon points="42,16 42,26 52,21" fill="#ffffff"/>
      <text x="64" y="26" font-family="-apple-system, BlinkMacSystemFont, Segoe UI, Roboto, sans-serif" font-size="13" font-weight="700" fill="#ffffff">Execute Workflow</text>
    </g>

    <!-- Bottom Left Zoom Controls -->
    <g transform="translate(30, {height - 60})" filter="url(#btnShadow)">
      <rect width="110" height="36" rx="6" fill="#ffffff" stroke="#e2e8f0" stroke-width="1"/>
      <text x="24" y="23" font-family="-apple-system, BlinkMacSystemFont, Segoe UI, Roboto, sans-serif" font-size="16" fill="#475569" text-anchor="middle">-</text>
      <line x1="45" y1="6" x2="45" y2="30" stroke="#f1f5f9" stroke-width="1.5"/>
      <text x="56" y="22" font-family="-apple-system, BlinkMacSystemFont, Segoe UI, Roboto, sans-serif" font-size="11" fill="#64748b" text-anchor="middle">100%</text>
      <line x1="75" y1="6" x2="75" y2="30" stroke="#f1f5f9" stroke-width="1.5"/>
      <text x="93" y="23" font-family="-apple-system, BlinkMacSystemFont, Segoe UI, Roboto, sans-serif" font-size="16" fill="#475569" text-anchor="middle">+</text>
    </g>

    <!-- Right Side Toolbar -->
    <g transform="translate({width - 48}, 140)" filter="url(#btnShadow)">
      <rect width="36" height="150" rx="6" fill="#ffffff" stroke="#e2e8f0" stroke-width="1"/>
      <text x="18" y="32" font-family="-apple-system, BlinkMacSystemFont, Segoe UI, Roboto, sans-serif" font-size="18" fill="#64748b" text-anchor="middle">+</text>
      <circle cx="18" cy="65" r="7" fill="none" stroke="#64748b" stroke-width="1.8"/>
      <line x1="23" y1="70" x2="28" y2="75" stroke="#64748b" stroke-width="1.8"/>
      <rect x="12" y="98" width="12" height="12" rx="2" fill="none" stroke="#64748b" stroke-width="1.8"/>
      <line x1="12" y1="130" x2="24" y2="130" stroke="#64748b" stroke-width="1.8"/>
      <line x1="12" y1="135" x2="20" y2="135" stroke="#64748b" stroke-width="1.8"/>
    </g>

    </svg>''')

    svg_content = "".join(svg_parts)

    svg_path = output_png_path.replace(".png", ".svg")
    with open(svg_path, "w", encoding="utf-8") as f:
        f.write(svg_content)
    print(f"Saved SVG to {svg_path}")

    doc = fitz.open("svg", svg_content.encode("utf-8"))
    pix = doc[0].get_pixmap(dpi=150)
    pix.save(output_png_path)
    print(f"✅ Rendered high-res PNG to {output_png_path}")
    return output_png_path

if __name__ == "__main__":
    assets_dir = r"C:\Users\DHANUSH\.gemini\antigravity\scratch\morning-tech-pulse\assets"
    os.makedirs(assets_dir, exist_ok=True)
    out_png = os.path.join(assets_dir, "n8n_workflow_canvas.png")
    generate_n8n_canvas_image(out_png)

    artifact_dir = r"C:\Users\DHANUSH\.gemini\antigravity\brain\d76fee6a-950c-43b2-bf0e-24756e2da5b5"
    art_png = os.path.join(artifact_dir, "n8n_workflow_canvas.png")
    import shutil
    shutil.copy(out_png, art_png)
    print(f"Copied to {art_png}")
