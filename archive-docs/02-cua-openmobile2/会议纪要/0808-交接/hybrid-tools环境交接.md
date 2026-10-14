# GUI+Tools 混合调用环境交接

分支：`codex/env-tooluse-integration`，commit `b38e86dd`（已与 `main` 同步）。

分支上有两套可用的 GUI+Tools 混合调用任务集：

- **套件一**：7 个自建 App，183 条任务（第 2 节）。
- **套件二**：`hybrid_tools_v1`，90 条任务，用官方复刻 App（第 2 节末尾）。

## 1. 环境怎么起

```bash
git checkout codex/env-tooluse-integration
npm install && pip install -r bench_env/requirements.txt && playwright install chromium
curl -L -o mobilegym-data.tar.gz https://github.com/Purewhiter/mobilegym/releases/download/data-v1.0/mobilegym-data-v1.tar.gz
tar -xzf mobilegym-data.tar.gz && rm mobilegym-data.tar.gz
npm run build && npm run preview -- --port 4173      # 起模拟器,http://localhost:4173
```

列出某个批次的任务：

```bash
python -m bench_env.hybrid_benchmark --list --suite hybrid_tools_selfbuilt_v4   # 换成任意一个suite名,见第2节
```

跑一个批次（hybrid = GUI+Tools 都暴露；gui_only = 只暴露 GUI，对照组）：

```bash
python -m bench_env.hybrid_benchmark \
  --suite hybrid_tools_selfbuilt_v4 --interaction-mode hybrid \
  --env-url http://127.0.0.1:4173 \
  --model-base-url "$MODEL_BASE_URL" --model-api-key "$MODEL_API_KEY" --model-name "$MODEL_NAME" \
  --parallel 8 --headless --output-dir runs/xxx
```

跑完之后，`runs/xxx/results.jsonl` 里每一行就是一条任务的判分结果（`success: true/false`），`summary.json` 是整批的汇总 SR。

**架构简述**：模拟器是跑在浏览器里的网页 App，所有 App 数据存在页面里的 `window.__SIM__` 上。Python 用 Playwright 控制这个网页，封装成 `MobileGymEnv`（`bench_env/env/mobile_gym.py`）：`reset()`/`step(action)`/`get_observation()`。Tool 不是另一个系统，是和 GUI 共享同一份 `__SIM__` 数据的一批函数，代理把它们当成和点击/输入平级的动作调用。想接自己的 RL 框架，可以直接用这三个方法自己写 loop，不一定要用上面的 `hybrid_benchmark` runner；唯一必须复用的是第 3 节的判分逻辑。

## 2. 任务在哪



### 2.1 套件一：7 个自建 App × Tool


| App            | Tool 数 | Tool 名称                                                                                                                                                                                                  | Tool 定义文件                                 | Tool 实现文件                           |
| -------------- | ------ | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ----------------------------------------- | ----------------------------------- |
| Taobao（淘宝）     | 14     | search_items, search_shops, get_item_summary, compare_items, get_cart, list_orders, get_order_summary, list_coupons, open_search_results, open_item, open_shop, open_cart, add_to_cart, prepare_checkout | `app_tools/apps/taobao/definitions.ts`    | `app_tools/apps/taobao/index.ts`    |
| Jingdong（京东）   | 12     | search_items, get_item_summary, compare_items, get_cart, list_orders, get_order_summary, list_coupons, search_life_shops, open_item, open_cart, add_to_cart, prepare_checkout                            | `app_tools/apps/jingdong/definitions.ts`  | `app_tools/apps/jingdong/index.ts`  |
| Ctrip（携程）      | 8      | search_hotels, get_hotel_summary, search_trains, search_flights, search_attractions, list_orders, open_hotel, open_orders                                                                                | `app_tools/apps/ctrip/definitions.ts`     | `app_tools/apps/ctrip/index.ts`     |
| Dianping（大众点评） | 10     | search_shops, get_shop_summary, list_shop_deals, list_recommended_dishes, search_reviews, open_shop, open_review, open_voucher, add_favorite_shop, prepare_voucher_checkout                              | `app_tools/apps/dianping/definitions.ts`  | `app_tools/apps/dianping/index.ts`  |
| Broadcast（播客）  | 8      | search_shows, search_episodes, get_show_summary, get_episode_summary, list_up_next, open_show, open_episode, add_to_queue                                                                                | `app_tools/apps/broadcast/definitions.ts` | `app_tools/apps/broadcast/index.ts` |
| Kapi（记账）       | 8      | search_bills, get_category_summary, get_budget_status, list_accounts, open_bill, open_category, open_stats, prepare_bill_draft                                                                           | `app_tools/apps/kapi/definitions.ts`      | `app_tools/apps/kapi/index.ts`      |
| Luckin（瑞幸）     | 7      | search_products, list_stores, list_coupons, get_cart, open_product, open_cart, add_to_cart                                                                                                               | `app_tools/apps/luckin/definitions.ts`    | `app_tools/apps/luckin/index.ts`    |


任务本身分 4 个批次，每个 App 一个 `specs_<app>.py` 文件，放在各批次自己的 `defs/` 目录下：


| 批次（`--suite` 传的名字）          | 路径                                               | 任务数（按 App）                                                                                  | 示例任务                                                              |
| --------------------------- | ------------------------------------------------ | ------------------------------------------------------------------------------------------- | ----------------------------------------------------------------- |
| `hybrid_tools_selfbuilt_v1` | `bench_env/task/hybrid_tools_selfbuilt_v1/defs/` | ctrip 12 / dianping 12 / jingdong 12 / taobao 12 / broadcast 10 / kapi 10 / luckin 10（共 78） | "比较播客「42章经」「晚点聊 LateTalk」「硅谷101」三个节目的评分，找出评分最高的一个，在笔记中记录节目名称与评分。" |
| `hybrid_tools_selfbuilt_v2` | `bench_env/task/hybrid_tools_selfbuilt_v2/defs/` | taobao 6 / ctrip 3 / kapi 3 / jingdong 2 / broadcast 2 / dianping 2 / daysmatter 1（共 16）    | Ctrip 查到某个航班起飞时间后，切换到 Daysmatter 建一个倒计时事件，写入同一个日期（跨 App）。         |
| `hybrid_tools_selfbuilt_v3` | `bench_env/task/hybrid_tools_selfbuilt_v3/defs/` | taobao 3 / broadcast 2 / daysmatter 2 / jingdong 1 / ctrip 1 / dianping 1 / kapi 1（共 10）    | 播客「已保存」单集列表核实，判分直接读 `broadcast.savedEpisodeIds` 而不经过笔记转述。         |
| `hybrid_tools_selfbuilt_v4` | `bench_env/task/hybrid_tools_selfbuilt_v4/defs/` | broadcast 12 / ctrip 12 / jingdong 12 / taobao 12 / dianping 11 / kapi 10 / luckin 10（共 79） | 专门探测工具设计边界的一批任务（这块是我们自己做工具设计分析用的，不影响怎么跑）。                         |




### 2.2 套件二：`hybrid_tools_v1`（90 条，`--suite hybrid_tools_v1`）

路径：`bench_env/task/hybrid_tools_v1/`（注意不带 `_selfbuilt_`，是另一套，跟上面 7 个自建 App 无关，用官方复刻 App）。


| App 分组                                  | 任务数 | 举例                                      |
| --------------------------------------- | --- | --------------------------------------- |
| Calendar（日历）                            | 12  | 在日历里查一个会议的地点/会议码，另建一个关联事件               |
| WeChat（微信）                              | 12  | 在微信消息里找一个信息片段，转发/引用给另一个联系人；改联系人权限/置顶/星标 |
| Taobao Instant（淘宝闪购，独立 App，非上面的 Taobao） | 12  | 搜商品加购物车、订单备注、给骑手/店铺留言                   |
| Days Matter（倒数日）                        | 12  | 建/改倒数日事件                                |
| Clock（时钟）                               | 12  | 建闹钟、加世界时钟城市                             |
| Notes（备忘录）                              | 12  | 建笔记/待办                                  |
| 跨 App                                   | 18  | 上述几个 App 之间的信息传递任务                      |


任务定义：`specs.py`；判分逻辑：`verifier.py`；任务清单和完整 instruction 原文：`bench_env/task/hybrid_tools_v1/TASK_CATALOG.md`（直接看这个文件就是全部 90 条原文）。

## 3. 怎么判断一条任务有没有完成

判分三个输入：**任务开始前的 App 状态、任务结束后的 App 状态、模型给出的最终文字回答**，跟走 GUI 还是走 Tool、用什么 agent 完全无关：

```python
from bench_env.task.judge import JudgeInput, JudgeResult
result: JudgeResult = task.verify(JudgeInput(init_obs, last_obs, answer))
# result.success -> bool，这条任务通过/不通过
# result.issues   -> list[dict]，每一项是具体哪个检查点没通过，调试用
```

每条任务内部会产出一组"检查点"（`check_goals`），每个检查点是一个 `{field, expected, actual, passed}` 的字典，`result.success` = 这些检查点是否**全部** `passed=True`。例如一条"往购物车加 2 杯指定规格饮品"的任务，`result.issues` 里失败时大概长这样：

```json
[{"field": "cart.lemon-tea.qty", "expected": 2, "actual": 1, "passed": false}]
```

183 条任务里，检查点具体怎么构造分两种：

1. **状态直查类**（购物车/收藏/账单/关注等写入型任务）：检查点直接对比 App 最终状态里的具体字段和期望值，不看模型说了什么。这部分自定义逻辑写在各批次 `defs/specs_<app>.py` 里的 `EXTRA_CHECKS` 字典中，和任务定义放在同一个文件、同一个 App 分组。
2. **纯查询类**（找信息、算数字、比较后给结论）：要求模型把结果写进笔记 App，检查点是"笔记内容里必须包含这些关键词、不能包含那些关键词"（`notes_note`），通用实现在 `bench_env/task/hybrid_tools_selfbuilt_v1/base.py`，v2/v3/v4 都复用这一份。



## 4. 外部 GUI agent 怎么接工具调用

`app_tools/TOOLS_DESIGN.md` 第 7 节「Agent-Side Integration Guide」：怎么发现当前 App 有哪些工具、怎么把 schema 转成模型可用的函数定义、怎么执行、怎么把结果拼回下一轮 observation。我们自己的 agent runtime（可插拔多种模型协议：Qwen XML / GPT 原生 computer-use / Kimi）在 `bench_env/hybrid_agent/README.md`，可以参考也可以完全不用，只要满足第 1 节末尾说的接口约定即可。