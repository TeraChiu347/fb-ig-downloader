import sys
import threading
import tkinter as tk
from tkinter import messagebox

from core import DOWNLOAD_DIR, download_one, extract_urls

IS_MAC = sys.platform == "darwin"
IS_WINDOWS = sys.platform.startswith("win")


def bind_mac_edit_shortcuts(root):
    """PyInstaller 打包後的 Tk App 沒有原生選單列，macOS 有時不會把 Cmd+C/V/X/A
    轉成 Tk 的 <<Copy>>/<<Paste>>/<<Cut>>/選取全部事件，這裡手動補上對應綁定。"""

    def handler(virtual_event, select_all=False):
        def _handle(event):
            widget = event.widget
            if select_all:
                if isinstance(widget, tk.Text):
                    widget.tag_add("sel", "1.0", "end")
                elif isinstance(widget, tk.Entry):
                    widget.select_range(0, "end")
            else:
                widget.event_generate(virtual_event)
            return "break"

        return _handle

    root.bind_class("Text", "<Command-c>", handler("<<Copy>>"))
    root.bind_class("Text", "<Command-v>", handler("<<Paste>>"))
    root.bind_class("Text", "<Command-x>", handler("<<Cut>>"))
    root.bind_class("Text", "<Command-a>", handler(None, select_all=True))
    root.bind_class("Entry", "<Command-c>", handler("<<Copy>>"))
    root.bind_class("Entry", "<Command-v>", handler("<<Paste>>"))
    root.bind_class("Entry", "<Command-x>", handler("<<Cut>>"))
    root.bind_class("Entry", "<Command-a>", handler(None, select_all=True))


def add_paste_context_menu(widget):
    menu = tk.Menu(widget, tearoff=0)
    menu.add_command(label="剪下", command=lambda: widget.event_generate("<<Cut>>"))
    menu.add_command(label="複製", command=lambda: widget.event_generate("<<Copy>>"))
    menu.add_command(label="貼上", command=lambda: widget.event_generate("<<Paste>>"))

    def show_menu(event):
        menu.tk_popup(event.x_root, event.y_root)

    widget.bind("<Button-2>", show_menu)
    widget.bind("<Control-Button-1>", show_menu)


class App:
    def __init__(self, root):
        self.root = root
        root.title("FB / IG 影片下載工具")
        root.geometry("520x460")
        root.resizable(False, False)

        if IS_MAC:
            bind_mac_edit_shortcuts(root)
            self._add_edit_menu(root)

        tk.Label(
            root,
            text="貼上 Facebook 或 Instagram 影片網址（一行一個，可貼多個）",
            font=("Microsoft JhengHei", 12),
        ).pack(pady=(10, 4))

        self.url_box = tk.Text(root, height=6)
        self.url_box.pack(fill="x", padx=10)
        add_paste_context_menu(self.url_box)

        self.download_btn = tk.Button(root, text="開始下載", command=self.start_download)
        self.download_btn.pack(pady=8)

        tk.Label(root, text=f"儲存位置：{DOWNLOAD_DIR}", fg="#666").pack()

        self.log = tk.Text(root, height=14, state="disabled")
        self.log.pack(fill="both", expand=True, padx=10, pady=10)

        self._last_line_is_progress = False

    def _add_edit_menu(self, root):
        """加上標準 Edit 選單（macOS Aqua 對 name='edit' 的選單有特殊處理，
        有了它系統才會把 Cmd+X/C/V/A 正確路由給焦點所在的文字框）。"""
        menubar = tk.Menu(root)
        edit_menu = tk.Menu(menubar, name="edit", tearoff=0)
        edit_menu.add_command(
            label="剪下", accelerator="Cmd+X",
            command=lambda: root.focus_get().event_generate("<<Cut>>"),
        )
        edit_menu.add_command(
            label="複製", accelerator="Cmd+C",
            command=lambda: root.focus_get().event_generate("<<Copy>>"),
        )
        edit_menu.add_command(
            label="貼上", accelerator="Cmd+V",
            command=lambda: root.focus_get().event_generate("<<Paste>>"),
        )
        menubar.add_cascade(label="Edit", menu=edit_menu)
        root.config(menu=menubar)

    def log_msg(self, msg, replace_last=False):
        def _update():
            self.log.config(state="normal")
            if replace_last and self._last_line_is_progress:
                self.log.delete("end-2l", "end-1l")
            self.log.insert("end", msg + "\n")
            self.log.see("end")
            self.log.config(state="disabled")
            self._last_line_is_progress = replace_last

        self.root.after(0, _update)

    def start_download(self):
        text = self.url_box.get("1.0", "end")
        urls = extract_urls(text)
        if not urls:
            messagebox.showinfo("提示", "請先貼上至少一個網址")
            return
        self.download_btn.config(state="disabled")
        threading.Thread(target=self.run_downloads, args=(urls,), daemon=True).start()

    def run_downloads(self, urls):
        for url in urls:
            self.log_msg(f"開始下載：{url}")
            download_one(url, self.log_msg)
        self.log_msg("全部完成！")
        self.root.after(0, lambda: self.download_btn.config(state="normal"))


def main():
    root = tk.Tk()
    App(root)
    root.mainloop()


if __name__ == "__main__":
    main()
