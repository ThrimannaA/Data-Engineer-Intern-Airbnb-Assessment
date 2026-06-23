# simple_assumptions_convert.py
import markdown
from pathlib import Path

def create_html():
    md_path = Path('reports/assumptions.md')
    html_path = Path('reports/assumptions.html')
    
    with open(md_path, 'r', encoding='utf-8') as f:
        md_content = f.read()
    
    html_content = markdown.markdown(md_content, extensions=['tables', 'fenced_code'])
    
    styled = f"""
    <!DOCTYPE html>
    <html>
    <head><meta charset="UTF-8">
    <style>
        body {{ font-family: Times New Roman; margin: 1in; line-height: 1.6; }}
        h1 {{ color: #FF5A5F; border-bottom: 2px solid #FF5A5F; }}
        table {{ border-collapse: collapse; width: 100%; margin: 10px 0; }}
        th, td {{ border: 1px solid #ddd; padding: 8px; }}
        th {{ background-color: #FF5A5F; color: white; }}
    </style>
    </head>
    <body>{html_content}</body>
    </html>
    """
    
    with open(html_path, 'w', encoding='utf-8') as f:
        f.write(styled)
    
    print(f"✅ HTML created: {html_path}")
    print("📌 Open in browser and File → Print → Save as PDF")

if __name__ == "__main__":
    create_html()