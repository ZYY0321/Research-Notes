# 真机逐 case 记录

设备：双折叠 `22M0223928009654`（USB 已授权，内屏常亮）  
检测模型：无校园网时走本机 `.env` 备用对话接口（不走 10.176.44.15）。验收用校园网官方 `/detect`。  
数据：`测试集/整理` 最新 Labelme 版  
模式：到达页面后 `npm run ux-detect -- --mode=slide`  
时延：端到端 ≤10 秒 = **模型 3 秒 + 其余算法 7 秒**。备用接口现场慢不算；验收用自建模型。算法段含截图、dump、layout、滑动、恢复。

## 2026-09-21 合作方：没有 XML 不跑端到端

微信原话：没有的就不用测端到端；只测有 xml 的就行；没有的都是直接模型判断。

已写成 [docs/有XML才端到端.md](../有XML才端到端.md)，并挂到根目录 README、`AGENTS.md`、给人看 / 给 AI / 测试队列。美团 g04/g05 无 XML，不再端到端。后面 truncated 正例同样先查有没有 `.xml`。

## 2026-09-21：挂了要写清问题和证据

原 run-log 模板只有过/不过和一句话，筛查不出算法哪一段有问题、后面怎么改。已写成 [docs/失败要写清问题和证据.md](../失败要写清问题和证据.md)。真机 unknown/bad 必须写：哪一段、什么情况、改进方向、dump/滑后图/恢复图路径。测前 `git pull`，算法改完立刻 push。

**导航：** 刚 `aa start` 腾讯视频后，模型把闪屏当成空白，按了 BACK，人被送回支付宝。已改：启动后等前台包名对上；忽略 BACK；提示词写明不要离开刚打开的 App。检测算法未改。

**底切停靠（G02，导航不是检测算法）：** GPT 对不准「最后一行刚好被底边切开」那条缝。已改成 GPT 只负责进「花呗 / 全部」列表；随后 `dumpLayout` 找服务行坐标，按像素差 `fling/swipe` 把目标行底边停在 `screenH+110px`。优先「花呗分期商家服务」，没有就停最后一条服务行。检测算法未改。

## 测试集 XML 能不能提前筛「不用滑」

结论：**同源，但不能拿来预筛 truncated 正例。**

- 测试集 77 份 XML 全在 `*_xml_normal/`，源是 `uitest dumpLayout`，和现场 dump 同一套树（bounds / type / scrollable / origBounds）。
- 现场拿到的是 JSON（`window_dump.json`），测试集转成了 XML；我们的 layout 解析器吃 JSON。字段能对上，序列化不一样。
- **150 个 image_truncated 正例一份 XML 都没有。** 同 app/g0x/屏配对到 xml_normal 的有 58 组，但是**另一页**：支付宝 g01 的 xml_normal 是「理财」Tab，truncated 是「我的」订单行。
- xml_normal 里 66 张真负例、11 张其实标了切（见反馈）。拿这份树离线跑，筛的是负例页，不是我们在测的切字页。
- 支付宝这条也说明：就算现场 dump，混合渲染（XComponent/JsView）对不上「待付款」这些字，layout 判 unknown，还是得滑。归档 XML 更帮不上。

所以预筛先不做。继续现场 dump；XML 只当对照，不当 GT。

## 待做：滑动过程弹出的截屏分享要防御

美团会监听截屏，弹出「截图分享至」。`uitest screenCap` 和 `snapshot_display` 都会触发，只是后者晚一点，出现在**恢复截图**那一步。反向滑打在遮罩上，整组 `restore_failed`，可滚框也消不掉（`105447-696` restore 图）。

现场勾了「下次不再出现」之后 `110026-079` 恢复成功。这不能当验收依赖。算法侧要防：恢复图若是盖住页面的分享/截屏浮层，应先关掉再比，不能直接 `restore_failed`。不要写成扫「微信/朋友圈」文案。已过的支付宝/B站/番茄没有这种浮层，加防御时只在确认是盖住的浮层后再点关闭，避免误点列表。

## 今天汇报：这几题做不了，先记风险（2026-09-23）

测试仍走 API，为的是模型每次给出的框更全。下面三题的改法都只是保底：万一模型标出截断，算法还能消掉。保不住就丢弃，不留半截改动。

### 1. 平板 WPS 最近：白底列表动了，回滑被跳过

- 现场：定制提示词后，模型框住右下角被红色加号挡住的分享图标。`213220-738`。
- 哪一段：滑动后的恢复。
- 什么情况：上滑后列表已经换行，整页平均差 2.49%，变化像素 14.9%。回滑只看平均差是否大于 2.5%，差 0.01，跳过回滑，页面停在滑后。框内差 4.31%，没过 5%，遮盖留 confirmed。
- 为啥做不了：临时加过「变化像素不少于 8% 且平均差大于 1% 也算动过」，重跑 `213836-856` 回滑差 0.96%，能回来。空探的变化像素都不到 1%（番茄 g01 0.56%、12306 右缘 0.84%、高德顶栏 0%），那条规则打不中它们，但为了不碰已过 case，已从 `slide-verify.ts` 撤掉。恢复仍只看平均差。

### 2. 平板 WPS 云盘：画面是省略号，dump 里没有

- 现场：`214251-108`。模型 1 框打在「查看空间及云...」。
- 哪一段：layout。dump 文字是完整句「查看空间及云功能」，bounds 与 orig 重合，没有 `...` / `…` / `⋯`。layout 只看到底边探出 5px，`glyph_clipping_boundary_not_found`。左滑 0% 留 confirmed。
- 为啥做不了：现有产物分不出这是省略号还是真切字。关于页同样是 hidden 0、小探出、0% confirmed，那是真截断。交叉轴消框试过，会和真切字搅在一起，已撤。美团拼好饭 dump 里店名会带 `...`，这条规则只在文字里真有省略号时才生效。

### 3. 三屏 QQ 音乐推荐：右缘露出的下一列，不是截断

- 昨天合作方 `214906-234`：模型 0 框，没滑，页级 ok。参考模型 `labels_json` 也是空的。
- 今天下午我们的模型标过。第一次 `230205-338` 在「大家都在听」右缘框了 3 张只露出一截的封面，左滑差 0%，页级 bad。人眼确认不是截断，在卡片内部左滑能到下一列。
- 手势：必须落在卡片里面，从被截断的那张图标起手可以。划在「大家都在听」这几个字上，列表不动。划得太短，列表弹回原列，探测差还是 0。从屏幕右缘起手，系统当成返回，应用被关掉（`232423-702`，起点 x=3155）。
- 已按人说的改。宽屏右缘同一条列表合成一次左滑，不按行各滑一次。起点在行内，不贴右缘（贴右缘会拉出工具栏）。复用上次两个模型框重放 `234501-154`：一组，起点 `(2165,1307)`，行程 180/1000，两框都可滑并消掉，回滑一次，差 0%，页级 ok。窄屏右缘芯片仍从框内侧起手、按行分开。番茄那种不贴边的左滑仍是 100。单测 11 条过。这次一次滑动加一次回滑，算法 10.8s，仍超 7s。

## 风险 2026-09-23（WPS 最近：白底列表动了但回滑被跳过）已改回

定制提示词让模型框住右下角被加号挡住的分享图标后，上滑列表已经换行，整页平均差 2.49%，变化像素 14.9%。回滑只看平均差是否大于 2.5%，差 0.01，跳过回滑，页面停在滑后。临时加过「变化像素不少于 8% 且平均差大于 1% 也算动过」并重跑成功（回滑差 0.96%）。为了不碰已过 case，这条已从 `slide-verify.ts` 撤掉，恢复仍只看平均差。空探变化像素都不到 1%（番茄 g01 0.56%、12306 右缘 0.84%、高德顶栏 0%）。框内差 4.31%，没过 5%，遮盖仍留 confirmed。证据：`213220-738`（没回滑）、`213836-856`（临时规则回滑成功）。回去汇总风险 case 时带上这条。

## 风险 2026-09-23（WPS 云盘：画面是省略号，dump 里没有）算法未改

平板 WPS 云盘「查看空间及云...」是省略号，不算截断。现场 `214251-108`：模型 1 框，dump 文字是完整句「查看空间及云功能」，bounds 与 orig 重合，没有 `...` / `…` / `⋯`。layout 只看到底边探出 5px，判 `glyph_clipping_boundary_not_found`，左滑 0% 留 confirmed。页级 bad。现有产物里分不出这是省略号还是真切字（关于页同样是 hidden 0、小探出、0% confirmed）。交叉轴消框试过，已撤。回去汇总风险 case 时带上这条。证据：`/Users/zhangyingying/UX-Agent/HarmonyArena-fdu_agent/ux-detect-output/20260923-214251-108/snapshot_ux.json`。同日三屏 QQ 音乐推荐页右缘露出的下一张封面，人眼确认这一行卡片里长滑能到下一列，不是截断。宽屏同一条列表合成一次左滑后，复用上次模型框重放 `234501-154`，两框都消掉，回滑一次差 0%，页级 ok。证据：`/Users/zhangyingying/UX-Agent/HarmonyArena-fdu_agent/ux-detect-output/20260923-234501-154/snapshot_ux.json`

## 算法改动 2026-09-21（回滑冲过头不要再同向补）

美团 g03 底切：第一次回滑已过原位（5.11%），再反向补到「大牌驾到」（9%）。番茄 g03 相反，第一次欠回滑 3.2%，必须再反向。

已改 `slide-verify.ts`：**第一次回滑距离/方向不变**。失败后用滑动那一栏的画面 1D 平移判断：冲过头就短距离正向补（60）；欠回滑或看不出峰值仍全量反向（100）。支付宝/番茄/美团 g01/g02 第一次恢复就过的不走补刀。

单测：`npm run test:ux-detect:slide`。美团 g03 复测。

## 算法改动 2026-09-21（横滑起点不要落到邻芯片）

美团 g03 分类右切：模型框只有 ~20/1000 宽。左右滑沿切开边再收 80，手指落到旁边「炒饭拌饭」上，被当成点选，横条不走。探测区 21% 多半是顶上 banner 自己在变。

已改 `slide-verify.ts`：`SWIPE_CONTENT_INSET` **只给上/下**（离开 Tab 进列表）。左右用框中心；若边缘避让把点推出框，再夹回框内 ±8。底栏上滑单测仍要求 y<850。

影响：支付宝 g01/g03、番茄 g02/g03、美团 g01/g02 都是 up，起点不变。番茄 g01 左滑改用框中心，切字仍在框附近，探测 0% → confirmed 预期不变。B 站 g03 右切 layout 消了没滑。

单测：`npm run test:ux-detect:slide`。美团 g03 需人再摆到拼好饭同类页后复测。

## 算法改动 2026-09-20（同尺寸 clip 包装不当真截断）

美团 g01 `110026-079`：GT「丰厚榴莲」layout 已按可滚消掉。右上「【外送/到店】甄选尊享」两行完整、dump 无省略号、bounds=origBounds。glyph 兜底 `requireOverflow=false` 把同框 `Custom clip=true` 当成 `local_clip`，`true_truncation` 还跳过滑动。页级被判 bad。

已改 `verifier.ts` 1.1.3：glyph 兜底里，无溢出的 `local_clip` / `text_self_clip` 丢掉；可滚 / 翻页祖先仍留。真裁切（origBounds 探出 clip 容器）仍走 `findOwner`，单测「confirms clipping by a local non-scroll container」不变。

影响预估：已过的支付宝/B 站/番茄不靠「零溢出 local_clip → true_truncation」。支付宝待付款是 overhang 无 clip 父，本来就是 unknown。B 站底切是 List/Grid recoverable。榴莲那条有 orig 底溢出，findOwner 仍 recoverable。截屏分享防御还没做。

单测：`node --import tsx --test tests/text-trunc-verifier/verifier.test.ts`。lab 左切 fixture 原先 Stack 右沿对齐文字左沿，findOwner 看不见 left overflow，已改成 Stack 左沿对齐。

## 算法改动 2026-09-20（截屏不走系统截屏事件）

美团 g01 滑动中途弹出截屏分享，恢复失败。`uitest screenCap` 会通知 App。已改成 `snapshot_display -t png`（合成器出图）。分辨率仍 2224×2496 PNG，像素门槛不改；不用 jpeg，否则 restore 2.5% 会误失败。已过的支付宝/B站/番茄不依赖「系统截屏事件」，判定逻辑不变。

## 算法改动 2026-09-20（滑动等待叠层）

番茄看剧那次滑动 9.3s：滑完已经等 600ms，恢复再干等 400ms。**已撤回。** 看剧第一次恢复 3.2%（门槛 2.5%）靠第二次才过；支付宝 g01/g03、番茄 g02 都靠恢复成功才把可滚框消掉。恢复失败会把整组改成 `restore_failed`，以前的 ok 会变成 unknown。截图前 `rm` 也撤回，避免 screenCap 失败拉到旧图改判定。后面改滑动先对照「会滑的已过 case」再动等待和恢复。

## 算法改动 2026-09-20（滑动空探还去恢复）

番茄短篇「更多」前一个小框：layout 绑不上，模型让左滑。探测区 diff=0（画面没动，本应 `confirmed`），却照样反向右滑，整页平均差 6.3%，改判 `restore_failed`，还多滑一次。算法被拖到 9.4s，页也划歪。

已改 `slide-verify.ts`：**正向滑之后探测区和整页都没动，就不再反向恢复。** 探测没动但整页动了（滑到别的控件）仍要恢复。单测：`npm run test:ux-detect:slide`。

复测 `101603-514`：三框一次左滑，探测区 0%、整页 0.02%，`restore_skipped`，slide **2.4s**，算法 **4.2s**。框留下 `confirmed`。页级仍 unknown，因为汇总只认 layout `true_truncation`、不认 slide confirmed。已改 `recomputeOverall`：slide `confirmed` 算缺陷（`restore_failed` 仍 unknown）。再测 `101733-732` 页级 **bad**，算法 **4.1s**。

## 算法改动 2026-09-20（支付宝「我的」暴露）

BF-ALIPAY-G01-S2 一框一滑五次、反向滑完人眼仍不在原位、整次 45 秒。已改 `HarmonyArena-fdu_agent/.opencode/lib/slide-verify.ts`：

- 同方向、中心落在同一条带（50/1000）的框合成一组，只滑一次、只恢复一次。这条底栏 4 框 + 顶卡 = 2 组，不再 5 次。
- 滑动起点从切字框中心改到内容区（切开边上收 80/1000），避开 Tab / 状态栏。
- 恢复比对从 64×64 / 5% 改成 256×256，平均差 >2.5% 或变像素 >12% 算失败，失败再反向滑一次。
- 单次 settle 1000ms+1200ms 收到 600+400。

单测：`npm run test:ux-detect:slide`。下一条 BF-ALIPAY-G02-S2 起用新逻辑。g01 若要回归，需重新点到「我的」。

## 算法改动 2026-09-20（弹窗背景误标）

腾讯视频「确认开通」负例：模型给遮罩后面最底一行打了 3 框。dump 里弹窗是居中 `CustomFrameNode`，不是贴边 TabBar，旧 overlay 规则消不掉；滑动点在弹窗上，diff=0 还当成 confirmed。

已改 `src/text-trunc-verifier/verifier.ts`（v1.1.2）：不再扫「确认/继续/开通」文案。改为叠层结构：全屏可点遮罩或 `SheetWrapper`/`Dialog` 一类宿主上面有一块更小的内容卡，**框落在这张卡外面 → `not_truncation` / `overlay_background_occlusion_out_of_scope`**。页面里普通居中卡片没有遮罩层，不走这条。卡自己身上的框仍走原逻辑。

这是 layout 消解，不是改提示词。检测模型仍可能标遮盖，我们在后处理丢掉。

- [x] USB 已授权，Mate X5 内屏常亮

## Case 队列（先双折叠内屏）

### BF-XHS-G01-S2 小红书活动页（正例）

- 图：`bifold_image_truncated/xiaohongshu/g01/..._s2.jpg`（内屏 2224×2496）
- GT：底栏切掉左列、右列各一条标题（bottom）
- 包名：`com.xingin.xhs_hos`
- 真机：2026-09-19 23:51 已在「上海 / 活动」三列瀑布流。底栏切到「求救信」「抵抗之力」「Monday Run」标题，和 GT 同类，内容因直播页有变化。
- 产物：
  - 第一次（会 hidumper 切折叠，已停）：`ux-detect-output/20260920-074955-305/` dual+single 都是 0 框
  - 第二次（真机只测当前屏）：`ux-detect-output/20260920-075222-396/` 7.4s，gpt-5.6-sol `overall=ok` issues=0，未滑动
- 提示词：已改成只看图标框，不再写底栏排除规则。
- 第三次：`ux-detect-output/20260920-075415-064/` gpt-5.6 标了 3 个底切（求救信 / 抵抗之力 / Monday Run），红框对上了。layout 判 `continuous_scroll_glyph_clipping_recoverable`，3 条全部消解，**没有滑动**。页级仍是 ok。
- 状态：**通过，暂时放着。** 简单底栏切字，XML 可滚动兜底可接受。不改算法。

### BF-ALIPAY-G01-S2 支付宝「我的」订单行（正例）

- 图：`/Users/zhangyingying/UX-Agent/测试集/整理/bifold_image_truncated/alipay/g01/bifold_image_truncated_alipay_g01_s2.jpg`
- GT：底栏切掉「我的订单」四个入口文字（待付款 / 进行中待使用 / 退款售后 / 全部订单），bottom，4 框
- 包名：`com.alipay.mobile.client`
- 你怎么点：展开内屏 → 支付宝 → 底栏「我的」。页面应看到头像/Jack、账单、总资产、蚂蚁保，最底下「我的订单」四个字被底栏切掉。
- 真机：2026-09-20 00:03 已到「我的」。账号不是 Jack（实名认证卡），底栏仍切「待付款 / 进行中待使用 / 退款售后 / 全部订单」，和 GT 同类。
- 产物：`ux-detect-output/20260920-080259-884/`
  - 模型 5 框：顶「请完成实名认证」1 个（多标）+ 底 4 个对上 GT
  - layout 5 条全 unknown（2 条绑到图标字体 `/`，3 条 `no_matching_component`），**XML 没兜住**
  - slide 5 次全判 `scrollable`（diff 14%–40%）后消解
- 页级：`ok`，issues=0
- 整次耗时：约 **45 秒**（滑动段约 32 秒），远超 10 秒
- 为什么滑 5 次：layout 全 unknown，代码是 **一框一滑一恢复**，同方向底栏 4 框没有合并。顶上「实名认证」还多滑了一次 down（可能碰到下拉刷新）。
- 为什么看起来没回到原位：每次反向滑后，相对**初始截图**的整屏差是 0.53% → 0.63% → 0.69% → 0.83% → **1.12%**，单调变大，但阈值 5%，所以日志全是 `restoreFailed=false`。人眼能看出列表漂了。底栏框的滑动起点就在 Tab 上，反向滑不一定能原路退回。
- 自动回归（分组后）`npm run case:run -- --case BF-ALIPAY-G01-S2`：GPT 直接 arrived。
  - `082105-397`：2 组滑，restore 阈值过严（changedPercent 把时钟当失败），**30.8s**，作废。
  - **`082214-410`**：layout 把「待付款」判 `true_truncation`（无裁切父节点还当真），不进滑动，留下 1 框。**没过。**
  - **`082806-346`**：无 owner 的 overhang 改为 unknown。4 框全 unknown → 1 组滑全部消解。页级 **ok**，issues=0。算法 **6.3s**（layout 4ms + slide 4.9s），≤7s。
- 状态：**通过。** layout 不再把没裁切父节点的框定成真截断。

问测试团队（见 `给测试团队的问题.md`）：验收现场能否保证和 GT 截图同一账号/实名/运营位。GT 没有「请完成实名认证」大卡。

### BF-ALIPAY-G02-S2 支付宝搜索「花呗」列表底切（正例）

- 图：`/Users/zhangyingying/UX-Agent/测试集/整理/bifold_image_truncated/alipay/g02/bifold_image_truncated_alipay_g02_s2.jpg`
- GT：列表最后一行被屏幕底边切掉（「花呗分期商家服务」描述 + 右侧「5000+人最近使用」），bottom，2 框
- 包名：`com.alipay.mobile.client`
- 你怎么点：支付宝顶栏搜索「花呗」→ 结果页「全部」→ 往下看到「花呗金 / 花呗账单 / 备用金 / 花呗收钱」，最底下「花呗分期商家服务」那一行被切掉即可。
- 真机：GPT arrived 花呗「全部」结果。直播页没有「花呗分期商家服务」，停靠在「花呗亲密度」贴底。
- 停靠：`dumpLayout` 慢滑，`084616-143`。亲密度 `y2=2496` 贴齐底边。GT 框也只在最底 18px。
- 检测：模型 2 框（公司名 + 最近使用，和 GT 同类底切）。layout 判 `continuous_scroll_glyph_clipping_recoverable`，2 条消解，**没滑**。页级 **ok**。算法 **2.2s**。
- 状态：**到达同类切字并检出；页级按可恢复滚动通过。** GPT 盲滑打不中这条缝，已改成 dump 停靠。检测算法未改。

### BF-TXV-G01-S2 腾讯视频开通弹窗（负例）

- 图：`/Users/zhangyingying/UX-Agent/测试集/整理/bifold_image_normal/tencentvideo/g01/bifold_image_normal_tencentvideo_g01_s2.jpg`
- GT：`正常图=true`，无框。弹窗里字是完整的；后面被挡住的字按规则不审。
- 包名：`com.tencent.videohm`（Ability `AppAbility`）
- 你怎么点：展开内屏 → 腾讯视频 → 走到会员/开通确认弹窗（标题「确认开通」）
- 真机：`aa start` 成功；忽略 BACK 后 5 步点到「确认开通」弹窗。`arrived=true`。第一次 `092014-955` 误报。
- 复测（页还在，只跑检测）：`/Users/zhangyingying/UX-Agent/HarmonyArena-fdu_agent/ux-detect-output/20260920-094538-981/snapshot.png`
- 检测：模型仍在遮罩后最底一行打 3 框。layout 判 `overlay_background_occlusion_out_of_scope`（全屏可点层 68 + 内容卡 69），3 框全消。滑动跳过。页级 **ok**。算法 **1.7s**。
- 状态：**负例通过。** 模型仍会标遮盖，layout 消掉。仍记测试团队问题第 4 条。

### BF-ALIPAY-G03-S2 支付宝选城市底切（正例）

- 图：`/Users/zhangyingying/UX-Agent/测试集/整理/bifold_image_truncated/alipay/g03/bifold_image_truncated_alipay_g03_s2.jpg`
- GT：城市列表最后一行「巴音郭楞蒙古自治州」被底边切开，bottom，1 框
- 包名：`com.alipay.mobile.client`
- 你怎么点：支付宝首页左上角城市 → 国内 → 划到 A/B 列表最底一行被切
- 真机：人手点到。现场同一页、同一行被切。`095100-226`
- 检测：模型 1 框，绑到 Text「巴音郭楞蒙古自治州」。dump 的 bounds=origBounds，layout `glyph_clipping_boundary_not_found`（unknown）。滑动 1 次 diff=14.3% 判可滚，消解。页级 **ok**。算法 **6.5s**。
- 状态：**到达同类切字并检出；页级按可恢复滚动通过。** dump 没露出 overflow，所以 layout 没预筛掉，靠滑动。

### BF-BILI-G01-S2 B站热门底栏切标题（正例）

- 图：`/Users/zhangyingying/UX-Agent/测试集/整理/bifold_image_truncated/bilibili/g01/bifold_image_truncated_bilibili_g01_s2.jpg`
- GT：热门两列流最底右卡标题被底栏切开，bottom，1 框
- 包名：`yylx.danmaku.bili`
- 你怎么点：B站 → 首页 → 热门 → 划到最底一行标题被底栏切
- 真机：人手点到。同类底切，标题是「变形强强【B站笑点大赛】」。`095411-334`
- 检测：模型 1 框。layout 绑到该 Text，Grid 可滚 + TabBar，`continuous_scroll_glyph_clipping_recoverable`，消解，**没滑**。页级 **ok**。算法 **2.0s**。
- 状态：**到达同类切字并检出；页级按可恢复滚动通过。**

### BF-BILI-G02-S2 B站视频详情相关推荐底切（正例）

- 图：`/Users/zhangyingying/UX-Agent/测试集/整理/bifold_image_truncated/bilibili/g02/bifold_image_truncated_bilibili_g02_s2.jpg`
- GT：播放器+简介页，最底相关视频标题被屏幕底边切开，bottom，1 框
- 包名：`yylx.danmaku.bili`
- 你怎么点：热门点进视频 → 简介 → 相关推荐贴底切开
- 真机：人手点到同类页（不是峰哥那条）。第一次 `095721-837` 弹幕开着，播放器角多一框，unknown。关掉弹幕复测 `100205-946`。
- 检测（关弹幕）：模型只打底栏 1 框，layout `continuous_scroll_glyph_clipping_recoverable`，消解，**没滑**。页级 **ok**。算法 **1.9s**。
- 状态：**到达同类切字并检出；页级按可恢复滚动通过。** 弹幕会让模型乱标，这条要关弹幕再测。

### BF-BILI-G03-S2 B站会员购右侧切开（正例）

- 图：`/Users/zhangyingying/UX-Agent/测试集/整理/bifold_image_truncated/bilibili/g03/bifold_image_truncated_bilibili_g03_s2.jpg`
- GT：会员购顶栏右侧文字/图标被右边缘切开。文字框主要是「平台资质」；另有组件/图标框，这次不计截断真值。
- 包名：`yylx.danmaku.bili`
- 你怎么点：底栏会员购，停在首页顶
- 真机：人手点到。分类芯片这回是完整的；「平台资」仍被右边缘切。`100453-129`
- 检测：模型 1 框打在「平台资质」。layout 横滑 List 可滚，`continuous_scroll_glyph_clipping_recoverable`，消解，**没滑**。页级 **ok**。算法 **2.0s**。
- 状态：**到达同类右切并检出；页级按可恢复滚动通过。**

### BF-FANQIE-G01-S2 番茄短篇「更多」前右切（正例）

- 图：`/Users/zhangyingying/UX-Agent/测试集/整理/bifold_image_truncated/fanqie/g01/bifold_image_truncated_fanqie_g01_s2.jpg`
- GT：短篇三张卡简介最后一行在「更多」前被右切，3 个文字框；标签条另有组件框不计
- 包名：`com.dragon.read.next`
- 你怎么点：番茄小说 → 书城 → 短篇
- 真机：人手点到。第一篇就是 GT 那篇。空探修完再测 `101603-514`（三框 confirmed，页级 unknown），汇总改完再测 `101733-732`
- 检测：layout 仍 `no_matching_component`。左滑探测 0%、整页没动，**跳过反向恢复**。slide `confirmed` → 页级 **bad**。算法 **4.1s**。这次模型只标了第一卡。
- 状态：**滑动空探恢复已修好，正例检出。** dump 里没有「更多」节点，layout 绑不上。

### BF-FANQIE-G02-S2 番茄搜索「我的书架」底切书名（正例）

- 图：`/Users/zhangyingying/UX-Agent/测试集/整理/bifold_image_truncated/fanqie/g02/bifold_image_truncated_fanqie_g02_s2.jpg`
- GT：书籍搜索结果最后一本「山野村欲」书名被底边切开，bottom，1 框。`正常图=false`
- 包名：`com.dragon.read.next`
- 你怎么点：搜索「我的书架」→ 书籍 → 最底书名被切
- 真机：人手点到。同类底切，书名是「天渊」。`102604-248`
- 检测：模型 1 框打在底切书名。layout `no_matching_component`。上滑探测 29%，`scrollable` 消解，反向恢复成功。页级 **ok**。算法 **7.2s**（略超 7s）。
- 状态：**到达同类底切并检出；页级按可恢复滚动通过。**

### BF-FANQIE-G03-S2 番茄「看剧」海报页（官方负例）

- 图：`/Users/zhangyingying/UX-Agent/测试集/整理/bifold_image_truncated/fanqie/g03/bifold_image_truncated_fanqie_g03_s2.jpg`
- GT：在 truncated 文件夹里，但 `正常图=true`、空框。底下海报被底栏挡住不算截断。
- 包名：`com.dragon.read.next`
- 你怎么点：书城 → 看剧
- 真机：人手点到看剧热剧榜。`103118-119` 过；黑屏复测 `104133-208` 没过；再测 `104426-529` **过**
- 检测（`104426-529`）：海报误标 1 框。上滑 28.6% 可滚消解，恢复一次 1.34% 成功，没二次滑。页级 **ok**。算法 **7.7s**。
- 状态：**负例通过。** 上次 unknown 按黑屏作废。官方 GT 无截断。

### BF-MEITUAN-G01-S2 美团达美乐团购底切（正例）

- 图：`/Users/zhangyingying/UX-Agent/测试集/整理/bifold_image_truncated/meituan/g01/bifold_image_truncated_meituan_g01_s2.jpg`
- GT：右侧团购最后一条「丰厚榴莲」标题被底边切开，bottom，1 框。`正常图=false`
- 包名：`com.sankuai.hmeituan`
- 你怎么点：搜达美乐比萨进店 → 团购 → 最底标题被切
- 真机：人手点到。截屏分享弹窗：`104813-346` / `105447-696` 作废。勾选「下次不再出现」后 `110026-079` 页级没过（标题假阳）。修完同尺寸 clip 包装后再测 `112100-798`
- 检测（`112100-798`）：模型 4 框。左栏顶切 2 框 + GT「丰厚榴莲」layout 可滚消掉。底边另 1 框 layout 绑不上，上滑 26.1% 可滚，恢复 0.89% 成功。这次模型没再标右上「甄选尊享」（旧 dump `110026-079` 回放已是 unknown，会进滑动）。页级 **ok**。算法 **9.0s**（滑动 5.7s，略超 7s）。无截屏分享弹窗。
- 状态：**页级通过。** GT 底切按可恢复不算缺陷。截屏分享浮层仍待防御。

### BF-MEITUAN-G02-S2 美团影院列表底切（正例）

- 图：`/Users/zhangyingying/UX-Agent/测试集/整理/bifold_image_truncated/meituan/g02/bifold_image_truncated_meituan_g02_s2.jpg`
- GT：右栏影院列表最后一条「大光明星汇影城（杨浦店）」和「22.9元起」被底下定位条切开，bottom，2 框。`正常图=false`
- 包名：`com.sankuai.hmeituan`
- 你怎么点：首页 → 右栏底「电影/影院」→ 「影院」→ 列表最底店名被切
- 真机：人手点到。`113147-818`
- 检测：模型 2 框打在店名和价格。dump 字完整、bounds=origBounds，layout `unknown`。一组上滑 19.7%/6.5% 可滚，恢复 2.42%（门槛 2.5%）成功。页级 **ok**。算法 **7.2s**。
- 状态：**到达同类底切并检出；页级按可恢复滚动通过。**

### BF-MEITUAN-G03-S2 美团拼好饭右切+底切（正例）

- 图：`/Users/zhangyingying/UX-Agent/测试集/整理/bifold_image_truncated/meituan/g03/bifold_image_truncated_meituan_g03_s2.jpg`
- GT：分类条右切（图标/文字/组件）+ 最底套餐名底切。`正常图=false`
- 包名：`com.sankuai.hmeituan`
- 你怎么点：首页 → 拼好饭 → 搜库迪 → 右栏分类被切、底条挡住最后一条
- 真机：人手点到拼好饭。搜的是「肉夹馍」，定位东苑新天地。`090017-619` 恢复失败。人划回去再测 `090241-364`。改横滑落点后再测 `20260921-092155-697`
- 检测（`090241-364`）：仍 2 框、layout 绑不上。左滑可滚并恢复 1.15%。上滑 14.4% 能滚，回滑 4.46% 失败，再补一次更差 8.98%。共 **5 次滑**（左、右恢复、上、下恢复、再下）。页级 **unknown**。算法 **33.5s**。
- 检测（`092155-697`）：起点改到框内后，左滑 (2151,834)→(1928,834)，分类条真的横移（炸鸡烤串完整、饺子粥出来），探测 18.1%，恢复 2.41% 成功。底切上滑 17.7% 能滚，回滑 5.11% 失败，再补 9.08% 更偏。页级仍 **unknown**。算法 **33.3s**（模型 21s 不算）。
- 检测（`092942-523`）：改回滑补刀后再测。模型 2 框（右缘分类 + 底锄禾）。layout 仍 unknown。左滑 20.7% 可滚，恢复 0.29%。上滑 19.2% 可滚，**第一次回滑 1.61% 即过**（没走到冲过头补刀）。两框都消。页级 **ok**。算法 **27.2s**（模型 26s 不算）。
- 状态：**到达同类切；可滚消解，页级通过。** 这次第一次回滑就进门槛，补刀没触发；补刀逻辑仍留着防冲过头。

### BF-MEITUAN-G04-S2 美团酒店星级/价格底切（正例，无法复现）

- 图：`/Users/zhangyingying/UX-Agent/测试集/整理/bifold_image_truncated/meituan/g04/bifold_image_truncated_meituan_g04_s2.jpg`
- GT：全屏「美团酒店」筛选项「星级/价格」，底栏「重置 / 查看」被屏幕底切开。`正常图=false`。外屏 s1 同页底栏完整，json 是负例。
- 包名：`com.sankuai.hmeituan`
- 真机：人手点。现版入口只有「酒店民宿」，铺满内屏后是搜索列表上的下拉「价格·星级」，「重置 / 查看」完整，底下露出酒店卡片。不是 GT 那种铺到屏幕底的红条筛选项。预览图 `/tmp/ux-agent-preview/preview_g04c.png`。
- 检测：未跑。
- 状态：**作废，切字无法复现。** App 改版，不是算法问题。无 XML，按 2026-09-21 约定也不再端到端。

### BF-MEITUAN-G05-S2 美团酒店位置区域顶切（正例）

- 图：`/Users/zhangyingying/UX-Agent/测试集/整理/bifold_image_truncated/meituan/g05/bifold_image_truncated_meituan_g05_s2.jpg`
- GT：全屏「美团酒店」→「位置区域」，第一行「0.5%的人选择」被顶栏切开。底「横沥镇」是遮盖，不算截断。
- 检测：未跑。无配套 `.xml`。
- 状态：**不端到端，交给模型判断。**

### BF-TXV-XML-G01-S2 腾讯视频首页「短视」右切（xml_normal 正例）

- GT：`/Users/zhangyingying/UX-Agent/测试集/整理/bifold_xml_normal/tencentvideo/g01/bifold_xml_normal_tencentvideo_g01_s2.jpg`
- XML：`/Users/zhangyingying/UX-Agent/测试集/整理/bifold_xml_normal/tencentvideo/g01/bifold_xml_normal_tencentvideo_g01_s2.xml`
- 现场图：`/Users/zhangyingying/UX-Agent/HarmonyArena-fdu_agent/ux-detect-output/20260921-230455-301/snapshot.png`
- 页级：**ok**
- 人眼：顶部分类最右仍是「短视」，和 GT 同类。dump 节点文案是完整「短视频」，bounds 未探出屏。
- 算法秒数：**1.5s**（模型 TokenHub 76s 不算）
- 哪一段：模型 0 框，layout/滑动没跑
- 什么情况：GT 正例，现场切还在。检测模型没标这个可滚分类条。没有框，XML/layout/滑动都用不上。
- 改进方向：不改算法。可恢复 Tab 切本来不算缺陷；模型漏标这条符合精度优先。若以后要测 layout 兜底，得先有框。
- 证据：
  - dump：`/Users/zhangyingying/UX-Agent/HarmonyArena-fdu_agent/ux-detect-output/20260921-230455-301/snapshot_window.json`（树里 button「短视频」bounds `[860,93][955,153]`）
  - 模型：`/Users/zhangyingying/UX-Agent/HarmonyArena-fdu_agent/ux-detect-output/20260921-230455-301/model_result.json` issues=[]
  - layout：`/Users/zhangyingying/UX-Agent/HarmonyArena-fdu_agent/ux-detect-output/20260921-230455-301/layout_result.json` inputCount=0
  - 滑动：skipped
  - 总结果：`/Users/zhangyingying/UX-Agent/HarmonyArena-fdu_agent/ux-detect-output/20260921-230455-301/snapshot_ux.json`
- 状态：**到达同类切；页级通过。** 和已测的 `bifold_image_normal/tencentvideo/g01`「确认开通」不是同一页。

### SAMPLE-ABOUT 代码工坊关于页（构造正例）

- 工程：`测试集/sample_in_harmonyos`（zip 不必再解）。**没有测试集 GT 图**，缺陷是源码 `AboutView.ets` `.translate({ y: -42 })`，标题被版本卡片盖住。
- 路径：我的 → 设置 → 关于（SI-002）
- 包名：`com.huawei.hmos.sample`
- 现场：`arrived=true`。`/Users/zhangyingying/UX-Agent/HarmonyArena-fdu_agent/ux-detect-output/20260920-092333-674/snapshot.png`
- 真机内屏上「HMOS代码工坊」标题是完整的，版本卡片没有盖住标题，构造缺陷没复现。模型标了弹窗后面「用户体验/内容」被挡住的字，页级 unknown。
- 状态：**导航到了；切字没出现。**

### SAMPLE-SI001 代码工坊内容上新 Sample 底部（构造正例）

- 路径：我的 → 内容上新 → Sample → 列表底部。没有 Labelme 图，位置只在 `test-set/构造缺陷位置.txt`。
- 源码：`NewContentItem.ets` 底部「以上是全部更新内容」`.translate({ y: -55 })` 再 `clip(true)`。
- 现场外屏 1080×2504。`/Users/zhangyingying/UX-Agent/HarmonyArena-fdu_agent/ux-detect-output/20260922-192549-509/snapshot.png`
- 模型 1 框打在这行字上。layout `true_truncation` / `local_non_scroll_glyph_clip`，上沿藏 22px（orig `[343,2119][737,2170]`，可见 `[343,2141][737,2170]`）。滑动未跑。
- 算法秒数：**1.9s**（模型 30s 不算）
- 状态：**构造切复现，检出。页级 bad。**

### SAMPLE-SI003 代码工坊设置页标题（构造正例）

- 路径：我的 → 设置。没有 Labelme 图。
- 源码：`SettingView.ets` 标题「设置」`.translate({ y: -36 })`，标题行高 56、字高 24。
- 现场外屏 1080×2504。`/Users/zhangyingying/UX-Agent/HarmonyArena-fdu_agent/ux-detect-output/20260922-193014-743/snapshot.png`
- 模型 1 框打在「设置」上。layout `true_truncation` / `render_layer_occlusion_with_local_clip`，上沿藏约 38px（orig `[75,99][200,174]`，可见 `[75,137][200,174]`）。滑动未跑。
- 算法秒数：**1.7s**（模型 23s 不算）
- 状态：**构造切复现，检出。页级 bad。**

### SAMPLE-SI002 代码工坊关于页（构造正例，外屏）

- 路径：我的 → 设置 → 关于。没有 Labelme 图。`构造缺陷位置.txt` 里这 6 条都是构造截断。
- 源码：`AboutView.ets` 版本卡片 `.translate({ y: -42 })`，盖住标题下沿。
- 现场外屏 1080×2504。`/Users/zhangyingying/UX-Agent/HarmonyArena-fdu_agent/ux-detect-output/20260922-193137-309/snapshot.png`
- 人眼：「HMOS代码工坊」下沿被白卡片切掉。dump 里 Text 的 orig 与可见都是 `[320,662][760,735]`，layout 看不到这块遮挡，verdict `unknown`。上滑 diff 0%，字没让出来，滑动留 `confirmed`。
- 算法秒数：**3.8s**（模型 28s 不算）
- 状态：**构造切复现，检出。页级 bad。**

### SAMPLE-SI004 代码工坊用户体验调研提交按钮（构造正例）

- GT：没有 Labelme 图。位置：我的 → 用户体验调研。清单写「体检按钮」，页面上的字是「提交」。
- XML：无。9 月 17 日包。源码 `QuestionnaireView.ets` 按钮 `.translate({ y: 20 })`，外层 `.clip(true)`。
- 现场图：`/Users/zhangyingying/UX-Agent/HarmonyArena-fdu_agent/ux-detect-output/20260922-195244-097/snapshot.png`
- 页级：ok（漏报）。人眼底部蓝按钮只剩「提交」上沿，下半被屏底裁掉。
- 算法秒数：**1.5s**（模型 13s 不算）
- 哪一段：layout。模型框打在「提交」上，框 `[451,944][551,960]`。
- 什么情况：layout 判 `not_truncation` / `overlay_background_occlusion_out_of_scope`。它把上方 Blank（`[50,1276][1030,2292]`）当成 SheetPage 里的卡片，框在卡片外面（`query_inside_ratio` 0），于是消掉。滑动没跑。页级因此 ok。
- 改进方向：框在内容卡片下方、贴着页面底边被裁时，不要按「框不在卡片内」消掉。改之前要核对腾讯视频「确认开通」那条遮罩负例，框在弹层后面的不能一起打回来。
- 证据：
  - dump：`/Users/zhangyingying/UX-Agent/HarmonyArena-fdu_agent/ux-detect-output/20260922-195244-097/snapshot_window.json`（树里 text「提交」bounds `[46,940][954,965]`）
  - 模型：`/Users/zhangyingying/UX-Agent/HarmonyArena-fdu_agent/ux-detect-output/20260922-195244-097/model_result.json`
  - layout：`/Users/zhangyingying/UX-Agent/HarmonyArena-fdu_agent/ux-detect-output/20260922-195244-097/layout_result.json`
  - 滑动：skipped
  - 总结果：`/Users/zhangyingying/UX-Agent/HarmonyArena-fdu_agent/ux-detect-output/20260922-195244-097/snapshot_ux.json`
- 状态：**第一次漏报。** 已改 `1.1.4-sheet-own-control`。同一页重跑 `20260922-200100-590`：layout `true_truncation`，绑「提交」，下沿 `NavBarContent` 裁切，滑动未跑，页级 bad。单测 22 条通过，框在弹层外的遮罩用例仍消掉。

### SAMPLE-SI005 代码工坊样例分类条（构造正例）

- 路径：样例。源码 `PracticesView.ets` 最后一格分类 `.translate({ x: 48 })`。没有 Labelme 图。
- 现场外屏。`/Users/zhangyingying/UX-Agent/HarmonyArena-fdu_agent/ux-detect-output/20260922-200244-237/snapshot.png`
- 人眼：分类条左边「ArkUI实践」、右边「更多案例」都被切。条还停在中间。
- 模型 2 框。layout 都判 `not_truncation` / `continuous_scroll_glyph_clipping_recoverable`。右边「更多案例」藏 63px（可见右沿 1080，orig 右沿 1143），滚动内容右沿 1193，还能往右滚。滑动未跑。
- 算法秒数：**1.6s**（模型 46s 不算）
- 状态：**第一次两框都按可滚消掉。** 滚动范围改成内容盒之后，同一份 dump 重放：左边「ArkUI实践」仍是可滚 `not_truncation`（内容左沿 -223），右边「更多案例」`toward_end=false`，`scroll_exhausted_glyph_clipping_persists`。

### SAMPLE-SI006 代码工坊实践文章顶栏标题（构造正例）

- 路径：实践 → 文章下滑后顶栏标题。源码 `ArticleDetailView.ets` 标题行高 16、`.translate({ y: -8 })`、`.clip(true)`。没有 Labelme 图。
- 现场图：`/Users/zhangyingying/UX-Agent/HarmonyArena-fdu_agent/ux-detect-output/20260922-200907-178/snapshot.png`
- 页级：ok（漏报）。标题已收到顶栏，「多端UX设计」可见 `[225,175][568,200]`，orig `[225,150][568,200]`，上沿藏 25px。
- 算法秒数：**1.4s**（模型 14s 不算）
- 哪一段：模型。0 框，layout 和滑动都没跑。
- 什么情况：切在顶栏这行字的上沿。模型没标，后面的裁切判断没有输入。
- 改进方向：不改 layout 去扫没框的字。要检出得模型先框到这行标题。
- 证据：
  - dump：`/Users/zhangyingying/UX-Agent/HarmonyArena-fdu_agent/ux-detect-output/20260922-200907-178/snapshot_window.json`
  - 模型：`/Users/zhangyingying/UX-Agent/HarmonyArena-fdu_agent/ux-detect-output/20260922-200907-178/model_result.json` issues=[]
  - 总结果：`/Users/zhangyingying/UX-Agent/HarmonyArena-fdu_agent/ux-detect-output/20260922-200907-178/snapshot_ux.json`
- 状态：**构造切在；模型漏标。页级 ok。**

### TAB-AMAP-G01-S1 高德平板首页（有 XML，图上有截断框）

- GT：`/Users/zhangyingying/UX-Agent/test-set/整理/tablet_xml_normal/amap/g01/tablet_xml_normal_amap_g01_s1.jpg`
- XML：有。`/Users/zhangyingying/UX-Agent/test-set/整理/tablet_xml_normal/amap/g01/tablet_xml_normal_amap_g01_s1.xml`
- 现场图：`/Users/zhangyingying/UX-Agent/HarmonyArena-fdu_agent/ux-detect-output/20260922-222103-655/snapshot.png`
- 页级：unknown
- 算法秒数：**25.9s**（模型 86.5s 不算）。滑动 23.7s。`git pull` 卡在 fetch，用的是本机 verifier `1.1.5`。
- 哪一段：滑动恢复。GT 那颗星本身被消掉了。
- 什么情况：左边快捷条「收藏」被卡片右沿切掉，和 GT 同一处。模型打了一条窄框。layout 绑上 Text「收藏」，右边藏 41px（可见右沿 1050，orig 右沿 1091），方向没认成裁切，`glyph_clipping_boundary_not_found`。左滑探测 16.83%，滑后「收藏」「常去地点」都出来了，判 `scrollable` 消掉。另外顶上一框下滑 diff 0% 留 `confirmed`；地图右缘左滑 14.7%、底栏两框上滑，回滑分别 18.52% / 6.34%，`restore_failed`。页级因此 unknown。底栏「兴豪路1288号」layout 按可滚消掉。
- 改进方向：这张有 XML，快捷条滑得开，GT 框按可滚消掉是对的。页级挂在别的框回不去。先不改算法，下一条之前人把页面拉回原位。
- 证据：
  - dump：`/Users/zhangyingying/UX-Agent/HarmonyArena-fdu_agent/ux-detect-output/20260922-222103-655/snapshot_window.json`
  - 总结果：`/Users/zhangyingying/UX-Agent/HarmonyArena-fdu_agent/ux-detect-output/20260922-222103-655/snapshot_ux.json`
  - 滑后：`.../snapshot_slide_left_1.png`（收藏已完整）
  - 恢复失败：`.../snapshot_slide_left_2.png`、`.../snapshot_slide_up_3.png`
- 状态：**GT 星标滑得出来，已消。页级 unknown（别的框回滑失败）。**

### TAB-AMAP-G02-S1 高德平板消息页（有 XML，负例）

- GT：`/Users/zhangyingying/UX-Agent/test-set/整理/tablet_xml_normal/amap/g02/tablet_xml_normal_amap_g02_s1.jpg`。`正常图=true`，无框。
- XML：有。`/Users/zhangyingying/UX-Agent/test-set/整理/tablet_xml_normal/amap/g02/tablet_xml_normal_amap_g02_s1.xml`
- 现场图：`/Users/zhangyingying/UX-Agent/HarmonyArena-fdu_agent/ux-detect-output/20260922-224507-190/snapshot.png`。左栏是消息列表，条目和 GT 不是同一批，页面同类。
- 页级：unknown
- 算法秒数：**28.0s**（模型 97s 不算）。滑动 25.8s。
- 哪一段：模型误标，滑动把其中 3 框消掉，剩下的没清干净。
- 什么情况：负例不该报截断。模型 6 框。layout 一个都没消。上滑一组里，底边右侧那框探测 13.41% 按可滚消掉；「两周前和长期未读消息」同组但探测 0%，留 `confirmed`。地图右缘一框左滑 9.77% 消掉。消息卡片中间一框右滑 10.93% 消掉。屏最左边两条窄边右滑后回不去，diff 16.58% / 12.12%，`restore_failed`。
- 改进方向：负例页底栏那行字 orig 与可见重合，上滑没动却留 confirmed。先不改，下一条再看是不是同一类底边。
- 证据：`/Users/zhangyingying/UX-Agent/HarmonyArena-fdu_agent/ux-detect-output/20260922-224507-190/snapshot_ux.json`
- 状态：**负例未过。页级 unknown。**

### TAB-DIANPING-G01-S1 大众点评「我的」（有 XML，负例）

- GT：`/Users/zhangyingying/UX-Agent/test-set/整理/tablet_xml_normal/dianping/g01/tablet_xml_normal_dianping_g01_s1.jpg`。`正常图=true`，无框。
- XML：有。现场图和 GT 同一页（FindingRust，「我的」）。`/Users/zhangyingying/UX-Agent/HarmonyArena-fdu_agent/ux-detect-output/20260922-225245-877/snapshot.png`
- 页级：ok。模型 0 框，未滑动。
- 算法秒数：**1.4s**（模型 36s 不算）
- 状态：**负例通过。**

### TAB-12306-G02-S1 铁路 12306 车次列表（有 XML，图上有截断框）

- GT：`/Users/zhangyingying/UX-Agent/test-set/整理/tablet_xml_normal/railway12306/g02/tablet_xml_normal_railway12306_g02_s1.jpg`。框在筛选条右缘。
- XML：有。现场图：`/Users/zhangyingying/UX-Agent/HarmonyArena-fdu_agent/ux-detect-output/20260922-230744-707/snapshot.png`。北京到上海车次列表，和 GT 同类。
- 页级：bad
- 算法秒数：**4.5s**（模型 38s 不算）。滑动 2.5s。
- 哪一段：layout 绑不上，滑动留下。
- 什么情况：模型 1 框，打在右缘车站芯片。dump 里「筛选」按钮在 `[2330,411][2367,430]`，完整。被切的是「上海南」：可见右沿 2800，orig 右沿 2829。这块在 Web 里，类型是 checkBox，不是 Text，layout `no_matching_component`。左滑探测 1.56%，没过 5% 门槛，留 `confirmed`。
- 改进方向：Web 里的 checkBox 右缘探出屏幕时，layout 现在对不上。先不改。
- 证据：`/Users/zhangyingying/UX-Agent/HarmonyArena-fdu_agent/ux-detect-output/20260922-230744-707/snapshot_ux.json`
- 状态：**右缘切到了，页级 bad。切的是「上海南」，不是 GT 上的「筛选」。**

### TAB-DIANPING-G02-S1 大众点评首页（有 XML，负例）

- GT：`/Users/zhangyingying/UX-Agent/test-set/整理/tablet_xml_normal/dianping/g02/tablet_xml_normal_dianping_g02_s1.jpg`。`正常图=true`，无框。
- 状态：**现场复现不了，未跑检测。**

### TAB-KUGOU-G01-S1 酷狗搜索页（有 XML，负例）

- GT：`/Users/zhangyingying/UX-Agent/test-set/整理/tablet_xml_normal/kugou/g01/tablet_xml_normal_kugou_g01_s1.jpg`。`正常图=true`，无框。
- XML：有。现场图是搜索页（历史搜索、猜你想搜、热搜榜、DJ榜），和 GT 同类。`/Users/zhangyingying/UX-Agent/HarmonyArena-fdu_agent/ux-detect-output/20260923-210450-195/snapshot.png`
- 页级：ok。模型 1 框，打在底栏播放条「10」上。layout 绑到完整可见的 Text「10」，判成 TabBar 遮挡消掉。未滑动。
- 算法秒数：**2.4s**（模型 18.6s 不算）
- 状态：**负例通过。layout 消掉，不是靠滑动过的。**

### TAB-KUGOU-G02-S1 酷狗粤语歌单（有 XML，负例）

- GT：`/Users/zhangyingying/UX-Agent/test-set/整理/tablet_xml_normal/kugou/g02/tablet_xml_normal_kugou_g02_s1.jpg`。`正常图=true`，无框。
- XML：有。现场图是粤语单曲推荐，和 GT 同类。`/Users/zhangyingying/UX-Agent/HarmonyArena-fdu_agent/ux-detect-output/20260923-210654-923/snapshot.png`
- 页级：ok。模型 1 框，打在底栏盖住的最后一首「蔡国权」上。layout 绑到完整可见的 Text「蔡国权」，判成 TabBar 遮挡消掉。未滑动。
- 算法秒数：**2.6s**（模型 11.2s 不算）
- 状态：**负例通过。layout 消掉，不是靠滑动过的。**

### TAB-12306-G01-S1 铁路 12306「我的」（有 XML，负例）

- GT：`/Users/zhangyingying/UX-Agent/test-set/整理/tablet_xml_normal/railway12306/g01/tablet_xml_normal_railway12306_g01_s1.jpg`。`正常图=true`，无框。
- XML：有。现场图是「我的」未登录页，和 GT 同一页。`/Users/zhangyingying/UX-Agent/HarmonyArena-fdu_agent/ux-detect-output/20260923-211010-600/snapshot.png`
- 页级：ok。模型 0 框，未滑动。
- 算法秒数：**1.5s**（模型 6.2s 不算）
- 状态：**负例通过。模型没出框，滑动没跑。**

### TAB-MEETING-G01-S1 腾讯会议登录页（有 XML，负例）

- GT：`/Users/zhangyingying/UX-Agent/test-set/整理/tablet_xml_normal/tencentmeeting/g01/tablet_xml_normal_tencentmeeting_g01_s1.jpg`。`正常图=true`，无框。
- 状态：**人眼看过，页面正常，未跑检测。**

### TAB-MEETING-G02-S1 腾讯会议首页（有 XML，负例）

- GT：`/Users/zhangyingying/UX-Agent/test-set/整理/tablet_xml_normal/tencentmeeting/g02/tablet_xml_normal_tencentmeeting_g02_s1.jpg`。`正常图=true`，无框。
- 模型标注：`labels_json` 空，没有框图。
- 状态：**模型没标，未跑检测。**

### TAB-WPS-G01-S1 WPS 最近（有 XML，遮盖图标）

- GT：`/Users/zhangyingying/UX-Agent/test-set/整理/tablet_xml_normal/wps/g01/tablet_xml_normal_wps_g01_s1.jpg`。`正常图=false`，1 个 `遮盖-图标`，在右下角分享图标上。
- XML：有。现场图是「最近」文件列表，和 GT 同类。`/Users/zhangyingying/UX-Agent/HarmonyArena-fdu_agent/ux-detect-output/20260923-212942-395/snapshot.png`
- 参考模型：`labels_json` 空，没有框图。
- 页级：ok。我们的模型 0 框，未滑动。正式标注是加号挡住分享图标，不是文字截断。
- 算法秒数：**2.0s**（模型 8.3s 不算）
- 状态：**遮盖没标出来。滑动没跑。**

### TAB-WPS-G01-S1-PROMPT WPS 最近，定制提示词重跑

- 提示词：在默认提示后加了一句，要求把右下角被红色加号挡住的小组件框出来，不要框加号本身。只这一次，`UX_DETECT_PROMPT`，没改默认提示词。
- 现场图：仍是 WPS「最近」。`/Users/zhangyingying/UX-Agent/HarmonyArena-fdu_agent/ux-detect-output/20260923-213220-738/snapshot.png`
- 页级：bad
- 算法秒数：**4.6s**（模型 12.5s 不算）。滑动 2.2s。
- 哪一段：layout 绑不上，滑动没过门槛。
- 什么情况：模型 1 框 `[941,957,956,982]`，打在加号左边的分享图标上，和正式标注的遮盖图标基本重合。layout `no_matching_component`。上滑 diff 3.77%，没过 5%，留 `confirmed`。
- 改进方向：加号是固定按钮，上滑列表盖不住这块。先不改。
- 证据：`/Users/zhangyingying/UX-Agent/HarmonyArena-fdu_agent/ux-detect-output/20260923-213220-738/snapshot_ux.json`
- 状态：**标出来了，算法没消掉。页级 bad。**

### TAB-WPS-G02-S1 WPS 云盘（有 XML，负例）

- GT：`/Users/zhangyingying/UX-Agent/test-set/整理/tablet_xml_normal/wps/g02/tablet_xml_normal_wps_g02_s1.jpg`。`正常图=true`，无框。
- XML：有。现场图是云盘，和 GT 同一页。`/Users/zhangyingying/UX-Agent/HarmonyArena-fdu_agent/ux-detect-output/20260923-214251-108/snapshot.png`
- 参考模型：`labels_json` 空。
- 页级：bad
- 算法秒数：**5.0s**（模型 12.6s 不算）。滑动 2.8s。
- 哪一段：模型把省略号当截断，layout 没消，左滑 0% 留下。
- 什么情况：负例不该报截断。模型 1 框打在「我的云服务」下的「查看空间及云...」。dump 里这段字是「查看空间及云功能」，bounds 与 orig 重合 `[294,337][515,372]`，没有藏字。layout `glyph_clipping_boundary_not_found`。左滑探测 0%，整页差 0%，回滑跳过，留 `confirmed`。
- 改进方向：dump 里没有省略号字符，和真切字的产物一样。算法不改。记入文首风险。
- 证据：`/Users/zhangyingying/UX-Agent/HarmonyArena-fdu_agent/ux-detect-output/20260923-214251-108/snapshot_ux.json`
- 状态：**负例未过。页级 bad。算法未改。**

### TAB-UC-G01-S1 UC「我的」（有 XML，负例）

- GT：`/Users/zhangyingying/UX-Agent/test-set/整理/tablet_xml_normal/uc/g01/tablet_xml_normal_uc_g01_s1.jpg`。`正常图=true`，无框。
- 参考模型：`labels_json` 空。
- 状态：**人眼看过，页面正常，未跑检测。**

### TRI-JD-XML-G01-S3-R 京东首页三屏（本机 2026-09-23）

- 设备：`5GU0125610000110`，三屏 `3184×2232`。未改折叠。
- GT：`正常图=true`。参考模型 `labels_json` 空。
- 现场：京东首页。`/Users/zhangyingying/UX-Agent/HarmonyArena-fdu_agent/ux-detect-output/20260923-230011-700/snapshot.png`
- 页级：ok。模型 0 框，未滑动。算法 **2.1s**（模型 21.4s 不算）。
- 状态：**负例通过。**

### TRI-QQMUSIC-XML-G01-S3-R QQ 音乐推荐页三屏（本机 2026-09-23）

- GT：`正常图=true`。参考模型空。
- 现场：推荐页，「大家都在听」。开屏广告点了跳过。`/Users/zhangyingying/UX-Agent/HarmonyArena-fdu_agent/ux-detect-output/20260923-230205-338/snapshot.png`
- 页级：bad
- 算法秒数：**6.3s**（模型 29.3s 不算）。滑动 3.6s。
- 哪一段：模型把屏幕右缘露出的下一张封面当截断，layout 绑不上，左滑 0% 留下。
- 什么情况：负例。三框都贴右缘 `[989,480,1000,507]`、`[976,570,1000,591]`、`[986,663,1000,684]`。layout 都是 `no_matching_component`。一组左滑，探测差都是 0%，留 `confirmed`。
- 改进方向：人眼确认不是截断，横向列表左滑滑得出来。算法这次手指在 `(3082,1299)`→`(2764,1299)`，探测差 0%，整页也没动，回滑跳过，三框留 confirmed。和真切字的 0% 同一条。算法先不改。
- 证据：`/Users/zhangyingying/UX-Agent/HarmonyArena-fdu_agent/ux-detect-output/20260923-230205-338/snapshot_ux.json`，滑动记录 `slide-ops.jsonl`
- 状态：**人眼：不是截断。宽屏合成一次左滑后已消掉。** 复用 `233642-501` 的两个模型框重放 `234501-154`：一组，起点 `(2165,1307)`，行程 180，两框差 25.48% / 67.38%，都移除，回滑一次差 0%，页级 ok。右缘起手会拉出工具栏，不再从那儿划。

### TRI-TOUTIAO-XML-G01-S3-R 今日头条推荐三屏（本机 2026-09-23）

- GT：`正常图=true`。参考模型空。
- 现场：推荐流。`/Users/zhangyingying/UX-Agent/HarmonyArena-fdu_agent/ux-detect-output/20260923-230314-943/snapshot.png`
- 页级：ok。模型 0 框，未滑动。算法 **1.6s**（模型 8.0s 不算）。
- 状态：**负例通过。**

### TRI-WECOM-XML-G01-S3-R 企业微信工作台三屏（本机 2026-09-23）

- GT：`正常图=true`。参考模型空。
- 现场：先落在 5.0.10 新功能介绍，退回工作台后再测。`/Users/zhangyingying/UX-Agent/HarmonyArena-fdu_agent/ux-detect-output/20260923-230411-777/snapshot.png`
- 页级：ok。模型 0 框，未滑动。算法 **1.5s**（模型 5.4s 不算）。
- 状态：**负例通过。**

| id | 到达 | 模型框 | 滑动 | 页级结论 | 和 GT | 备注 |
|---|---|---|---|---|---|---|
| BF-XHS-G01-S2 | 已到上海/活动 | 3 底切框 | 未滑（layout 消解） | ok | 通过（XML 兜底） | 075415-064；简单 case 先放着 |
| BF-ALIPAY-G01-S2 | GPT arrived | 4 底切框 | 1 组 4 框全消解 | ok | 通过（layout unknown→slide） | **6.3s 算法** / 082806-346 |
| BF-ALIPAY-G02-S2 | GPT arrived + dump 停靠 | 2 底切框 | 未滑（layout 消解） | ok | 同类底切（亲密度，非商家服务） | **2.2s 算法** / 084616-143 |
| BF-TXV-G01-S2 | GPT arrived 确认开通 | 3 底框（遮罩后） | 未滑（layout 消解） | ok | 负例通过 | **1.7s 算法** / 094538-981；遮罩后误标已消 |
| BF-ALIPAY-G03-S2 | 人手点到选城市 | 1 底切框（巴音郭楞） | 1 组可滚消解 | ok | 同类底切 | **6.5s 算法** / 095100-226 |
| BF-BILI-G01-S2 | 人手点到热门 | 1 底切框（变形强强） | 未滑（layout 消解） | ok | 同类底切 | **2.0s 算法** / 095411-334 |
| BF-BILI-G02-S2 | 人手点到视频详情 | 1 底切框 | 未滑（layout 消解） | ok | 同类底切 | **1.9s 算法** / 100205-946；关弹幕后过 |
| BF-BILI-G03-S2 | 人手点到会员购 | 1 右切框（平台资质） | 未滑（layout 消解） | ok | 同类右切 | **2.0s 算法** / 100453-129 |
| BF-FANQIE-G01-S2 | 人手点到短篇 | 1～3 框（更多前） | 左滑 0% 跳过恢复 | bad | 检出切字 | **4.1s 算法** / 101733-732 |
| BF-FANQIE-G02-S2 | 人手点到书籍搜索 | 1 底切框（天渊） | 上滑可滚消解 | ok | 同类底切 | **7.2s 算法** / 102604-248 |
| BF-FANQIE-G03-S2 | 人手点到看剧 | 1 框（海报误标） | 上滑可滚、一次恢复 | ok | 负例通过 | **7.7s 算法** / 104426-529；黑屏那次作废 |
| BF-MEITUAN-G01-S2 | 人手点到达美乐团购 | 4 框；GT 榴莲 layout 消 | 底边 unknown 上滑可滚 | ok | 通过（可恢复底切） | **9.0s 算法** / 112100-798；标题假阳已修，本次模型未再标 |
| BF-MEITUAN-G02-S2 | 人手点到影院列表 | 2 框（店名+价格） | 1 组上滑可滚 | ok | 同类底切 | **7.2s 算法** / 113147-818；恢复 2.42% 擦线 |
| BF-MEITUAN-G03-S2 | 人手点到拼好饭 | 2 框；layout unknown | 左+上均可滚并恢复 | ok | 同类切，可恢复通过 | **27.2s** / 092942-523；前回滑失败已修 |
| BF-MEITUAN-G04-S2 | 酒店民宿已铺满 | 未跑 | — | 作废 | 切字无法复现 | 现版下拉筛选底栏完整；无 XML 不端到端 |
| BF-MEITUAN-G05-S2 | 未测 | 未跑 | — | 不端到端 | 无 XML | 2026-09-21 起只测有 xml 的 |
| BF-TXV-XML-G01-S2 | 人手点到首页 | 0 框 | 未滑 | ok | 同类右切，模型未标 | **1.5s 算法** / 230455-301；dump 字完整 |
| SAMPLE-ABOUT | GPT arrived 关于 | 3 框（弹窗后背景） | 留下 | unknown | 构造切字未复现 | 092333-674；标题完整 |
| SAMPLE-SI001 | 人手点到内容上新 Sample 底 | 1 框（以上是全部更新内容） | 未滑（layout 真截断） | bad | 构造上切检出 | **1.9s 算法** / 192549-509；上沿藏 22px |
| SAMPLE-SI003 | 人手点到设置 | 1 框（设置） | 未滑（layout 真截断） | bad | 构造上切检出 | **1.7s 算法** / 193014-743；标题上沿被裁 |
| SAMPLE-SI002 | 人手点到关于（外屏） | 1 框（HMOS代码工坊） | 上滑 0% 留 confirmed | bad | 构造下切检出 | **3.8s 算法** / 193137-309；卡片切掉标题下沿 |
| SAMPLE-SI004 | 人手点到用户体验调研 | 1 框（提交） | 未滑（layout 消掉） | ok | 构造下切漏报 | **1.5s 算法** / 195244-097；框在 Blank 外被当成遮挡 |
| SAMPLE-SI004-R | 仍在用户体验调研 | 1 框（提交） | 未滑（layout 真截断） | bad | 构造下切检出 | **1.5s 算法** / 200100-590；1.1.4 后重跑 |
| SAMPLE-SI005 | 样例分类条停在中间 | 2 框（左 ArkUI实践、右更多案例） | 未滑（layout 可滚消掉） | ok | 两框都消了 | **1.6s 算法** / 200244-237 |
| SAMPLE-SI005-R | 仍在样例分类条 | 2 框，留下更多案例 | 未滑 | bad | 左可滚、右真截断 | **1.7s 算法** / 200718-914；1.1.5 |
| SAMPLE-SI006 | 实践文章顶栏「多端UX设计」 | 0 框 | 未滑 | ok | 构造上切漏报 | **1.4s 算法** / 200907-178；上沿藏 25px，模型未标 |
| SAMPLE-SI006-R | 再往下滚一点 | 0 框 | 未滑 | ok | 仍漏标 | **1.4s 算法** / 201050-414；标题 bounds 未变 |
| TAB-AMAP-G01-S1 | 人手点到高德首页 | 6 框；收藏左滑消掉 | 顶 confirmed；右缘和底栏 restore_failed | unknown | 星标滑得出来 | **25.9s 算法** / 222103-655 |
| TAB-AMAP-G02-S1 | 人手点到高德消息 | 6 框 | 3 框可滚消掉；底栏 confirmed；左边两条 restore_failed | unknown | 负例未过 | **28.0s 算法** / 224507-190 |
| TAB-DIANPING-G01-S1 | 人手点到大众点评我的 | 0 框 | 未滑 | ok | 负例通过 | **1.4s 算法** / 225245-877 |
| TAB-12306-G02-S1 | 人手点到北京-上海车次 | 1 框（右缘上海南） | 左滑 1.56% confirmed | bad | 右缘切到；不是筛选 | **4.5s 算法** / 230744-707 |
| TAB-DIANPING-G02-S1 | 复现不了 | 未跑 | — | 作废 | 负例未测 | 2026-09-23 现场对不上 |
| TAB-KUGOU-G01-S1 | 人手点到酷狗搜索 | 1 框（底栏「10」） | 未滑（layout 消掉） | ok | 负例通过 | **2.4s 算法** / 210450-195 |
| TAB-KUGOU-G02-S1 | 人手点到酷狗粤语 | 1 框（底栏「蔡国权」） | 未滑（layout 消掉） | ok | 负例通过 | **2.6s 算法** / 210654-923 |
| TAB-12306-G01-S1 | 人手点到 12306 我的 | 0 框 | 未滑 | ok | 负例通过 | **1.5s 算法** / 211010-600 |
| TAB-MEETING-G01-S1 | 人眼看过登录页 | 未跑 | — | 跳过 | 负例未测 | 2026-09-23 看着正常 |
| TAB-MEETING-G02-S1 | 模型没标 | 未跑 | — | 跳过 | 负例未测 | labels_json 空 |
| TAB-UC-G01-S1 | 人眼看过 UC 我的 | 未跑 | — | 跳过 | 负例未测 | 2026-09-23 看着正常 |
| TRI-JD-XML-G01-S3-R | 本机打开京东首页 | 0 框 | 未滑 | ok | 负例通过 | **2.1s 算法** / 230011-700 |
| TRI-QQMUSIC-XML-G01-S3-R | 本机打开推荐页 | 3 框（右缘封面） | 左滑 0% confirmed | bad | 人眼不是截断 | **6.3s 算法** / 230205-338；手指没带动列表 |
| TRI-TOUTIAO-XML-G01-S3-R | 本机打开头条推荐 | 0 框 | 未滑 | ok | 负例通过 | **1.6s 算法** / 230314-943 |
| TRI-WECOM-XML-G01-S3-R | 退回工作台后测 | 0 框 | 未滑 | ok | 负例通过 | **1.5s 算法** / 230411-777 |
| TAB-WPS-G01-S1 | 人手点到 WPS 最近 | 0 框 | 未滑 | ok | 遮盖图标未标 | **2.0s 算法** / 212942-395 |
| TAB-WPS-G01-S1-PROMPT | 仍在 WPS 最近 | 1 框（分享图标） | 上滑 3.77% confirmed | bad | 遮盖标出但没消 | **4.6s 算法** / 213220-738；定制提示词；回滑被跳过 |
| TAB-WPS-G01-S1-PROMPT-R | 人手滑回 WPS 最近 | 1 框（分享图标） | 上滑 4.31% confirmed，回滑 0.96% 成功 | bad | 遮盖仍留下 | **7.9s 算法** / 213836-856；变化像素 14.2% 触发回滑 |
| TAB-WPS-G02-S1 | 人手点到 WPS 云盘 | 1 框（查看空间及云...） | 左滑 0% confirmed，未回滑 | bad | 负例未过 | **5.0s 算法** / 214251-108；省略号 |

### WF-VIPSHOP-XML-G01-S2 唯品会首页分类栏右切（正例）

- GT：`测试集/整理/widefold_xml_normal/vipshop/g01/widefold_xml_normal_vipshop_g01_s2.jpg`
- XML：`测试集/整理/widefold_xml_normal/vipshop/g01/widefold_xml_normal_vipshop_g01_s2.xml`
- 包名：`com.vip.hosapp`
- 你怎么点：首页 + 右侧搜索页；搜索页停在「最近搜索 / 猜你想搜」，左侧首页顶部分类栏保持横向类目露出最右一项。
- 现场图：`HarmonyArena-fdu_agent/ux-detect-output/20260922-190710-095/snapshot.png`
- 页级：**算法 ok；人眼 bad / 模型漏报**
- 人眼：GT 是左侧首页顶部分类栏最右「数码」右切；现场同类位置最右「鞋…」/类目标签也被右侧边界切开，属于同类右切。
- 算法秒数：**2.3s**（模型 11.3s 不算；总 13.6s）
- 哪一段：**模型漏报**。官方 HTTP detect 返回 `overall=ok`、`issues=[]`，layout/slide 没有候选可验证。
- 什么情况：页面和 GT 同类且有 XML；截断在左侧横向分类 Tab 的最右项，模型没有出框，导致后续阶段跳过。
- 改进方向：需要让模型/前置提示更关注横向分类栏边缘截断；或者增加 layout 兜底扫描横向 tab 末项 bounds 是否探出/贴边，但要小心可横滑类目可恢复，不要直接判死。
- 证据：
  - dump：`HarmonyArena-fdu_agent/ux-detect-output/20260922-190710-095/snapshot_window.json`
  - 模型：`HarmonyArena-fdu_agent/ux-detect-output/20260922-190710-095/model_result.json` issues=[]
  - layout：`HarmonyArena-fdu_agent/ux-detect-output/20260922-190710-095/layout_result.json` inputCount=0
  - 滑动：`HarmonyArena-fdu_agent/ux-detect-output/20260922-190710-095/slide_result.json` skipped
  - 总结果：`HarmonyArena-fdu_agent/ux-detect-output/20260922-190710-095/snapshot_ux.json`
- 状态：**到达同类切；模型漏报，算法挂了。**

| id | 到达 | 模型框 | 滑动 | 页级结论 | 和 GT | 备注 |
|---|---|---|---|---|---|---|
| WF-VIPSHOP-XML-G01-S2 | 人手点到唯品会首页+右侧搜索页 | 0 框 | 未滑 | 算法 ok / 人眼 bad | 同类右切漏报 | **2.3s 算法** / 190710-095；左栏分类 Tab 最右「鞋…」被切，GT 为「数码」右切 |

### WF-XIANYU-XML-G01-S2 闲鱼首页分类栏右切（正例）

- GT：`测试集/整理/widefold_xml_normal/xianyu/g01/widefold_xml_normal_xianyu_g01_s2.jpg`
- XML：`测试集/整理/widefold_xml_normal/xianyu/g01/widefold_xml_normal_xianyu_g01_s2.xml`
- 包名：`com.taobao.idlefish4ohos`
- 你怎么点：首页推荐流；顶部搜索框可为「华为手机」/「笔记本电脑」等，顶部横向分类栏露出最右「包装…」。
- 现场图：`HarmonyArena-fdu_agent/ux-detect-output/20260922-193839-740/snapshot.png`
- 页级：**ok**
- 人眼：GT 标的是顶部横向分类栏右边缘文字右切；现场同类位置最右「包装…」被右边缘切开。
- 算法秒数：**9.0s**（模型 16.6s 不算；总 25.7s）
- 哪一段：模型命中，layout 未消，slide 消解；但算法段超 7s 预算。
- 什么情况：官方 HTTP detect 返回 1 个 `截断-文字/right` 框，框在右侧「包装…」。layout 判 `unsupported_or_unmatched_issue`，左滑后 diff=23.75%，判定为可横滑恢复，最终页级 ok。
- 改进方向：功能结论通过；性能上 slide 阶段 6.7s，加上截图/dump 后算法段 9.0s，需要继续压缩滑动/截图/恢复等待。此类横向分类栏如果 layout 能识别为可横滑容器，可减少实际滑动成本。
- 证据：
  - 框图：`HarmonyArena-fdu_agent/ux-detect-output/20260922-193839-740/snapshot_bbox.png`
  - dump：`HarmonyArena-fdu_agent/ux-detect-output/20260922-193839-740/snapshot_window.json`
  - 模型：`HarmonyArena-fdu_agent/ux-detect-output/20260922-193839-740/model_result.json` 1 框 `[928,136,962,160]`
  - layout：`HarmonyArena-fdu_agent/ux-detect-output/20260922-193839-740/layout_result.json` unknown
  - 滑动：`HarmonyArena-fdu_agent/ux-detect-output/20260922-193839-740/slide_result.json` left / scrollable / diff=23.75
  - 总结果：`HarmonyArena-fdu_agent/ux-detect-output/20260922-193839-740/snapshot_ux.json`
- 状态：**到达同类切；模型命中，slide 可恢复消解，页级通过；算法段超时。**

| id | 到达 | 模型框 | 滑动 | 页级结论 | 和 GT | 备注 |
|---|---|---|---|---|---|---|
| WF-XIANYU-XML-G01-S2 | 人手点到闲鱼首页推荐流 | 1 右切框 | 左滑可滚消解 | ok | 同类右切命中 | **9.0s 算法** / 193839-740；官方 8000，slide 6.7s 导致超预算 |

### WF-TAOBAO-XML-G01-S2 淘宝我的淘宝（负例）

- GT：`测试集/整理/widefold_xml_normal/taobao/g01/widefold_xml_normal_taobao_g01_s2.jpg`
- XML：`测试集/整理/widefold_xml_normal/taobao/g01/widefold_xml_normal_taobao_g01_s2.xml`
- 包名：`com.taobao.taobao4hmos`
- 你怎么点：淘宝底栏「我的淘宝」，停在账号页；看到「我的订单」「快递 / 收藏 / 关注店铺 / 足迹」「领券中心」等模块。
- 现场图：`HarmonyArena-fdu_agent/ux-detect-output/20260922-194833-143/snapshot.png`
- 页级：**ok**
- 人眼：现场为内屏大屏「我的淘宝」页，和 GT 同类；无明显文字/组件/图标截断。
- 算法秒数：**2.0s**（模型 4.5s 不算；总 6.5s）
- 哪一段：模型 0 框，layout 输入 0，slide 跳过。
- 什么情况：官方 HTTP detect 返回 `overall=ok`、`issues=[]`，负例无误报。
- 证据：
  - dump：`HarmonyArena-fdu_agent/ux-detect-output/20260922-194833-143/snapshot_window.json`
  - 模型：`HarmonyArena-fdu_agent/ux-detect-output/20260922-194833-143/model_result.json` issues=[]
  - layout：`HarmonyArena-fdu_agent/ux-detect-output/20260922-194833-143/layout_result.json` inputCount=0
  - 滑动：`HarmonyArena-fdu_agent/ux-detect-output/20260922-194833-143/slide_result.json` skipped
  - 总结果：`HarmonyArena-fdu_agent/ux-detect-output/20260922-194833-143/snapshot_ux.json`
- 状态：**负例通过；官方 8000 无误报，算法段未超时。**

| id | 到达 | 模型框 | 滑动 | 页级结论 | 和 GT | 备注 |
|---|---|---|---|---|---|---|
| WF-TAOBAO-XML-G01-S2 | 人手点到我的淘宝 | 0 框 | 未滑 | ok | 负例通过 | **2.0s 算法** / 194833-143；官方 8000 无误报 |

### WF-DIDI-XML-G01-S2 滴滴首页服务页（负例）

- GT：`测试集/整理/widefold_xml_normal/didi/g01/widefold_xml_normal_didi_g01_s2.jpg`
- XML：`测试集/整理/widefold_xml_normal/didi/g01/widefold_xml_normal_didi_g01_s2.xml`
- 包名：`com.sdu.didi.hmos.psnger`
- 你怎么点：滴滴首页内屏大屏；左侧为「出行 / 送货 / 旅行 / 车主」Tab 和「您想去哪儿？」卡片，右侧为服务列表。
- 现场图：`HarmonyArena-fdu_agent/ux-detect-output/20260922-195252-366/snapshot.png`
- 页级：**ok**
- 人眼：现场为滴滴内屏大屏服务页，和 GT 同类；无明显文字/组件/图标截断。
- 算法秒数：**1.9s**（模型 5.1s 不算；总 7.0s）
- 哪一段：模型 0 框，layout 输入 0，slide 跳过。
- 什么情况：官方 HTTP detect 返回 `overall=ok`、`issues=[]`，负例无误报。
- 证据：
  - dump：`HarmonyArena-fdu_agent/ux-detect-output/20260922-195252-366/snapshot_window.json`
  - 模型：`HarmonyArena-fdu_agent/ux-detect-output/20260922-195252-366/model_result.json` issues=[]
  - layout：`HarmonyArena-fdu_agent/ux-detect-output/20260922-195252-366/layout_result.json` inputCount=0
  - 滑动：`HarmonyArena-fdu_agent/ux-detect-output/20260922-195252-366/slide_result.json` skipped
  - 总结果：`HarmonyArena-fdu_agent/ux-detect-output/20260922-195252-366/snapshot_ux.json`
- 状态：**负例通过；官方 8000 无误报，算法段未超时。**

| id | 到达 | 模型框 | 滑动 | 页级结论 | 和 GT | 备注 |
|---|---|---|---|---|---|---|
| WF-DIDI-XML-G01-S2 | 人手点到滴滴首页服务页 | 0 框 | 未滑 | ok | 负例通过 | **1.9s 算法** / 195252-366；官方 8000 无误报 |

### WF-DOUYIN-XML-G01-S2 抖音消息页（负例）

- GT：`测试集/整理/widefold_xml_normal/douyin/g01/widefold_xml_normal_douyin_g01_s2.jpg`
- XML：`测试集/整理/widefold_xml_normal/douyin/g01/widefold_xml_normal_douyin_g01_s2.xml`
- 包名：`com.ss.hm.ugc.aweme`
- 你怎么点：抖音底栏「消息」，停在消息页；顶部标题「消息」，列表含「发日常 / 状态设置」「新关注我的 / 互动消息」。
- 现场图：`HarmonyArena-fdu_agent/ux-detect-output/20260922-195638-917/snapshot.png`
- 页级：**ok**
- 人眼：现场为抖音内屏大屏消息页，和 GT 同类；无明显文字/组件/图标截断。
- 算法秒数：**1.9s**（模型 3.7s 不算；总 5.6s）
- 哪一段：模型 0 框，layout 输入 0，slide 跳过。
- 什么情况：官方 HTTP detect 返回 `overall=ok`、`issues=[]`，负例无误报。
- 证据：
  - dump：`HarmonyArena-fdu_agent/ux-detect-output/20260922-195638-917/snapshot_window.json`
  - 模型：`HarmonyArena-fdu_agent/ux-detect-output/20260922-195638-917/model_result.json` issues=[]
  - layout：`HarmonyArena-fdu_agent/ux-detect-output/20260922-195638-917/layout_result.json` inputCount=0
  - 滑动：`HarmonyArena-fdu_agent/ux-detect-output/20260922-195638-917/slide_result.json` skipped
  - 总结果：`HarmonyArena-fdu_agent/ux-detect-output/20260922-195638-917/snapshot_ux.json`
- 状态：**负例通过；官方 8000 无误报，算法段未超时。**

| id | 到达 | 模型框 | 滑动 | 页级结论 | 和 GT | 备注 |
|---|---|---|---|---|---|---|
| WF-DOUYIN-XML-G01-S2 | 人手点到抖音消息页 | 0 框 | 未滑 | ok | 负例通过 | **1.9s 算法** / 195638-917；官方 8000 无误报 |

### WF-XIANYU-XML-G01-S1 闲鱼首页分类栏/服务区右切（正例）

- GT：`测试集/整理/widefold_xml_normal/xianyu/g01/widefold_xml_normal_xianyu_g01_s1.jpg`
- XML：`测试集/整理/widefold_xml_normal/xianyu/g01/widefold_xml_normal_xianyu_g01_s1.xml`
- 包名：`com.taobao.idlefish4ohos`
- 你怎么点：Pura X 外屏/单屏 `1264x1848`，闲鱼首页推荐流；顶部搜索框可为「牛仔裤」，顶部横向分类栏最右露出「手…」。
- 现场图：`HarmonyArena-fdu_agent/ux-detect-output/20260922-200818-182/snapshot.png`
- 页级：**算法 bad；人手复核应 ok**
- 人眼：GT 标的是顶部分类栏最右文字右切，以及右侧服务区图标/文字右切；现场同类位置都存在右切。
- 算法秒数：**7.4s**（模型 11.1s 不算；总 18.5s）
- 哪一段：模型命中 3 框，layout 全 unknown，但 slide 验证误判，最终把 3 个可恢复框都保留成 bad。算法段略超 7s 预算。
- 什么情况：官方 HTTP detect 返回 3 个框：顶部「手…」右切文字、右侧图标右切、右侧文字右切。layout 均 `unsupported_or_unmatched_issue`。slide 对顶部框错误试了 down；对右侧两框分组试 left，但 diff=0 判 confirmed。人手复核这几个框都能左滑恢复/消失，所以这轮最终 bad 是算法误判。
- 改进方向：右切框在横向可滚区域时应优先左滑验证，顶部分类栏 dump 里已有 `scrollable=true`，不应选 down。右侧服务区也需要把滑点落到实际可横滑区域；若用户左滑可恢复而算法 diff=0，要检查滑点、探测区域和可滚容器绑定。
- 证据：
  - 框图：`HarmonyArena-fdu_agent/ux-detect-output/20260922-200818-182/snapshot_bbox_final.png`
  - dump：`HarmonyArena-fdu_agent/ux-detect-output/20260922-200818-182/snapshot_window.json`
  - 模型：`HarmonyArena-fdu_agent/ux-detect-output/20260922-200818-182/model_result.json` 3 框
  - layout：`HarmonyArena-fdu_agent/ux-detect-output/20260922-200818-182/layout_result.json` 3 unknown
  - 滑动：`HarmonyArena-fdu_agent/ux-detect-output/20260922-200818-182/slide_result.json` confirmed x3（人手复核为左滑可恢复）
  - 总结果：`HarmonyArena-fdu_agent/ux-detect-output/20260922-200818-182/snapshot_ux.json`
- 状态：**到达同类切；模型命中 GT，但三框人手左滑可恢复，算法误判 bad。**

| id | 到达 | 模型框 | 滑动 | 页级结论 | 和 GT | 备注 |
|---|---|---|---|---|---|---|
| WF-XIANYU-XML-G01-S1 | 人手点到闲鱼外屏首页推荐流 | 3 右切框 | 算法 confirmed；人手左滑可恢复 | 算法 bad / 人眼应 ok | 同类右切命中但误保留 | **7.4s 算法** / 200818-182；顶部误选 down，右侧 left 探测未打到可恢复 |

### WF-TAOBAO-XML-G01-S1 淘宝我的淘宝顶切+右切（正例）

- GT：`测试集/整理/widefold_xml_normal/taobao/g01/widefold_xml_normal_taobao_g01_s1.jpg`
- XML：`测试集/整理/widefold_xml_normal/taobao/g01/widefold_xml_normal_taobao_g01_s1.xml`
- 包名：`com.taobao.taobao4hmos`
- 你怎么点：Pura X 外屏/单屏 `1264x1848`，淘宝底栏「我的淘宝」；页面停在顶部资产/权益区被上边缘切掉，同时底部领券中心右侧优惠券露出一部分。
- 现场图：`HarmonyArena-fdu_agent/ux-detect-output/20260922-202437-864/snapshot.png`
- 页级：**算法 ok；人眼仍有 GT 同类顶切 + 右切验证误消解**
- 人眼：GT 有 5 个标注：顶部「领红包 / 领优惠 / 领金币」一带 3 个顶切文字，右侧优惠券区域 1 个文字右切 + 1 个组件右切。现场同类页面里顶部资产/权益区仍被上边缘切开，右侧优惠券也露出右切。
- 算法秒数：**7.8s**（模型 9.0s 不算；总 16.8s）
- 哪一段：两处问题。第一，模型漏报顶部 3 个 GT 顶切文字；`model_result.json` 只返回右侧优惠券区域 2 个 `截断-文字/right` 框，不存在“顶部先检出再被消解”。第二，slide 对右切优惠券用了 up，上滑后 `snapshot_slide_up_0.png` 里最右优惠券仍然右切，却被判 `scrollable` 并移除，最终页级 ok 不可信。
- 什么情况：GT 有 5 个标注：顶部 3 个顶切文字、右侧 1 个文字右切、右侧 1 个组件右切。当前模型只命中右侧文字框，漏掉顶部顶切和右侧组件框。右侧优惠券按人眼/交互应通过左滑验证是否可恢复；本轮算法走上滑，虽然页面纵向滚动了，但没有证明右切消失，属于误消解。算法段 7.8s 也略超 7s 预算。
- 改进方向：提示/模型需要更关注顶部容器边缘顶切，尤其是卡片从屏幕上方露出一截的资产/权益区。slide 对 right-edge 框应优先 left，而不是 up；判定 removed 不能只看页面发生纵向滚动，还要确认目标框对应的右切确实消失或移出可审范围。性能上 slide 阶段 5.7s，仍需压缩滑动验证耗时。
- 证据：
  - 框图：`HarmonyArena-fdu_agent/ux-detect-output/20260922-202437-864/snapshot_bbox.png`
  - dump：`HarmonyArena-fdu_agent/ux-detect-output/20260922-202437-864/snapshot_window.json`
  - 模型：`HarmonyArena-fdu_agent/ux-detect-output/20260922-202437-864/model_result.json` 2 框，均为右侧优惠券文字
  - layout：`HarmonyArena-fdu_agent/ux-detect-output/20260922-202437-864/layout_result.json` 2 unknown
  - 滑动：`HarmonyArena-fdu_agent/ux-detect-output/20260922-202437-864/slide_result.json` up / scrollable / removed 2（但 `snapshot_slide_up_0.png` 里最右优惠券仍右切，误消解）
  - 总结果：`HarmonyArena-fdu_agent/ux-detect-output/20260922-202437-864/snapshot_ux.json`
- 状态：**到达同类切；顶部 GT 顶切模型漏报，右侧优惠券右切被错误上滑消解，算法最终 ok 不可信。**

| id | 到达 | 模型框 | 滑动 | 页级结论 | 和 GT | 备注 |
|---|---|---|---|---|---|---|
| WF-TAOBAO-XML-G01-S1 | 人手点到我的淘宝外屏资产/订单页 | 2 右切文字框 | 算法上滑误消解 | 算法 ok / 人眼仍漏 | 顶部 3 个 GT 顶切漏报，右切验证方向错 | **7.8s 算法** / 202437-864；右侧应左滑验证，up 后仍右切 |

### WF-DIDI-XML-G01-S1 滴滴日常出行服务页（负例）

- GT：`测试集/整理/widefold_xml_normal/didi/g01/widefold_xml_normal_didi_g01_s1.jpg`
- XML：`测试集/整理/widefold_xml_normal/didi/g01/widefold_xml_normal_didi_g01_s1.xml`
- 包名：`com.sdu.didi.hmos.psnger`
- 你怎么点：Pura X 外屏/单屏 `1264x1848`，滴滴「日常出行」服务列表页，顶部左上返回，下面有「打车 / 青桔骑行 / 代驾 / 顺风车 / 特价拼车」等。
- 现场图：`HarmonyArena-fdu_agent/ux-detect-output/20260922-203321-676/snapshot.png`
- 页级：**ok**
- 人眼：现场为滴滴外屏服务列表页，和 GT 同类；无明显文字/组件/图标截断。
- 算法秒数：**1.9s**（模型 4.6s 不算；总 6.5s）
- 哪一段：模型 0 框，layout 输入 0，slide 跳过。
- 什么情况：官方 HTTP detect 返回 `overall=ok`、`issues=[]`，负例无误报。
- 证据：
  - dump：`HarmonyArena-fdu_agent/ux-detect-output/20260922-203321-676/snapshot_window.json`
  - 模型：`HarmonyArena-fdu_agent/ux-detect-output/20260922-203321-676/model_result.json` issues=[]
  - layout：`HarmonyArena-fdu_agent/ux-detect-output/20260922-203321-676/layout_result.json` inputCount=0
  - 滑动：`HarmonyArena-fdu_agent/ux-detect-output/20260922-203321-676/slide_result.json` skipped
  - 总结果：`HarmonyArena-fdu_agent/ux-detect-output/20260922-203321-676/snapshot_ux.json`
- 状态：**负例通过；官方 8000 无误报，算法段未超时。**

| id | 到达 | 模型框 | 滑动 | 页级结论 | 和 GT | 备注 |
|---|---|---|---|---|---|---|
| WF-DIDI-XML-G01-S1 | 人手点到滴滴日常出行服务页 | 0 框 | 未滑 | ok | 负例通过 | **1.9s 算法** / 203321-676；官方 8000 无误报 |

### WF-DOUYIN-XML-G01-S1 抖音消息页（负例）

- GT：`测试集/整理/widefold_xml_normal/douyin/g01/widefold_xml_normal_douyin_g01_s1.jpg`
- XML：`测试集/整理/widefold_xml_normal/douyin/g01/widefold_xml_normal_douyin_g01_s1.xml`
- 包名：`com.ss.hm.ugc.aweme`
- 你怎么点：Pura X 外屏/单屏 `1264x1848`，抖音底栏「消息」，停在消息页；顶部标题「消息」，列表含「发日常 / 状态设置」「新关注我的 / 互动消息」。
- 现场图：`HarmonyArena-fdu_agent/ux-detect-output/20260922-203632-382/snapshot.png`
- 页级：**ok**
- 人眼：现场为抖音外屏消息页，和 GT 同类；无明显文字/组件/图标截断。
- 算法秒数：**1.7s**（模型 2.4s 不算；总 4.1s）
- 哪一段：模型 0 框，layout 输入 0，slide 跳过。
- 什么情况：官方 HTTP detect 返回 `overall=ok`、`issues=[]`，负例无误报。
- 证据：
  - dump：`HarmonyArena-fdu_agent/ux-detect-output/20260922-203632-382/snapshot_window.json`
  - 模型：`HarmonyArena-fdu_agent/ux-detect-output/20260922-203632-382/model_result.json` issues=[]
  - layout：`HarmonyArena-fdu_agent/ux-detect-output/20260922-203632-382/layout_result.json` inputCount=0
  - 滑动：`HarmonyArena-fdu_agent/ux-detect-output/20260922-203632-382/slide_result.json` skipped
  - 总结果：`HarmonyArena-fdu_agent/ux-detect-output/20260922-203632-382/snapshot_ux.json`
- 状态：**负例通过；官方 8000 无误报，算法段未超时。**

| id | 到达 | 模型框 | 滑动 | 页级结论 | 和 GT | 备注 |
|---|---|---|---|---|---|---|
| WF-DOUYIN-XML-G01-S1 | 人手点到抖音消息页 | 0 框 | 未滑 | ok | 负例通过 | **1.7s 算法** / 203632-382；官方 8000 无误报 |

### WF-VIPSHOP-XML-G01-S1 唯品会搜索页（负例）

- GT：`测试集/整理/widefold_xml_normal/vipshop/g01/widefold_xml_normal_vipshop_g01_s1.jpg`
- XML：`测试集/整理/widefold_xml_normal/vipshop/g01/widefold_xml_normal_vipshop_g01_s1.xml`
- 包名：`com.vip.hosapp`
- 你怎么点：Pura X 外屏/单屏 `1264x1848`，唯品会搜索页；搜索框内为「厨房纸巾」，页面展示「最近搜索」「猜你喜欢」标签。
- 现场图：`HarmonyArena-fdu_agent/ux-detect-output/20260922-203812-442/snapshot.png`
- 页级：**ok**
- 人眼：GT `正常图=true`、无标注；现场为唯品会外屏搜索页，和 GT 同类；无明显文字/组件/图标截断。
- 算法秒数：**1.8s**（模型 2.4s 不算；总 4.1s）
- 哪一段：模型 0 框，layout 输入 0，slide 跳过。
- 什么情况：官方 HTTP detect 返回 `overall=ok`、`issues=[]`，负例无误报。
- 证据：
  - dump：`HarmonyArena-fdu_agent/ux-detect-output/20260922-203812-442/snapshot_window.json`
  - 模型：`HarmonyArena-fdu_agent/ux-detect-output/20260922-203812-442/model_result.json` issues=[]
  - layout：`HarmonyArena-fdu_agent/ux-detect-output/20260922-203812-442/layout_result.json` inputCount=0
  - 滑动：`HarmonyArena-fdu_agent/ux-detect-output/20260922-203812-442/slide_result.json` skipped
  - 总结果：`HarmonyArena-fdu_agent/ux-detect-output/20260922-203812-442/snapshot_ux.json`
- 状态：**负例通过；官方 8000 无误报，算法段未超时。**

| id | 到达 | 模型框 | 滑动 | 页级结论 | 和 GT | 备注 |
|---|---|---|---|---|---|---|
| WF-VIPSHOP-XML-G01-S1 | 人手点到唯品会搜索页 | 0 框 | 未滑 | ok | 负例通过 | **1.8s 算法** / 203812-442；官方 8000 无误报 |

### TRI-JD-XML-G01-S3 京东首页（三屏态，负例）

- GT：`测试集/整理/trifold_xml_normal/jd/g01/trifold_xml_normal_jd_g01_s3.jpg`
- XML：`测试集/整理/trifold_xml_normal/jd/g01/trifold_xml_normal_jd_g01_s3.xml`
- 包名：`com.jd.hm.mall`
- 你怎么点：Mate XTs 三屏态 `3184x2232`，京东首页；顶部「特价 / 首页 / 秒送 / 外卖 / 新品」，搜索框下方是横向类目和首页商品流。
- 现场图：`HarmonyArena-fdu_agent/ux-detect-output/20260922-214216-812/snapshot.png`
- 页级：**ok**
- 人眼：GT `正常图=true`、无标注；现场为京东首页同类页。模型命中 1 个疑似右切文字框，用户确认该框被正确识别且左滑可消解，最终负例通过。
- 算法秒数：**10.5s**（模型 8.7s 不算；总 19.3s）
- 哪一段：模型 / 滑动 / 性能
- 什么情况：官方 HTTP detect 报 1 个右切文字框 `[941,200,961,222]`；layout 未匹配判 unknown；slide 对该组执行 left，`diffPercent=23.14`，判定 `scrollable` 并移除，最终 `issueCount=0`。算法判断合理，但算法段 10.5s 超过 7s budget。
- 改进方向：功能无需改；后续若做性能优化，可关注滑动验证耗时 7.7s。
- 证据：
  - dump：`HarmonyArena-fdu_agent/ux-detect-output/20260922-214216-812/snapshot_window.json`
  - 模型：`HarmonyArena-fdu_agent/ux-detect-output/20260922-214216-812/model_result.json`
  - layout：`HarmonyArena-fdu_agent/ux-detect-output/20260922-214216-812/layout_result.json`
  - 滑动：`HarmonyArena-fdu_agent/ux-detect-output/20260922-214216-812/slide_result.json`
  - 滑后图：`HarmonyArena-fdu_agent/ux-detect-output/20260922-214216-812/snapshot_slide_left_0.png`
  - 恢复图：`HarmonyArena-fdu_agent/ux-detect-output/20260922-214216-812/snapshot_slide_left_0.png.restore.png`
  - 总结果：`HarmonyArena-fdu_agent/ux-detect-output/20260922-214216-812/snapshot_ux.json`
- 状态：**负例通过；疑似截断被正确滑动消解，但算法段超时。**

| id | 到达 | 模型框 | 滑动 | 页级结论 | 和 GT | 备注 |
|---|---|---|---|---|---|---|
| TRI-JD-XML-G01-S3 | 人手点到京东首页三屏态 | 1 个右切文字框 | left 后消解 | ok | 负例通过 | **10.5s 算法超时** / 214216-812；用户确认该框消解合理 |

### TRI-QQMUSIC-XML-G01-S3 QQ 音乐推荐页（三屏态，负例）

- GT：`测试集/整理/trifold_xml_normal/qqmusic/g01/trifold_xml_normal_qqmusic_g01_s3.jpg`
- XML：`测试集/整理/trifold_xml_normal/qqmusic/g01/trifold_xml_normal_qqmusic_g01_s3.xml`
- 包名：`com.tencent.hm.qqmusic`
- 你怎么点：Mate XTs 三屏态 `3184x2232`，QQ 音乐推荐首页；顶部为「推荐 / 乐馆 / 听书 / 儿童 / AI作歌 / 金币 / AI唱 / 扑淘」等，页面中部有歌单卡片和「告别歌荒，从这开始」。
- 现场图：`HarmonyArena-fdu_agent/ux-detect-output/20260922-214906-234/snapshot.png`
- 页级：**ok**
- 人眼：GT `正常图=true`、无标注；当前检测范围是文字 / 组件 / 图标截断，现场同类推荐页无明显截断。
- 算法秒数：**2.7s**（模型 6.7s 不算；总 9.4s）
- 哪一段：模型 0 框，layout 输入 0，slide 跳过。
- 什么情况：官方 HTTP detect 返回 `overall=ok`、`issues=[]`，负例无误报。
- 证据：
  - dump：`HarmonyArena-fdu_agent/ux-detect-output/20260922-214906-234/snapshot_window.json`
  - 模型：`HarmonyArena-fdu_agent/ux-detect-output/20260922-214906-234/model_result.json` issues=[]
  - layout：`HarmonyArena-fdu_agent/ux-detect-output/20260922-214906-234/layout_result.json` inputCount=0
  - 滑动：`HarmonyArena-fdu_agent/ux-detect-output/20260922-214906-234/slide_result.json` skipped
  - 总结果：`HarmonyArena-fdu_agent/ux-detect-output/20260922-214906-234/snapshot_ux.json`
- 状态：**负例通过；官方 8000 无误报，算法段未超时。**

| id | 到达 | 模型框 | 滑动 | 页级结论 | 和 GT | 备注 |
|---|---|---|---|---|---|---|
| TRI-QQMUSIC-XML-G01-S3 | 人手点到 QQ 音乐推荐页三屏态 | 0 框 | 未滑 | ok | 负例通过 | **2.7s 算法** / 214906-234；当前范围文字/组件/图标截断 |

### TRI-TOUTIAO-XML-G01-S3 今日头条推荐流（三屏态，负例）

- GT：`测试集/整理/trifold_xml_normal/toutiao/g01/trifold_xml_normal_toutiao_g01_s3.jpg`
- XML：`测试集/整理/trifold_xml_normal/toutiao/g01/trifold_xml_normal_toutiao_g01_s3.xml`
- 包名：`com.ss.hm.article.news`
- 你怎么点：Mate XTs 三屏态 `3184x2232`，今日头条首页推荐流；顶部搜索栏左侧红色「头条」标识，tab 行为「关注 / 推荐 / 热榜 / 发现 / 北京 / 畅听」等。
- 现场图：`HarmonyArena-fdu_agent/ux-detect-output/20260922-215350-016/snapshot.png`
- 页级：**ok**
- 人眼：GT `正常图=true`、无标注；用户确认现场为头条推荐流同类页面，且无明显文字 / 组件 / 图标截断。
- 算法秒数：**2.6s**（模型 6.0s 不算；总 8.6s）
- 哪一段：模型 0 框，layout 输入 0，slide 跳过。
- 什么情况：官方 HTTP detect 返回 `overall=ok`、`issues=[]`，负例无误报。
- 证据：
  - dump：`HarmonyArena-fdu_agent/ux-detect-output/20260922-215350-016/snapshot_window.json`
  - 模型：`HarmonyArena-fdu_agent/ux-detect-output/20260922-215350-016/model_result.json` issues=[]
  - layout：`HarmonyArena-fdu_agent/ux-detect-output/20260922-215350-016/layout_result.json` inputCount=0
  - 滑动：`HarmonyArena-fdu_agent/ux-detect-output/20260922-215350-016/slide_result.json` skipped
  - 总结果：`HarmonyArena-fdu_agent/ux-detect-output/20260922-215350-016/snapshot_ux.json`
- 状态：**负例通过；官方 8000 无误报，算法段未超时。**

| id | 到达 | 模型框 | 滑动 | 页级结论 | 和 GT | 备注 |
|---|---|---|---|---|---|---|
| TRI-TOUTIAO-XML-G01-S3 | 人手点到今日头条推荐流三屏态 | 0 框 | 未滑 | ok | 负例通过 | **2.6s 算法** / 215350-016；用户确认无问题 |

### TRI-WECOM-XML-G01-S3 企业微信工作台（三屏态，负例）

- GT：`测试集/整理/trifold_xml_normal/wecom/g01/trifold_xml_normal_wecom_g01_s3.jpg`
- XML：`测试集/整理/trifold_xml_normal/wecom/g01/trifold_xml_normal_wecom_g01_s3.xml`
- 包名：`com.tencent.wework.hmos`
- 你怎么点：Mate XTs 三屏态 `3184x2232`，企业微信「工作台」页；左侧竖栏选中工作台，主区域上方为「AI开放能力升级」banner，下方有「效率工具」卡片。
- 现场图：`HarmonyArena-fdu_agent/ux-detect-output/20260922-220201-147/snapshot.png`
- 页级：**ok**
- 人眼：GT `正常图=true`、无标注；现场为企业微信工作台同类页面，无明显文字 / 组件 / 图标截断。
- 算法秒数：**2.5s**（模型 6.2s 不算；总 8.7s）
- 哪一段：模型 0 框，layout 输入 0，slide 跳过。
- 什么情况：官方 HTTP detect 返回 `overall=ok`、`issues=[]`，负例无误报。
- 证据：
  - dump：`HarmonyArena-fdu_agent/ux-detect-output/20260922-220201-147/snapshot_window.json`
  - 模型：`HarmonyArena-fdu_agent/ux-detect-output/20260922-220201-147/model_result.json` issues=[]
  - layout：`HarmonyArena-fdu_agent/ux-detect-output/20260922-220201-147/layout_result.json` inputCount=0
  - 滑动：`HarmonyArena-fdu_agent/ux-detect-output/20260922-220201-147/slide_result.json` skipped
  - 总结果：`HarmonyArena-fdu_agent/ux-detect-output/20260922-220201-147/snapshot_ux.json`
- 状态：**负例通过；官方 8000 无误报，算法段未超时。**

| id | 到达 | 模型框 | 滑动 | 页级结论 | 和 GT | 备注 |
|---|---|---|---|---|---|---|
| TRI-WECOM-XML-G01-S3 | 人手点到企业微信工作台三屏态 | 0 框 | 未滑 | ok | 负例通过 | **2.5s 算法** / 220201-147；三屏态负例通过 |

### TRI-JD-XML-G01-S2 京东首页（双屏态，正例）

- GT：`测试集/整理/trifold_xml_normal/jd/g01/trifold_xml_normal_jd_g01_s2.jpg`
- XML：`测试集/整理/trifold_xml_normal/jd/g01/trifold_xml_normal_jd_g01_s2.xml`
- 包名：`com.jd.hm.mall`
- 你怎么点：Mate XTs 双屏态 `2048x2232`，京东首页；顶部「特价 / 首页 / 秒送 / 外卖 / 新品」，搜索框下方为横向类目和首页商品流。
- 现场图：`HarmonyArena-fdu_agent/ux-detect-output/20260923-001434-749/snapshot.png`
- 页级：**算法 bad / 人眼应 ok**
- 人眼：GT 有 3 个截断标注（文字 / 图标 / 文字）；现场为京东双屏首页同类页。模型命中 4 个右切框，其中 3 个可滑动消解；用户确认最终保留的右切文字框位于横向频道栏，实际也应通过在横栏左滑消解，不应作为死截断保留。
- 算法秒数：**9.5s**（模型 14.4s 不算；总 23.9s）
- 哪一段：模型 / layout / 滑动 / 性能
- 什么情况：模型报 4 个右切框（1 文字、1 图标、2 文字），layout 全部 unknown；slide 对同组执行 left 后保留 1 个右切文字框 `[942,178,950,196]` 为 `confirmed`，其余 3 个判 `scrollable` 移除。用户复核认为保留框处于顶部横向频道栏，可通过在该横栏左滑消解；算法当前滑动没有命中/验证该横栏，导致误保留。算法段 9.5s 也超过 7s budget。
- 改进方向：滑动验证需要针对横向频道栏选择更准确的横滑落点，避免把可横滑露出的右切文字误判为 confirmed；性能可后续关注模型 14.4s 和滑动 6.7s。
- 证据：
  - dump：`HarmonyArena-fdu_agent/ux-detect-output/20260923-001434-749/snapshot_window.json`
  - 模型：`HarmonyArena-fdu_agent/ux-detect-output/20260923-001434-749/model_result.json`
  - layout：`HarmonyArena-fdu_agent/ux-detect-output/20260923-001434-749/layout_result.json`
  - 滑动：`HarmonyArena-fdu_agent/ux-detect-output/20260923-001434-749/slide_result.json`
  - 滑后图：`HarmonyArena-fdu_agent/ux-detect-output/20260923-001434-749/snapshot_slide_left_0.png`
  - 恢复图：`HarmonyArena-fdu_agent/ux-detect-output/20260923-001434-749/snapshot_slide_left_0.png.restore.png`
  - 标框图：`HarmonyArena-fdu_agent/ux-detect-output/20260923-001434-749/snapshot_bbox_final.png`
  - 总结果：`HarmonyArena-fdu_agent/ux-detect-output/20260923-001434-749/snapshot_ux.json`
- 状态：**到达同类页；算法最终 bad 不可信，保留框应可通过横栏左滑消解；同时算法段超时。**

| id | 到达 | 模型框 | 滑动 | 页级结论 | 和 GT | 备注 |
|---|---|---|---|---|---|---|
| TRI-JD-XML-G01-S2 | 人手点到京东首页双屏态 | 4 个右切框 | left 后误保留 1 个横栏文字框 | 算法 bad / 人眼应 ok | 保留框可横栏左滑消解 | **9.5s 算法超时** / 001434-749；滑动落点/分组需改进 |

### TRI-JD-XML-G01-S2-R 京东首页双屏（本机 2026-09-23）

- 人已点到京东首页，双屏 `2048×2232`。未改折叠。
- 第一次 `000155-609` 截成黑屏，模型 0 框，作废。
- 重跑 `000332-013`：模型 2 框。右缘「京东」layout 判可滑恢复，消掉。下方商品文案上滑差 14.2%，判可滑，回滑差 1.16%，也消掉。页级 ok。
- 算法 **8.3s**（模型 37.0s 不算），超 7s。
- 证据：`/Users/zhangyingying/UX-Agent/HarmonyArena-fdu_agent/ux-detect-output/20260924-000332-013/snapshot_ux.json`
- 状态：**人眼：右缘都能滑出来，不是截断。这次页级 ok。**

### TRI-QQMUSIC-XML-G01-S2 QQ 音乐推荐页（双屏态，负例）

- GT：`测试集/整理/trifold_xml_normal/qqmusic/g01/trifold_xml_normal_qqmusic_g01_s2.jpg`
- XML：`测试集/整理/trifold_xml_normal/qqmusic/g01/trifold_xml_normal_qqmusic_g01_s2.xml`
- 包名：`com.tencent.hm.qqmusic`
- 你怎么点：Mate XTs 双屏态 `2048x2232`，QQ 音乐推荐首页；顶部搜索框，tab 行为「推荐 / 乐馆 / 听书 / 儿童 / AI作歌 / 金币 / AI唱 / 扑淘」等，底部悬浮导航和播放条。
- 现场图：`HarmonyArena-fdu_agent/ux-detect-output/20260923-001917-907/snapshot.png`
- 页级：**ok**
- 人眼：GT `正常图=true`、无标注；当前检测范围是文字 / 组件 / 图标截断，现场同类推荐页无明显截断。
- 算法秒数：**2.5s**（模型 14.2s 不算；总 16.7s）
- 哪一段：模型 0 框，layout 输入 0，slide 跳过。
- 什么情况：官方 HTTP detect 返回 `overall=ok`、`issues=[]`，负例无误报。总耗时被模型 14.2s 拉长，但算法段未超 7s budget。
- 证据：
  - dump：`HarmonyArena-fdu_agent/ux-detect-output/20260923-001917-907/snapshot_window.json`
  - 模型：`HarmonyArena-fdu_agent/ux-detect-output/20260923-001917-907/model_result.json` issues=[]
  - layout：`HarmonyArena-fdu_agent/ux-detect-output/20260923-001917-907/layout_result.json` inputCount=0
  - 滑动：`HarmonyArena-fdu_agent/ux-detect-output/20260923-001917-907/slide_result.json` skipped
  - 总结果：`HarmonyArena-fdu_agent/ux-detect-output/20260923-001917-907/snapshot_ux.json`
- 状态：**负例通过；官方 8000 无误报，算法段未超时。**

| id | 到达 | 模型框 | 滑动 | 页级结论 | 和 GT | 备注 |
|---|---|---|---|---|---|---|
| TRI-QQMUSIC-XML-G01-S2 | 人手点到 QQ 音乐推荐页双屏态 | 0 框 | 未滑 | ok | 负例通过 | **2.5s 算法** / 001917-907；模型耗时 14.2s |

### TRI-TOUTIAO-XML-G01-S2 今日头条推荐流（双屏态，负例）

- GT：`测试集/整理/trifold_xml_normal/toutiao/g01/trifold_xml_normal_toutiao_g01_s2.jpg`
- XML：`测试集/整理/trifold_xml_normal/toutiao/g01/trifold_xml_normal_toutiao_g01_s2.xml`
- 包名：`com.ss.hm.article.news`
- 你怎么点：Mate XTs 双屏态 `2048x2232`，今日头条首页推荐流；顶部搜索栏左侧红色「头条」标识，tab 行为「关注 / 推荐 / 热榜 / 发现 / 北京 / 畅听」等，下面是双列新闻卡片流。
- 现场图：`HarmonyArena-fdu_agent/ux-detect-output/20260923-002253-799/snapshot.png`
- 页级：**ok**
- 人眼：GT `正常图=true`、无标注；现场为头条推荐流同类页面，无明显文字 / 组件 / 图标截断。
- 算法秒数：**2.4s**（模型 13.4s 不算；总 15.7s）
- 哪一段：模型 0 框，layout 输入 0，slide 跳过。
- 什么情况：官方 HTTP detect 返回 `overall=ok`、`issues=[]`，负例无误报。总耗时被模型 13.4s 拉长，但算法段未超 7s budget。
- 证据：
  - dump：`HarmonyArena-fdu_agent/ux-detect-output/20260923-002253-799/snapshot_window.json`
  - 模型：`HarmonyArena-fdu_agent/ux-detect-output/20260923-002253-799/model_result.json` issues=[]
  - layout：`HarmonyArena-fdu_agent/ux-detect-output/20260923-002253-799/layout_result.json` inputCount=0
  - 滑动：`HarmonyArena-fdu_agent/ux-detect-output/20260923-002253-799/slide_result.json` skipped
  - 总结果：`HarmonyArena-fdu_agent/ux-detect-output/20260923-002253-799/snapshot_ux.json`
- 状态：**负例通过；官方 8000 无误报，算法段未超时。**

| id | 到达 | 模型框 | 滑动 | 页级结论 | 和 GT | 备注 |
|---|---|---|---|---|---|---|
| TRI-TOUTIAO-XML-G01-S2 | 人手点到今日头条推荐流双屏态 | 0 框 | 未滑 | ok | 负例通过 | **2.4s 算法** / 002253-799；模型耗时 13.4s |

### TRI-WECOM-XML-G01-S2 企业微信工作台（双屏态，负例）

- GT：`测试集/整理/trifold_xml_normal/wecom/g01/trifold_xml_normal_wecom_g01_s2.jpg`
- XML：`测试集/整理/trifold_xml_normal/wecom/g01/trifold_xml_normal_wecom_g01_s2.xml`
- 包名：`com.tencent.wework.hmos`
- 你怎么点：Mate XTs 双屏态 `2048x2232`，企业微信「工作台」页；顶部标题「工作台」，主区域上方为「AI开放能力升级」banner，下方有「效率工具」卡片和底部导航。
- 现场图：`HarmonyArena-fdu_agent/ux-detect-output/20260923-002517-240/snapshot.png`
- 页级：**ok**
- 人眼：GT `正常图=true`、无标注；现场为企业微信工作台同类页面，无明显文字 / 组件 / 图标截断。
- 算法秒数：**2.1s**（模型 4.4s 不算；总 6.4s）
- 哪一段：模型 0 框，layout 输入 0，slide 跳过。
- 什么情况：官方 HTTP detect 返回 `overall=ok`、`issues=[]`，负例无误报。
- 证据：
  - dump：`HarmonyArena-fdu_agent/ux-detect-output/20260923-002517-240/snapshot_window.json`
  - 模型：`HarmonyArena-fdu_agent/ux-detect-output/20260923-002517-240/model_result.json` issues=[]
  - layout：`HarmonyArena-fdu_agent/ux-detect-output/20260923-002517-240/layout_result.json` inputCount=0
  - 滑动：`HarmonyArena-fdu_agent/ux-detect-output/20260923-002517-240/slide_result.json` skipped
  - 总结果：`HarmonyArena-fdu_agent/ux-detect-output/20260923-002517-240/snapshot_ux.json`
- 状态：**负例通过；官方 8000 无误报，算法段未超时。**

| id | 到达 | 模型框 | 滑动 | 页级结论 | 和 GT | 备注 |
|---|---|---|---|---|---|---|
| TRI-WECOM-XML-G01-S2 | 人手点到企业微信工作台双屏态 | 0 框 | 未滑 | ok | 负例通过 | **2.1s 算法** / 002517-240；双屏态负例通过 |

### TRI-JD-XML-G01-S1 京东首页（单屏态，正例）

- GT：`测试集/整理/trifold_xml_normal/jd/g01/trifold_xml_normal_jd_g01_s1.jpg`
- XML：`测试集/整理/trifold_xml_normal/jd/g01/trifold_xml_normal_jd_g01_s1.xml`
- 包名：`com.jd.hm.mall`
- 你怎么点：Mate XTs 单屏态 `1008x2232`，京东首页；顶部「特价 / 首页 / 秒送 / 外卖 / 新品」，搜索框下方为横向类目和首页商品流。
- 现场图：`HarmonyArena-fdu_agent/ux-detect-output/20260923-002850-798/snapshot.png`
- 页级：**算法 bad / 需人眼复核**
- 人眼：GT 有 `截断-图标` 标注；现场为京东单屏首页同类页。模型命中右侧频道栏图标/文字右切，但算法对该组执行了 down 滑，未做横向栏 left 滑。结合 S2 京东保留框可通过横栏左滑消解的情况，本条最终 bad 需要人眼复核是否同样可横栏左滑消解。
- 算法秒数：**5.1s**（模型 7.6s 不算；总 12.7s）
- 哪一段：模型 / layout / 滑动方向
- 什么情况：模型报 2 个右切框：图标 `[948,206,1000,248]`、文字 `[929,251,1000,266]`；layout 全部 unknown；slide 选择 `down`，`diffPercent=0`，两个框均判 `confirmed`。若目标属于横向频道栏，则应优先尝试 left 横滑，否则会把可横滑消解的截断误保留。
- 改进方向：针对右切且位于顶部横向频道/类目栏的框，滑动验证应选择横向 left，并用更准确的栏内落点验证；后续人工确认此框是否可横滑消解。
- 证据：
  - dump：`HarmonyArena-fdu_agent/ux-detect-output/20260923-002850-798/snapshot_window.json`
  - 模型：`HarmonyArena-fdu_agent/ux-detect-output/20260923-002850-798/model_result.json`
  - layout：`HarmonyArena-fdu_agent/ux-detect-output/20260923-002850-798/layout_result.json`
  - 滑动：`HarmonyArena-fdu_agent/ux-detect-output/20260923-002850-798/slide_result.json`
  - 滑后图：`HarmonyArena-fdu_agent/ux-detect-output/20260923-002850-798/snapshot_slide_down_0.png`
  - 标框图：`HarmonyArena-fdu_agent/ux-detect-output/20260923-002850-798/snapshot_bbox_final.png`
  - 总结果：`HarmonyArena-fdu_agent/ux-detect-output/20260923-002850-798/snapshot_ux.json`
- 状态：**模型命中右切；算法使用 down 滑后保留，疑似滑动方向错误，需确认是否可横栏左滑消解。**

### TRI-JD-XML-G01-S1-R 京东首页单屏（用 predicted 图标框重测）

- 模型框：`test-set/predicted/trifold_xml_normal_jd_g01_s1.json`，1 个右缘 `截断-图标`，像素 `[957,458]`–`[1008,554]`，换成 `[949,205,1000,248]`。未打 API。`011253-370` 底下那个框不算。
- 现场图：`HarmonyArena-fdu_agent/ux-detect-output/20260924-011928-315/snapshot.png`
- 页级：ok
- 哪一段：滑动。layout 对 `截断-图标` 是 unknown，左滑在图标行。
- 什么情况：起点像素 `(949,506)` → `(848,506)`，框内 diff 14.74%，判可滑，框消掉。回滑 diff 1.38%，页面回来了。
- 算法 **6.3s**（模型 0s）。
- 证据：`.../20260924-011928-315/snapshot_ux.json`、`slide-ops.jsonl`
- 状态：**predicted 这一个图标框被左滑消掉。页级 ok。** 回滑从原起点往右缘顶，行程被截短，栏没有完全回到原位。

### TRI-JD-XML-G01-S1-R2 回手沿原段滑回

- 改动：左右回滑从落点起，沿原段回到起点。上滑下划的回手没动。
- 模型框仍是 predicted 那一个图标，只有 `issue_type` 和 bbox。未打 API。
- 去程 `(949,506)` → `(848,506)`，框内差 14.57%，消掉。回程 `(848,506)` → `(949,506)`，整页差 0.24%。
- 证据：`HarmonyArena-fdu_agent/ux-detect-output/20260924-012237-248/slide-ops.jsonl`
- 状态：**框消掉，回滑走的是同一段。**

### TRI-JD-XML-G01-S2-R2 京东首页双屏（predicted 三框）

- 模型框：`test-set/predicted/trifold_xml_normal_jd_g01_s2.json`，3 个右缘框。未打 API，未手写 `slide_direction`。方向由启发式推出左滑。
- 现场：双屏 `2048×2232`，京东首页。`HarmonyArena-fdu_agent/ux-detect-output/20260924-012812-242/snapshot.png`
- 页级：ok。3 个框都消掉。
- 第一下分类栏 `(1918,416)` → `(1713,416)`，框内差 37.26%，回程同一段，整页差 0.49%。
- 第二下图标行 `(2001,561)` → `(1632,561)`，两个框差 23.02% 和 18.18%，回程 `(1632,561)` → `(2001,561)`，整页差 0.80%。
- 算法 **13.7s**，超过 7s，因为滑了两次再各回一次。
- 证据：`.../20260924-012812-242/slide-ops.jsonl`
- 状态：**三框消掉，回滑沿原段。**

| id | 到达 | 模型框 | 滑动 | 页级结论 | 和 GT | 备注 |
|---|---|---|---|---|---|---|
| TRI-JD-XML-G01-S1 | 人手点到京东首页单屏态 | 2 个右切框 | down 后保留 2 个 confirmed | 算法 bad / 需复核 | GT 正例，现场同类 | **5.1s 算法** / 002850-798；疑似应 left 横滑验证频道栏 |

### TRI-QQMUSIC-XML-G01-S1 QQ 音乐推荐页（单屏态，负例）

- GT：`测试集/整理/trifold_xml_normal/qqmusic/g01/trifold_xml_normal_qqmusic_g01_s1.jpg`
- XML：`测试集/整理/trifold_xml_normal/qqmusic/g01/trifold_xml_normal_qqmusic_g01_s1.xml`
- 包名：`com.tencent.hm.qqmusic`
- 你怎么点：Mate XTs 单屏态 `1008x2232`，QQ 音乐推荐首页；顶部搜索框，tab 行为「推荐 / 乐馆 / 听书 / 儿童 / AI作歌」等，底部播放条和导航。
- 现场图：`HarmonyArena-fdu_agent/ux-detect-output/20260923-003134-412/snapshot.png`
- 页级：**ok**
- 人眼：GT `正常图=true`、无标注；当前检测范围是文字 / 组件 / 图标截断，现场同类推荐页无明显截断。
- 算法秒数：**2.3s**（模型 3.3s 不算；总 5.6s）
- 哪一段：模型 0 框，layout 输入 0，slide 跳过。
- 什么情况：官方 HTTP detect 返回 `overall=ok`、`issues=[]`，负例无误报。
- 证据：
  - dump：`HarmonyArena-fdu_agent/ux-detect-output/20260923-003134-412/snapshot_window.json`
  - 模型：`HarmonyArena-fdu_agent/ux-detect-output/20260923-003134-412/model_result.json` issues=[]
  - layout：`HarmonyArena-fdu_agent/ux-detect-output/20260923-003134-412/layout_result.json` inputCount=0
  - 滑动：`HarmonyArena-fdu_agent/ux-detect-output/20260923-003134-412/slide_result.json` skipped
  - 总结果：`HarmonyArena-fdu_agent/ux-detect-output/20260923-003134-412/snapshot_ux.json`
- 状态：**负例通过；官方 8000 无误报，算法段未超时。**

| id | 到达 | 模型框 | 滑动 | 页级结论 | 和 GT | 备注 |
|---|---|---|---|---|---|---|
| TRI-QQMUSIC-XML-G01-S1 | 人手点到 QQ 音乐推荐页单屏态 | 0 框 | 未滑 | ok | 负例通过 | **2.3s 算法** / 003134-412；单屏态负例通过 |

### TRI-TOUTIAO-XML-G01-S1 今日头条推荐流（单屏态，负例）

- GT：`测试集/整理/trifold_xml_normal/toutiao/g01/trifold_xml_normal_toutiao_g01_s1.jpg`
- XML：`测试集/整理/trifold_xml_normal/toutiao/g01/trifold_xml_normal_toutiao_g01_s1.xml`
- 包名：`com.ss.hm.article.news`
- 你怎么点：Mate XTs 单屏态 `1008x2232`，今日头条首页推荐流；顶部搜索栏左侧红色「头条」标识，tab 行为「关注 / 推荐 / 热榜 / 发现 / 北京」等，下面是新闻列表。
- 现场图：`HarmonyArena-fdu_agent/ux-detect-output/20260923-003259-327/snapshot.png`
- 页级：**ok**
- 人眼：GT `正常图=true`、无标注；现场为头条推荐流同类页面，无明显文字 / 组件 / 图标截断。
- 算法秒数：**2.2s**（模型 2.7s 不算；总 4.9s）
- 哪一段：模型 0 框，layout 输入 0，slide 跳过。
- 什么情况：官方 HTTP detect 返回 `overall=ok`、`issues=[]`，负例无误报。
- 证据：
  - dump：`HarmonyArena-fdu_agent/ux-detect-output/20260923-003259-327/snapshot_window.json`
  - 模型：`HarmonyArena-fdu_agent/ux-detect-output/20260923-003259-327/model_result.json` issues=[]
  - layout：`HarmonyArena-fdu_agent/ux-detect-output/20260923-003259-327/layout_result.json` inputCount=0
  - 滑动：`HarmonyArena-fdu_agent/ux-detect-output/20260923-003259-327/slide_result.json` skipped
  - 总结果：`HarmonyArena-fdu_agent/ux-detect-output/20260923-003259-327/snapshot_ux.json`
- 状态：**负例通过；官方 8000 无误报，模型和算法段均未超时。**

| id | 到达 | 模型框 | 滑动 | 页级结论 | 和 GT | 备注 |
|---|---|---|---|---|---|---|
| TRI-TOUTIAO-XML-G01-S1 | 人手点到今日头条推荐流单屏态 | 0 框 | 未滑 | ok | 负例通过 | **2.2s 算法** / 003259-327；单屏态负例通过 |

### TRI-WECOM-XML-G01-S1 企业微信工作台（单屏态，负例）

- GT：`测试集/整理/trifold_xml_normal/wecom/g01/trifold_xml_normal_wecom_g01_s1.jpg`
- XML：`测试集/整理/trifold_xml_normal/wecom/g01/trifold_xml_normal_wecom_g01_s1.xml`
- 包名：`com.tencent.wework.hmos`
- 你怎么点：Mate XTs 单屏态 `1008x2232`，企业微信「工作台」页；顶部标题「工作台」，上方为「AI开放能力升级」banner，下方有「效率工具」「教学互动」「学校管理」等卡片，底部导航选中工作台。
- 现场图：`HarmonyArena-fdu_agent/ux-detect-output/20260923-003516-211/snapshot.png`
- 页级：**ok**
- 人眼：GT `正常图=true`、无标注；现场为企业微信工作台同类页面，无明显文字 / 组件 / 图标截断。
- 算法秒数：**2.1s**（模型 4.7s 不算；总 6.8s）
- 哪一段：模型 0 框，layout 输入 0，slide 跳过。
- 什么情况：官方 HTTP detect 返回 `overall=ok`、`issues=[]`，负例无误报。
- 证据：
  - dump：`HarmonyArena-fdu_agent/ux-detect-output/20260923-003516-211/snapshot_window.json`
  - 模型：`HarmonyArena-fdu_agent/ux-detect-output/20260923-003516-211/model_result.json` issues=[]
  - layout：`HarmonyArena-fdu_agent/ux-detect-output/20260923-003516-211/layout_result.json` inputCount=0
  - 滑动：`HarmonyArena-fdu_agent/ux-detect-output/20260923-003516-211/slide_result.json` skipped
  - 总结果：`HarmonyArena-fdu_agent/ux-detect-output/20260923-003516-211/snapshot_ux.json`
- 状态：**负例通过；官方 8000 无误报，算法段未超时。**

| id | 到达 | 模型框 | 滑动 | 页级结论 | 和 GT | 备注 |
|---|---|---|---|---|---|---|
| TRI-WECOM-XML-G01-S1 | 人手点到企业微信工作台单屏态 | 0 框 | 未滑 | ok | 负例通过 | **2.1s 算法** / 003516-211；单屏态负例通过 |

### ISSUE-DIANPING-HOTEL-FOLD 大众点评酒店（三折叠，双屏→单屏→双屏）

- 问题单：三折叠大众点评酒店民宿。测试集里没有这页的图和 XML，现场补记。
- 你怎么点：Mate XTs `5GU0125610000110`。大众点评里进酒店相关页，双屏收成单屏，再展开回双屏。当前停在城市选择（当前位置 / 热门城市 / 字母索引）。包名 `com.sankuai.dianping`。屏 `2048×2232`。未用 hidumper。
- 现场图：`/Users/zhangyingying/UX-Agent/HarmonyArena-fdu_agent/ux-detect-output/20260924-003833-529/snapshot.png`
- 界面树 XML：`/Users/zhangyingying/UX-Agent/HarmonyArena-fdu_agent/ux-detect-output/20260924-003833-529/snapshot_window.xml`（由同目录 `snapshot_window.json` 转出）
- 页级：ok
- 模型 1 框，底边城市名「安庆」`[28,997,67,1000]`，方向 up。layout 判 `continuous_scroll_glyph_clipping_recoverable`，文字 bounds `[58,2222][141,2232]`，orig 到底下 2280，列表还能往下滚，框被消掉，没有滑动。
- 算法 **2.1s**（模型 5.0s 不算）。
- 状态：**已记录到达路径、截图、XML。模型这一个框被 layout 消掉。** 这张是双屏城市选择，和手机外屏不一致，不作本条现场图。

### ISSUE-DIANPING-HOTEL-OUTER 大众点评酒店（三折叠外屏）

- 问题单：三折叠大众点评酒店民宿，外屏。测试集里没有这页。
- 你怎么点：Mate XTs `5GU0125610000110`。大众点评「酒店 / 旅行」，外屏 `1008×2232`。未用 hidumper。
- 现场图：`/Users/zhangyingying/UX-Agent/HarmonyArena-fdu_agent/ux-detect-output/20260924-004650-outer/snapshot.png`（`1008×2232`，04:50 外屏再截到）
- 界面树 XML：`/Users/zhangyingying/UX-Agent/HarmonyArena-fdu_agent/ux-detect-output/20260924-004650-outer/snapshot_window.xml`
- 界面树 JSON：`/Users/zhangyingying/UX-Agent/HarmonyArena-fdu_agent/ux-detect-output/20260924-004650-outer/snapshot_window.json`
- 人眼：右缘被切。「酒店民宿」页签只剩「酒店」，底部橙色按钮只剩「找」。
- dump 对得上：`酒店民宿` 可见 bounds `[892,591][1008,668]`，orig `[892,591][1156,668]`；`找 机 票` 可见 `[848,1874][1008,1989]`，orig `[848,1874][1198,1989]`。字的原始宽度超出外屏右缘。
- 更早一张同页图没有 XML：`.../20260924-003833-529/snapshot_outer.png`。04:49 那次 dump 是城市选择，已作废，不配这张。
- 作废检测：`20260924-004647-929` 截到的是城市选择，0 框，不算。
- 检测：`20260924-005158-212`。外屏 `1008×2232`，页面是「酒店 / 旅行」。模型 3 框，layout 一个都没消。
- 页级：unknown（3 框都留下）
- 哪一段：layout 保住两处真切；滑动落在标题栏，把页面划进空白页，回滑失败。
- 什么情况：
  - 框 1「酒店民宿」`[880,261,1000,294]`：layout `true_truncation` / `local_non_scroll_glyph_clip`，隐藏 148px，不滑。
  - 框 2「找 机 票」`[835,824,1000,871]`：同样 `true_truncation`，隐藏 190px，不滑。
  - 框 0「资质规则」`[775,74,1000,106]`：layout `no_matching_component`，送去左滑。起点像素 `(895,201)`，位移 100。框内 diff 10.5%，整页 52% 像素变了，滑进一张只有返回箭头的白页。回滑 diff 15.0%，`restore_failed`，框留下。
- 算法 **8.6s**（模型 17.4s 不算；总 26.0s）。算法超过 7s，多在这次回滑。
- 改进方向：标题栏上的窄框不要当内容横滑。两处右缘真切已被 layout 留下，这次不要为了消框改 verifier。
- 证据：
  - 检测图：`HarmonyArena-fdu_agent/ux-detect-output/20260924-005158-212/snapshot.png`
  - 框：`.../20260924-005158-212/snapshot_bbox_final.png`
  - dump：`.../20260924-005158-212/snapshot_window.json`
  - 模型：`.../20260924-005158-212/model_result.json`
  - layout：`.../20260924-005158-212/layout_result.json`
  - 滑动：`.../20260924-005158-212/slide_result.json`、`slide-ops.jsonl`
  - 滑后白页：`.../20260924-005158-212/snapshot_slide_left_0.png`
  - 回滑：`.../20260924-005158-212/snapshot_slide_left_0.png.restore.png`
  - 总结果：`.../20260924-005158-212/snapshot_ux.json`
- 状态：**两处右缘真切没有被消掉。标题栏那一框滑进白页，回不来，页级 unknown。**

### ISSUE-DIANPING-GUEST-TRIPLE 大众点评选人数（三折叠三屏）

- 问题单：大众点评酒店民宿 → 国内 → 选房间数量/人数，三屏。
- 你怎么点：Mate XTs `5GU0125610000110`。大众点评酒店民宿，国内，打开「请选择人数·居室数·床数」。屏 `3184×2232`。未用 hidumper。
- 现场图：`/Users/zhangyingying/UX-Agent/HarmonyArena-fdu_agent/ux-detect-output/20260924-005808-007/snapshot.png`
- 界面树 XML：`/Users/zhangyingying/UX-Agent/HarmonyArena-fdu_agent/ux-detect-output/20260924-005808-007/snapshot_window.xml`
- 页级：ok
- 哪一段：模型。`issues=[]`，0 框。layout 输入 0，slide 跳过。
- 什么情况：模型没有框。算法没有框可消。界面树里「4室」可见到底下 2133，orig 到 2162，仍在屏内 2232 以上。底部「推荐 / 江景房」等芯片在可滚容器里，orig 到底下 2331。没有单独的「床数」选项行，只有标题和入口文案「床数/居室数/人数」。
- 算法 **1.7s**（模型 4.8s 不算；总 6.5s）。
- 改进方向：暂无。模型没标，不能用来验证「真切不被消掉」。
- 证据：
  - dump：`.../20260924-005808-007/snapshot_window.json`
  - 模型：`.../20260924-005808-007/model_result.json`
  - 总结果：`.../20260924-005808-007/snapshot_ux.json`
- 状态：**三屏选人数页已记录。模型 0 框，未滑。** 这张是民宿「人数·居室数·床数」，和后面酒店入住条件不是同一页。

### ISSUE-DIANPING-STAY-TRIPLE 大众点评选择入住条件（三折叠三屏）

- 问题单：大众点评酒店民宿 → 国内 → 选房间数量/人数，三屏。
- 你怎么点：Mate XTs `5GU0125610000110`。酒店 / 旅行，国内，打开「选择入住条件」（房间数量、成人数量、儿童数量）。屏 `3184×2232`。未用 hidumper。
- 现场图：`/Users/zhangyingying/UX-Agent/HarmonyArena-fdu_agent/ux-detect-output/20260924-010249-861/snapshot.png`
- 界面树 XML：`/Users/zhangyingying/UX-Agent/HarmonyArena-fdu_agent/ux-detect-output/20260924-010249-861/snapshot_window.xml`
- 页级：ok
- 哪一段：模型。`issues=[]`，0 框。layout 输入 0，slide 未滑。
- 什么情况：检测图和开跑前手截的是同一张（都是 318969 字节）。「请准确维护儿童年龄…」bounds `[66,1374][3120,1450]`，右缘在 3184 以内。弹层底下的酒店推荐卡 orig 超出屏底，被弹层挡住。模型没框，算法没有框可消。
- 算法 **1.7s**（模型 5.7s 不算；总 7.4s）。
- 改进方向：暂无。
- 证据：
  - dump：`.../20260924-010249-861/snapshot_window.json`
  - 模型：`.../20260924-010249-861/model_result.json`
  - 总结果：`.../20260924-010249-861/snapshot_ux.json`
- 状态：**入住条件页已记录。模型 0 框，未滑。**

### PHONE-TENCENTNEWS-XML-G01-S1 腾讯新闻要闻（直屏）

- 设备：直屏 `LNG0123525000430`，`1260×2720`。未用 hidumper。
- GT：`test-set/整理/phone_xml_normal/tencentnews/g01/`。同名 json 三框，都是 `flags.right`：右缘露出的下一张「热点精选」卡片（红标和两行字）。`predicted` 不用。没有 `slide_direction`。
- 第一次 `20260924-013731-055`：三框拆成三次左滑，起点像素 x=1200，落在前一张卡片上，行程 100，探测差 0%，整页 0%，回滑跳过，三框留下。页级 bad。算法 9.8s。
- 收成一次、起点收到卡片里 `(857,1342)` 之后，默认速度 600 仍拖不动这张 Swiper，探测仍是 0%（`024608-827`、`024739-574`）。速度 2500、行程 450 才能换列。宽屏 QQ 音乐仍是行程 180、默认速度。窄屏单颗矮芯片仍从框内侧起手、行程 180。
- 复测 `20260924-025122-767`：一组左滑 `(857,1342)`→`(290,1342)`，速度 2500。两行字差 25.72% / 30.57%。红标框只有 1.13%（下一张右上角仍是红标），同组一起消。回滑差 0.00%，页级 ok。
- 算法 **8.3s**（模型约 0，fixture；总 8.3s）。超过 7s，多在这一次换列和回滑。
- 证据：
  - 现场：`HarmonyArena-fdu_agent/ux-detect-output/20260924-025122-767/snapshot.png`
  - 滑后：`.../20260924-025122-767/snapshot_slide_left_0.png`
  - 回滑：`.../20260924-025122-767/snapshot_slide_left_0.png.restore.png`
  - 滑动：`.../20260924-025122-767/slide-ops.jsonl`
  - 总结果：`.../20260924-025122-767/snapshot_ux.json`
- 状态：**三框消掉。一次左滑，回滑回到原页。**

### WIDE-TAOBAO-XML-G01-S1 淘宝我的（阔折）

- 设备：阔折 `6HQ0125A11000475`。未用 hidumper。
- GT：`test-set/整理/widefold_xml_normal/taobao/g01/widefold_xml_normal_taobao_g01_s1.jpg`，`1264×1848`。同名 json 5 框：顶上「U」「¥0.00」「益」是 `flags.top`，领券中心右缘下一张券是 `flags.right`。
- 现场没法按原图复现。截图 `1828×2584`，仍是账号 tb946509662985 的「我的淘宝」，底部「我的淘宝」。顶上「领红包 / 领优惠 / 领金币」那一行不在。领券中心是一整排券，不是原图只露出半张。下面多了「芭芭农场」一行和「猜你喜欢」，右侧商品卡被切。原图那 5 处对不上，现场多了截断。
- 这次按要求走接口，不用存好的框。TokenHub `fetch failed`，校园网 `10.176.44.15:8000` 也超时。模型没返回，layout / slide 都跳过，没有框。
- 证据：
  - 现场：`HarmonyArena-fdu_agent/ux-detect-output/20260924-030319-536/snapshot.png`
  - dump：`.../20260924-030319-536/snapshot_window.json`
  - 模型：`.../20260924-030319-536/model_result.json`（`fetch failed`）
  - 总结果：`.../20260924-030319-536/snapshot_ux.json`
- 状态：**页面记下来了。接口没通，没测滑动。**

### WIDE-TAOBAO-XML-G01-S1-R 淘宝我的（阔折，接口）

- 设备：阔折 `6HQ0125A11000475`。人说已经到对应页。未用 hidumper。
- 现场仍是 `1828×2584` 的「我的淘宝」，不是数据集那张 `1264×1848`。顶上「领红包 / U / ¥0.00 / 益」不在。领券中心是一整排券。下面有「芭芭农场」和「猜你喜欢」，右侧商品卡被切。
- 这次走接口。模型 38.0s，两框，都写了 `slide_direction: down`：
  - `[24,88,113,100]` 绑到「我的订单」，bounds 与 orig 重合 `[44,223][208,271]`，没有藏字。layout `model_bbox_not_partial_glyph_edge_candidate`。
  - `[923,88,978,100]` 绑到「全部」旁的符号「큚」，hidden 0。layout `glyph_clipping_boundary_not_found`。
- 哪一段：滑动把整页带下去了，回滑没回到原位。
- 什么情况：两框合成一次下划，像素 `(1062,465)`→`(1062,724)`。框内差 32.03% / 21.88%，标成可滑。回滑 `(1062,465)`→`(1062,207)` 差 7.05%，再向上补一刀后差 14.33%，`restore_failed`。两框留下。页级 unknown。结束后「我的订单」和待付款那一行已经滚出屏幕。
- 算法 **10.0s**（模型 38.0s 不算；总 47.9s）。滑动 7.6s，超过 7s，多在这次失败的回滑。
- 证据：
  - 现场：`HarmonyArena-fdu_agent/ux-detect-output/20260924-031846-852/snapshot.png`
  - 滑后：`.../20260924-031846-852/snapshot_slide_down_0.png`
  - 回滑：`.../20260924-031846-852/snapshot_slide_down_0.png.restore.png`
  - 模型：`.../20260924-031846-852/model_result.json`
  - layout：`.../20260924-031846-852/layout_result.json`
  - 滑动：`.../20260924-031846-852/slide-ops.jsonl`
  - 总结果：`.../20260924-031846-852/snapshot_ux.json`
- 状态：**接口有结果。两框被整页下划带动，回不到原位，页级 unknown。原图那 5 个框这次模型没标。**

### WIDE-TAOBAO-XML-G01-S1-R2 淘宝我的（沿用上次两框）

- 设备：阔折 `6HQ0125A11000475`。沿用 `20260924-031846-852` 的两框，都是 `slide_direction: down`。没有再调接口。
- 回手改为从落点起：下划 `(1062,465)`→`(1062,724)`，回滑 `(1062,724)`→`(1062,465)`。框内差 30.6% / 9.4%，两框消掉。回滑差 0.44%，`restore_failed` 为假。页级 ok。
- 算法 **6.8s**（模型不算）。
- 证据：`HarmonyArena-fdu_agent/ux-detect-output/20260924-032330-038/snapshot_ux.json`，滑动 `.../slide-ops.jsonl`，回滑 `.../snapshot_slide_down_0.png.restore.png`
- 状态：**两框消掉，页面回到原位。**

### WIDE-VIPSHOP-XML-G01-S2 唯品会首页（阔折内屏）

- 设备：阔折 `6HQ0125A11000475`，内屏 `2584×1828`。未用 hidumper。
- GT：`test-set/整理/widefold_xml_normal/vipshop/g01/widefold_xml_normal_vipshop_g01_s2.json`。一框 `截断-文字`，`flags.right`，分类栏「数码」右缘。没有 `slide_direction`，按 `flags.right` 左滑。没有调接口。
- 左滑 `(1085,431)`→`(827,431)`，框内差 8.74%，消掉。回滑从落点回到 `(1085,431)`，差 0.07%。页级 ok。
- 算法 **7.0s**（模型不算）。刚过 7s。
- 证据：`HarmonyArena-fdu_agent/ux-detect-output/20260924-032622-860/snapshot_ux.json`，滑动 `.../slide-ops.jsonl`
- 状态：**一框消掉，分类栏回到原位。**

### WIDE-XIANYU-XML-G01-S1 闲鱼推荐（阔折）

- 设备：阔折 `6HQ0125A11000475`。人说页面布局和原图不一样，「印」那处截断少了。未用 hidumper。
- GT：`test-set/整理/widefold_xml_normal/xianyu/g01/widefold_xml_normal_xianyu_g01_s1.jpg`，`1264×1848`。三框都是 `flags.right`：分类栏「手」、右缘红图标、底下的「印」。
- 现场 `1828×2584`，搜索框是「手机壳」，「推荐」。分类栏排到「宠」，图标行是「吃喝玩乐 / 手机数码 / 上门回收 / 领红包 / 神奇鱼塘」，右缘没有原图那半个红图标和「印」。
- 这次走接口。模型 1 框 `[58,907,146,925]`，`slide_direction: up`，绑到瀑布流底部「¥400」。layout `not_truncation` / `continuous_scroll_glyph_clipping_recoverable`，隐藏 66px，内容到底下 3058，视口底 2375。没送去滑动。页级 ok。
- 算法 **2.1s**（模型 40.5s 不算；总 42.6s）。
- 证据：
  - 现场：`HarmonyArena-fdu_agent/ux-detect-output/20260924-032905-995/snapshot.png`
  - 模型：`.../20260924-032905-995/model_result.json`
  - layout：`.../20260924-032905-995/layout_result.json`
  - 总结果：`.../20260924-032905-995/snapshot_ux.json`
- 状态：**原图三处右缘切不在这张上。接口只标了底部价格，layout 按可滚消掉，未滑。**

### WIDE-XIANYU-XML-G01-S2 闲鱼推荐（阔折内屏）

- 设备：阔折 `6HQ0125A11000475`，内屏 `2584×1828`。未用 hidumper。
- GT：`test-set/整理/widefold_xml_normal/xianyu/g01/widefold_xml_normal_xianyu_g01_s2.json`。一框 `截断-文字`，`flags.right`，分类栏右缘「包表」。没有 `slide_direction`，按 `flags.right` 左滑。没有调接口。
- 左滑 `(2452,269)`→`(2194,269)`，框内差 18.79%，消掉。回滑从落点回到 `(2452,269)`，差 0.05%。页级 ok。
- 算法 **7.4s**（模型不算）。超过 7s。
- 证据：`HarmonyArena-fdu_agent/ux-detect-output/20260924-033213-779/snapshot_ux.json`，滑动 `.../slide-ops.jsonl`
- 状态：**一框消掉，分类栏回到原位。**

### TAB-12306-找回密码 铁路 12306 找回密码（平板，不在问题单）

- 设备：平板 `37XUN24711G01412`，`1840×2800`。前台 `com.chinarailway.ticketingHM`。未用 hidumper。
- 问题单：`docs/三折叠-平板问题单.txt` 只有点评民宿和滴滴加油/充电，没有这页。测试集也没有这页的图和 XML。
- 现场：找回密码，三个页签「人脸识别 / 手机号码 / 电子邮件」。字的黑边停在 x=1686，离右缘 153px。页签容器贴边（可见右缘 1840，原始右缘 1841）。上面这几行不能下滑。
- 第一次 `20260924-033653-136`：模型 3 框，都是 `text_truncation`、`slide_direction: down`，落在三个页签上。layout 全是 `unknown`。下滑 `(1069,510)`→`(1069,790)`，框内差 0%，整页 0%。整组都是 confirmed 时，`clearConfirmedInMovedGroup` 返回同一个数组，接着 `results.length = 0` 把结果抹掉，读 `slide_result` 崩了。页级 unknown。
- 改进：先复制再清空。可滚的组仍走新数组，已过的上滑 case 不改这条。0% 的组不再崩，按原意留下 confirmed。
- 重跑 `20260924-033831-133`：模型仍是 3 框、方向 down。layout 仍不是真截断：左右两框 `no_matching_component`，中间框绑到标题「找回密码」（覆盖只有 3%），`model_bbox_not_partial_glyph_edge_candidate`。同一段下滑，三框差都是 0%，`slide_result: confirmed`。页级 **bad**，三框留下。算法 **4.3s**（模型 8.7s 不算）。
- 证据：
  - 现场：`HarmonyArena-fdu_agent/ux-detect-output/20260924-033831-133/snapshot.png`
  - 模型：`.../20260924-033831-133/model_result.json`
  - layout：`.../20260924-033831-133/layout_result.json`
  - 滑动：`.../20260924-033831-133/slide-ops.jsonl`，滑后 `.../snapshot_slide_down_0.png`
  - 总结果：`.../20260924-033831-133/snapshot_ux.json`
  - 第一次崩在：`.../20260924-033653-136/slide-ops.jsonl` 的 `screen_fatal`
- 状态：**人定为真截断。** 页签「电子邮件」原始右缘 1841，可见右缘 1840，父级 tabList `scrollable=false`。上面这几行不能下滑。

### TAB-12306-找回密码-真截断 专记

- 定性：真截断。已写入 `docs/三折叠-平板问题单.txt` 和 `docs/合作与测试队列.md`。不放进 `tablet_xml_normal`，那个文件夹名是非截断。
- XML：`docs/20260919-测试集存档/问题单/平板-12306-找回密码/window_dump.xml`。由这次检测的 `snapshot_window.json` 转成和测试集一样的 `uitest dumpLayout` hierarchy。设备 `37XUN24711G01412`，`1840×2800`。页是 `getPwd.html`（忘记密码）。
- 检测 `20260924-034135-011`：模型 3 框，都是 `text_truncation`、`slide_direction: down`，落在三页签。layout 三框 `unknown`。下滑 `(773,507)`→`(773,787)`，三框差 0%，`confirmed`。页级 **bad**，三框留下。算法 **4.7s**（模型 6.6s 不算）。
- 证据：
  - XML：`docs/20260919-测试集存档/问题单/平板-12306-找回密码/window_dump.xml`
  - 现场：`HarmonyArena-fdu_agent/ux-detect-output/20260924-034135-011/snapshot.png`
  - 模型：`.../20260924-034135-011/model_result.json`
  - layout：`.../20260924-034135-011/layout_result.json`
  - 滑动：`.../20260924-034135-011/slide-ops.jsonl`
  - 总结果：`.../20260924-034135-011/snapshot_ux.json`
- 状态：**真截断。算法页级 bad，三框留下。layout 仍是 unknown，靠下滑 0% 留住。**

### TAB-12306-XML-G02-S1 铁路 12306 车次列表（平板横屏）

- 设备：平板 `37XUN24711G01412`，现场 `2800×1840`。未用 hidumper。没有调接口。
- GT：`test-set/整理/tablet_xml_normal/railway12306/g02/tablet_xml_normal_railway12306_g02_s1.json`。文件夹是 normal，两框要消掉。`截断-文字` `[954,306,991,324]`、`截断-组件` `[940,297,991,335]`，都是 `flags.right`，没有 `slide_direction`。右缘车站芯片「上海虹」被切。
- XML：`test-set/整理/tablet_xml_normal/railway12306/g02/tablet_xml_normal_railway12306_g02_s1.xml`
- layout：两框 `unknown` / `unsupported_or_unmatched_issue`（中文标签不进文字核对）。
- 滑动：按 `flags.right` 左滑一组 `(2688,581)`→`(2408,581)`，位移 100。芯片行确实滑了：滑前「北京南 / 北京丰台 / 上海虹」，滑后「上海虹桥 / 上海松江 / 上」。框内平均差只有 0.66% 和 3.68%，没过 5%，变化像素 17.54% / 19.45%。两框都 `confirmed`。整页平均差 3.33%，所以回了滑，回滑差 0.00%。页级 **bad**。
- 哪一段：滑动判定。落点和方向是对的，回滑也回到原位。白底芯片换了字，平均差被大片白底压在 5% 下面。
- 改进方向：这组页面已经动了，而且框内变化像素将近两成，不要只因为平均差不到 5% 就留下。不要把以前撤掉的「变化像素不少于 8%」全局规则加回来。
- 算法 **8.3s**（模型不算）。超过 7s，滑动加回滑 5.8s。
- 证据：
  - 现场：`HarmonyArena-fdu_agent/ux-detect-output/20260924-034545-575/snapshot.png`
  - 滑后：`.../20260924-034545-575/snapshot_slide_left_0.png`
  - 回滑：`.../20260924-034545-575/snapshot_slide_left_0.png.restore.png`
  - 模型框：`/tmp/railway12306-g02-model.json`
  - layout：`.../20260924-034545-575/layout_result.json`
  - 滑动：`.../20260924-034545-575/slide-ops.jsonl`
  - 总结果：`.../20260924-034545-575/snapshot_ux.json`
- 状态：**芯片行滑开了，两框没消，页级 bad。页面已回到原位。**
- 重跑 `20260924-035008-034`：整页动过，且框内变化像素不少于 12%、平均差不少于 2%、最深像素差不少于 80，才把白底换字算滑走。组件框 20% / 4.23% / 最深 153，升级成 scrollable；文字框 18.71% / 0.68% / 最深 47 自己不够，同组一起消。整页没动的不走这条，空探变化像素不到 1% 也打不中。左滑仍是 `(2688,581)`→`(2408,581)`。回滑差 0.01%。页级 **ok**，两框消掉。算法 **8.3s**，仍超过 7s。
- 证据：`HarmonyArena-fdu_agent/ux-detect-output/20260924-035008-034/snapshot_ux.json`，滑动 `.../slide-ops.jsonl`
- 状态：**两框消掉，芯片行回到原位。**

### TAB-WPS-XML-G01-S1 WPS 最近（平板横屏，遮盖图标）

- 设备：平板 `37XUN24711G01412`，现场 `2800×1840`。未用 hidumper。没有调接口。
- GT：`test-set/整理/tablet_xml_normal/wps/g01/tablet_xml_normal_wps_g01_s1.json`。文件夹是 normal，一框要消掉。`遮盖-图标` `[941,958,956,976]`，`flags` 只有 `系统` / `应用内正常`，都是 false，没有上下左右，也没有 `slide_direction`。右下角红色加号挡住分享图标。
- XML：`test-set/整理/tablet_xml_normal/wps/g01/tablet_xml_normal_wps_g01_s1.xml`
- layout：`unknown` / `unsupported_or_unmatched_issue`。
- 滑动：启发式按离中心更远的横轴判成左滑。`(2656,1779)`→`(2376,1779)`，起点在加号上。框内差 0%，整页 0%，`confirmed`。没回滑。页级 **bad**。
- 哪一段：方向。加号不横滑，分享图标还在加号下面。
- 改进方向：这框没有边缘 flags。右下角贴着加号的遮盖，中心距会判成左滑，手势落在加号上。上次用上滑，列表会换行。先别改启发式，问过再动。
- 算法 **5.5s**（模型不算）。
- 证据：
  - 现场：`HarmonyArena-fdu_agent/ux-detect-output/20260924-035454-528/snapshot.png`
  - 滑后：`.../20260924-035454-528/snapshot_slide_left_0.png`
  - 模型框：`/tmp/wps-g01-model.json`
  - layout：`.../20260924-035454-528/layout_result.json`
  - 滑动：`.../20260924-035454-528/slide-ops.jsonl`
  - 总结果：`.../20260924-035454-528/snapshot_ux.json`
- 状态：**左滑打在加号上，画面没动，遮盖框留下。**

### TAB-AMAP-XML-G01-S1 高德首页（平板横屏）

- 设备：平板 `37XUN24711G01412`，现场 `2800×1840`。未用 hidumper。没有调接口。
- GT：`test-set/整理/tablet_xml_normal/amap/g01/tablet_xml_normal_amap_g01_s1.json`。文件夹是 normal，一框要消掉。模型标注 1 框 `截断-组件`，`flags.right`，`[346,220,375,269]`。左边路线卡片上的星标被地图切到。没有 `slide_direction`。
- XML：`test-set/整理/tablet_xml_normal/amap/g01/tablet_xml_normal_amap_g01_s1.xml`
- layout：`unknown` / `unsupported_or_unmatched_issue`。
- 左滑 `(1009,450)`→`(729,450)`，框内平均差 10.5%，变化像素 70.73%，消掉。回滑差 0.11%。页级 **ok**。
- 算法 **7.6s**（模型不算）。超过 7s。
- 证据：`HarmonyArena-fdu_agent/ux-detect-output/20260924-040155-674/snapshot_ux.json`，滑动 `.../slide-ops.jsonl`
- 状态：**一框消掉，页面回到原位。**

### ISSUE-DIANPING-STAY-TRIPLE-R 大众点评选择入住条件（三折叠三屏，真截断检测）

- 设备：三折叠 `29L0124226000058`，现场 `3184×2232`。未用 hidumper。这次走接口。
- 页：酒店住宿里打开人数，现场是「选择入住条件」（房间数量、成人数量、儿童数量）。
- 模型 1 框 `text_truncation`，`[34,850,58,889]`，`slide_direction: up`。框在底部提示「请准确维护儿童年龄…」最左边的「请」，黄色「确认」按钮压住这行。
- layout：`unknown` / `glyph_clip_direction_ambiguous`，绑到「09.23」，hidden 0。没有判成真截断。
- 上滑 `(146,1719)`→`(146,1495)`，框内差 0%，整页 0%，`confirmed`。没回滑。页级 **bad**。
- 人数文案「1间 · 1成人 · 0儿童」的字在屏内（成人、儿童的底边 2091，屏幕底 2232）。这一行容器 orig 底 2244，比屏幕多 12px。
- 算法 **5.0s**（模型 17.2s 不算）。
- 证据：
  - 现场：`HarmonyArena-fdu_agent/ux-detect-output/20260924-040514-905/snapshot.png`
  - 模型：`.../20260924-040514-905/model_result.json`
  - layout：`.../20260924-040514-905/layout_result.json`
  - 滑动：`.../20260924-040514-905/slide-ops.jsonl`
  - 总结果：`.../20260924-040514-905/snapshot_ux.json`
- 状态：**遮盖，不在当前范围。** 黄色「确认」压住「请准确维护儿童年龄…」。当前只做文字 / 组件 / 图标截断。已写入 `docs/三折叠-平板问题单.txt`、`docs/合作与测试队列.md`、`docs/20260919-测试集存档/给测试团队的问题.md`。

### ISSUE-DIANPING-HOTEL-SINGLE 大众点评酒店/旅行（三折叠单屏，真截断）

- 设备：三折叠 `29L0124226000058`，单屏 `1008×2232`。未用 hidumper。
- 模型调用：这次没有 `model_http.json`，不是校园网 `/detect`。走兼容对话接口，请求是 `POST {baseURL}/chat/completions`。`snapshot_ux.json` 的 `apiConfig.model` 是 `gpt-5.6-sol`。返回 2 个 `text_truncation`，都是 `slide_direction: left`。接口主机名不写入交付材料，`apiConfig.baseURL` 留空。布局和左滑是这次调用之后的结果。
- 定性：人定为真截断。已写入 `docs/三折叠-平板问题单.txt` 和 `docs/合作与测试队列.md`。
- XML：`docs/20260919-测试集存档/问题单/三折叠-点评-酒店旅行-单屏/window_dump.xml`
- 模型 2 框，都是 `text_truncation`、`slide_direction: left`。
- 标题「酒店 / 旅行」右缘：框 `[891,66,1000,137]`。layout `unknown` / `no_matching_component`。左滑 `(948,227)`→`(847,227)`，框内差 0%，整页平均差 2.23% 没过 2.5%，没回滑，`confirmed`。滑后标题仍是「旅」被切。
- 「火车票」：框 `[806,345,1000,391]`。layout `true_truncation` / `local_non_scroll_glyph_clip`，绑到「火车票」，可见右缘 1008，原始右缘 1121，藏 113px。没送去滑动。
- 页级 **bad**，两框留下。算法 **3.9s**（模型 9.0s 不算）。
- 证据：
  - XML：`docs/20260919-测试集存档/问题单/三折叠-点评-酒店旅行-单屏/window_dump.xml`
  - 现场：`HarmonyArena-fdu_agent/ux-detect-output/20260924-040930-479/snapshot.png`
  - 模型：`.../20260924-040930-479/model_result.json`
  - layout：`.../20260924-040930-479/layout_result.json`
  - 滑动：`.../20260924-040930-479/slide-ops.jsonl`
  - 总结果：`.../20260924-040930-479/snapshot_ux.json`
- 状态：**真截断。标题右缘和火车票右缘都留下。**

### ISSUE-DIDI-TRIFOLD 滴滴加油/充电（三折叠，没找到）

- 问题单：`docs/三折叠-平板问题单.txt` 三折叠一条，滴滴加油或充电主页，单屏、双屏。
- 2026-09-23 在三折叠上没找到这页。未跑检测。
- 平板那条滴滴加油/充电仍留在问题单里，这次没动。
- 状态：**没找到。**

### ISSUE-DIDI-TABLET 滴滴加油（平板横屏，截到了，检测没跑完）

- 设备：平板 `37XUN24711G01412`，现场 `2800×1840`。未用 hidumper。
- 问题单：`docs/三折叠-平板问题单.txt` 平板一条是加油或充电主页。仓库里没有更早的检出留档。
- 现场：左边是滴滴出行首页，右边是「滴滴加油」。截图 `docs/20260919-测试集存档/问题单/平板-滴滴加油/snapshot.png`（16:06）。
- 哪一段：还没进模型。接着跑 `ux-detect` 时 `hdc list targets` 变成空的，dump 只有 `Device not found or connected`。产物 `HarmonyArena-fdu_agent/ux-detect-output/20260925-000703-375/snapshot_window.json`。
- 改进方向：平板重新连上、人还停在这一页之后再跑。不要把这张截图写成已经检出。
- 状态：**截到了，没有检测结果。** 2026-09-28 已补测，见 TRUE-08。

### TRUE-01 代码工坊内容上新 Sample 底（真截断，收成数据集）

- 设备：双折叠外屏 `22M0223928009654`，`1080×2504`。未用 hidumper，没有滑动。
- 怎么点：代码工坊 → 我的 → 内容上新 → Sample，停在列表底。「以上是全部更新内容」上沿被列表行切掉。
- 数据集（和测试集一样的三件套）：
  - 图：`test-set/true_truncation/bifold_xml_truncated/sample/g01/bifold_xml_truncated_sample_g01_s1.jpg`
  - 标注：同名 `.json`，Labelme 7.0.4，1 个框，标签 `截断-文字`，`flags.bottom`
  - XML：同名 `.xml`，`uitest dumpLayout` 转成测试集那种 hierarchy
- 模型：校园网 `http://10.176.44.15:8000/detect`，4.9 秒。`overall: bad`。框 `[319,854,681,864]`（0–1000），换成像素是 `[345,2138]–[735,2163]`，落在底行这几个字上。`truncated_edges: bottom`。
- 布局：这行 Text 可见 `[343,2141][737,2170]`，原始 `[343,2119][737,2170]`。上沿藏 22px。外层 List `clip=true`，行从 y=2141 开始。
- 证据：`docs/20260919-测试集存档/true-truncation-detect/01-sample-g01/pred.json`
- 状态：**已收成一条正例。模型标到了这行字。**

### TRUE-01-DETECT 代码工坊内容上新 Sample 底（检测）

- 设备：双折叠外屏 `22M0223928009654`，`1080×2504`。未用 hidumper。前台 `com.huawei.hmos.sample`，页是「内容上新 / Sample」。
- 数据集：`test-set/true_truncation/bifold_xml_truncated/sample/g01/bifold_xml_truncated_sample_g01_s1.jpg`。json 仍是模型框占位，不是人标 GT。
- 模型：校园网 `http://10.176.44.15:8000/detect`，日志里记为 `campus-http-detect`。4.98s。1 框，`issue_type: 截断-文字`，`truncated_edges: bottom`，框 `[319,854,681,864]`。
- layout：`unknown` / `unsupported_or_unmatched_issue`。标签是中文「截断-文字」，layout 只认 `text_truncation`，所以没判成真截断，送去滑动。
- 滑动：底边对应上滑。像素 `(454,1938)→(454,1688)`，位移 100。框内变化 0%，整页平均差 0.0003%，页面没动，没回滑。`slide_result: confirmed`。
- 页级 **bad**，1 框留下。算法 **3.7s**（模型 5.0s 不算）。没超 7s。
- 布局对照：这行「以上是全部更新内容」可见 `[343,2141][737,2170]`，原始 `[343,2119][737,2170]`，上沿藏 22px。上滑没把这行滑出来。
- 改进方向：进 layout 之前把校园网的「截断-文字」映射成 `text_truncation`。这次先不改，避免动到已经过的 case。
- 证据：
  - 现场：`HarmonyArena-fdu_agent/ux-detect-output/20260929-024948-084/snapshot.png`
  - 模型：`.../20260929-024948-084/model_result.json`
  - layout：`.../20260929-024948-084/layout_result.json`
  - 滑动：`.../20260929-024948-084/slide-ops.jsonl`，滑后 `.../snapshot_slide_up_0.png`
  - 总结果：`.../20260929-024948-084/snapshot_ux.json`
- 状态：**真截断。框留下。**

### TRUE-01-DETECT-R 代码工坊内容上新 Sample 底（官方接口完整日志）

- 设备：双折叠外屏 `22M0223928009654`，`1080×2504`。未用 hidumper。页是「内容上新 / Sample」。
- 数据集：`test-set/true_truncation/bifold_xml_truncated/sample/g01/bifold_xml_truncated_sample_g01_s1.jpg`
- 模型原文 `model_http.json`：`image_path=/tmp/ux_upload__etdz87j.png`，`total_inference_sec=4.5445`，`parse_status=valid_root_json`，`inference_error=null`。`pred_text` 是 `{"overall":"bad","issues":[{"issue_type":"截断-文字","bbox":[319,854,681,864],"truncated_edges":["bottom"]}]}`。`used_instruction` 2370 字。接口 `http://10.176.44.15:8000/detect`。
- layout：`unknown` / `unsupported_or_unmatched_issue`。中文标签没进 layout 的真截断判定，送去滑动。
- 滑动：上滑像素 `(454,1938)→(454,1688)`，位移 100。框内变化 0%，没回滑，`confirmed`。
- 页级 **bad**，1 框留下。算法 **3.8s**（模型 5.0s 不算）。
- 布局：这行「以上是全部更新内容」可见 `[343,2141][737,2170]`，原始 `[343,2119][737,2170]`，上沿藏 22px。
- 证据：`HarmonyArena-fdu_agent/ux-detect-output/true_truncation/bifold_xml_truncated/sample/g01/20260929-031423-178/` 下的 `snapshot.png`、`model_http.json`、`model_result.json`、`layout_result.json`、`slide-ops.jsonl`、`snapshot_slide_up_0.png`、`snapshot_ux.json`
- 状态：**真截断。框留下。这次日志带官方接口原文。**

### TRUE-02 代码工坊设置页标题（真截断，两步）

- 设备：双折叠外屏 `22M0223928009654`，`1080×2504`。未用 hidumper。页是「设置」。
- 数据集：`test-set/true_truncation/bifold_xml_truncated/sample/g02/bifold_xml_truncated_sample_g02_s1.jpg`，同名 json、xml。json 是模型框占位。
- 模型原文：`image_path=/tmp/ux_upload_yu2wogkp.png`，`total_inference_sec=4.3134`，`parse_status=valid_root_json`，`inference_error=null`。`pred_text` 是 `{"overall":"bad","issues":[{"issue_type":"截断-文字","bbox":[77,54,183,66],"truncated_edges":["top"]}]}`。
- layout：`unknown` / `unsupported_or_unmatched_issue`。中文标签送去滑动。
- 滑动：顶边对应下滑。像素 `(140,366)→(140,616)`，位移 100。框内变化 0%，整页没动，没回滑，`confirmed`。
- 页级 **bad**，1 框留下。算法 **3.5s**（模型 4.7s 不算）。
- 布局：标题「设置」可见 `[75,137][200,174]`，原始 `[75,99][200,174]`，上沿藏 38px。
- 证据：`HarmonyArena-fdu_agent/ux-detect-output/true_truncation/bifold_xml_truncated/sample/g02/20260929-033617-243/` 下的 `snapshot.png`、`model_http.json`、`model_result.json`、`layout_result.json`、`slide-ops.jsonl`、`snapshot_slide_down_0.png`、`snapshot_ux.json`
- 状态：**真截断。标题框留下。**

### TRUE-03-VOID 代码工坊关于页（页面不对，未收）

- 设备：双折叠外屏 `22M0223928009654`，`1080×2504`。未用 hidumper。
- 什么情况：人说已经到关于页。dump 仍是设置页：标题「设置」可见 `[75,137][200,174]`、原始 `[75,99][200,174]`，列表里有一行「关于」。没有进入关于页。
- 模型原文：`image_path=/tmp/ux_upload_axr42c20.png`，`total_inference_sec=2.0841`，`parse_status=valid_root_json`。`pred_text` 是 `{"overall":"ok","issues":[]}`。没有滑动。
- 处理：没有收成 `g03`。日志挪到 `HarmonyArena-fdu_agent/ux-detect-output/true_truncation/_page_mismatch/20260929-033838-210-still-settings/`。
- 状态：**作废。还在设置页。**

### TRUE-03 代码工坊关于页（真截断，模型没标）

- 设备：双折叠外屏 `22M0223928009654`，`1080×2504`。未用 hidumper。页是「关于」。
- 数据集：`test-set/true_truncation/bifold_xml_truncated/sample/g03/bifold_xml_truncated_sample_g03_s1.jpg`，同名 json、xml。json 的 `shapes` 是空的，因为这次模型没给框。
- 人眼：标题「HMOS代码工坊」下沿被「版本信息」白卡片挡住。
- 布局：标题 Text 可见和原始都是 `[320,662][760,735]`，bounds 与 orig 重合。切在卡片盖住字，不在这个节点自己的 bounds 差里。
- 模型原文：`image_path=/tmp/ux_upload_8f4cwqdb.png`，`total_inference_sec=2.0861`，`parse_status=valid_root_json`，`inference_error=null`。`pred_text` 是 `{"overall":"ok","issues":[]}`。
- layout / 滑动：没有框，滑动跳过。
- 页级 **ok**。算法 **1.4s**（模型 2.5s 不算）。
- 哪一段：模型。图上标题下沿被挡住，模型没框。
- 改进方向：暂无。先留这张图和 XML。
- 证据：`HarmonyArena-fdu_agent/ux-detect-output/true_truncation/bifold_xml_truncated/sample/g03/20260929-034151-214/` 下的 `snapshot.png`、`model_http.json`、`snapshot_window.json`、`snapshot_ux.json`
- 状态：**页面是关于页真截断。这次模型漏了，0 框。**

### TRUE-04 代码工坊用户体验调研提交按钮（真截断，两步）

- 设备：双折叠外屏 `22M0223928009654`，`1080×2504`。未用 hidumper。页是「用户体验调研」。
- 数据集：`/Users/zhangyingying/UX-Agent/test-set/true_truncation/bifold_xml_truncated/sample/g04/bifold_xml_truncated_sample_g04_s1.jpg`，同名 json、xml。json 是模型框占位，2 个框，都是底边。
- 模型原文：`image_path=/tmp/ux_upload_xg0homo8.png`，`total_inference_sec=7.2483`，`parse_status=valid_root_json`，`inference_error=null`。`pred_text` 是 `{"overall":"bad","issues":[{"issue_type":"截断-组件","bbox":[46,939,954,965],"truncated_edges":["bottom"]},{"issue_type":"截断-文字","bbox":[454,954,544,965],"truncated_edges":["bottom"]}]}`。
- layout：两框都是 `unknown` / `unsupported_or_unmatched_issue`，送去滑动。
- 滑动：底边对应上滑。像素 `(454,2151)→(454,1901)`，位移 100。两框变化都是 0%，整页没动，没回滑，都是 `confirmed`。
- 页级 **bad**，2 框留下。算法 **3.7s**（模型 7.7s 不算）。
- 布局：「提交」可见 `[50,2354][1030,2417]`，原始 `[50,2354][1030,2479]`，下沿藏 62px。
- 证据：`/Users/zhangyingying/UX-Agent/HarmonyArena-fdu_agent/ux-detect-output/true_truncation/bifold_xml_truncated/sample/g04/20260929-034410-781/` 下的 `snapshot.png`、`model_http.json`、`model_result.json`、`layout_result.json`、`slide-ops.jsonl`、`snapshot_slide_up_0.png`、`snapshot_ux.json`
- 状态：**真截断。提交按钮两框留下。**

### TRUE-05 代码工坊样例分类条（右边是真截断，左边不是）

- 设备：双折叠外屏 `22M0223928009654`，`1080×2504`。未用 hidumper。页是「样例」，分类条停在中间。前面几次没过的目录已删，只留这一次。
- 数据集：`/Users/zhangyingying/UX-Agent/test-set/true_truncation/bifold_xml_truncated/sample/g05/bifold_xml_truncated_sample_g05_s1.jpg`，同名 json、xml。json 是模型框占位。
- 模型原文：`image_path=/tmp/ux_upload_wca98nnu.png`，`total_inference_sec=11.8598`，`parse_status=valid_root_json`。四框：左文字 `[0,582,27,601]`、右文字 `[896,582,1000,601]`，再加上左组件 `[0,572,75,612]`、右组件 `[848,572,1000,612]`。
- 人看的结果：右边「更多案例」是真截断，框要留。左边「ArkUI实践」不是真截断，滑全后框要消。横幅自己在转，不算。
- 左边：右滑像素 `(346,1482)→(540,1482)`，两框都滑走。往左滑回，分类条这一行和开测图一致，两框消掉。
- 右边：左滑像素 `(998,1482)→(890,1482)`，分类条这一行没动，两框留下。没有再往回滑。
- 页级 **bad**。算法 **8.5s**，超过 7s。
- 证据：`/Users/zhangyingying/UX-Agent/HarmonyArena-fdu_agent/ux-detect-output/true_truncation/bifold_xml_truncated/sample/g05/20260929-042046-704/`
- 状态：**过了。右边留下，左边消掉。**

### TRUE-06 代码工坊实践文章顶栏标题（真截断）

- 设备：双折叠外屏 `22M0223928009654`，`1080×2504`。未用 hidumper。页是实践文章，下滑后标题收到顶栏。
- 数据集：`/Users/zhangyingying/UX-Agent/test-set/true_truncation/bifold_xml_truncated/sample/g06/bifold_xml_truncated_sample_g06_s1.jpg`，同名 json、xml。json 是模型框占位，1 框，上沿。
- 模型原文：`image_path=/tmp/ux_upload_k2o4x2k7.png`，`total_inference_sec=4.3832`，`parse_status=valid_root_json`，`inference_error=null`。`pred_text` 是 `{"overall":"bad","issues":[{"issue_type":"截断-文字","bbox":[209,69,522,86],"truncated_edges":["top"]}]}`。
- 布局：「多端UX设计」可见 `[225,175][568,200]`，原始 `[225,150][568,200]`，上沿藏 25px。
- 下滑像素 `(395,416)→(395,666)`，位移 100。标题上沿还是切着的，框留下。整页动了，再上滑回去，页面回到了。
- 页级 **bad**。算法 **5.9s**。
- 证据：`/Users/zhangyingying/UX-Agent/HarmonyArena-fdu_agent/ux-detect-output/true_truncation/bifold_xml_truncated/sample/g06/20260929-042820-384/`
- 状态：**真截断。顶栏标题框留下。过了。**

### TRUE-07 大众点评酒店/旅行（三折叠单屏，官方看图）

- 三折叠没连上，现在连的是双折叠 `22M0223928009654`。用收集好的图调校园网官方接口（`--mode=image`），没有连机滑动。
- 数据集：`/Users/zhangyingying/UX-Agent/test-set/true_truncation/trifold_xml_truncated/dianping/g01/`。同名 json 里 2 个「截断-文字」，都贴右边。
- 模型原文：`image_path=/tmp/ux_upload_6q0stqi0.png`，`total_inference_sec=9.4901`，`parse_status=valid_root_json`，`inference_error=null`。`pred_text` 是 `{"overall":"bad","issues":[{"issue_type":"截断-文字","bbox":[341,68,997,141],"truncated_edges":["right"]},{"issue_type":"截断-图标","bbox":[849,217,1000,320],"truncated_edges":["right"]},{"issue_type":"截断-文字","bbox":[809,347,1000,392],"truncated_edges":["right"]}]}`。
- layout / 滑动：图不在当前设备上，这两段没跑。模型 3 框，页级 **bad**。算法 **0.5s**（模型 9.9s 不算）。
- 哪一段：模型。旧的 `20260924-040930-479` 是备用模型，没有 `model_http.json`。这次官方接口标了 3 框，比数据集多 1 个「截断-图标」。
- 改进方向：三折叠点到这一页后再跑滑动，看框留不留。
- 证据：官方看图模型在 `/Users/zhangyingying/UX-Agent/HarmonyArena-fdu_agent/ux-detect-output/true_truncation/trifold_xml_truncated/dianping/g01/20260924-040930-479/官方看图模型/`。不再单独放一个看图时间目录。这次看图的三个框不是外面这次滑动的输入。
- 状态：**官方模型 3 框。滑动还没跑。**

### TRUE-08 平板滴滴加油底栏按钮（真截断）

- 设备：平板 `37XUN24711G01412`，横屏 `2800×1840`。未用 hidumper。左边是滴滴出行首页，右边是「滴滴加油」。
- 数据集：`/Users/zhangyingying/UX-Agent/test-set/true_truncation/tablet_xml_truncated/didi/g01/tablet_xml_truncated_didi_g01_s1.jpg`，同名 json、xml。json 是模型框占位，2 框，都是下沿。
- 模型原文：`image_path=/tmp/ux_upload_9zc3_jn1.png`，`total_inference_sec=8.3321`，`parse_status=valid_root_json`，`inference_error=null`。`pred_text` 是 `{"overall":"bad","issues":[{"issue_type":"截断-文字","bbox":[712,989,788,1000],"truncated_edges":["bottom"]},{"issue_type":"截断-组件","bbox":[618,964,882,1000],"truncated_edges":["bottom"]}]}`。
- 上滑像素 `(2100,1582)→(2100,1398)`，位移 100。两框都是 0%，整页没动，没再回滑，两框留下。
- 页级 **bad**。算法 **4.5s**。
- 证据：`/Users/zhangyingying/UX-Agent/HarmonyArena-fdu_agent/ux-detect-output/true_truncation/tablet_xml_truncated/didi/g01/20260929-043228-850/`
- 状态：**真截断。底栏橙色按钮两框留下。**

### TRUE-09 平板 12306 找回密码页签（真截断）

- 设备：平板 `37XUN24711G01412`，竖屏 `1840×2800`。未用 hidumper。页是「找回密码」。
- 数据集：`/Users/zhangyingying/UX-Agent/test-set/true_truncation/tablet_xml_truncated/railway12306/g01/tablet_xml_truncated_railway12306_g01_s1.jpg`，同名 json、xml。json 是模型框占位，3 框，都是上沿。
- 模型原文：`image_path=/tmp/ux_upload_66f8xjqk.png`，`total_inference_sec=10.3491`，`parse_status=valid_root_json`，`inference_error=null`。`pred_text` 是 `{"overall":"bad","issues":[{"issue_type":"截断-文字","bbox":[74,76,250,101],"truncated_edges":["top"]},{"issue_type":"截断-文字","bbox":[414,76,584,101],"truncated_edges":["top"]},{"issue_type":"截断-文字","bbox":[748,76,918,101],"truncated_edges":["top"]}]}`。
- 布局：「电子邮件」可见 `[1226,217][1840,280]`，原始 `[1226,217][1841,280]`。三个页签上沿被模型框住。
- 下滑像素 `(765,507)→(765,787)`，位移 100。三框都是 0%，整页没动，没再回滑，三框留下。
- 页级 **bad**。算法 **4.3s**。
- 证据：`/Users/zhangyingying/UX-Agent/HarmonyArena-fdu_agent/ux-detect-output/true_truncation/tablet_xml_truncated/railway12306/g01/20260929-043730-337/`
- 状态：**真截断。三个页签框留下。**

### TRUE-10 平板 12306 订单页右上角图标（真截断）

- 设备：平板 `37XUN24711G01412`，竖屏 `1840×2800`。未用 hidumper。页是「订单」，下面是「火车票订单」。
- 数据集：`/Users/zhangyingying/UX-Agent/test-set/true_truncation/tablet_xml_truncated/railway12306/g02/tablet_xml_truncated_railway12306_g02_s1.jpg`，同名 json、xml。json 是模型框占位，2 框，都是上沿。
- 模型原文：`image_path=/tmp/ux_upload_6j503drf.png`，`total_inference_sec=7.8009`，`parse_status=valid_root_json`，`inference_error=null`。`pred_text` 是 `{"overall":"bad","issues":[{"issue_type":"截断-图标","bbox":[891,10,936,39],"truncated_edges":["top"]},{"issue_type":"截断-文字","bbox":[857,44,971,55],"truncated_edges":["top"]}]}`。
- 布局：标题「订单」可见 `[437,98][1403,152]`，原始 `[437,72][1403,152]`，上沿藏 26px。右上角图标可见 `[1575,98][1791,189]`，原始 `[1575,39][1791,189]`，上沿藏 59px。两框都落在这个图标上。
- layout：两框都是 `unknown` / `unsupported_or_unmatched_issue`，送去滑动。
- 下滑像素 `(1682,378)→(1682,658)`，位移 100。两框都是 0%，整页没动，没再回滑，两框留下。
- 页级 **bad**。算法 **4.1s**（模型 8.5s 不算）。
- 证据：`/Users/zhangyingying/UX-Agent/HarmonyArena-fdu_agent/ux-detect-output/true_truncation/tablet_xml_truncated/railway12306/g02/20260929-044451-760/`
- 状态：**真截断。右上角图标两框留下。**

### TAB-AMAP-XML-G01-S1-R 高德首页（平板横屏，假截断）

- 设备：平板 `37XUN24711G01412`，横屏 `2800×1840`。未用 hidumper。页是高德首页 `MainMapPage`。
- 数据集：`/Users/zhangyingying/UX-Agent/test-set/测试集0928/tablet_xml_normal/amap/g01/`。文件夹是 normal，框要消掉。同名 json 里模型标注 1 框「截断-组件」，右边。
- 模型原文：`image_path=/tmp/ux_upload_anpmzm7j.png`，`total_inference_sec=5.5572`，`parse_status=valid_root_json`，`inference_error=null`。`pred_text` 是 `{"overall":"bad","issues":[{"issue_type":"截断-文字","bbox":[364,236,374,257],"truncated_edges":["right"]}]}`。
- layout：`unknown` / `unsupported_or_unmatched_issue`，送去滑动。
- 左滑像素 `(1033,454)→(753,454)`，位移 100。框内平均差 26.89%，变化像素 61.08%，标成可滑，框消掉。这一行先右滑回去差 6.19%，再右滑一次后差 0%。
- 页级 **ok**。算法 **10.1s**，超过 7s。多出来的时间在第二次回滑。
- 证据：`/Users/zhangyingying/UX-Agent/HarmonyArena-fdu_agent/ux-detect-output/testset_0928/tablet_xml_normal/amap/g01/20260929-050257-753/`
- 状态：**假截断。一框消掉，页面回到原位。过了。**

### TAB-12306-XML-G02-S1-R 铁路 12306 车次列表（平板横屏，假截断）

- 设备：平板 `37XUN24711G01412`，横屏 `2800×1840`。未用 hidumper。页是「北京 <> 上海」车次列表。第一次 0 框的目录已删，只留这次。
- 数据集：`/Users/zhangyingying/UX-Agent/test-set/测试集0928/tablet_xml_normal/railway12306/g02/`。文件夹是 normal。同名 json 里有 2 框，都在右边。
- 模型原文：`image_path=/tmp/ux_upload_5fo3ph89.png`，`total_inference_sec=3.195`，`parse_status=valid_root_json`，`inference_error=null`。`pred_text` 是 `{"overall":"ok","issues":[]}`。
- layout / 滑动：没有框，滑动跳过。
- 页级 **ok**。算法 **2.1s**（模型 3.9s 不算）。
- 哪一段：模型。数据集里那 2 个车站芯片框，重测仍没标。
- 改进方向：暂无。模型没给框，算法没有框可消。
- 证据：`/Users/zhangyingying/UX-Agent/HarmonyArena-fdu_agent/ux-detect-output/testset_0928/tablet_xml_normal/railway12306/g02/20260929-050818-676/`
- 状态：**假截断页。模型 0 框，页级 ok。**

### TAB-WPS-XML-G01-S1-R WPS 最近（平板横屏）

- 设备：平板 `37XUN24711G01412`，横屏 `2800×1840`。未用 hidumper。页是 WPS「最近」。
- 数据集：`/Users/zhangyingying/UX-Agent/test-set/测试集0928/tablet_xml_normal/wps/g01/`。文件夹是 normal。同名 json 里 1 框，「遮盖-图标」。
- 模型原文：`image_path=/tmp/ux_upload_52o3euie.png`，`total_inference_sec=3.1706`，`parse_status=valid_root_json`，`inference_error=null`。`pred_text` 是 `{"overall":"ok","issues":[]}`。
- layout / 滑动：没有框，滑动跳过。
- 页级 **ok**。算法 **2.1s**（模型 3.9s 不算）。
- 哪一段：模型。数据集里那个遮盖框，这次没标。
- 改进方向：暂无。模型没给框，算法没有框可消。
- 证据：`/Users/zhangyingying/UX-Agent/HarmonyArena-fdu_agent/ux-detect-output/testset_0928/tablet_xml_normal/wps/g01/20260929-051338-269/`
- 状态：**页是最近。模型 0 框，页级 ok。**

### BF-TENCENTVIDEO-XML-G01-S2-R 腾讯视频首页（双折叠内屏）

- 设备：双折叠 `22M0223928009654`，内屏 `2224×2496`。未用 hidumper。页是腾讯视频首页，搜索框是「黑岛监狱」。
- 数据集：`/Users/zhangyingying/UX-Agent/test-set/测试集0928/bifold_xml_normal/tencentvideo/g01/`。文件夹是 normal。同名 s2 json 里 1 框，「截断-文字」，贴在分类条右边。
- 模型原文：`image_path=/tmp/ux_upload_uexwqc_k.png`，`total_inference_sec=3.3892`，`parse_status=valid_root_json`，`inference_error=null`。`pred_text` 是 `{"overall":"ok","issues":[]}`。
- layout / 滑动：没有框，滑动跳过。
- 页级 **ok**。算法 **1.5s**（模型 4.6s 不算）。
- 哪一段：模型。分类条右边「短视」被切，数据集那 1 框这次没标。
- 改进方向：暂无。模型没给框，算法没有框可消。
- 证据：`/Users/zhangyingying/UX-Agent/HarmonyArena-fdu_agent/ux-detect-output/testset_0928/bifold_xml_normal/tencentvideo/g01/20260929-052447-091/`
- 状态：**页是首页。模型 0 框，页级 ok。**

### PH-TENCENTNEWS-XML-G01-S1-R 腾讯新闻要闻（手机）

- 设备：双折叠外屏 `22M0223928009654`，`1080×2504`。未用 hidumper。页是腾讯新闻「要闻」。
- 数据集：`/Users/zhangyingying/UX-Agent/test-set/测试集0928/phone_xml_normal/tencentnews/g01/`。文件夹是 normal。同名 json 里 4 框，都贴屏幕右沿：3 个「截断-文字」、1 个「截断-图标」，落在旁边露出来的下一张卡片上。
- 模型原文：`image_path=/tmp/ux_upload_qdxwp383.png`，`total_inference_sec=12.5163`，`parse_status=valid_root_json`，`inference_error=null`。`pred_text` 是 `{"overall":"bad","issues":[{"issue_type":"截断-文字","bbox":[954,486,1000,507],"truncated_edges":["right"]},{"issue_type":"截断-文字","bbox":[954,583,1000,608],"truncated_edges":["right"]},{"issue_type":"截断-文字","bbox":[954,614,1000,637],"truncated_edges":["right"]},{"issue_type":"截断-文字","bbox":[954,649,1000,664],"truncated_edges":["right"]}]}`。4 个都是「截断-文字」，没有「截断-图标」。
- layout：4 个框都是中文类型，layout 判 unknown，4 个都交给滑动。
- 滑动：4 框合成一组，向左。落点 `(734,1440)→(248,1440)`，位移 450。整行平均差 29.76%，变动 90.36%。第 1 框自身几乎没变（0.75%），其余三框变动 88%–97%。右滑恢复，行差 0。4 框都消掉。
- 页级 **ok**。算法 **5.6s**（模型 13.0s 不算）。
- 哪一段：模型把数据集里那个图标标成了文字。滑动把右沿露出来的卡片滑走了，页面滑回。
- 改进方向：暂无。这页按假截断消掉了。
- 证据：`/Users/zhangyingying/UX-Agent/HarmonyArena-fdu_agent/ux-detect-output/testset_0928/phone_xml_normal/tencentnews/g01/20260929-052734-389/`
- 状态：**页是要闻。模型 4 框，左滑后消掉，页级 ok。**

### 无框图官方检测 测试集0928 有 XML 且 json 没有框（50）

这 50 条同名 json 的 `shapes` 是空的。平板还停在 WPS，没有逐页连机滑动。每条用测试集里的 jpg 调校园网官方接口（`--mode=image`），目录里有这次的 `snapshot.png` 和 `model_http.json`。50 条模型都是 0 框，`parse_status=valid_root_json`，`inference_error=null`，`pred_text` 都是 `{"overall":"ok","issues":[]}`。layout 和滑动没跑。页级 **ok**。

#### bifold_xml_normal_alipay_g01_s1

- 数据集：`/Users/zhangyingying/UX-Agent/test-set/测试集0928/bifold_xml_normal/alipay/g01/bifold_xml_normal_alipay_g01_s1.jpg`，同名 json、xml。json 没有框。
- 模型原文：`image_path=/tmp/ux_upload_xhvfekx2.png`，`total_inference_sec=2.0997`，`parse_status=valid_root_json`，`inference_error=null`。`pred_text` 是 `{"overall":"ok","issues":[]}`。
- layout / 滑动：图不在当前设备上，这两段没跑。页级 **ok**。算法 **0.3s**。
- 证据：`/Users/zhangyingying/UX-Agent/HarmonyArena-fdu_agent/ux-detect-output/testset_0928/bifold_xml_normal/alipay/g01/20260929-051715-264`
- 状态：**模型 0 框，页级 ok。**

#### bifold_xml_normal_alipay_g01_s2

- 数据集：`/Users/zhangyingying/UX-Agent/test-set/测试集0928/bifold_xml_normal/alipay/g01/bifold_xml_normal_alipay_g01_s2.jpg`，同名 json、xml。json 没有框。
- 模型原文：`image_path=/tmp/ux_upload_unfmwvtl.png`，`total_inference_sec=3.3272`，`parse_status=valid_root_json`，`inference_error=null`。`pred_text` 是 `{"overall":"ok","issues":[]}`。
- layout / 滑动：图不在当前设备上，这两段没跑。页级 **ok**。算法 **0.2s**。
- 证据：`/Users/zhangyingying/UX-Agent/HarmonyArena-fdu_agent/ux-detect-output/testset_0928/bifold_xml_normal/alipay/g01/20260929-051718-357`
- 状态：**模型 0 框，页级 ok。**

#### bifold_xml_normal_bilibili_g01_s1

- 数据集：`/Users/zhangyingying/UX-Agent/test-set/测试集0928/bifold_xml_normal/bilibili/g01/bifold_xml_normal_bilibili_g01_s1.jpg`，同名 json、xml。json 没有框。
- 模型原文：`image_path=/tmp/ux_upload_o42qgxyj.png`，`total_inference_sec=2.0352`，`parse_status=valid_root_json`，`inference_error=null`。`pred_text` 是 `{"overall":"ok","issues":[]}`。
- layout / 滑动：图不在当前设备上，这两段没跑。页级 **ok**。算法 **0.3s**。
- 证据：`/Users/zhangyingying/UX-Agent/HarmonyArena-fdu_agent/ux-detect-output/testset_0928/bifold_xml_normal/bilibili/g01/20260929-051722-919`
- 状态：**模型 0 框，页级 ok。**

#### bifold_xml_normal_bilibili_g01_s2

- 数据集：`/Users/zhangyingying/UX-Agent/test-set/测试集0928/bifold_xml_normal/bilibili/g01/bifold_xml_normal_bilibili_g01_s2.jpg`，同名 json、xml。json 没有框。
- 模型原文：`image_path=/tmp/ux_upload_heglojai.png`，`total_inference_sec=3.3172`，`parse_status=valid_root_json`，`inference_error=null`。`pred_text` 是 `{"overall":"ok","issues":[]}`。
- layout / 滑动：图不在当前设备上，这两段没跑。页级 **ok**。算法 **0.3s**。
- 证据：`/Users/zhangyingying/UX-Agent/HarmonyArena-fdu_agent/ux-detect-output/testset_0928/bifold_xml_normal/bilibili/g01/20260929-051725-900`
- 状态：**模型 0 框，页级 ok。**

#### bifold_xml_normal_fanqie_g01_s1

- 数据集：`/Users/zhangyingying/UX-Agent/test-set/测试集0928/bifold_xml_normal/fanqie/g01/bifold_xml_normal_fanqie_g01_s1.jpg`，同名 json、xml。json 没有框。
- 模型原文：`image_path=/tmp/ux_upload_77d9cv5v.png`，`total_inference_sec=2.0339`，`parse_status=valid_root_json`，`inference_error=null`。`pred_text` 是 `{"overall":"ok","issues":[]}`。
- layout / 滑动：图不在当前设备上，这两段没跑。页级 **ok**。算法 **0.3s**。
- 证据：`/Users/zhangyingying/UX-Agent/HarmonyArena-fdu_agent/ux-detect-output/testset_0928/bifold_xml_normal/fanqie/g01/20260929-051730-550`
- 状态：**模型 0 框，页级 ok。**

#### bifold_xml_normal_fanqie_g01_s2

- 数据集：`/Users/zhangyingying/UX-Agent/test-set/测试集0928/bifold_xml_normal/fanqie/g01/bifold_xml_normal_fanqie_g01_s2.jpg`，同名 json、xml。json 没有框。
- 模型原文：`image_path=/tmp/ux_upload_5p9zpzwd.png`，`total_inference_sec=3.3257`，`parse_status=valid_root_json`，`inference_error=null`。`pred_text` 是 `{"overall":"ok","issues":[]}`。
- layout / 滑动：图不在当前设备上，这两段没跑。页级 **ok**。算法 **0.3s**。
- 证据：`/Users/zhangyingying/UX-Agent/HarmonyArena-fdu_agent/ux-detect-output/testset_0928/bifold_xml_normal/fanqie/g01/20260929-051733-457`
- 状态：**模型 0 框，页级 ok。**

#### bifold_xml_normal_meituan_g01_s1

- 数据集：`/Users/zhangyingying/UX-Agent/test-set/测试集0928/bifold_xml_normal/meituan/g01/bifold_xml_normal_meituan_g01_s1.jpg`，同名 json、xml。json 没有框。
- 模型原文：`image_path=/tmp/ux_upload_dueuio0l.png`，`total_inference_sec=2.0408`，`parse_status=valid_root_json`，`inference_error=null`。`pred_text` 是 `{"overall":"ok","issues":[]}`。
- layout / 滑动：图不在当前设备上，这两段没跑。页级 **ok**。算法 **0.3s**。
- 证据：`/Users/zhangyingying/UX-Agent/HarmonyArena-fdu_agent/ux-detect-output/testset_0928/bifold_xml_normal/meituan/g01/20260929-051738-231`
- 状态：**模型 0 框，页级 ok。**

#### bifold_xml_normal_meituan_g01_s2

- 数据集：`/Users/zhangyingying/UX-Agent/test-set/测试集0928/bifold_xml_normal/meituan/g01/bifold_xml_normal_meituan_g01_s2.jpg`，同名 json、xml。json 没有框。
- 模型原文：`image_path=/tmp/ux_upload_hygdno98.png`，`total_inference_sec=3.3258`，`parse_status=valid_root_json`，`inference_error=null`。`pred_text` 是 `{"overall":"ok","issues":[]}`。
- layout / 滑动：图不在当前设备上，这两段没跑。页级 **ok**。算法 **0.3s**。
- 证据：`/Users/zhangyingying/UX-Agent/HarmonyArena-fdu_agent/ux-detect-output/testset_0928/bifold_xml_normal/meituan/g01/20260929-051741-166`
- 状态：**模型 0 框，页级 ok。**

#### bifold_xml_normal_tencentvideo_g01_s1

- 数据集：`/Users/zhangyingying/UX-Agent/test-set/测试集0928/bifold_xml_normal/tencentvideo/g01/bifold_xml_normal_tencentvideo_g01_s1.jpg`，同名 json、xml。json 没有框。
- 模型原文：`image_path=/tmp/ux_upload_pdjwcnpz.png`，`total_inference_sec=2.0388`，`parse_status=valid_root_json`，`inference_error=null`。`pred_text` 是 `{"overall":"ok","issues":[]}`。
- layout / 滑动：图不在当前设备上，这两段没跑。页级 **ok**。算法 **0.3s**。
- 证据：`/Users/zhangyingying/UX-Agent/HarmonyArena-fdu_agent/ux-detect-output/testset_0928/bifold_xml_normal/tencentvideo/g01/20260929-051745-714`
- 状态：**模型 0 框，页级 ok。**

#### bifold_xml_normal_weibo_g01_s1

- 数据集：`/Users/zhangyingying/UX-Agent/test-set/测试集0928/bifold_xml_normal/weibo/g01/bifold_xml_normal_weibo_g01_s1.jpg`，同名 json、xml。json 没有框。
- 模型原文：`image_path=/tmp/ux_upload_w6izrs6a.png`，`total_inference_sec=2.0411`，`parse_status=valid_root_json`，`inference_error=null`。`pred_text` 是 `{"overall":"ok","issues":[]}`。
- layout / 滑动：图不在当前设备上，这两段没跑。页级 **ok**。算法 **0.3s**。
- 证据：`/Users/zhangyingying/UX-Agent/HarmonyArena-fdu_agent/ux-detect-output/testset_0928/bifold_xml_normal/weibo/g01/20260929-051748-685`
- 状态：**模型 0 框，页级 ok。**

#### bifold_xml_normal_weibo_g01_s2

- 数据集：`/Users/zhangyingying/UX-Agent/test-set/测试集0928/bifold_xml_normal/weibo/g01/bifold_xml_normal_weibo_g01_s2.jpg`，同名 json、xml。json 没有框。
- 模型原文：`image_path=/tmp/ux_upload_jnvdchod.png`，`total_inference_sec=3.369`，`parse_status=valid_root_json`，`inference_error=null`。`pred_text` 是 `{"overall":"ok","issues":[]}`。
- layout / 滑动：图不在当前设备上，这两段没跑。页级 **ok**。算法 **0.3s**。
- 证据：`/Users/zhangyingying/UX-Agent/HarmonyArena-fdu_agent/ux-detect-output/testset_0928/bifold_xml_normal/weibo/g01/20260929-051751-689`
- 状态：**模型 0 框，页级 ok。**

#### bifold_xml_normal_xiaohongshu_g01_s1

- 数据集：`/Users/zhangyingying/UX-Agent/test-set/测试集0928/bifold_xml_normal/xiaohongshu/g01/bifold_xml_normal_xiaohongshu_g01_s1.jpg`，同名 json、xml。json 没有框。
- 模型原文：`image_path=/tmp/ux_upload_vjcjj8l4.png`，`total_inference_sec=2.0448`，`parse_status=valid_root_json`，`inference_error=null`。`pred_text` 是 `{"overall":"ok","issues":[]}`。
- layout / 滑动：图不在当前设备上，这两段没跑。页级 **ok**。算法 **0.3s**。
- 证据：`/Users/zhangyingying/UX-Agent/HarmonyArena-fdu_agent/ux-detect-output/testset_0928/bifold_xml_normal/xiaohongshu/g01/20260929-051756-280`
- 状态：**模型 0 框，页级 ok。**

#### bifold_xml_normal_xiaohongshu_g01_s2

- 数据集：`/Users/zhangyingying/UX-Agent/test-set/测试集0928/bifold_xml_normal/xiaohongshu/g01/bifold_xml_normal_xiaohongshu_g01_s2.jpg`，同名 json、xml。json 没有框。
- 模型原文：`image_path=/tmp/ux_upload_8htqwlup.png`，`total_inference_sec=3.3831`，`parse_status=valid_root_json`，`inference_error=null`。`pred_text` 是 `{"overall":"ok","issues":[]}`。
- layout / 滑动：图不在当前设备上，这两段没跑。页级 **ok**。算法 **0.3s**。
- 证据：`/Users/zhangyingying/UX-Agent/HarmonyArena-fdu_agent/ux-detect-output/testset_0928/bifold_xml_normal/xiaohongshu/g01/20260929-051759-148`
- 状态：**模型 0 框，页级 ok。**

#### bifold_xml_normal_zhihu_g01_s1

- 数据集：`/Users/zhangyingying/UX-Agent/test-set/测试集0928/bifold_xml_normal/zhihu/g01/bifold_xml_normal_zhihu_g01_s1.jpg`，同名 json、xml。json 没有框。
- 模型原文：`image_path=/tmp/ux_upload_si0k2scz.png`，`total_inference_sec=2.0335`，`parse_status=valid_root_json`，`inference_error=null`。`pred_text` 是 `{"overall":"ok","issues":[]}`。
- layout / 滑动：图不在当前设备上，这两段没跑。页级 **ok**。算法 **0.3s**。
- 证据：`/Users/zhangyingying/UX-Agent/HarmonyArena-fdu_agent/ux-detect-output/testset_0928/bifold_xml_normal/zhihu/g01/20260929-051803-774`
- 状态：**模型 0 框，页级 ok。**

#### bifold_xml_normal_zhihu_g01_s2

- 数据集：`/Users/zhangyingying/UX-Agent/test-set/测试集0928/bifold_xml_normal/zhihu/g01/bifold_xml_normal_zhihu_g01_s2.jpg`，同名 json、xml。json 没有框。
- 模型原文：`image_path=/tmp/ux_upload_qc4qowxi.png`，`total_inference_sec=3.381`，`parse_status=valid_root_json`，`inference_error=null`。`pred_text` 是 `{"overall":"ok","issues":[]}`。
- layout / 滑动：图不在当前设备上，这两段没跑。页级 **ok**。算法 **0.3s**。
- 证据：`/Users/zhangyingying/UX-Agent/HarmonyArena-fdu_agent/ux-detect-output/testset_0928/bifold_xml_normal/zhihu/g01/20260929-051806-633`
- 状态：**模型 0 框，页级 ok。**

#### phone_xml_normal_ctrip_g01_s1

- 数据集：`/Users/zhangyingying/UX-Agent/test-set/测试集0928/phone_xml_normal/ctrip/g01/phone_xml_normal_ctrip_g01_s1.jpg`，同名 json、xml。json 没有框。
- 模型原文：`image_path=/tmp/ux_upload_i3pebrw1.png`，`total_inference_sec=2.3175`，`parse_status=valid_root_json`，`inference_error=null`。`pred_text` 是 `{"overall":"ok","issues":[]}`。
- layout / 滑动：图不在当前设备上，这两段没跑。页级 **ok**。算法 **0.3s**。
- 证据：`/Users/zhangyingying/UX-Agent/HarmonyArena-fdu_agent/ux-detect-output/testset_0928/phone_xml_normal/ctrip/g01/20260929-051811-158`
- 状态：**模型 0 框，页级 ok。**

#### phone_xml_normal_dingding_g01_s1

- 数据集：`/Users/zhangyingying/UX-Agent/test-set/测试集0928/phone_xml_normal/dingding/g01/phone_xml_normal_dingding_g01_s1.jpg`，同名 json、xml。json 没有框。
- 模型原文：`image_path=/tmp/ux_upload_4fvste47.png`，`total_inference_sec=2.3068`，`parse_status=valid_root_json`，`inference_error=null`。`pred_text` 是 `{"overall":"ok","issues":[]}`。
- layout / 滑动：图不在当前设备上，这两段没跑。页级 **ok**。算法 **0.3s**。
- 证据：`/Users/zhangyingying/UX-Agent/HarmonyArena-fdu_agent/ux-detect-output/testset_0928/phone_xml_normal/dingding/g01/20260929-051814-439`
- 状态：**模型 0 框，页级 ok。**

#### phone_xml_normal_iqiyi_g01_s1

- 数据集：`/Users/zhangyingying/UX-Agent/test-set/测试集0928/phone_xml_normal/iqiyi/g01/phone_xml_normal_iqiyi_g01_s1.jpg`，同名 json、xml。json 没有框。
- 模型原文：`image_path=/tmp/ux_upload_vj1gpab6.png`，`total_inference_sec=2.3096`，`parse_status=valid_root_json`，`inference_error=null`。`pred_text` 是 `{"overall":"ok","issues":[]}`。
- layout / 滑动：图不在当前设备上，这两段没跑。页级 **ok**。算法 **0.3s**。
- 证据：`/Users/zhangyingying/UX-Agent/HarmonyArena-fdu_agent/ux-detect-output/testset_0928/phone_xml_normal/iqiyi/g01/20260929-051817-782`
- 状态：**模型 0 框，页级 ok。**

#### phone_xml_normal_qq_g01_s1

- 数据集：`/Users/zhangyingying/UX-Agent/test-set/测试集0928/phone_xml_normal/qq/g01/phone_xml_normal_qq_g01_s1.jpg`，同名 json、xml。json 没有框。
- 模型原文：`image_path=/tmp/ux_upload_kzvq9vwl.png`，`total_inference_sec=2.3074`，`parse_status=valid_root_json`，`inference_error=null`。`pred_text` 是 `{"overall":"ok","issues":[]}`。
- layout / 滑动：图不在当前设备上，这两段没跑。页级 **ok**。算法 **0.3s**。
- 证据：`/Users/zhangyingying/UX-Agent/HarmonyArena-fdu_agent/ux-detect-output/testset_0928/phone_xml_normal/qq/g01/20260929-051821-106`
- 状态：**模型 0 框，页级 ok。**

#### tablet_xml_normal_amap_g02_s1

- 数据集：`/Users/zhangyingying/UX-Agent/test-set/测试集0928/tablet_xml_normal/amap/g02/tablet_xml_normal_amap_g02_s1.jpg`，同名 json、xml。json 没有框。
- 模型原文：`image_path=/tmp/ux_upload_3h6sad02.png`，`total_inference_sec=3.1288`，`parse_status=valid_root_json`，`inference_error=null`。`pred_text` 是 `{"overall":"ok","issues":[]}`。
- layout / 滑动：图不在当前设备上，这两段没跑。页级 **ok**。算法 **0.3s**。
- 证据：`/Users/zhangyingying/UX-Agent/HarmonyArena-fdu_agent/ux-detect-output/testset_0928/tablet_xml_normal/amap/g02/20260929-051824-368`
- 状态：**模型 0 框，页级 ok。**

#### tablet_xml_normal_dianping_g01_s1

- 数据集：`/Users/zhangyingying/UX-Agent/test-set/测试集0928/tablet_xml_normal/dianping/g01/tablet_xml_normal_dianping_g01_s1.jpg`，同名 json、xml。json 没有框。
- 模型原文：`image_path=/tmp/ux_upload_u65ouq0m.png`，`total_inference_sec=3.1207`，`parse_status=valid_root_json`，`inference_error=null`。`pred_text` 是 `{"overall":"ok","issues":[]}`。
- layout / 滑动：图不在当前设备上，这两段没跑。页级 **ok**。算法 **0.3s**。
- 证据：`/Users/zhangyingying/UX-Agent/HarmonyArena-fdu_agent/ux-detect-output/testset_0928/tablet_xml_normal/dianping/g01/20260929-051828-733`
- 状态：**模型 0 框，页级 ok。**

#### tablet_xml_normal_dianping_g02_s1

- 数据集：`/Users/zhangyingying/UX-Agent/test-set/测试集0928/tablet_xml_normal/dianping/g02/tablet_xml_normal_dianping_g02_s1.jpg`，同名 json、xml。json 没有框。
- 模型原文：`image_path=/tmp/ux_upload_3ku_zfvz.png`，`total_inference_sec=3.1663`，`parse_status=valid_root_json`，`inference_error=null`。`pred_text` 是 `{"overall":"ok","issues":[]}`。
- layout / 滑动：图不在当前设备上，这两段没跑。页级 **ok**。算法 **0.3s**。
- 证据：`/Users/zhangyingying/UX-Agent/HarmonyArena-fdu_agent/ux-detect-output/testset_0928/tablet_xml_normal/dianping/g02/20260929-051832-992`
- 状态：**模型 0 框，页级 ok。**

#### tablet_xml_normal_kugou_g01_s1

- 数据集：`/Users/zhangyingying/UX-Agent/test-set/测试集0928/tablet_xml_normal/kugou/g01/tablet_xml_normal_kugou_g01_s1.jpg`，同名 json、xml。json 没有框。
- 模型原文：`image_path=/tmp/ux_upload_wrnehxek.png`，`total_inference_sec=3.1753`，`parse_status=valid_root_json`，`inference_error=null`。`pred_text` 是 `{"overall":"ok","issues":[]}`。
- layout / 滑动：图不在当前设备上，这两段没跑。页级 **ok**。算法 **0.3s**。
- 证据：`/Users/zhangyingying/UX-Agent/HarmonyArena-fdu_agent/ux-detect-output/testset_0928/tablet_xml_normal/kugou/g01/20260929-051837-513`
- 状态：**模型 0 框，页级 ok。**

#### tablet_xml_normal_kugou_g02_s1

- 数据集：`/Users/zhangyingying/UX-Agent/test-set/测试集0928/tablet_xml_normal/kugou/g02/tablet_xml_normal_kugou_g02_s1.jpg`，同名 json、xml。json 没有框。
- 模型原文：`image_path=/tmp/ux_upload_m5ojlxk1.png`，`total_inference_sec=3.1711`，`parse_status=valid_root_json`，`inference_error=null`。`pred_text` 是 `{"overall":"ok","issues":[]}`。
- layout / 滑动：图不在当前设备上，这两段没跑。页级 **ok**。算法 **0.2s**。
- 证据：`/Users/zhangyingying/UX-Agent/HarmonyArena-fdu_agent/ux-detect-output/testset_0928/tablet_xml_normal/kugou/g02/20260929-051841-845`
- 状态：**模型 0 框，页级 ok。**

#### tablet_xml_normal_railway12306_g01_s1

- 数据集：`/Users/zhangyingying/UX-Agent/test-set/测试集0928/tablet_xml_normal/railway12306/g01/tablet_xml_normal_railway12306_g01_s1.jpg`，同名 json、xml。json 没有框。
- 模型原文：`image_path=/tmp/ux_upload__ahgck98.png`，`total_inference_sec=3.1708`，`parse_status=valid_root_json`，`inference_error=null`。`pred_text` 是 `{"overall":"ok","issues":[]}`。
- layout / 滑动：图不在当前设备上，这两段没跑。页级 **ok**。算法 **0.3s**。
- 证据：`/Users/zhangyingying/UX-Agent/HarmonyArena-fdu_agent/ux-detect-output/testset_0928/tablet_xml_normal/railway12306/g01/20260929-051846-166`
- 状态：**模型 0 框，页级 ok。**

#### tablet_xml_normal_tencentmeeting_g01_s1

- 数据集：`/Users/zhangyingying/UX-Agent/test-set/测试集0928/tablet_xml_normal/tencentmeeting/g01/tablet_xml_normal_tencentmeeting_g01_s1.jpg`，同名 json、xml。json 没有框。
- 模型原文：`image_path=/tmp/ux_upload_uuomdwwd.png`，`total_inference_sec=3.1394`，`parse_status=valid_root_json`，`inference_error=null`。`pred_text` 是 `{"overall":"ok","issues":[]}`。
- layout / 滑动：图不在当前设备上，这两段没跑。页级 **ok**。算法 **0.3s**。
- 证据：`/Users/zhangyingying/UX-Agent/HarmonyArena-fdu_agent/ux-detect-output/testset_0928/tablet_xml_normal/tencentmeeting/g01/20260929-051850-550`
- 状态：**模型 0 框，页级 ok。**

#### tablet_xml_normal_tencentmeeting_g02_s1

- 数据集：`/Users/zhangyingying/UX-Agent/test-set/测试集0928/tablet_xml_normal/tencentmeeting/g02/tablet_xml_normal_tencentmeeting_g02_s1.jpg`，同名 json、xml。json 没有框。
- 模型原文：`image_path=/tmp/ux_upload_dp8r2eaa.png`，`total_inference_sec=3.1216`，`parse_status=valid_root_json`，`inference_error=null`。`pred_text` 是 `{"overall":"ok","issues":[]}`。
- layout / 滑动：图不在当前设备上，这两段没跑。页级 **ok**。算法 **0.3s**。
- 证据：`/Users/zhangyingying/UX-Agent/HarmonyArena-fdu_agent/ux-detect-output/testset_0928/tablet_xml_normal/tencentmeeting/g02/20260929-051854-798`
- 状态：**模型 0 框，页级 ok。**

#### tablet_xml_normal_uc_g01_s1

- 数据集：`/Users/zhangyingying/UX-Agent/test-set/测试集0928/tablet_xml_normal/uc/g01/tablet_xml_normal_uc_g01_s1.jpg`，同名 json、xml。json 没有框。
- 模型原文：`image_path=/tmp/ux_upload_dokkxf94.png`，`total_inference_sec=3.1228`，`parse_status=valid_root_json`，`inference_error=null`。`pred_text` 是 `{"overall":"ok","issues":[]}`。
- layout / 滑动：图不在当前设备上，这两段没跑。页级 **ok**。算法 **0.3s**。
- 证据：`/Users/zhangyingying/UX-Agent/HarmonyArena-fdu_agent/ux-detect-output/testset_0928/tablet_xml_normal/uc/g01/20260929-051859-072`
- 状态：**模型 0 框，页级 ok。**

#### tablet_xml_normal_uc_g02_s1

- 数据集：`/Users/zhangyingying/UX-Agent/test-set/测试集0928/tablet_xml_normal/uc/g02/tablet_xml_normal_uc_g02_s1.jpg`，同名 json、xml。json 没有框。
- 模型原文：`image_path=/tmp/ux_upload_nc_qs4p4.png`，`total_inference_sec=3.1285`，`parse_status=valid_root_json`，`inference_error=null`。`pred_text` 是 `{"overall":"ok","issues":[]}`。
- layout / 滑动：图不在当前设备上，这两段没跑。页级 **ok**。算法 **0.3s**。
- 证据：`/Users/zhangyingying/UX-Agent/HarmonyArena-fdu_agent/ux-detect-output/testset_0928/tablet_xml_normal/uc/g02/20260929-051903-333`
- 状态：**模型 0 框，页级 ok。**

#### tablet_xml_normal_wechat_g01_s1

- 数据集：`/Users/zhangyingying/UX-Agent/test-set/测试集0928/tablet_xml_normal/wechat/g01/tablet_xml_normal_wechat_g01_s1.jpg`，同名 json、xml。json 没有框。
- 模型原文：`image_path=/tmp/ux_upload_g0shqqdc.png`，`total_inference_sec=3.1227`，`parse_status=valid_root_json`，`inference_error=null`。`pred_text` 是 `{"overall":"ok","issues":[]}`。
- layout / 滑动：图不在当前设备上，这两段没跑。页级 **ok**。算法 **0.3s**。
- 证据：`/Users/zhangyingying/UX-Agent/HarmonyArena-fdu_agent/ux-detect-output/testset_0928/tablet_xml_normal/wechat/g01/20260929-051907-680`
- 状态：**模型 0 框，页级 ok。**

#### tablet_xml_normal_wechat_g02_s1

- 数据集：`/Users/zhangyingying/UX-Agent/test-set/测试集0928/tablet_xml_normal/wechat/g02/tablet_xml_normal_wechat_g02_s1.jpg`，同名 json、xml。json 没有框。
- 模型原文：`image_path=/tmp/ux_upload_cu3zc2w_.png`，`total_inference_sec=3.1298`，`parse_status=valid_root_json`，`inference_error=null`。`pred_text` 是 `{"overall":"ok","issues":[]}`。
- layout / 滑动：图不在当前设备上，这两段没跑。页级 **ok**。算法 **0.3s**。
- 证据：`/Users/zhangyingying/UX-Agent/HarmonyArena-fdu_agent/ux-detect-output/testset_0928/tablet_xml_normal/wechat/g02/20260929-051911-925`
- 状态：**模型 0 框，页级 ok。**

#### tablet_xml_normal_wps_g02_s1

- 数据集：`/Users/zhangyingying/UX-Agent/test-set/测试集0928/tablet_xml_normal/wps/g02/tablet_xml_normal_wps_g02_s1.jpg`，同名 json、xml。json 没有框。
- 模型原文：`image_path=/tmp/ux_upload_jts6ptts.png`，`total_inference_sec=3.192`，`parse_status=valid_root_json`，`inference_error=null`。`pred_text` 是 `{"overall":"ok","issues":[]}`。
- layout / 滑动：图不在当前设备上，这两段没跑。页级 **ok**。算法 **0.2s**。
- 证据：`/Users/zhangyingying/UX-Agent/HarmonyArena-fdu_agent/ux-detect-output/testset_0928/tablet_xml_normal/wps/g02/20260929-051916-208`
- 状态：**模型 0 框，页级 ok。**

#### tablet_xml_normal_ximalaya_g01_s1

- 数据集：`/Users/zhangyingying/UX-Agent/test-set/测试集0928/tablet_xml_normal/ximalaya/g01/tablet_xml_normal_ximalaya_g01_s1.jpg`，同名 json、xml。json 没有框。
- 模型原文：`image_path=/tmp/ux_upload_ploozhui.png`，`total_inference_sec=3.1882`，`parse_status=valid_root_json`，`inference_error=null`。`pred_text` 是 `{"overall":"ok","issues":[]}`。
- layout / 滑动：图不在当前设备上，这两段没跑。页级 **ok**。算法 **0.3s**。
- 证据：`/Users/zhangyingying/UX-Agent/HarmonyArena-fdu_agent/ux-detect-output/testset_0928/tablet_xml_normal/ximalaya/g01/20260929-051920-507`
- 状态：**模型 0 框，页级 ok。**

#### tablet_xml_normal_ximalaya_g02_s1

- 数据集：`/Users/zhangyingying/UX-Agent/test-set/测试集0928/tablet_xml_normal/ximalaya/g02/tablet_xml_normal_ximalaya_g02_s1.jpg`，同名 json、xml。json 没有框。
- 模型原文：`image_path=/tmp/ux_upload_qxw5t92h.png`，`total_inference_sec=3.1882`，`parse_status=valid_root_json`，`inference_error=null`。`pred_text` 是 `{"overall":"ok","issues":[]}`。
- layout / 滑动：图不在当前设备上，这两段没跑。页级 **ok**。算法 **0.3s**。
- 证据：`/Users/zhangyingying/UX-Agent/HarmonyArena-fdu_agent/ux-detect-output/testset_0928/tablet_xml_normal/ximalaya/g02/20260929-051924-869`
- 状态：**模型 0 框，页级 ok。**

#### trifold_xml_normal_jd_g01_s3

- 数据集：`/Users/zhangyingying/UX-Agent/test-set/测试集0928/trifold_xml_normal/jd/g01/trifold_xml_normal_jd_g01_s3.jpg`，同名 json、xml。json 没有框。
- 模型原文：`image_path=/tmp/ux_upload_5bidutqz.png`，`total_inference_sec=4.1396`，`parse_status=valid_root_json`，`inference_error=null`。`pred_text` 是 `{"overall":"ok","issues":[]}`。
- layout / 滑动：图不在当前设备上，这两段没跑。页级 **ok**。算法 **0.3s**。
- 证据：`/Users/zhangyingying/UX-Agent/HarmonyArena-fdu_agent/ux-detect-output/testset_0928/trifold_xml_normal/jd/g01/20260929-051929-191`
- 状态：**模型 0 框，页级 ok。**

#### trifold_xml_normal_qqmusic_g01_s1

- 数据集：`/Users/zhangyingying/UX-Agent/test-set/测试集0928/trifold_xml_normal/qqmusic/g01/trifold_xml_normal_qqmusic_g01_s1.jpg`，同名 json、xml。json 没有框。
- 模型原文：`image_path=/tmp/ux_upload_h7e22lhg.png`，`total_inference_sec=1.8812`，`parse_status=valid_root_json`，`inference_error=null`。`pred_text` 是 `{"overall":"ok","issues":[]}`。
- layout / 滑动：图不在当前设备上，这两段没跑。页级 **ok**。算法 **0.3s**。
- 证据：`/Users/zhangyingying/UX-Agent/HarmonyArena-fdu_agent/ux-detect-output/testset_0928/trifold_xml_normal/qqmusic/g01/20260929-051934-736`
- 状态：**模型 0 框，页级 ok。**

#### trifold_xml_normal_qqmusic_g01_s2

- 数据集：`/Users/zhangyingying/UX-Agent/test-set/测试集0928/trifold_xml_normal/qqmusic/g01/trifold_xml_normal_qqmusic_g01_s2.jpg`，同名 json、xml。json 没有框。
- 模型原文：`image_path=/tmp/ux_upload__r650kp9.png`，`total_inference_sec=2.8731`，`parse_status=valid_root_json`，`inference_error=null`。`pred_text` 是 `{"overall":"ok","issues":[]}`。
- layout / 滑动：图不在当前设备上，这两段没跑。页级 **ok**。算法 **0.3s**。
- 证据：`/Users/zhangyingying/UX-Agent/HarmonyArena-fdu_agent/ux-detect-output/testset_0928/trifold_xml_normal/qqmusic/g01/20260929-051937-506`
- 状态：**模型 0 框，页级 ok。**

#### trifold_xml_normal_qqmusic_g01_s3

- 数据集：`/Users/zhangyingying/UX-Agent/test-set/测试集0928/trifold_xml_normal/qqmusic/g01/trifold_xml_normal_qqmusic_g01_s3.jpg`，同名 json、xml。json 没有框。
- 模型原文：`image_path=/tmp/ux_upload_u8x1ysl9.png`，`total_inference_sec=4.2189`，`parse_status=valid_root_json`，`inference_error=null`。`pred_text` 是 `{"overall":"ok","issues":[]}`。
- layout / 滑动：图不在当前设备上，这两段没跑。页级 **ok**。算法 **0.3s**。
- 证据：`/Users/zhangyingying/UX-Agent/HarmonyArena-fdu_agent/ux-detect-output/testset_0928/trifold_xml_normal/qqmusic/g01/20260929-051941-581`
- 状态：**模型 0 框，页级 ok。**

#### trifold_xml_normal_toutiao_g01_s1

- 数据集：`/Users/zhangyingying/UX-Agent/test-set/测试集0928/trifold_xml_normal/toutiao/g01/trifold_xml_normal_toutiao_g01_s1.jpg`，同名 json、xml。json 没有框。
- 模型原文：`image_path=/tmp/ux_upload_hanmknls.png`，`total_inference_sec=1.8861`，`parse_status=valid_root_json`，`inference_error=null`。`pred_text` 是 `{"overall":"ok","issues":[]}`。
- layout / 滑动：图不在当前设备上，这两段没跑。页级 **ok**。算法 **0.3s**。
- 证据：`/Users/zhangyingying/UX-Agent/HarmonyArena-fdu_agent/ux-detect-output/testset_0928/trifold_xml_normal/toutiao/g01/20260929-051947-261`
- 状态：**模型 0 框，页级 ok。**

#### trifold_xml_normal_toutiao_g01_s2

- 数据集：`/Users/zhangyingying/UX-Agent/test-set/测试集0928/trifold_xml_normal/toutiao/g01/trifold_xml_normal_toutiao_g01_s2.jpg`，同名 json、xml。json 没有框。
- 模型原文：`image_path=/tmp/ux_upload_tv0jpcac.png`，`total_inference_sec=2.8262`，`parse_status=valid_root_json`，`inference_error=null`。`pred_text` 是 `{"overall":"ok","issues":[]}`。
- layout / 滑动：图不在当前设备上，这两段没跑。页级 **ok**。算法 **0.3s**。
- 证据：`/Users/zhangyingying/UX-Agent/HarmonyArena-fdu_agent/ux-detect-output/testset_0928/trifold_xml_normal/toutiao/g01/20260929-051950-071`
- 状态：**模型 0 框，页级 ok。**

#### trifold_xml_normal_toutiao_g01_s3

- 数据集：`/Users/zhangyingying/UX-Agent/test-set/测试集0928/trifold_xml_normal/toutiao/g01/trifold_xml_normal_toutiao_g01_s3.jpg`，同名 json、xml。json 没有框。
- 模型原文：`image_path=/tmp/ux_upload_t5pb42f1.png`，`total_inference_sec=4.1448`，`parse_status=valid_root_json`，`inference_error=null`。`pred_text` 是 `{"overall":"ok","issues":[]}`。
- layout / 滑动：图不在当前设备上，这两段没跑。页级 **ok**。算法 **0.3s**。
- 证据：`/Users/zhangyingying/UX-Agent/HarmonyArena-fdu_agent/ux-detect-output/testset_0928/trifold_xml_normal/toutiao/g01/20260929-051954-010`
- 状态：**模型 0 框，页级 ok。**

#### trifold_xml_normal_wecom_g01_s1

- 数据集：`/Users/zhangyingying/UX-Agent/test-set/测试集0928/trifold_xml_normal/wecom/g01/trifold_xml_normal_wecom_g01_s1.jpg`，同名 json、xml。json 没有框。
- 模型原文：`image_path=/tmp/ux_upload_w5u5jqma.png`，`total_inference_sec=1.8886`，`parse_status=valid_root_json`，`inference_error=null`。`pred_text` 是 `{"overall":"ok","issues":[]}`。
- layout / 滑动：图不在当前设备上，这两段没跑。页级 **ok**。算法 **0.3s**。
- 证据：`/Users/zhangyingying/UX-Agent/HarmonyArena-fdu_agent/ux-detect-output/testset_0928/trifold_xml_normal/wecom/g01/20260929-051959-559`
- 状态：**模型 0 框，页级 ok。**

#### trifold_xml_normal_wecom_g01_s2

- 数据集：`/Users/zhangyingying/UX-Agent/test-set/测试集0928/trifold_xml_normal/wecom/g01/trifold_xml_normal_wecom_g01_s2.jpg`，同名 json、xml。json 没有框。
- 模型原文：`image_path=/tmp/ux_upload_1h2v7r0i.png`，`total_inference_sec=2.8342`，`parse_status=valid_root_json`，`inference_error=null`。`pred_text` 是 `{"overall":"ok","issues":[]}`。
- layout / 滑动：图不在当前设备上，这两段没跑。页级 **ok**。算法 **0.3s**。
- 证据：`/Users/zhangyingying/UX-Agent/HarmonyArena-fdu_agent/ux-detect-output/testset_0928/trifold_xml_normal/wecom/g01/20260929-052002-345`
- 状态：**模型 0 框，页级 ok。**

#### trifold_xml_normal_wecom_g01_s3

- 数据集：`/Users/zhangyingying/UX-Agent/test-set/测试集0928/trifold_xml_normal/wecom/g01/trifold_xml_normal_wecom_g01_s3.jpg`，同名 json、xml。json 没有框。
- 模型原文：`image_path=/tmp/ux_upload___czjj8z.png`，`total_inference_sec=4.1508`，`parse_status=valid_root_json`，`inference_error=null`。`pred_text` 是 `{"overall":"ok","issues":[]}`。
- layout / 滑动：图不在当前设备上，这两段没跑。页级 **ok**。算法 **0.3s**。
- 证据：`/Users/zhangyingying/UX-Agent/HarmonyArena-fdu_agent/ux-detect-output/testset_0928/trifold_xml_normal/wecom/g01/20260929-052006-311`
- 状态：**模型 0 框，页级 ok。**

#### widefold_xml_normal_didi_g01_s1

- 数据集：`/Users/zhangyingying/UX-Agent/test-set/测试集0928/widefold_xml_normal/didi/g01/widefold_xml_normal_didi_g01_s1.jpg`，同名 json、xml。json 没有框。
- 模型原文：`image_path=/tmp/ux_upload_njh1mpwh.png`，`total_inference_sec=1.9238`，`parse_status=valid_root_json`，`inference_error=null`。`pred_text` 是 `{"overall":"ok","issues":[]}`。
- layout / 滑动：图不在当前设备上，这两段没跑。页级 **ok**。算法 **0.2s**。
- 证据：`/Users/zhangyingying/UX-Agent/HarmonyArena-fdu_agent/ux-detect-output/testset_0928/widefold_xml_normal/didi/g01/20260929-052011-887`
- 状态：**模型 0 框，页级 ok。**

#### widefold_xml_normal_didi_g01_s2

- 数据集：`/Users/zhangyingying/UX-Agent/test-set/测试集0928/widefold_xml_normal/didi/g01/widefold_xml_normal_didi_g01_s2.jpg`，同名 json、xml。json 没有框。
- 模型原文：`image_path=/tmp/ux_upload_w3f8b6ai.png`，`total_inference_sec=2.9582`，`parse_status=valid_root_json`，`inference_error=null`。`pred_text` 是 `{"overall":"ok","issues":[]}`。
- layout / 滑动：图不在当前设备上，这两段没跑。页级 **ok**。算法 **0.2s**。
- 证据：`/Users/zhangyingying/UX-Agent/HarmonyArena-fdu_agent/ux-detect-output/testset_0928/widefold_xml_normal/didi/g01/20260929-052014-558`
- 状态：**模型 0 框，页级 ok。**

#### widefold_xml_normal_douyin_g01_s1

- 数据集：`/Users/zhangyingying/UX-Agent/test-set/测试集0928/widefold_xml_normal/douyin/g01/widefold_xml_normal_douyin_g01_s1.jpg`，同名 json、xml。json 没有框。
- 模型原文：`image_path=/tmp/ux_upload_qysh0kf6.png`，`total_inference_sec=1.9273`，`parse_status=valid_root_json`，`inference_error=null`。`pred_text` 是 `{"overall":"ok","issues":[]}`。
- layout / 滑动：图不在当前设备上，这两段没跑。页级 **ok**。算法 **0.8s**。
- 证据：`/Users/zhangyingying/UX-Agent/HarmonyArena-fdu_agent/ux-detect-output/testset_0928/widefold_xml_normal/douyin/g01/20260929-052018-664`
- 状态：**模型 0 框，页级 ok。**

#### widefold_xml_normal_douyin_g01_s2

- 数据集：`/Users/zhangyingying/UX-Agent/test-set/测试集0928/widefold_xml_normal/douyin/g01/widefold_xml_normal_douyin_g01_s2.jpg`，同名 json、xml。json 没有框。
- 模型原文：`image_path=/tmp/ux_upload_e14o2yb_.png`，`total_inference_sec=2.9412`，`parse_status=valid_root_json`，`inference_error=null`。`pred_text` 是 `{"overall":"ok","issues":[]}`。
- layout / 滑动：图不在当前设备上，这两段没跑。页级 **ok**。算法 **0.3s**。
- 证据：`/Users/zhangyingying/UX-Agent/HarmonyArena-fdu_agent/ux-detect-output/testset_0928/widefold_xml_normal/douyin/g01/20260929-052022-012`
- 状态：**模型 0 框，页级 ok。**

#### widefold_xml_normal_taobao_g01_s2

- 数据集：`/Users/zhangyingying/UX-Agent/test-set/测试集0928/widefold_xml_normal/taobao/g01/widefold_xml_normal_taobao_g01_s2.jpg`，同名 json、xml。json 没有框。
- 模型原文：`image_path=/tmp/ux_upload_gvuex5fq.png`，`total_inference_sec=2.9569`，`parse_status=valid_root_json`，`inference_error=null`。`pred_text` 是 `{"overall":"ok","issues":[]}`。
- layout / 滑动：图不在当前设备上，这两段没跑。页级 **ok**。算法 **0.3s**。
- 证据：`/Users/zhangyingying/UX-Agent/HarmonyArena-fdu_agent/ux-detect-output/testset_0928/widefold_xml_normal/taobao/g01/20260929-052026-093`
- 状态：**模型 0 框，页级 ok。**

#### widefold_xml_normal_vipshop_g01_s1

- 数据集：`/Users/zhangyingying/UX-Agent/test-set/测试集0928/widefold_xml_normal/vipshop/g01/widefold_xml_normal_vipshop_g01_s1.jpg`，同名 json、xml。json 没有框。
- 模型原文：`image_path=/tmp/ux_upload_fliug1pb.png`，`total_inference_sec=1.9317`，`parse_status=valid_root_json`，`inference_error=null`。`pred_text` 是 `{"overall":"ok","issues":[]}`。
- layout / 滑动：图不在当前设备上，这两段没跑。页级 **ok**。算法 **0.3s**。
- 证据：`/Users/zhangyingying/UX-Agent/HarmonyArena-fdu_agent/ux-detect-output/testset_0928/widefold_xml_normal/vipshop/g01/20260929-052030-197`
- 状态：**模型 0 框，页级 ok。**
