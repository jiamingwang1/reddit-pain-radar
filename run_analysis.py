"""批量分析所有未处理帖子，高分自动推送Discord"""
import json, time, sqlite3, os, sys
sys.path.insert(0, os.path.dirname(__file__))

from analyzer.pain_analyzer import PainAnalyzer
from api.notifier import send_opportunity

p = PainAnalyzer()
WEBHOOK = os.getenv('DISCORD_WEBHOOK_URL', '')

total_analyzed = 0
total_pushed = 0
errors = 0

while True:
    with sqlite3.connect('data/radar.db') as conn:
        conn.row_factory = sqlite3.Row
        rows = conn.execute('SELECT * FROM posts WHERE analyzed=0 LIMIT 5').fetchall()
    if not rows:
        break
    for row in rows:
        post = dict(row)
        try:
            result = p.analyze_post(post)
            score = result.get('pain_score', 0)
            total_analyzed += 1
            print(f"[{total_analyzed}] [{score}/10] {result.get('summary_zh','')[:60]}", flush=True)
            if score >= 6 and WEBHOOK:
                try:
                    send_opportunity(post, result, WEBHOOK)
                    total_pushed += 1
                    print(f"  >>> Pushed to Discord!", flush=True)
                except:
                    pass
        except Exception as e:
            errors += 1
            print(f"[ERROR] {post.get('title','')[:40]}: {e}", flush=True)
            # Mark as analyzed to skip
            with sqlite3.connect('data/radar.db') as conn:
                conn.execute("UPDATE posts SET analyzed=1 WHERE id=?", (post['id'],))
                conn.commit()
        time.sleep(2)

print(f"\nDONE: {total_analyzed} analyzed, {total_pushed} pushed, {errors} errors", flush=True)
