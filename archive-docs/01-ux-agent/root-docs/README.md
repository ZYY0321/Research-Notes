# UX-Agent

HarmonyOS 多设备 UX **截断**检测。人把 App 点到和 GT 同一类页面，程序截图、读布局树、必要时滑动，判断有没有滑不出来的截断。

**2026-09-21：没有 XML 的 case 不跑端到端，只测有 xml 的；没有的交给模型判断。** 见 [docs/有XML才端到端.md](docs/有XML才端到端.md)。

大图大字、拉伸、横屏、避让还没做。当前只跑文字 / 组件 / 图标截断。

---

## 先看哪份

| 你是 | 打开 |
|---|---|
| **有没有 XML、能不能端到端** | [docs/有XML才端到端.md](docs/有XML才端到端.md) |
| **挂了怎么写问题和证据** | [docs/失败要写清问题和证据.md](docs/失败要写清问题和证据.md) |
| 人（交接、合作同学） | [docs/给人看.md](docs/给人看.md) |
| Cursor / 其它 Agent | [docs/给AI.md](docs/给AI.md) 或根目录 `AGENTS.md` |
| 测哪条、谁占设备 | [docs/合作与测试队列.md](docs/合作与测试队列.md) |
| **茶思屋 ToDesk 账号和点哪** | [docs/茶思屋ToDesk连接.md](docs/茶思屋ToDesk连接.md) |
| GitHub 账号和上传 | [docs/GITHUB账号.md](docs/GITHUB账号.md) |
| 已跑过的真机记录 | [docs/20260919-测试集存档/case-run-log.md](docs/20260919-测试集存档/case-run-log.md) |

仓库必须 **Private**。测试集是真实 App 截图；密钥只放本机 `.env`。

---

## 本机跑一次检测

1. Node.js 20+，`hdc` 在 PATH 里。
2. 设备 USB 或远程连上：`hdc list targets`。
3. 复制环境变量：

```bash
cp HarmonyArena-fdu_agent/.env.example HarmonyArena-fdu_agent/.env
# 把校园网 Key 和备用接口 Key 私下填进去，不要提交
```

4. 人对着 `测试集/整理/...jpg` 把 App 点到同一类页。
5. 检测：

```bash
cd HarmonyArena-fdu_agent
npm install
cd .opencode && npm install && cd ..
set -a && source .env && set +a
export HDC_TARGET=<hdc list 出来的 id>   # 多设备时
npm run ux-detect -- --mode=slide
```

有校园网时验收走 `http://10.176.44.15:8000/detect`（`.env` 里 `UX_DETECT_HTTP_*`）。现在这条命令默认还是备用对话接口，慢的那段不计入 10 秒。

---

## 仓库里有什么、没有什么

会上传：

- `HarmonyArena-fdu_agent` 源码、测试、脚本（不含 `node_modules`、`.env`、现场输出）
- `测试集/整理`（带 Labelme 的评测集）和 `测试集/构造缺陷位置.txt`
- `docs/` 里跟人协作有关的说明和测试集存档

不会上传（本机太大或是密钥 / 旧稿）：

- `测试集/整理 2`、`整理_older`、`sample_in_harmonyos`（约 12G）
- `apps/`、`delivery/`、演示和会议过程稿
- `ux-detect-output/`、`results/`、`log/`

代码工坊工程用本机已解压的 `测试集/sample_in_harmonyos`，或上游 [sample_in_harmonyos](https://gitcode.com/HarmonyOS_Samples/sample_in_harmonyos)，不要把 6G zip 推进 GitHub。
