# 開發日誌

## v1.0.0（2026-07-18）

首次發布，[GitHub Release](https://github.com/TeraChiu347/fb-ig-downloader/releases/tag/v1.0.0)。

### 功能

- 貼上 Facebook / Instagram 公開影片網址，一次可貼多個（一行一個），下載到 `~/Downloads/FB_IG_影片下載/`
- 底層用 [yt-dlp](https://github.com/yt-dlp/yt-dlp)，格式固定用 `best`（單一檔案含影音），不需要對方電腦裝 ffmpeg
- 兩個版本共用 `core.py` 的下載邏輯：
  - **桌面版**（`main.py`）：tkinter 原生視窗
  - **網頁版**（`web_app.py`）：本機 Flask 網頁，雙擊後自動跳出瀏覽器，有貓咪跑跑進度動畫 🐱→😻，完成/失敗會有「喵～」對話泡泡
- 兩者都打包成不需要對方裝 Python 的 macOS `.app`

### 開發過程中修掉的問題

- **SSL 憑證驗證失敗**：python.org 版 Python 沒跑過 `Install Certificates.command` 就會炸，改成程式內用 `certifi` 顯式指定 `SSL_CERT_FILE`，不依賴使用者環境
- **PyInstaller 打包後 codesign 失敗**（`resource fork ... not allowed`）：改用 `xattr -cr` 清除擴充屬性後手動 `codesign --sign -` 重簽
- **桌面版 Cmd+V 貼上沒作用**：tkinter 在 macOS 上沒有原生選單列時，Cmd+V 不會正確轉成貼上事件；試過手動綁定快捷鍵、加標準 Edit 選單，都沒有根治，最後改用右鍵/兩指按貼上選單（已確認可行），並在網頁版直接用瀏覽器原生文字框繞開這個問題
- **Gatekeeper 封鎖**：沒有 Apple 開發者公證，macOS 判定為有風險。「Control 點兩下開啟」在新版 macOS 上實測無效，改成「系統設定 → 隱私權與安全性 → 仍要打開」為主要教學方法，終端機 `xattr -cr` 為備案
- **重複雙擊跳出「應用程式並未打開」假錯誤**：網頁版偵測到本機已有實例在跑時，原本會秒開瀏覽器分頁後立刻結束程式；這種瞬間退出的行為在（尤其是因 Gatekeeper 而被 App Translocation 到隨機路徑執行的）情況下，會被 Finder 的 LaunchServices 誤判成啟動失敗。修法是改成開完瀏覽器後留在背景待命（idle loop），不要退出

### 部署

- 獨立開一個新的 git repo（跟主要業務專案的 monorepo 分開），public，避免把其他客戶專案一起公開
- 用 GitHub Release 附上打包好的 `.app` zip（兩個版本都有），朋友不需要自己 build，直接下載 Release 頁面的 Assets 即可
