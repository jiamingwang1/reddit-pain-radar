"""Pain Point Analyzer - AI分析Reddit帖子的痛点和商业机会"""
import os, json, sqlite3, time, re
from openai import OpenAI

ANALYSIS_PROMPT = """You are a JSON API that classifies Reddit posts. Return ONLY valid JSON, no explanation.

Classify this Reddit post:

Subreddit: r/{subreddit}
Title: {title}
Content: {selftext}
Upvotes: {score} | Comments: {num_comments}

Return this JSON structure:
{{
  "is_pain_point": true or false,
  "pain_score": 0-10,
  "pain_type": "frustration|request|complaint|question|rant|comparison|workaround",
  "category": "saas|devtools|automation|finance|health|productivity|ecommerce|other",
  "summary": "1-2 sentence English summary",
  "summary_zh": "1-2句中文摘要",
  "target_audience": "who posted this",
  "solution_idea": "what tool or service could help",
  "business_potential": "low|medium|high",
  "competition": "none|low|medium|high",
  "mvp_effort": "hours|days|weeks|months",
  "tags": ["keyword1", "keyword2"]
}}

Most posts score below 6. Only high scores for posts where someone clearly needs something that does not exist yet."""

class PainAnalyzer:
    def __init__(self, db_path="data/radar.db"):
        self.db_path = db_path
        self.client = OpenAI(
            api_key=os.getenv("AI_API_KEY", ""),
            base_url=os.getenv("AI_API_BASE", "https://ai.t8star.cn/v1")
        )
        self.model = os.getenv("AI_MODEL", "claude-sonnet-4-20250514")

    def analyze_post(self, post: dict) -> dict:
        prompt = ANALYSIS_PROMPT.format(
            subreddit=post.get("subreddit", ""),
            title=post.get("title", ""),
            selftext=(post.get("selftext", "") or "")[:2000],
            score=post.get("score", 0),
            num_comments=post.get("num_comments", 0)
        )
        try:
            resp = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are a JSON API. Return only valid JSON, no other text."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                max_tokens=800
            )
            text = resp.choices[0].message.content.strip()
            # 清理markdown包裹
            if "```" in text:
                m = re.search(r'```(?:json)?\s*\n?(.*?)\n?```', text, re.DOTALL)
                if m:
                    text = m.group(1).strip()
            # 兜底：提取第一个JSON对象
            if not text.startswith("{"):
                start = text.find("{")
                end = text.rfind("}")
                if start >= 0 and end > start:
                    text = text[start:end+1]
            result = json.loads(text)
        except Exception as e:
            return {"error": str(e), "is_pain_point": False, "pain_score": 0}

        self._save(post.get("id", ""), result)
        return result

    def _save(self, post_id: str, r: dict):
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("""UPDATE posts SET 
                    analyzed = 1,
                    pain_score = ?,
                    pain_type = ?,
                    business_potential = ?,
                    solution_idea = ?,
                    analysis = ?
                    WHERE id = ?""",
                    (r.get("pain_score", 0),
                     r.get("pain_type", ""),
                     r.get("business_potential", ""),
                     r.get("solution_idea", ""),
                     json.dumps(r),
                     post_id))
        except Exception:
            pass

    def analyze_unprocessed(self, limit=20, delay=1.0):
        """批量分析未处理帖子"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            rows = conn.execute(
                "SELECT * FROM posts WHERE analyzed = 0 LIMIT ?", (limit,)
            ).fetchall()
        results = []
        for row in rows:
            post = dict(row)
            result = self.analyze_post(post)
            results.append(result)
            time.sleep(delay)
        return results

    def get_top_opportunities(self, min_score: int = 6, limit: int = 20) -> list:
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            rows = conn.execute(
                """SELECT * FROM posts 
                   WHERE analyzed = 1 AND pain_score >= ?
                   ORDER BY pain_score DESC LIMIT ?""",
                (min_score, limit)
            ).fetchall()
            return [dict(r) for r in rows]


if __name__ == "__main__":
    analyzer = PainAnalyzer()
    print("PainAnalyzer initialized OK")
    print(f"Model: {analyzer.model}")
    print(f"API Base: {analyzer.client.base_url}")
