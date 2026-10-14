# 这个文件夹只有截图

这里是早期剪出来的 6 条轨迹加秘书精选图，一共 221 张 jpg。没有 agent 的思考，没有工具返回，也没有「为什么选这道题」。

完整材料和给孙秋实的说明在：

`/Users/zhangyingying/Desktop/mobilegym-mock-tooluse/docs/不要上传-修bug/正式论文写作/incoming/2026-09-29-arxiv放出前/给孙秋实-先读.md`

轨迹文件在同级压缩包：

`/Users/zhangyingying/Desktop/mobilegym-mock-tooluse/docs/不要上传-修bug/正式论文写作/incoming/2026-09-29-arxiv放出前/mobilegympp-demo-materials-v2.zip`

压缩包里每一步都有 `step_NNN_response.txt`（思考和工具调用）、`step_NNN_result.json`（工具返回）、`step_NNN_prompt.json`，不只是 jpg。另外有仓库怎么打开、215 题单、应用名单，以及 case74、case73 的只点屏幕对照。说明在压缩包里的 `01-仓库和产物在哪.md`。

下面仍是这个截图文件夹自己的目录说明。

---

# MobileGym++ Demo Materials / 演示素材

Website demo pack for MobileGym++.  
Contact: [contact TBD]

本包供项目网站使用。联系方式：[contact TBD]

---

## 中文

### 项目简介

MobileGym++ 是首个将手机 App 原生工具调用（hybrid mode）与 GUI 操作结合的移动端 agent 评测环境，支持 63 款 App，其中 35 款为新商业 App（含淘宝、淘宝闪购、小红书、哔哩哔哩等）。

Agent 在同一条轨迹里既可以调用 App 提供的结构化工具（例如搜索、加购、发消息），也可以像人一样点击、滑动、输入。下面每条轨迹都是 hybrid 模式：既有原生工具调用，也有 GUI 操作。

### 案例一览

模型均为 **Gemini 3.1 Pro Preview**（`gemini-3.1-pro-preview`）。  
「Tool Calls」一列是 **App 原生工具**的调用次数与顺序，不含每步都可能出现的 GUI 动作 `mobile_use`。步数（Steps）含 GUI 与工具调用。

| 目录名 | 模型 | Task | Apps | Steps | Tool Calls | 指令（中文） |
| --- | --- | --- | --- | --- | --- | --- |
| `v5-hybrid_tbsg_notes_pantry` | Gemini 3.1 Pro Preview | HTV5Case74 | notes, tbsg（笔记、淘宝闪购） | 28 | 9：`tbsg__get_cart` → `tbsg__search_shops` → `tbsg__get_shop_menu` → `tbsg__search_items` → `tbsg__add_item_to_cart` ×2 → `tbsg__search_shops` → `tbsg__search_items` → `tbsg__add_item_to_cart` | 按笔记（Notes）App 中“Office pantry”列出的缺货补齐独立的淘宝闪购 App 购物车，每种只加一件；不要进入淘宝 App 内的闪购入口，不要加入清单之外的商品，也不要结算或下单。 |
| `v5-hybrid_redbook_wechat_ranking` | Gemini 3.1 Pro Preview | HTV5Case29 | redbook, wechat（小红书、微信） | 22 | 10：`redbook__search_notes` → `redbook__open_user` → `redbook__search_notes` → `redbook__open_user` → `redbook__search_notes` → `redbook__search_users` → `redbook__search_notes` ×2 → `wechat__search_contacts` → `wechat__send_text_message` | 在小红书搜索“旅行”，把前 10 篇帖子中点赞最多的一个帖子的作者主页发过的收藏最多的帖子的标题和这个作者的昵称和获赞与收藏数微信发给“陈静”。 |
| `v5-hybrid_map_weather_wechat` | Gemini 3.1 Pro Preview | HTV5Case37 | map, weather, wechat（地图、天气、微信） | 18 | 6：`map__search_places` → `weather__get_current_weather` → `weather__search_cities` → `weather__get_current_weather` → `wechat__search_contacts` → `wechat__send_text_message` | 在地图中查询中国国家博物馆显示的完整详细地址，并查询该地址所在城市的当前天气，把地址、天气和温度一起微信发给陈静。 |
| `v5-hybrid_spotify_playlist` | Gemini 3.1 Pro Preview | HTV5Case38 | spotify | 13 | 6：`spotify__search_tracks` → `spotify__add_to_playlist` ×2 → `spotify__search_tracks` → `spotify__add_to_playlist` ×2 | 新建歌单《双艺人精选》，搜索周杰伦和林俊杰，恰好各加入 2 首歌，不加入其他歌曲，然后播放这个歌单。 |
| `v5-hybrid_taobao_purchase` | Gemini 3.1 Pro Preview | HTV5Case70 | taobao（淘宝） | 12 | 1：`taobao__open_search_results`（其余为 GUI：选商品、下单、支付） | 搜索「清风山」，购买「清风山 山雾香氛护手霜 75mL 保湿滋润 生日礼物」并完成支付（数量 1，规格默认）。 |
| `v4_tbsg_notes_pantry_v4` | Gemini 3.1 Pro Preview | HTV4Case74 | notes, tbsg（笔记、淘宝闪购） | 13 | 6：`tbsg__search_items` → `tbsg__add_item_to_cart` → `tbsg__search_items` → `tbsg__add_item_to_cart` → `tbsg__search_items` → `tbsg__add_item_to_cart` | 与 `v5-hybrid_tbsg_notes_pantry` 同一条任务（Office pantry 缺货补齐淘宝闪购购物车），这是更早的 v4 轨迹。 |
| `secretary_0828_gemini` | Gemini 3.1 Pro Preview | HTV1SecretaryWangHangzhouPrep | tencent_meeting, ctrip, kapi, wechat（腾讯会议、携程、卡皮记账、微信） | 46（本目录只有 9 张精选图） | 9：`list_scheduled` → `open_meeting(sched_003)` → `get_budget_status` → `search_hotels` ×2 → `open_hotel(h_qinghe_icc)` → `search_trains` → `prepare_bill_draft` ×2（住房 310、交通 118） | 王总后天下午在杭州西湖国际会议中心有个合作方会议。你去腾讯会议里把这场会的时间和会前材料看清楚，再按日程去携程旅行订上海到杭州的火车和当晚酒店。酒店就近选西湖国际会议中心附近的，不能超过住房预算，火车和酒店都进填单就行先别付。卡皮记账里进公司账本，按住房和交通把当晚房价和火车票记上，再导出本月账单，保存图片到相册。最后用微信把会前材料和这张账单图发给张伟。 |

上表前 6 条轨迹验收通过。秘书演示整局 46 步走完会议、酒店、卡皮和微信，但火车选成了第一屏凌晨普速 K810（04:10），因此整题验收未通过。网站文案不要把火车写成「订票成功」。

### 截图命名

前 6 个目录是完整轨迹，每一步两张图：

- `step_NNN_before.jpg`：该步动作执行前
- `step_NNN_after.jpg`：该步动作执行后

`NNN` 从 `001` 起，与步号对齐。同目录里的 `index.html` 可在浏览器中本地打开，按步查看前后截图（不需要服务器）。

### 秘书演示：9 张精选图，不是完整轨迹

`secretary_0828_gemini/` 只有 **9 张精选展示截图**。完整轨迹是 **46 步**，本包没有逐步的 before/after 图，文件名也不是 `step_NNN_before.jpg`。

建议按文件名顺序做口播或网页轮播：

| 文件 | 对应完整轨迹 | 画面 |
| --- | --- | --- |
| `01-会议详情-14点备忘录.jpg` | step 7 | 会议 14:00，青禾备忘录与议程 |
| `02-卡皮-公司账本预算.jpg` | step 13 | 卡皮公司账本；住房预算要自己查出来（`get_budget_status`） |
| `03-青禾酒店-310.jpg` | step 18 | 青禾会议中心店，¥310 |
| `04-酒店填单-先别付.jpg` | step 21 | 酒店已进填单，尚未支付 |
| `05-火车列表-第一屏凌晨普速.jpg` | step 31 | 火车列表第一屏都是凌晨普速。这里展示「还要挑选」，不要写成已经订对 |
| `06-卡皮-住房310交通118.jpg` | step 39 | 卡皮记下住房 310、交通 118 |
| `07-月账单海报-428.jpg` | step 41 | 导出的本月账单，合计 428 |
| `08-分享张伟-备忘录正文.jpg` | step 44 | 系统分享给张伟，正文带备忘录 |
| `09-已分享到微信.jpg` | step 45 | 已发到微信 |

不要使用火车填单页（完整轨迹 step 33，车次 K810、凌晨四点）当作订票成功。微信头像在该局显示不完整，裁图时保留文字和账单，不要给头像特写。

### 各目录截图数量

| 目录 | 截图数 |
| --- | --- |
| `v5-hybrid_tbsg_notes_pantry` | 56 |
| `v5-hybrid_redbook_wechat_ranking` | 44 |
| `v5-hybrid_map_weather_wechat` | 36 |
| `v5-hybrid_spotify_playlist` | 26 |
| `v5-hybrid_taobao_purchase` | 24 |
| `v4_tbsg_notes_pantry_v4` | 26 |
| `secretary_0828_gemini` | 9 |

---

## English

### About

MobileGym++ is the first mobile-agent evaluation environment that combines native in-app tool calls (hybrid mode) with GUI actions. It includes 63 apps, of which 35 are newly built commercial apps (including Taobao, Taobao Flash Purchase, Xiaohongshu, and Bilibili).

On a single trajectory the agent can call structured app tools (search, add-to-cart, send a message) and also tap, swipe, and type. Every trace below is hybrid: native tool calls and GUI actions in one episode.

### Cases

All runs use **Gemini 3.1 Pro Preview** (`gemini-3.1-pro-preview`).  
The Tool Calls column lists **native app-tool** invocations and their order. It does not repeat the GUI action `mobile_use`, which accounts for the other steps. Steps counts both.

| Directory | Model | Task | Apps | Steps | Tool Calls | Instruction (Chinese; English below) |
| --- | --- | --- | --- | --- | --- | --- |
| `v5-hybrid_tbsg_notes_pantry` | Gemini 3.1 Pro Preview | HTV5Case74 | Notes, Taobao Flash Purchase (`tbsg`) | 28 | 9: `tbsg__get_cart` → `tbsg__search_shops` → `tbsg__get_shop_menu` → `tbsg__search_items` → `tbsg__add_item_to_cart` ×2 → `tbsg__search_shops` → `tbsg__search_items` → `tbsg__add_item_to_cart` | Restock the Taobao Flash Purchase cart from the “Office pantry” note. One of each listed item only. Do not use the flash-purchase entry inside the Taobao app, do not add unlisted items, and do not check out. |
| `v5-hybrid_redbook_wechat_ranking` | Gemini 3.1 Pro Preview | HTV5Case29 | Xiaohongshu (`redbook`), WeChat | 22 | 10: `redbook__search_notes` → `redbook__open_user` → `redbook__search_notes` → `redbook__open_user` → `redbook__search_notes` → `redbook__search_users` → `redbook__search_notes` ×2 → `wechat__search_contacts` → `wechat__send_text_message` | Search Xiaohongshu for “旅行”. Among the top 10 posts, open the author of the most-liked post, find that author’s most-saved post, and WeChat Chen Jing the post title, the author’s nickname, and their likes-and-saves count. |
| `v5-hybrid_map_weather_wechat` | Gemini 3.1 Pro Preview | HTV5Case37 | Map, Weather, WeChat | 18 | 6: `map__search_places` → `weather__get_current_weather` → `weather__search_cities` → `weather__get_current_weather` → `wechat__search_contacts` → `wechat__send_text_message` | Look up the full address shown for the National Museum of China, look up the current weather of that city, and WeChat Chen Jing the address, weather, and temperature. |
| `v5-hybrid_spotify_playlist` | Gemini 3.1 Pro Preview | HTV5Case38 | Spotify | 13 | 6: `spotify__search_tracks` → `spotify__add_to_playlist` ×2 → `spotify__search_tracks` → `spotify__add_to_playlist` ×2 | Create a playlist named 《双艺人精选》, search Jay Chou and JJ Lin, add exactly two songs from each and no other songs, then play the playlist. |
| `v5-hybrid_taobao_purchase` | Gemini 3.1 Pro Preview | HTV5Case70 | Taobao | 12 | 1: `taobao__open_search_results` (the rest is GUI: pick the item, order, and pay) | Search “清风山”, buy “清风山 山雾香氛护手霜 75mL 保湿滋润 生日礼物”, quantity 1, default spec, and complete payment. |
| `v4_tbsg_notes_pantry_v4` | Gemini 3.1 Pro Preview | HTV4Case74 | Notes, Taobao Flash Purchase (`tbsg`) | 13 | 6: `tbsg__search_items` → `tbsg__add_item_to_cart` → `tbsg__search_items` → `tbsg__add_item_to_cart` → `tbsg__search_items` → `tbsg__add_item_to_cart` | Same Office-pantry restock task as `v5-hybrid_tbsg_notes_pantry`, from an earlier v4 run. |
| `secretary_0828_gemini` | Gemini 3.1 Pro Preview | HTV1SecretaryWangHangzhouPrep | Tencent Meeting, Ctrip, Kapi, WeChat | 46 (only 9 curated stills in this folder) | 9: `list_scheduled` → `open_meeting(sched_003)` → `get_budget_status` → `search_hotels` ×2 → `open_hotel(h_qinghe_icc)` → `search_trains` → `prepare_bill_draft` ×2 (housing 310, transport 118) | Mr. Wang has a partner meeting tomorrow-but-one afternoon at Hangzhou West Lake International Conference Center. Read the time and pre-meeting notes in Tencent Meeting, then on Ctrip draft (do not pay) a Shanghai–Hangzhou train and a hotel near the venue within the housing budget. In the Kapi company ledger, record the hotel and the train fare under housing and transport, export this month’s bill to the photo album, and WeChat Zhang Wei the pre-meeting notes and the bill image. |

The first six episodes passed automatic checks. The secretary run finished the meeting, hotel, ledger, and WeChat portions in 46 steps, but the train it opened was the overnight conventional train K810 (04:10) on the first screen, so the episode did not pass. Do not caption the train frame as a successful booking.

### Screenshot names

The first six folders are full trajectories. Each step has two images:

- `step_NNN_before.jpg`: before the action
- `step_NNN_after.jpg`: after the action

`NNN` starts at `001` and matches the step index. `index.html` in the same folder opens locally in a browser and walks the before/after pairs. No server is required.

### Secretary stills: 9 curated frames, not the full trace

`secretary_0828_gemini/` contains **9 curated stills**. The full episode is **46 steps**. This pack does not include a before/after pair for every step, and these files are not named `step_NNN_before.jpg`.

Suggested order:

| File | Full-trace step | What it shows |
| --- | --- | --- |
| `01-会议详情-14点备忘录.jpg` | step 7 | Meeting at 14:00, Qinghe memo and agenda |
| `02-卡皮-公司账本预算.jpg` | step 13 | Kapi company ledger; the housing budget is read with `get_budget_status` |
| `03-青禾酒店-310.jpg` | step 18 | Qinghe ICC hotel, ¥310 |
| `04-酒店填单-先别付.jpg` | step 21 | Hotel booking form, not yet paid |
| `05-火车列表-第一屏凌晨普速.jpg` | step 31 | First screen of trains, all overnight conventional services. Show this as “a choice still to make”, not as a correct booking |
| `06-卡皮-住房310交通118.jpg` | step 39 | Kapi entries: housing 310, transport 118 |
| `07-月账单海报-428.jpg` | step 41 | Exported monthly bill, total 428 |
| `08-分享张伟-备忘录正文.jpg` | step 44 | Share to Zhang Wei, body includes the memo |
| `09-已分享到微信.jpg` | step 45 | Delivered in WeChat |

Do not use the train order form (full-trace step 33, train K810 at 04:10) as a successful booking. The WeChat avatar was incomplete in this run; crop to the message text and the bill, not an avatar close-up.

### Screenshot counts

| Directory | Images |
| --- | --- |
| `v5-hybrid_tbsg_notes_pantry` | 56 |
| `v5-hybrid_redbook_wechat_ranking` | 44 |
| `v5-hybrid_map_weather_wechat` | 36 |
| `v5-hybrid_spotify_playlist` | 26 |
| `v5-hybrid_taobao_purchase` | 24 |
| `v4_tbsg_notes_pantry_v4` | 26 |
| `secretary_0828_gemini` | 9 |
