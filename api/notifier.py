"""Discord Webhook推送 - 高分痛点自动通知"""
import os, json, requests

WEBHOOK_URL = os.getenv("DISCORD_WEBHOOK_URL", "")

def send_opportunity(post: dict, analysis: dict, webhook_url: str = None):
    url = webhook_url or WEBHOOK_URL
    if not url:
        return False

    score = analysis.get("pain_score", 0)
    color = 0xFF0000 if score >= 8 else 0xFF8C00 if score >= 6 else 0x00FF00

    embed = {
        "title": f"🔥 [{score}/10] {post.get('title', 'No title')[:200]}",
        "url": post.get("url", ""),
        "color": color,
        "fields": [
            {"name": "📌 痛点类型", "value": analysis.get("pain_type", "N/A"), "inline": True},
            {"name": "📂 分类", "value": analysis.get("category", "N/A"), "inline": True},
            {"name": "💰 商业潜力", "value": analysis.get("business_potential", "N/A"), "inline": True},
            {"name": "🎯 目标用户", "value": analysis.get("target_audience", "N/A")[:200], "inline": False},
            {"name": "💡 解决方案", "value": analysis.get("solution_idea", "N/A")[:200], "inline": False},
            {"name": "⚔️ 竞争", "value": analysis.get("competition", "N/A"), "inline": True},
            {"name": "⏱️ MVP耗时", "value": analysis.get("mvp_effort", "N/A"), "inline": True},
            {"name": "📝 摘要", "value": analysis.get("summary_zh", analysis.get("summary", "N/A"))[:300], "inline": False},
        ],
        "footer": {"text": f"r/{post.get('subreddit', '?')} | 👍 {post.get('score', 0)} | 💬 {post.get('num_comments', 0)}"}
    }

    payload = {
        "username": "Reddit Pain Radar ⚡",
        "embeds": [embed]
    }

    try:
        resp = requests.post(url, json=payload, timeout=10)
        return resp.status_code in (200, 204)
    except Exception:
        return False


def notify_batch(posts_with_analysis: list, min_score: int = 6, webhook_url: str = None):
    """批量推送高分痛点"""
    sent = 0
    for item in posts_with_analysis:
        post = item.get("post", item)
        analysis = item.get("analysis", {})
        if not analysis:
            try:
                analysis = json.loads(post.get("analysis", "{}"))
            except:
                analysis = {}
        if analysis.get("pain_score", 0) >= min_score:
            if send_opportunity(post, analysis, webhook_url):
                sent += 1
    return sent
