# 新聞總匯頁同步手冊（sync worker 必讀）

目的：將 Andrew 經 WhatsApp 收到嘅新聞 briefing，歸檔去新聞總匯頁
（repo：~/workspace/news-digest，公開頁：https://at3838.github.io/news-digest/）。
由 2026-11-02 起，之前嘅內容一律唔入。同步每 15 分鐘跑一轉，務求
WhatsApp 一收到新聞，頁面 15 分鐘內就出到；冇新 briefing 嘅轉靜默，
只推 watermark，唔好出聲。

## 頁面排序（2026-11-02 Andrew 親口定）

- 日由新到舊；同一日入面，來源組按最遲嗰則嘅 time 由新到舊排（即係當日最遲
  嗰份 briefing 排第一）；組入面同時間嘅則保持 briefing 原來次序，唔同時段
  嘅則新嗰轉行先。冇 time 嘅則排最後。呢個排序由 build.py 做，同步唔使理。

## 固定規則（唔好違反）

- 絕對唔好改任何 briefing cron、唔好掂佢哋嘅 seen 檔、唔好喺 WhatsApp 度出聲。
  呢個同步只係讀 WhatsApp 對話、寫 news.json、rebuild、push。
- 只收新聞內容類 briefing（下面「入選」表）。數據類 briefing 見到都要跳過。
- 每則 item：標題、廣東話撮要（一至兩句，照送出嘅原文撮要，唔好自己重寫）、
  原文 link（briefing 有先寫，冇就寫 null，絕對唔好估 link）。
- 每則 item 一定要有 time 欄：該 briefing 經 WhatsApp 送到嗰陣嘅倫敦時間，
  格式 HH:MM（例如 07:05）。注意：呢個係 WhatsApp 送達時間，唔係原文刊登
  時間（briefing 入面多數冇刊登時間，唔好估）。
- 補時間：news.json 入面已有但冇 time 嘅 item，根據佢哋來源 briefing 當日
  嘅 WhatsApp 送達時間補返 time（同一來源同一日有多轉嘅，盡量按標題對返
  嗰一轉；對唔返就用當日該 briefing 最近嗰轉嘅時間，並喺嗰則 summary
  尾加「（時間約數）」註明）。
- 去重：同一日＋同一來源＋同一 URL 已經有就唔再入；冇 URL 嘅就用同一日＋
  同一來源＋同一標題去重。
- 來源名要跟上面入選表一字不差（例如 Gmail 一律寫「Gmail 股市信件」，
  有空格）；舊寫法（冇空格嗰個）由 build.py 嘅 SOURCE_ALIASES 自動歸一，
  但新入嘅一律用正名，唔好再靠歸一。
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
   每則 {date, source, briefing, title, summary, url, time}，
   time 係該 briefing 嘅 WhatsApp 送達倫敦時間 HH:MM。
   source 用 briefing 來源名（例如 Benzinga、Threads、X財經台、TradingView、
   大行報告、FT、Substack、Reddit、YouTube、英國報章、蔡天鳳案）。
4. 更新 .sync-state.json 嘅 watermark 去今轉處理過嘅最新訊息時間；
   今轉冇新 briefing 就將 watermark 推到今轉開始時間。
5. 行 `python3 build.py`（喺 ~/workspace/news-digest 目錄），
   git add news.json index.html .sync-state.json，commit（訊息例如
   `news digest sync 2026-11-02 morning`），git push。
6. curl 驗證公開頁返 200 同埋有新日期嗰節，唔得就先唔好報成功，
   睇下係 Pages 傳播延遲（隔幾分鐘再驗）定真係 push 失敗。

## 親手同步規則（2026-11-02 Andrew 決定）
- 助手喺 WhatsApp 親手送出 briefing 嗰陣，順手將該 briefing 嘅 item 入 news.json、行 build.py、git commit＋push，唔使等 15 分鐘嗰轉。
- 每次親手同步都要將 .sync-state.json 嘅 watermark 推到該 briefing 送達時間之後，等 15 分鐘嗰支同步唔會重複入多次。
- 15 分鐘同步 cron 留返做後備：萬一邊轉漏咗親手同步，佢會補返。
