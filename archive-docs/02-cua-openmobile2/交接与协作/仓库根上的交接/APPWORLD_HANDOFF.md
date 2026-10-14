# AppWorld 评测交接（转 Linux dev）

更新：2026-09-20 21:26 CST。评测已经搬到 **linux-dev**（`10.151.196.17`，用户 `gui-5d025-2`，目录 `~/zyy/mobilegym-mock/appworld-eval`）。Mac 窗口通过 SSH 监控；GPU `10.210.6.10:19554/19553` 起来后会自动续跑（Qwen 8 / Venus 4，`skip_if_finished`）。

`appworld-eval/` 已 gitignore，**必须整棵拷走**，不能只拷仓库。 Linux 上不要用 `/tmp`。

---

## 现在跑到哪（不要重跑）

只跑 `test_challenge`（417 题）。dev / test_normal 历史分数已经有了，**不要重跑**。

| 实验 | 输出目录 | 已完成 | 说明 |
|---|---|---:|---|
| Qwen3.6-27B | `qwen36_appworld_test_challenge` | **155/417** | 155 题都调了 `complete_task`（交了答案 ≠ 官方对） |
| UI-Venus-2-9B | `venus2_appworld_test_challenge` | **68/417** | 51 题交了答案，17 题没交就结束；对比项，不是主分数 |

官方 TGC/SGC **要等 417 题全部 `misc/finished` 之后**才评。现在只有冒烟：`evaluations/on_only_5238afc_1`（Qwen，TGC 100）。

`skip_if_finished: true`：同一输出目录续跑会跳过已有 `tasks/<id>/misc/finished` 的题。

历史分数（数字还在，本机 `/tmp` 轨迹已没了，不必重跑）：

```text
Qwen3.6-27B  dev         TGC 73.7  SGC 52.6
Qwen3.8-27B  dev         TGC 84.2  SGC 68.4
Qwen3.6-27B  test_normal TGC 75.6  SGC 60.7
```

19553 现在是 **UI-Venus-2-9B**，**不要标成 Qwen3.8**。确认 19553 真正切回 Qwen3.8-27B 之前不要跑 Qwen3.8。

---

## Linux dev 上已经就位（2026-09-20 21:25）

```text
机器   linux-dev = 10.151.196.17  user=gui-5d025-2  （本机只有 4060 8G，不跑 27B）
目录   /home/gui-5d025-2/zyy/mobilegym-mock/appworld-eval
       （~/appworld-eval 是指向上面的软链）
venv   .../appworld-eval/src/.venv  Python 3.11.15（uv）
脚本   run_linux.sh / wait_and_start.sh（每 30s 探端口，通了就拉 Qwen8 / Venus4）
日志   .../appworld-eval/logs/
```

本机 SSH：`ssh linux-dev`（`~/.ssh/config` 里 Host linux-dev）。

看进度：

```bash
ssh linux-dev 'tail -n 20 ~/appworld-eval/logs/wait_and_start.log'
ssh linux-dev 'find ~/appworld-eval/root/experiments/outputs/qwen36_appworld_test_challenge/tasks -name finished | wc -l'
```

GPU 仍在 `10.210.6.10`。linux-dev 上也 ping 不通时，wait 脚本会空转等到端口恢复。

手动启动（端口已通时）：

```bash
ssh linux-dev
cd ~/appworld-eval
nohup ./run_linux.sh qwen36_appworld_test_challenge 8 >> logs/qwen36_test_challenge.log 2>&1 &
nohup ./run_linux.sh venus2_appworld_test_challenge 4 >> logs/venus2_test_challenge.log 2>&1 &
```

---

## 必须带走的目录

Mac 路径：

```text
/Users/zhangyingying/Desktop/mobilegym-mock-tooluse/appworld-eval/
```

| 路径 | 作用 |
|---|---|
| `src/` | AppWorld 0.2.0.dev0 代码（main）+ `experiments/` |
| `src/experiments/configs/qwen36_appworld_test_challenge.jsonnet` | Qwen ReAct，19554，`max_completion_tokens=8192` |
| `src/experiments/configs/venus2_appworld_test_challenge.jsonnet` | Venus ReAct，19553，4096 |
| `src/experiments/code/simplified/react_code_agent.py` | 已打补丁：`reasoning_content` 为 null 时不 `.strip()` 崩 |
| `root/data/` | 公开数据 0.2.0（train/dev/test_normal/test_challenge = 90/57/168/417） |
| `root/experiments/outputs/` | **已完成轨迹，续跑靠这个** |
| `run_qwen36_challenge.sh` / `run_appworld_cli.py` | 启动器 |

**不要拷** `src/.venv/`（Mac arm64，Linux 要重建）。日志可拷可不拷。

拷之前在 Mac 停掉本机 runner，避免半写 `finished`：

```bash
pkill -f 'qwen36_appworld_test_challenge' || true
pkill -f 'venus2_appworld_test_challenge' || true
```

rsync 示例（把 `USER@LINUX_DEV` 和目标路径改掉）：

```bash
rsync -aH --info=progress2 \
  --exclude '.venv/' \
  --exclude 'src/.venv/' \
  /Users/zhangyingying/Desktop/mobilegym-mock-tooluse/appworld-eval/ \
  USER@LINUX_DEV:~/appworld-eval/
```

到 Linux 后确认：

```bash
cat ~/appworld-eval/root/data/version.txt          # 必须 0.2.0
find ~/appworld-eval/root/experiments/outputs/qwen36_appworld_test_challenge/tasks -name finished | wc -l
# 期望 155
find ~/appworld-eval/root/experiments/outputs/venus2_appworld_test_challenge/tasks -name finished | wc -l
# 期望 68
```

---

## 模型端口

```text
Qwen3.6-27B     http://10.210.6.10:19554/v1   主实验
UI-Venus-2-9B   http://10.210.6.10:19553/v1   对比；曾和 215 gui_only 抢卡
```

2026-09-20 21:16 起 Mac 上看 **整机 10.210.6.10 ping 不通**，两个端口都 `connection refused`。Linux 上先测：

```bash
curl -sS --max-time 8 http://10.210.6.10:19554/v1/models
curl -sS --max-time 8 http://10.210.6.10:19553/v1/models
```

若 vLLM 就在这台 Linux 上，可把 jsonnet 里 `base_url` 改成 `http://127.0.0.1:19554/v1`（Venus 改 19553）。`name` 必须和 `/v1/models` 的 id 一致。

OpenAI 兼容客户端：`OPENAI_API_KEY=EMPTY`。默认 connect timeout 约 5s，GPU 卡住时会刷 `APITimeoutError` / `APIConnectionError`，**不是题失败**；runner `retry_after_n_seconds=15`，`max_retries=100`。

---

## Linux 上安装（只做一次）

需要：Python 3.11、uv、git。不要用 `/tmp` 当数据根。

```bash
export AW=~/appworld-eval          # 改成你的实际路径
cd "$AW/src"
uv venv --python 3.11 .venv
uv pip install --python .venv/bin/python -e .
uv pip install --python .venv/bin/python -e experiments
```

启动器里的 Mac 绝对路径要改。Linux 建议直接用下面命令，不必死磕 `run_qwen36_challenge.sh`：

```bash
export AW=~/appworld-eval
export APPWORLD_ROOT="$AW/root"
export OPENAI_API_KEY=EMPTY
export PYTHONUNBUFFERED=1
export PYTHONPATH="$AW/src/src${PYTHONPATH:+:$PYTHONPATH}"

cd "$APPWORLD_ROOT"
"$AW/src/.venv/bin/python" -u -c '
import __editable___appworld_agents_0_1_0_dev0_finder as f
f.install()
from appworld.cli import main
raise SystemExit(main())
' run qwen36_appworld_test_challenge --num-processes 8 --root "$APPWORLD_ROOT"
```

或把 `run_appworld_cli.py` 拷到 `$AW/` 后：

```bash
"$AW/src/.venv/bin/python" -u "$AW/run_appworld_cli.py" \
  run qwen36_appworld_test_challenge --num-processes 8 --root "$APPWORLD_ROOT"
```

必须 `--root` 指到带 `data/` 和 `experiments/outputs/` 的那个 root，否则会当成空评测。

Agent 用 **ReAct code**（`simplified_react_code_agent`），不用 function-calling（19554 vLLM 没确认 tool-call parser）。

---

## 并发（已经踩过坑）

端口侧大约能 16 并发，**本机 AppWorld world + 27B thinking 不要按 16 开**。

| 尝试 | 结果 |
|---|---|
| Qwen 3 | 稳；19554 `running=3 waiting=0` |
| Qwen 8 | 可用；墙钟明显快于 3 |
| Qwen 16 | 本机 worker 会掉；再叠 Venus 12 把 19553/19554 一起打挂 |
| Venus 1 | 稳（当时 19553 还有 215×3 vision） |
| Venus 4 | 可试 |
| Venus 12 | 和 215 一起把 19553 堵死 |

**Linux 起步：Qwen 8 + Venus 4。** 先看 10～20 题和 vLLM `waiting`，再加。不要一上来 16。

Venus 是 GUI/vision 模型在跑文本 ReAct，经常吐 JSON 而不是 ` ```python `，轨迹里会有 `No code available to execute.` 属预期，不当 Qwen 分数。

---

## 续跑 / 出分

```bash
# Qwen 主实验
... run qwen36_appworld_test_challenge --num-processes 8 --root "$APPWORLD_ROOT"

# Venus 对比（确认 19553 仍是 UI-Venus-2-9B）
... run venus2_appworld_test_challenge --num-processes 4 --root "$APPWORLD_ROOT"
```

进度：

```bash
find "$APPWORLD_ROOT/experiments/outputs/qwen36_appworld_test_challenge/tasks" -name finished | wc -l
# / 417
```

417 齐了再评（会写 `evaluations/test_challenge.txt`）：

```bash
cd "$APPWORLD_ROOT"
"$AW/src/.venv/bin/appworld" evaluate qwen36_appworld_test_challenge test_challenge --root "$APPWORLD_ROOT"
"$AW/src/.venv/bin/appworld" evaluate venus2_appworld_test_challenge test_challenge --root "$APPWORLD_ROOT"
```

看 TGC / SGC。没齐不要报官方分。

---

## 版本

```text
代码     AppWorld main  0.2.0.dev0
数据     公开 bundle    0.2.0
release  v0.1.3.post1   不要和 main 混装
划分     90 / 57 / 168 / 417 = 732
论文旧划分 105 / 60 / 168 / 417 = 750
```

`cat root/data/version.txt` 必须是 `0.2.0`。

---

## 不要做的事

- 不要再写 `/tmp`
- 不要重跑 dev / test_normal
- 不要把 Venus 轨迹标成 Qwen3.8
- 不要在 19553 仍是 Venus 时开 Qwen3.8
- 不要用没打补丁的 `react_code_agent.py` 跑 Venus（`None.strip()`）
- 不要等 417 齐之前对外报 TGC/SGC

---

## 官方

- 论文：https://arxiv.org/html/2407.18901
- 仓库：https://github.com/StonyBrookNLP/appworld
- 数据 CHANGELOG：https://github.com/StonyBrookNLP/appworld/blob/main/data/CHANGELOG.md
