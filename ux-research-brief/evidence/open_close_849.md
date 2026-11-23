类型：记录 ｜ 归属：2026-11-23 离线统计 ｜ 状态：已出数（Grok 子 agent 计算，主 agent 核过合计）

# 开合 849 组打标分布

复现：`python3 /tmp/ana_0123/analyze_0123.py`

每一组是一个 `tNN.json`。result、hits、result_cut10、result_cut20 都从该 json 读。`summary.json`、`summary.md`、`fail_266_索引.csv` 只做核对，不作为计数来源。规则原文用来解释 P1–P6 是什么，没有按规则重判。

目录：`/Users/zhangyingying/UX-Agent/docs/开合检测/交付/打包_2026-11-17_双折叠开合/02_打标结果_vlm_judge_1029_gpt/`

## 1. 规模

- run 目录 20 个。每个目录名都含 `_uniform_`，前缀取这之前的一段。
- 前缀 13 个，映射成 13 个中文名。`news` 的中文名就是索引里的「新闻类(今日头条或腾讯新闻)」，json 里没有字段可以再拆成今日头条和腾讯新闻，所以 App 数按 13 计，不按 14。
- 组数 849。材料写的是 849。差额：0。
- fail 266，pass 523，invalid 60，uncertain 0，其他 0。材料写 fail 约 266。差额：fail 0。
- 有的 run 编号不连续。组数按现有 json 文件计，缺号没有补进去：
  - hmeituan_uniform_1028_191442 min=1 max=44 缺 3 4 23 24
  - hos_uniform_1029_073950 min=1 max=12 缺 8
- run 目录里的 json 都是 `t` 加数字，没有别的 json。
- `_meta.model`：gpt-5.6-sol 849。`_meta.bucket`：ok 485、flagged 364。

## 2. 按 App

同一前缀的多个 run 已合并。分 run 的数在第 5 节和 `/tmp/ana_0123/B_open_close_by_run.csv`。

fail 率两列都给：`fail/组数` 的分母含 invalid；`fail/已判定` 的分母是 fail+pass。去哪儿几乎全是 invalid，两列差很多。

| 前缀 | 中文名 | run数 | 组数 | fail | pass | invalid | uncertain | fail/组数 | fail/已判定 | 只P1 |
|---|---|---|---|---|---|---|---|---|---|---|
| news | 新闻类(今日头条或腾讯新闻) | 2 | 156 | 66 | 85 | 5 | 0 | 66/156（42.3%） | 66/151（43.7%） | 52 |
| hmeituan | 美团 | 2 | 94 | 52 | 38 | 4 | 0 | 52/94（55.3%） | 52/90（57.8%） | 43 |
| hosapp | 唯品会 | 2 | 123 | 29 | 93 | 1 | 0 | 29/123（23.6%） | 29/122（23.8%） | 14 |
| dianping | 大众点评 | 3 | 98 | 25 | 73 | 0 | 0 | 25/98（25.5%） | 25/98（25.5%） | 23 |
| bili | 哔哩哔哩 | 1 | 62 | 21 | 26 | 15 | 0 | 21/62（33.9%） | 21/47（44.7%） | 17 |
| hmos | 知乎 | 1 | 80 | 19 | 60 | 1 | 0 | 19/80（23.8%） | 19/79（24.1%） | 11 |
| stage | 微博 | 1 | 77 | 18 | 59 | 0 | 0 | 18/77（23.4%） | 18/77（23.4%） | 14 |
| hongmeng | 大麦 | 1 | 42 | 14 | 27 | 1 | 0 | 14/42（33.3%） | 14/41（34.1%） | 13 |
| xhs_hos | 小红书 | 1 | 22 | 10 | 11 | 1 | 0 | 10/22（45.5%） | 10/21（47.6%） | 7 |
| idlefish4ohos | 闲鱼 | 2 | 36 | 5 | 28 | 3 | 0 | 5/36（13.9%） | 5/33（15.2%） | 2 |
| mall | 京东 | 1 | 7 | 4 | 3 | 0 | 0 | 4/7（57.1%） | 4/7（57.1%） | 4 |
| life | 58同城 | 1 | 23 | 3 | 19 | 1 | 0 | 3/23（13.0%） | 3/22（13.6%） | 1 |
| hos | 去哪儿 | 2 | 29 | 0 | 1 | 28 | 0 | 0/29（0.0%） | 0/1（0.0%） | 0 |
| 合计 | 13 个前缀 | 20 | 849 | 266 | 523 | 60 | 0 | 266/849（31.3%） | 266/789（33.7%） | 201 |

中文名来源：

- `bili` → 哔哩哔哩。fail_266_索引.csv 的 app 列。
- `dianping` → 大众点评。fail_266_索引.csv 的 app 列。
- `hmeituan` → 美团。fail_266_索引.csv 的 app 列。
- `hmos` → 知乎。fail_266_索引.csv 的 app 列。
- `hongmeng` → 大麦。fail_266_索引.csv 的 app 列。
- `hos` → 去哪儿。口径说明里的「hos（去哪儿）」；该前缀 fail=0，索引里没有行。
- `hosapp` → 唯品会。fail_266_索引.csv 的 app 列。
- `idlefish4ohos` → 闲鱼。fail_266_索引.csv 的 app 列。
- `life` → 58同城。fail_266_索引.csv 的 app 列。
- `mall` → 京东。fail_266_索引.csv 的 app 列。
- `news` → 新闻类(今日头条或腾讯新闻)。fail_266_索引.csv 的 app 列。
- `stage` → 微博。fail_266_索引.csv 的 app 列。
- `xhs_hos` → 小红书。fail_266_索引.csv 的 app 列。

备注抽查只用来看中文名是否出现在 notes / not_covered 里，不用来改上表，也不用来分页面类型。一句备注可以两个词都不写。

| 前缀 | 抽查 | 组数 |
|---|---|---|
| bili | 命中 0、词 哔哩哔哩、哔哩 | 62 |
| dianping | 命中 0、词 大众点评、点评 | 98 |
| hmeituan | 命中 5、词 美团 | 94 |
| hmos | 命中 3、词 知乎 | 80 |
| hongmeng | 命中 1、词 大麦 | 42 |
| hos | 命中 0、词 去哪儿、去哪 | 29 |
| hosapp | 命中 1、词 唯品会 | 123 |
| idlefish4ohos | 命中 12、词 闲鱼 | 36 |
| life | 命中 5、词 58同城 | 23 |
| mall | 命中 4、词 京东 | 7 |
| news | 头条 13、腾讯新闻 4 | 156 |
| stage | 命中 19、词 微博 | 77 |
| xhs_hos | 命中 6、词 小红书 | 22 |

`news` 这一行的「头条」「腾讯新闻」是备注里出现该词的组数，不是拆开后的 App 组数。

表文件：`/tmp/ana_0123/B_open_close_849.csv`。

## 3. fail 组的 hit 码

只统计 result=fail 的组。一组可以同时命中多条，所以下面的组数相加大于 fail 组数。码从 hits 数组里用 P1–P6 抽出。

| 码 | 含该码的 fail 组 |
|---|---|
| P1 | 264 |
| P2 | 37 |
| P3 | 2 |
| P4 | 0 |
| P5 | 27 |
| P6 | 1 |

只命中 P1 一条（hits 解析后恰好是 [P1]）的 fail 组：201。材料写约 201。差额：0。

fail 组 266 里，含 P1 的 264，不含 P1 的 2。

hits 组合（解析后，去重保序）：

| hits | 组数 |
|---|---|
| P1 | 201 |
| P1 P2 | 35 |
| P1 P5 | 25 |
| P1 P2 P3 | 2 |
| P5 | 2 |
| P1 P6 | 1 |

有 1 条 hits 不是裸编号，原文并进了说明。解析时只取其中的 P 码。

| run | test | 解析 | 原文 |
|---|---|---|---|
| hosapp_uniform_1028_210135 | t18 | P5 | P5：同一首页的“今日特卖”商品列表自动换成另一批；折叠态为 VANS、JEEP、DEBRAND、斯凯奇，展开态变为安德玛、波司登、马克华菲、真维斯 |

解析失败 0 条。

灰区核对（不是另做的分类）：result=fail 且 result_cut10=fail 且 result_cut20=pass 的组有 30。索引 README 写 30，索引列 only_gray_cut10_fail=是 的行有 30。

表文件：`/tmp/ana_0123/B_open_close_hits.csv`。

## 4. 页面类型

推不出。

849 个 json 的顶层键都是同一组：_meta、defect_types、exclusions、hits、missing_in_excluded_zone、missing_in_gray_zone、missing_in_keep_zone、not_covered、notes、result、result_cut10、result_cut20。

`_meta` 的键都是：bucket、folded、model、run、test、unfolded。没有页面名、模板号、页面类型。

这个打包目录下没有布局树。截图文件名在 `_meta` 里是 `tNN_1_folded.png` 这种，也没有页面类型。notes 是自由文本，没有按首页 / 详情 / 搜索 / 列表 / 弹层去分类，避免编出一列 fail 率。

## 5. 同一 App 的多个 run 是否合并

第 2 节按前缀合并了。dianping 有 3 个 run，合并后是上表那一行（大众点评）。分开的数：

前缀对应多个 run 的有 6 个：dianping 3 个 run、hmeituan 2 个 run、hos 2 个 run、hosapp 2 个 run、idlefish4ohos 2 个 run、news 2 个 run。

| run | 前缀 | 中文名 | 组数 | fail | pass | invalid | fail/组数 | 只P1 |
|---|---|---|---|---|---|---|---|---|
| bili_uniform_1029_011533 | bili | 哔哩哔哩 | 62 | 21 | 26 | 15 | 21/62（33.9%） | 17 |
| dianping_uniform_1028_190316 | dianping | 大众点评 | 1 | 1 | 0 | 0 | 1/1（100.0%） | 1 |
| dianping_uniform_1028_190517 | dianping | 大众点评 | 12 | 1 | 11 | 0 | 1/12（8.3%） | 1 |
| dianping_uniform_1029_053112 | dianping | 大众点评 | 85 | 23 | 62 | 0 | 23/85（27.1%） | 21 |
| hmeituan_uniform_1028_191442 | hmeituan | 美团 | 40 | 19 | 19 | 2 | 19/40（47.5%） | 16 |
| hmeituan_uniform_1029_064309 | hmeituan | 美团 | 54 | 33 | 19 | 2 | 33/54（61.1%） | 27 |
| hmos_uniform_1028_230047 | hmos | 知乎 | 80 | 19 | 60 | 1 | 19/80（23.8%） | 11 |
| hongmeng_uniform_1029_044938 | hongmeng | 大麦 | 42 | 14 | 27 | 1 | 14/42（33.3%） | 13 |
| hos_uniform_1028_201016 | hos | 去哪儿 | 18 | 0 | 1 | 17 | 0/18（0.0%） | 0 |
| hos_uniform_1029_073950 | hos | 去哪儿 | 11 | 0 | 0 | 11 | 0/11（0.0%） | 0 |
| hosapp_uniform_1028_210135 | hosapp | 唯品会 | 119 | 28 | 90 | 1 | 28/119（23.5%） | 14 |
| hosapp_uniform_1029_075746 | hosapp | 唯品会 | 4 | 1 | 3 | 0 | 1/4（25.0%） | 0 |
| idlefish4ohos_uniform_1028_202149 | idlefish4ohos | 闲鱼 | 29 | 4 | 22 | 3 | 4/29（13.8%） | 2 |
| idlefish4ohos_uniform_1029_074850 | idlefish4ohos | 闲鱼 | 7 | 1 | 6 | 0 | 1/7（14.3%） | 0 |
| life_uniform_1029_042624 | life | 58同城 | 23 | 3 | 19 | 1 | 3/23（13.0%） | 1 |
| mall_uniform_1028_223355 | mall | 京东 | 7 | 4 | 3 | 0 | 4/7（57.1%） | 4 |
| news_uniform_1029_021354 | news | 新闻类(今日头条或腾讯新闻) | 83 | 40 | 42 | 1 | 40/83（48.2%） | 29 |
| news_uniform_1029_032228 | news | 新闻类(今日头条或腾讯新闻) | 73 | 26 | 43 | 4 | 26/73（35.6%） | 23 |
| stage_uniform_1029_001053 | stage | 微博 | 77 | 18 | 59 | 0 | 18/77（23.4%） | 14 |
| xhs_hos_uniform_1028_224026 | xhs_hos | 小红书 | 22 | 10 | 11 | 1 | 10/22（45.5%） | 7 |

表文件：`/tmp/ana_0123/B_open_close_by_run.csv`。

## 核对

fail 的 (run, test) 与 `fail_266_索引.csv` 的 266 行一一对应。
与 `summary.json` 的总数和分前缀 n/fail/pass/invalid/uncertain 一致。
