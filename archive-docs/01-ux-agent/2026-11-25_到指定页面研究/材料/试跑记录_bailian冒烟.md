类型：材料 ｜ 归属：2026-11-24_1215高低级指令导航交付 ｜ 状态：维护中

# 百炼渠道直接跑（冒烟起）

## 关键澄清

用户给的 `alibailiana` key **不是** 官方 DashScope API key（直连 `dashscope.aliyuncs.com` → `invalid_api_key`）。  
它是 **TokenHub 百炼渠道** key：`GET {TOKENHUB}/v1/models` 返回 qwen3.5/3.6/3.7/3.8 等。  
视觉冒烟：`qwen3.8-max-0902/bailian_L/bailian` 通过。

## 生产机旁路（不改默认 `run_demo.sh`）

- `~/uxagent/run_demo_bailian.sh`
- `~/uxagent/.secrets/bailian_alibailiana.env`（600）
- `~/uxagent/HarmonyArena-fdu_agent/opencode.bailian.json` → agent 用 `tokenhub/qwen3.8-max-bailian`
- 任务：`benchmarks/tasks-smoke-bilibili-hl.json`（B 站 H+L 各一）
- 检测：`HARMONY_FINAL_UX_DETECT=1`，`FINAL_UX_MODEL=qwen3.8-max-0902/bailian_L/bailian`

## 本轮

| 时间 | 动作 | 结果 |
|---|---|---|
| 22:54 | 启动 `smoke-bilibili-bailian-1124` | B站高级约 2 步报到达；卡在 final UX |
| 22:58 | 根因 | `final-ux-detect` 写死 `reasoning_effort: medium` → Qwen content 空、JSON 解析失败重试；fetch 无超时 |
| 22:59 | 补丁 + 重跑 `1124b` | `reasoning_effort: none` + 120s abort + 空 content 兜底；本地与生产机 `.opencode/lib/final-ux-detect.ts` 已改 |

| 23:02 | `1124b` 结束 | **2/2 pass**（H 72.6s / L 84.5s）；已启动 `demo5-bailian-1124`（10 条）后台跑 |
| 23:32 | demo5 收结果 | **9/10 pass**；失败：`COM-xiaohongshu-bifold-g01-H`（`session.prompt timed out after 600000ms`）；同任务 L 通过。已单独重跑 H |
| | 检测 | 通过的任务均有 `final_ux_detect.json`（single+dual） |
| 11-25 10:00 | 用户催进度 | Cursor 会话过夜停了；当时 SSH 拒连 |
| 11-25 14:56 | 恢复 | 本机 `hdc` 可见 `22M0223928009654`；生产机 SSH 恢复；小红书-H **重跑已于 23:34 通过**（实质 10/10）；写基线报告，明确还要扩测 |
| 11-25 15:02 | 本机扩测 | 目标改为模糊指令到页；同步 settle；跑 18 条 high `nav-high-local-1125`（FINAL_UX=0）；失败自动重跑 |
| 11-25 15:14 | 换机位 | `prod.sh`→`10.202.6.167`；停本机空跑；可见冒烟开 B 站；`nav-high-167-1125b` 18 条高级在跑 |
| 11-25 17:44 | 收结果 | `nav-high-167-1125b` **13/18**（短路径商业 13/15≈87%；3 条 deep 全挂：超时/登录墙/截图管道） |
| 11-25 17:47 | 失败 API 归因 | 5 条失败→12 标签；存档 `失败归因_1125/`；改 screenCap、PNG 校验、高德去太平洋；钉钉待登录/换卡 |
| 11-25 18:05 | 跳过需登录 | 钉钉/企微/微信等先不跑；高德新卡重跑后接 `nav-high-nologin-1125d` 12 条首页/频道类 |
| 11-25 18:31 | 1125d 收 + 监控 | **11/12**；失败酷狗粤语频道超时；开监控；API 总归因+笔记对照；接 `1125e` 11 条 |
| 11-25 18:45 | 新文献+扩量 | 新搜 DestBench/DAC-Bench/GUI-Robust 等；归因标明 Opus5.5/Fable；排队 **149** 条免登录 H+L（`1125f`） |
| 11-25 19:07 | 1125e 收 | **11/11** 全过；已接扩包 `1125f` 149 条（监控中） |
