import os
import re

import certifi

os.environ.setdefault("SSL_CERT_FILE", certifi.where())

import yt_dlp

URL_PATTERN = re.compile(
    r"https?://[^\s]*(facebook\.com|fb\.watch|instagram\.com)[^\s]*",
    re.IGNORECASE,
)

DOWNLOAD_DIR = os.path.join(os.path.expanduser("~"), "Downloads", "FB_IG_影片下載")


def extract_urls(text):
    return [line.strip() for line in text.splitlines() if line.strip()]


def download_one(url, log_fn):
    """log_fn(msg, replace_last=False) 會被呼叫來回報進度/結果。"""
    if not URL_PATTERN.search(url):
        log_fn(f"略過（不是 FB 或 IG 網址）：{url}")
        return

    os.makedirs(DOWNLOAD_DIR, exist_ok=True)

    def progress_hook(d):
        if d["status"] == "downloading":
            pct = d.get("_percent_str", "").strip()
            log_fn(f"下載中 {pct} ...", replace_last=True)
        elif d["status"] == "finished":
            log_fn("處理中（合併/轉檔）...", replace_last=True)

    ydl_opts = {
        "format": "best",
        "outtmpl": os.path.join(DOWNLOAD_DIR, "%(title).80s.%(ext)s"),
        "progress_hooks": [progress_hook],
        "quiet": True,
        "no_warnings": True,
        "noplaylist": True,
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            filename = ydl.prepare_filename(info)
        log_fn(f"完成：{os.path.basename(filename)}")
    except Exception as e:
        log_fn(f"失敗：{url}（{e}）")
