# FB / IG 影片下載工具

雙擊開啟的 macOS 桌面小程式，貼上 Facebook 或 Instagram 的公開影片網址（可一次貼多個，一行一個），按「開始下載」就會存到 `~/Downloads/FB_IG_影片下載/`。

底層都用 [yt-dlp](https://github.com/yt-dlp/yt-dlp) 處理實際下載，打包成不需要對方裝 Python 的 `.app`。有兩個版本，程式邏輯（`core.py`）共用：

| 版本 | 檔案 | 介面 |
|------|------|------|
| 桌面版 | `main.py` | tkinter 原生視窗 |
| 網頁版（推薦，介面較美觀） | `web_app.py` + `templates/index.html` | 本機網頁，雙擊開啟後自動跳出瀏覽器，有貓咪跑跑進度動畫 |

兩個版本都是「每個人在自己電腦上執行」，不是部署到網路上給任何人存取（那是完全不同量級的架構，見下方說明）。

## 開發 / 打包步驟

1. 建立虛擬環境並安裝套件：
   ```
   python3 -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   ```
2. 先直接執行測試：
   ```
   python main.py       # 桌面版
   python web_app.py    # 網頁版（會自動開瀏覽器 http://127.0.0.1:5111）
   ```
   貼幾個網址進去，確認能正常下載到 `~/Downloads/FB_IG_影片下載/`。
3. 打包成 App：
   ```
   # 桌面版
   pyinstaller --windowed --name "FBIGDownloader" main.py

   # 網頁版（要帶上 templates 資料夾）
   pyinstaller --windowed --name "FBIGWebDownloader" --add-data "templates:templates" web_app.py
   ```
   完成後分別在 `dist/FBIGDownloader.app`、`dist/FBIGWebDownloader.app`。
4. **簽章**：PyInstaller 打包中文名稱或含特定套件（curl_cffi 等）的 App 時，自動簽章常會失敗（`resource fork ... not allowed`），需要手動清除擴充屬性後重簽：
   ```
   xattr -cr dist/FBIGWebDownloader.app
   codesign --force --deep --sign - dist/FBIGWebDownloader.app
   ```
5. 打包完成的 `.app` 就可以直接給別人雙擊使用，不需要對方裝 Python。網頁版雙擊後會自動開瀏覽器；重複雙擊也沒關係，程式會偵測本機是否已經在跑，直接開新分頁而不會出錯。

## 已知限制

- **只支援 macOS**。iOS（iPhone/iPad）因 App Store 沙盒限制無法跑這類程式；若要 Windows 版，需在 Windows 機器上用同一份原始碼重新打包一次。
- 只支援**公開**影片，需要登入才能看的私人貼文/限時動態無法下載。
- 下載格式固定用 `best`（單一檔案、已包含影音），確保不需要對方電腦裝 ffmpeg 就能用；相對地畫質不一定是網站上的最高選項。
- 首次執行如果 macOS 跳出「無法驗證開發者」，需要到「系統設定 → 隱私權與安全性」允許執行，或按住 Control 點兩下開啟。
- yt-dlp 依賴各平台網頁結構，FB/IG 改版可能導致下載失效，屆時執行 `pip install -U yt-dlp` 更新後重新打包即可。
- 桌面版（tkinter）**Cmd+V 貼上快捷鍵在打包後的 App 裡不會作用**（macOS 上一個常見、目前沒找到根治方法的問題），改用右鍵（或兩指按 / Control+點擊）叫出貼上選單。網頁版因為是一般瀏覽器文字框，沒有這個問題。

## 如果之後想改成「大家開網址就能用」的公開網站

現在這兩個版本都是「本機執行」，只是介面不同。若要做成不需要任何安裝、任何人打開網址就能用的公開服務，需要：

- 租一台雲端伺服器（VPS，月費約 $5-20 美金起），把 `web_app.py` 部署上去
- 影片下載很吃頻寬，用量大的話頻寬費用會跟著漲
- 從「個人小工具」變成「公開服務」，需要考慮 FB/IG 平台使用條款與版權責任，也要處理維運（伺服器穩定性、被平台封鎖 IP 等）

這是完全不同量級的投入，先不在目前範圍內。
