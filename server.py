import os
import queue
import secrets
import shutil
import tempfile
import threading
import time

from flask import Flask, Response, after_this_request, render_template, request, send_file

from core import download_one, extract_urls

app = Flask(__name__)

TEMP_ROOT = os.path.join(tempfile.gettempdir(), "fbig_downloads")
FILE_TTL_SECONDS = 30 * 60

_files_lock = threading.Lock()
_files = {}  # token -> {"path": str, "dir": str, "created": float}


def _register_file(path, tmp_dir):
    token = secrets.token_urlsafe(16)
    with _files_lock:
        _files[token] = {"path": path, "dir": tmp_dir, "created": time.time()}
    return token


def _pop_file(token):
    with _files_lock:
        return _files.pop(token, None)


def _cleanup_loop():
    while True:
        time.sleep(300)
        now = time.time()
        with _files_lock:
            expired = [t for t, v in _files.items() if now - v["created"] > FILE_TTL_SECONDS]
            for t in expired:
                entry = _files.pop(t)
                shutil.rmtree(entry["dir"], ignore_errors=True)


_cleanup_started = False


def _ensure_cleanup_thread():
    global _cleanup_started
    if not _cleanup_started:
        os.makedirs(TEMP_ROOT, exist_ok=True)
        threading.Thread(target=_cleanup_loop, daemon=True).start()
        _cleanup_started = True


_ensure_cleanup_thread()


@app.route("/")
def index():
    return render_template("server_index.html")


@app.route("/download", methods=["POST"])
def download():
    urls = extract_urls(request.get_json(force=True).get("text", ""))

    def generate():
        if not urls:
            yield "請先貼上至少一個網址\n"
            return
        for url in urls:
            yield f"開始下載：{url}\n"
            tmp_dir = tempfile.mkdtemp(dir=TEMP_ROOT)
            q = queue.Queue()
            result_holder = {}
            last_emit = [0.0]

            def log_fn(msg, replace_last=False):
                now = time.time()
                if replace_last and now - last_emit[0] < 0.3:
                    return
                last_emit[0] = now
                q.put((msg, replace_last))

            def worker():
                result_holder["path"] = download_one(url, log_fn, output_dir=tmp_dir)
                result_holder["done"] = True

            t = threading.Thread(target=worker, daemon=True)
            t.start()
            while not result_holder.get("done") or not q.empty():
                try:
                    msg, replace_last = q.get(timeout=0.2)
                    prefix = "\r" if replace_last else ""
                    yield f"{prefix}{msg}\n"
                except queue.Empty:
                    continue

            path = result_holder.get("path")
            if path:
                token = _register_file(path, tmp_dir)
                yield f"READY:{token}:{os.path.basename(path)}\n"
            else:
                shutil.rmtree(tmp_dir, ignore_errors=True)
        yield "全部完成！\n"

    return Response(generate(), mimetype="text/plain")


@app.route("/file/<token>")
def file(token):
    entry = _pop_file(token)
    if not entry:
        return "下載連結已過期或已被下載過，請重新下載一次影片。", 404

    @after_this_request
    def _cleanup(response):
        shutil.rmtree(entry["dir"], ignore_errors=True)
        return response

    return send_file(entry["path"], as_attachment=True, download_name=os.path.basename(entry["path"]))


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5111)), debug=False)
