import os
import queue
import socket
import sys
import threading
import time
import webbrowser

from flask import Flask, Response, render_template, request

from core import DOWNLOAD_DIR, download_one, extract_urls

if getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS"):
    _BASE_DIR = sys._MEIPASS
else:
    _BASE_DIR = os.path.dirname(os.path.abspath(__file__))

app = Flask(__name__, template_folder=os.path.join(_BASE_DIR, "templates"))

HOST = "127.0.0.1"
PORT = 5111


@app.route("/")
def index():
    return render_template("index.html", download_dir=DOWNLOAD_DIR)


@app.route("/download", methods=["POST"])
def download():
    urls = extract_urls(request.get_json(force=True).get("text", ""))

    def generate():
        if not urls:
            yield "請先貼上至少一個網址\n"
            return
        for url in urls:
            yield f"開始下載：{url}\n"
            q = queue.Queue()
            result_holder = {}
            last_emit = [0.0]

            def log_fn(msg, replace_last=False):
                now = time.time()
                # 進度訊息每 0.3 秒才轉發一次，避免洗版
                if replace_last and now - last_emit[0] < 0.3:
                    return
                last_emit[0] = now
                q.put((msg, replace_last))

            def worker():
                download_one(url, log_fn)
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
        yield "全部完成！\n"

    return Response(generate(), mimetype="text/plain")


def open_browser():
    time.sleep(0.8)
    webbrowser.open(f"http://{HOST}:{PORT}")


def _port_in_use():
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        return sock.connect_ex((HOST, PORT)) == 0
    finally:
        sock.close()


def main():
    if _port_in_use():
        # 已經有一個實例在跑（例如使用者重複雙擊開啟），開新分頁就好。
        # 開完不能馬上結束行程——.app 秒退會被 Finder 的 LaunchServices
        # 誤判成「應用程式並未打開」而跳出錯誤視窗，所以在這裡靜靜待著。
        webbrowser.open(f"http://{HOST}:{PORT}")
        while True:
            time.sleep(3600)
    threading.Thread(target=open_browser, daemon=True).start()
    app.run(host=HOST, port=PORT, debug=False)


if __name__ == "__main__":
    main()
