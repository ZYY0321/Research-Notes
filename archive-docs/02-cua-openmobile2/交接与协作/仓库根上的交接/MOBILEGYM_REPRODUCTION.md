# MobileGym-Bench Gemini 3.1 Pro 复现记录

记录时间：2026-07-11  
本地代码：`/Users/chengkanzhi/Desktop/mobilegym-mock/trial_apps/mobilegym`  
官方仓库：`https://github.com/Purewhiter/mobilegym`  
官方对比 commit：`093a3292d13fc4186e279af4ef1b005ac8e4d2b7` (`main`)

## 目标

复现 MobileGym-Bench 官方 256 个 test tasks 上 Gemini 3.1 Pro 的结果。

官方 README 中 Gemini 3.1 Pro 汇报结果：

| Model | Overall SR | PR | L1 | L2 | L3 | L4 | FC | USE |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| Gemini 3.1 Pro | 58.8 ± 1.4 | 72.1 | 97.5 | 83.6 | 63.3 | 21.9 | 34.0 | 5.5 |

本地官方 test split 是 `bench_env/splits/test.txt`，共 256 个任务。这个 split 不包含我们后来新增的淘宝等 app 任务；新增 app 主要通过 launcher 状态影响评测 clean/USE。

## 评测配置

官方文档中 proprietary/general VLM 推荐使用：

- agent: `generic_v2`
- split: `test`
- judge mode: `state`
- eval mode: `grounded`
- query/answer 类任务：grounded mode 会注入 AnswerSheet，并把任务指令扩展为打开答题卡填写并提交
- action 输出：`generic_v2` 要求模型输出 JSON action，最后用 `COMPLETE` 结束任务

本次最终使用配置：

```bash
cd /Users/chengkanzhi/Desktop/mobilegym-mock/trial_apps/mobilegym
conda activate mobilegym-bench

# 本地 API 和 MobileGym preview 都不要走代理。
unset HTTP_PROXY HTTPS_PROXY ALL_PROXY http_proxy https_proxy all_proxy
export NO_PROXY=127.0.0.1,localhost
export no_proxy=127.0.0.1,localhost

# 另一个终端启动模拟器前端。
npm run preview -- --host 127.0.0.1 --port 4181

# 评测命令的核心参数。
python -m bench_env.run \
  --split test \
  --agent generic_v2 \
  --env-url http://127.0.0.1:4181 \
  --model-base-url https://tokenhub.sensetime.com/v1 \
  --model-name gemini-3.1-pro-preview \
  --parallel 4 \
  --isolation pages \
  --headless \
  --judge-mode state \
  --eval-mode grounded \
  --temperature 0 \
  --top-p 1 \
  --max-tokens 8192 \
  --no-stream \
  --runs-dir runs/gemini31pro-test256-par4-rerun8192-nolauncher
```

API smoke test 在 `tools/test_api.py`。不要把 API key 写入文档或日志。

## 关键问题和修正

### 1. Launcher clean 检查与本地新增 app 不适配

本地环境新增了商业 app，launcher 主屏从官方默认页数变成更多页。评测时即使任务不涉及 launcher，环境初始化/打开 app 后 launcher layout 也可能 reconcile，导致：

- `os.launcher.screens`
- `os.launcher.screensCount`

被判为 unexpected side effects，USE 虚高。

本地临时修正是在 `BaseTask.always_ignore` 里忽略这两个字段。这个是本地扩展 app 引入的兼容修正，不是模型问题。

### 2. API 空响应导致 ABORT

早期一次 run 使用 `max_tokens=4096`，出现较多 `empty_response`。代码把空响应解析为 agent 没有有效动作，最后记为 `ABORT`，导致 stop reason 中 ABORT 数量异常。

现象：

- 上一轮 256 任务：`ABORT=32`
- 其中很多是 API 返回空 content，而不是模型主动选择 abort

处理：

- `max_tokens` 改为 `8192`
- `bench_env/llm/openai_chat.py` 对 non-streaming 空 content 增加 retry
- 继续使用 `--no-stream`

可能原因是 TokenHub/OpenAI-compatible Gemini endpoint 在 token budget 或内部 finish reason 下会返回空 content；这类空响应不能直接当作 agent 失败。

### 3. USE 偏高：本地 codebase 没同步官方 clean/ignore 修正

第一次完整 rerun 后，raw USE 仍然偏高：

```text
raw USE = 37/256 = 14.45%
```

逐条查看 `clean=False` 轨迹后发现，大量任务目标已经完成，但因为运行时镜像状态变化被判 dirty：

- Spotify 播放任务成功，但 `os.services.media_session.*` 被判 side effect
- Clock 闹钟任务成功，但 `os.services.alarm_manager.*` 被判 side effect
- Redbook 任务必须搜索用户，但 `redbook.searchHistory` 没列入 expected changes
- 相册分享任务中 `os.tasks...intent` 被判 side effect

对比官方 GitHub 后确认，官方当前代码已经修正这些问题：

`bench_env/task/base.py` 官方 `always_ignore` 包含：

```python
"os.tasks",
"os.services.taskManager.tasks",
"os.isRecentsVisible",
"os.services.taskManager.isRecentsVisible",
"os.services.alarm_manager",
"os.services.media_session",
```

两个 Redbook crossapp 任务官方也已经补了：

```python
"redbook.searchHistory"
```

本地已按官方代码补齐这些点，同时保留本地 launcher screens ignore。

### 4. Proxy / NO_PROXY 问题

本地 `tools/test_api.py` 在 `mobilegym-bench` 环境下直接运行可以成功，但如果 shell 里带了代理环境变量，可能导致 API 或 localhost preview 请求异常。

建议评测前统一执行：

```bash
unset HTTP_PROXY HTTPS_PROXY ALL_PROXY http_proxy https_proxy all_proxy
export NO_PROXY=127.0.0.1,localhost
export no_proxy=127.0.0.1,localhost
```

### 5. ABORT / COMPLETE 语义

MobileGym agent 的 episode 结束由动作决定：

- `COMPLETE`: agent 声称任务完成
- `ABORT`: agent 声称任务无法完成
- `MAX_STEPS`: 超过 step budget

`COMPLETE` 不代表任务一定成功。最终 verdict 是 state judge 决定的：

```text
judge.passed = judge.success and judge.clean
is_success = judge.passed
```

所以会出现：

- 目标完成但 clean=False：`judge.success=True`, `judge.passed=False`
- agent 提前 COMPLETE 但 state 不满足：`false_complete=True`

### 6. 三页 Launcher 中一次左滑跳过第二页

扩充本地 app 后，Launcher 有三页桌面。GUI+Tools 测试中的 `cross_15` 暴露出一个原来两页桌面不容易观察到的输入模拟问题：agent 从当前页执行一次标准左滑

```text
[800, 500] -> [200, 500]
```

坐标是当前屏幕 `0..1000` 归一化坐标，本应只前进一页，但实际从第一页直接跳到第三页。浏览器实测数据为：

```text
page width = 360
scroll width = 1080
before swipe: scrollLeft = 0
after swipe:  scrollLeft = 720
```

根因在前端通用输入模拟，不在 agent 坐标解析：

- `os/simInput.ts` 将合成 swipe 拆成多次 `scrollBy`，并追加人工惯性滚动；
- Launcher 的横向分页容器同时使用 `scroll-snap-type: x mandatory`；
- 分段滚动过程中浏览器反复执行强制吸附，导致一次手势跨过多个分页。

本地修正仅作用于满足以下全部条件的手势：

- 手势方向是水平；
- 命中的元素可横向滚动；
- 元素启用了 `x` 轴 scroll snap。

执行这类手势时暂时关闭目标元素的 scroll snap，完成手指位移和惯性后在 `finally` 中恢复原值，让浏览器只对最终位置吸附一次。纵向滚动、无 scroll snap 的横向列表、点击和 drag 不走该逻辑。

修正后真实浏览器回归：

```text
initial:     scrollLeft = 0
left swipe:  scrollLeft = 360
right swipe: scrollLeft = 0
```

同时验证普通淘宝纵向页面仍可从 `scrollTop=0` 滚动到 `scrollTop=658`。对应单元测试为 `tests/simInputScrollSnap.test.ts`。

## 最终 run

结果目录：

```text
/Users/chengkanzhi/Desktop/mobilegym-mock/trial_apps/mobilegym/runs/gemini31pro-test256-par4-rerun8192-nolauncher/20260711_105711
```

运行完成情况：

```text
256/256 episodes
errors = 0
stop_reason = COMPLETE 233, ABORT 12, MAX_STEPS 11
```

原始记录结果，即修正官方 clean 规则前：

| Metric | Value |
|---|---:|
| SR | 134/256 = 52.34 |
| PR | 70.24 |
| L1 | 19/20 = 95.0 |
| L2 | 56/73 = 76.7 |
| L3 | 42/83 = 50.6 |
| L4 | 17/80 = 21.2 |
| FC | 99/256 = 38.67 |
| USE | 37/256 = 14.45 |

按已同步的官方 clean/ignore 规则离线重算后的口径：

| Metric | Value |
|---|---:|
| Overall SR | 146/256 = 57.03 |
| PR | 70.24 |
| L1 | 20/20 = 100.0 |
| L2 | 61/73 = 83.6 |
| L3 | 45/83 = 54.2 |
| L4 | 20/80 = 25.0 |
| FC | 87/256 = 33.98 |
| USE | 22/256 = 8.59 |

和官方 Gemini 3.1 Pro 对比：

| Metric | Local corrected | Official |
|---|---:|---:|
| Overall SR | 57.0 | 58.8 ± 1.4 |
| PR | 70.2 | 72.1 |
| L1 | 100.0 | 97.5 |
| L2 | 83.6 | 83.6 |
| L3 | 54.2 | 63.3 |
| L4 | 25.0 | 21.9 |
| FC | 34.0 | 34.0 |
| USE | 8.6 | 5.5 |

说明：

- corrected 结果是基于同一份 `results.jsonl` 离线按新 clean 规则重算，不是重新跑出来的新 `summary`。
- 修正后 SR 已接近官方，L2/FC 基本对齐，L1/L4 略高。
- 主要剩余差距在 L3 和 USE。

## 修正后追回的任务

以下任务原始 run 中目标已完成，但因为旧 clean 规则被判失败；同步官方规则后会计为成功：

- `clock.AddAlarmWithSettings`
- `clock.ToggleAlarm`
- `crossapp_content.RedbookUserTopCollectToWechat`
- `crossapp_content.RedbookUserBestWorstToNotes`
- `crossapp_life.WeatherFirstSunnyDayCalendarAlarm`
- `crossapp_work.WeatherConditionalCancelMeeting`
- `spotify.AddToQueueAndPlay`
- `spotify.BuildPlaylistFromTwoArtists`
- `spotify.PlaySongFromSearch`
- `spotify.SearchPlayAndReport`
- `spotify.CollectLikedRecentAndPlay`
- `spotify.SearchBuildPlaylistAndPlay`

另外还有 3 个失败任务的 dirty warning 会被官方规则清掉，但任务目标本身仍失败：

- `clock.EnableAllAlarms`
- `clock.SetupMorningAlarms`
- `crossapp_content.FavoriteWaterSceneryPhotos`

## 剩余差异

修正后仍有 USE 高于官方，主要来自：

- 模型真实多操作：例如 Bilibili 多关注、X 多关了一批推送设置
- browser fallback：部分跨 app life/map/weather 任务中模型跑去浏览器/百度/必应，任务未完成并留下浏览器状态
- Alipay `lastReadAt`：官方当前代码也没有全局忽略，是否应忽略还需要进一步确认

这些不建议一概 ignore。下一步如果继续追官方结果，应优先逐条 audit L3 失败任务和剩余 `clean=False` 任务，而不是继续扩大全局 ignore。

## 当前本地相关改动

与本次复现直接相关的本地代码改动：

- `bench_env/llm/openai_chat.py`: 空 content response retry
- `bench_env/task/base.py`: launcher screens 本地 ignore；同步官方 runtime ignore
- `bench_env/task/crossapp_content/defs/RedbookUserTopCollectToWechat.py`: 补 `redbook.searchHistory`
- `bench_env/task/crossapp_content/defs/RedbookUserBestWorstToNotes.py`: 补 `redbook.searchHistory`
- `tools/test_api.py`: API smoke test 和启动注意事项

其他本地扩展 app 相关改动不属于官方 benchmark 复现核心路径。
