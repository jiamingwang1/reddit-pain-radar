"""Reddit Pain Radar - Main Application"""
import os
import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from dotenv import load_dotenv

load_dotenv()

from scanner.reddit_scanner import RedditScanner
from analyzer.pain_analyzer import PainAnalyzer
from api.notifier import Notifier

app = FastAPI(title="Reddit Pain Radar", version="0.1.0")

DB_PATH = "data/radar.db"
scanner = RedditScanner(db_path=DB_PATH)
analyzer = PainAnalyzer(db_path=DB_PATH)
notifier = Notifier()

@app.get("/", response_class=HTMLResponse)
async def dashboard():
    """Main dashboard"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    
    # Stats
    total = conn.execute("SELECT COUNT(*) FROM posts").fetchone()[0]
    analyzed = conn.execute("SELECT COUNT(*) FROM posts WHERE analyzed=1").fetchone()[0]
    pain_points = conn.execute("SELECT COUNT(*) FROM posts WHERE pain_score >= 6").fetchone()[0]
    
    # Top opportunities
    opps = conn.execute(
        """SELECT * FROM posts WHERE analyzed=1 AND pain_score >= 6 
        ORDER BY pain_score DESC, score DESC LIMIT 20"""
    ).fetchall()
    
    # Recent scans
    config = conn.execute("SELECT * FROM scan_config WHERE id=1").fetchone()
    last_scan = config["last_scan"] if config else "Never"
    subreddits = json.loads(config["subreddits"]) if config else []
    
    conn.close()
    
    opp_rows = ""
    for o in opps:
        try:
            analysis = json.loads(o["analysis"]) if o["analysis"] else {}
        except:
            analysis = {}
        
        biz_color = {"high": "#22c55e", "medium": "#eab308", "low": "#ef4444"}.get(
            o["business_potential"], "#666"
        )
        
        opp_rows += f"""
        <tr>
            <td><span class="pain-score">{o['pain_score']:.0f}</span></td>
            <td>r/{o['subreddit']}</td>
            <td><a href="{o['url']}" target="_blank">{o['title'][:80]}</a></td>
            <td>{analysis.get('summary', '')[:100]}</td>
            <td>{o['solution_idea'][:100] if o['solution_idea'] else ''}</td>
            <td style="color:{biz_color};font-weight:bold">{o['business_potential']}</td>
            <td>👍{o['score']} 💬{o['num_comments']}</td>
        </tr>"""
    
    html = f"""<!DOCTYPE html>
<html><head>
<title>Reddit Pain Radar ⚡</title>
<style>
    * {{ margin: 0; padding: 0; box-sizing: border-box; }}
    body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; 
            background: #0f172a; color: #e2e8f0; padding: 20px; }}
    .header {{ display: flex; justify-content: space-between; align-items: center; margin-bottom: 30px; }}
    h1 {{ color: #f59e0b; font-size: 28px; }}
    .stats {{ display: flex; gap: 20px; }}
    .stat {{ background: #1e293b; padding: 15px 25px; border-radius: 12px; text-align: center; }}
    .stat-num {{ font-size: 32px; font-weight: bold; color: #f59e0b; }}
    .stat-label {{ color: #94a3b8; font-size: 13px; }}
    .controls {{ margin: 20px 0; display: flex; gap: 10px; }}
    .btn {{ background: #f59e0b; color: #0f172a; border: none; padding: 10px 20px; 
            border-radius: 8px; cursor: pointer; font-weight: bold; font-size: 14px; }}
    .btn:hover {{ background: #d97706; }}
    .btn-secondary {{ background: #334155; color: #e2e8f0; }}
    table {{ width: 100%; border-collapse: collapse; margin-top: 20px; }}
    th {{ background: #1e293b; padding: 12px; text-align: left; color: #94a3b8; font-size: 13px; }}
    td {{ padding: 12px; border-bottom: 1px solid #1e293b; font-size: 14px; }}
    tr:hover {{ background: #1e293b; }}
    a {{ color: #60a5fa; text-decoration: none; }}
    a:hover {{ text-decoration: underline; }}
    .pain-score {{ background: #dc2626; color: white; padding: 4px 10px; border-radius: 20px; 
                   font-weight: bold; font-size: 13px; }}
    .meta {{ color: #64748b; font-size: 12px; margin-top: 10px; }}
    .subreddits {{ color: #94a3b8; font-size: 13px; }}
</style>
</head><body>
<div class="header">
    <div>
        <h1>⚡ Reddit Pain Radar</h1>
        <p class="subreddits">Scanning: {', '.join(f'r/{s}' for s in subreddits[:8])}</p>
        <p class="meta">Last scan: {last_scan or 'Never'}</p>
    </div>
    <div class="stats">
        <div class="stat"><div class="stat-num">{total}</div><div class="stat-label">Posts Scanned</div></div>
        <div class="stat"><div class="stat-num">{analyzed}</div><div class="stat-label">Analyzed</div></div>
        <div class="stat"><div class="stat-num">{pain_points}</div><div class="stat-label">Opportunities</div></div>
    </div>
</div>

<div class="controls">
    <button class="btn" onclick="runScan()">🔍 Scan Now</button>
    <button class="btn btn-secondary" onclick="runAnalyze()">🧠 Analyze</button>
    <button class="btn btn-secondary" onclick="location.reload()">🔄 Refresh</button>
</div>

<table>
<thead><tr>
    <th>Pain</th><th>Sub</th><th>Post</th><th>Pain Point</th><th>Solution Idea</th><th>Biz</th><th>Engagement</th>
</tr></thead>
<tbody>{opp_rows if opp_rows else '<tr><td colspan="7" style="text-align:center;color:#64748b;padding:40px">No opportunities found yet. Click "Scan Now" then "Analyze" to start!</td></tr>'}</tbody>
</table>

<script>
async function runScan() {{
    const btn = event.target;
    btn.textContent = '⏳ Scanning...';
    btn.disabled = true;
    try {{
        const resp = await fetch('/api/scan', {{method: 'POST'}});
        const data = await resp.json();
        alert(`Scan complete! Found ${{data.new_posts}} new posts`);
    }} catch(e) {{ alert('Scan failed: ' + e); }}
    btn.textContent = '🔍 Scan Now';
    btn.disabled = false;
    location.reload();
}}
async function runAnalyze() {{
    const btn = event.target;
    btn.textContent = '⏳ Analyzing...';
    btn.disabled = true;
    try {{
        const resp = await fetch('/api/analyze', {{method: 'POST'}});
        const data = await resp.json();
        alert(`Analyzed ${{data.analyzed}} posts, found ${{data.opportunities}} opportunities`);
    }} catch(e) {{ alert('Analysis failed: ' + e); }}
    btn.textContent = '🧠 Analyze';
    btn.disabled = false;
    location.reload();
}}
</script>
</body></html>"""
    return HTMLResponse(html)

@app.post("/api/scan")
async def api_scan():
    """Trigger a Reddit scan"""
    new_posts = scanner.scan_all(limit=25)
    return {"status": "ok", "new_posts": new_posts}

@app.post("/api/analyze")
async def api_analyze():
    """Analyze unprocessed posts"""
    count, opps = analyzer.analyze_unprocessed(limit=20)
    return {"status": "ok", "analyzed": count, "opportunities": len(opps)}

@app.get("/api/opportunities")
async def api_opportunities(limit: int = 20):
    """Get top opportunities as JSON"""
    opps = analyzer.get_top_opportunities(limit=limit)
    return opps

@app.get("/api/stats")
async def api_stats():
    """Get scan stats"""
    conn = sqlite3.connect(DB_PATH)
    total = conn.execute("SELECT COUNT(*) FROM posts").fetchone()[0]
    analyzed = conn.execute("SELECT COUNT(*) FROM posts WHERE analyzed=1").fetchone()[0]
    pain = conn.execute("SELECT COUNT(*) FROM posts WHERE pain_score >= 6").fetchone()[0]
    conn.close()
    return {"total_posts": total, "analyzed": analyzed, "opportunities": pain}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=int(os.getenv("PORT", 8081)))
