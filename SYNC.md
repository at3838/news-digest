# 新聞總匯頁同步手冊（sync worker 必讀）

目的：將 Andrew 經 WhatsApp 收到嘅新聞 briefing，歸檔去新聞總匯頁
（repo：~/workspace/news-digest，公開頁：https://at3838.github.io/news-digest/）。
由 2026-11-02 起，之前嘅內容一律唔入。

## 固定規則（唔好違反）

- 絕對唔好改任何 briefing cron、唔好掂佢哋嘅 seen 檔、唔好喺 WhatsApp 度出聲。
  呢個同步只係讀 WhatsApp 對話、寫 news.json、rebuild、push。
- 只收新聞內容類 briefing（下面「入選」表）。數據類 briefing 見到都要跳過。
- 每則 item：標題、廣東話撮要（一至兩句，照送出嘅原文撮要，唔好自己重寫）、
  原文 link（briefing 有先寫，冇就寫 null，絕對唔好估 link）。
- 全文一律繁體廣東話口語，唔用簡體字、唔用普通話詞彙。
- 去重：同一日＋同一來源＋同一 URL 已經有就唔再入；冇 URL 嘅就用同一日＋
  同一來源＋同一標題去重。
- 成功就靜音（唔使向任何 chat 報告）；失敗先向 main chat 報告邊一步失敗、
  失敗前做到邊，唔好重複 push 同一批內容。

## 入選 briefing（新聞內容類）

- Benzinga 美股頭條（開市前／中午／收市後）
- Substack 熱門美股＋AI（開市／收市後）
- Reddit 熱門美股＋AI（開市／收市後）
- Threads 美股摘要、Threads AI 摘要
- Facebook 美股／AI 摘要
- X財經台（朝早／夜晚）
- TradingView 新聞摘要（中午／夜晚）
- 大行新報告撮要
- FT／FinGuider／Finimize／WSJ 即時推送（每篇獨立文章當一則）
- Gmail 股市信件每日摘要（每封信／每主題當一則；太長就撮做一至兩句）
- 美股老司機新一期（Terry Cheng，每期一則）
- YouTube 財經／科技 Podcast 摘要（每條片一則）
- 英國報章網站每日摘要
- 每週深度研究（星期一，一則）
- 突發財經新聞 alert（每則 alert 一則）
- 早晨簡報入面嘅新聞節（只取新聞部分）

## 唔入（數據類，見到即跳過）

美股觀察名單（中午／夜晚）、板塊資金流、財報跟進、期權資金流、
盤前異動、開盤預測、收盤復盤、TimesFM 預測、市場快照、國會議員交易、
公司內部人交易、Stifel 評級、13F filing、ETF flow、Gmail 安全警告、
BA 查價、天氣換衫、任何非新聞嘅系統訊息。
蔡天鳳案法庭更新都唔入（2026-11-02 Andrew 話 delete：案件本身有自己嘅
報道頁，唔歸入呢個財經＋科技新聞總匯）。

## 同步步驟

1. 讀 ~/workspace/news-digest/.sync-state.json，攞 watermark（ISO 倫敦時間）。
   第一轉 watermark 係 2026-11-02T00:00:00+00:00。
2. 用 chat.read_messages 讀 WhatsApp chat（chat_id
   3664266c-1bb4-449e-805d-a1d36af8e3d3），newest first，逐頁向後讀，
   直到訊息時間早過 watermark 為止。只取 role=assistant 且有實質 briefing
   內容嘅訊息；純 handoff、靜音轉、系統訊息全部跳過。
3. 按上面入選表抽 item，寫入 news.json 對應日期（倫敦日期）：
   每則 {date, source, briefing, title, summary, url}。
   source 用 briefing 來源名（例如 Benzinga、Threads、X財經台、TradingView、
   大行報告、FT、Substack、Reddit、YouTube、英國報章、蔡天鳳案）。
4. 更新 .sync-state.json 嘅 watermark 去今轉處理過嘅最新訊息時間；
   今轉冇新 briefing 就將 watermark 推到今轉開始時間。
5. 行 `python3 build.py`（喺 ~/workspace/news-digest 目錄），
   git add news.json index.html .sync-state.json，commit（訊息例如
   `news digest sync 2026-11-02 morning`），git push。
6. curl 驗證公開頁返 200 同埋有新日期嗰節，唔得就先唔好報成功，
   睇下係 Pages 傳播延遲（隔幾分鐘再驗）定真係 push 失敗。
