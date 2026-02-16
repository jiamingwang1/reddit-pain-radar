"""Reddit Scanner - fetches posts from target subreddits"""
import praw
import json
import os
import time
import sqlite3
from datetime import datetime, timezone

# Alternative: use requests directly if praw auth fails
import requests

class RedditScanner:
    def __init__(self, db_path="data/radar.db"):
        self.db_path = db_path
        self._init_db()
        
        # Try PRAW first, fallback to public JSON API
        self.use_praw = False
        client_id = os.getenv("REDDIT_CLIENT_ID", "")
        if client_id:
            try:
                self.reddit = praw.Reddit(
                    client_id=client_id,
                    client_secret=os.getenv("REDDIT_CLIENT_SECRET", ""),
                    user_agent=os.getenv("REDDIT_USER_AGENT", "RedditPainRadar/1.0")
                )
                self.use_praw = True
            except:
                pass
    
    def _init_db(self):
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        conn = sqlite3.connect(self.db_path)
        conn.execute("""CREATE TABLE IF NOT EXISTS posts (
            id TEXT PRIMARY KEY,
            subreddit TEXT,
            title TEXT,
            selftext TEXT,
            url TEXT,
            score INTEGER,
            num_comments INTEGER,
            created_utc REAL,
            fetched_at TEXT,
            analyzed INTEGER DEFAULT 0,
            pain_score REAL DEFAULT 0,
            pain_type TEXT DEFAULT '',
            business_potential TEXT DEFAULT '',
            analysis TEXT DEFAULT '',
            solution_idea TEXT DEFAULT ''
        )""")
        conn.execute("""CREATE TABLE IF NOT EXISTS scan_config (
            id INTEGER PRIMARY KEY,
            subreddits TEXT,
            keywords TEXT,
            last_scan TEXT
        )""")
        # Insert default config if empty
        cur = conn.execute("SELECT COUNT(*) FROM scan_config")
        if cur.fetchone()[0] == 0:
            default_subs = json.dumps([
                "SaaS", "startups", "smallbusiness", "Entrepreneur",
                "webdev", "artificial", "ChatGPT", "freelance",
                "nocode", "automation", "indiehackers"
            ])
            default_keywords = json.dumps([
                "I wish", "I need", "pain point", "looking for",
                "anyone know", "hate", "frustrated", "problem",
                "struggling", "help me", "alternative to",
                "why isn't there", "someone should build"
            ])
            conn.execute(
                "INSERT INTO scan_config (subreddits, keywords, last_scan) VALUES (?, ?, ?)",
                (default_subs, default_keywords, "")
            )
        conn.commit()
        conn.close()
    
    def scan_subreddit_web(self, subreddit, sort="hot", limit=25):
        """Fetch posts using web search (fallback when Reddit blocks direct access)"""
        # Use Brave search to find recent Reddit posts
        posts = []
        # This will be called from the main app which has web_search access
        return posts
    
    def scan_subreddit_praw(self, subreddit, sort="hot", limit=25):
        """Fetch posts using PRAW"""
        posts = []
        try:
            sub = self.reddit.subreddit(subreddit)
            if sort == "hot":
                submissions = sub.hot(limit=limit)
            elif sort == "new":
                submissions = sub.new(limit=limit)
            elif sort == "top":
                submissions = sub.top(time_filter="week", limit=limit)
            else:
                submissions = sub.hot(limit=limit)
            
            for s in submissions:
                posts.append({
                    "id": s.id,
                    "subreddit": subreddit,
                    "title": s.title,
                    "selftext": s.selftext[:2000] if s.selftext else "",
                    "url": f"https://www.reddit.com{s.permalink}",
                    "score": s.score,
                    "num_comments": s.num_comments,
                    "created_utc": s.created_utc
                })
        except Exception as e:
            print(f"Error scanning r/{subreddit}: {e}")
        return posts
    
    def scan_subreddit_json(self, subreddit, sort="hot", limit=25):
        """Fetch posts using Reddit JSON API (no auth needed)"""
        posts = []
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
        url = f"https://www.reddit.com/r/{subreddit}/{sort}.json?limit={limit}"
        proxy = os.getenv("PROXY_URL", "socks5h://14abcd07338e1:d19f419c72@175.29.206.191:12324")
        proxies = {"http": proxy, "https": proxy} if proxy else None
        
        try:
            resp = requests.get(url, headers=headers, proxies=proxies, timeout=15)
            if resp.status_code == 200:
                data = resp.json()
                for child in data.get("data", {}).get("children", []):
                    d = child.get("data", {})
                    posts.append({
                        "id": d.get("id", ""),
                        "subreddit": subreddit,
                        "title": d.get("title", ""),
                        "selftext": d.get("selftext", "")[:2000],
                        "url": f"https://www.reddit.com{d.get('permalink', '')}",
                        "score": d.get("score", 0),
                        "num_comments": d.get("num_comments", 0),
                        "created_utc": d.get("created_utc", 0)
                    })
            else:
                print(f"Reddit JSON API returned {resp.status_code} for r/{subreddit}")
        except Exception as e:
            print(f"Error fetching r/{subreddit}: {e}")
        return posts
    
    def scan_all(self, limit=25):
        """Scan all configured subreddits"""
        conn = sqlite3.connect(self.db_path)
        cur = conn.execute("SELECT subreddits FROM scan_config WHERE id=1")
        row = cur.fetchone()
        subreddits = json.loads(row[0]) if row else []
        
        total_new = 0
        for sub in subreddits:
            if self.use_praw:
                posts = self.scan_subreddit_praw(sub, limit=limit)
            else:
                posts = self.scan_subreddit_json(sub, limit=limit)
            
            for p in posts:
                try:
                    conn.execute(
                        """INSERT OR IGNORE INTO posts 
                        (id, subreddit, title, selftext, url, score, num_comments, created_utc, fetched_at)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                        (p["id"], p["subreddit"], p["title"], p["selftext"],
                         p["url"], p["score"], p["num_comments"], p["created_utc"],
                         datetime.now(timezone.utc).isoformat())
                    )
                    if conn.total_changes:
                        total_new += 1
                except:
                    pass
            
            time.sleep(2)  # Rate limit
        
        conn.execute(
            "UPDATE scan_config SET last_scan=? WHERE id=1",
            (datetime.now(timezone.utc).isoformat(),)
        )
        conn.commit()
        conn.close()
        return total_new


if __name__ == "__main__":
    scanner = RedditScanner()
    new = scanner.scan_all(limit=10)
    print(f"Fetched {new} new posts")
