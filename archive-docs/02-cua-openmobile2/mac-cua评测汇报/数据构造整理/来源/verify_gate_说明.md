类型：核心 ｜ 归属：11-24 E31 验证门 ｜ 状态：维护中

# 新题包一条命令：假文件是不是 0，手头的真导出是不是还是 1

给一道已经写好的题包，这个脚本在本机把三道门跑完，并给每道可评分题标现在到了 L 几。不调模型，不开应用，不连生产机和集群。

先看两道已经有真文件的题。

`ps-2-14-ps-channel-manipulation` 的成品在 `/Users/zhangyingying/CUA/评测集建设/实验/E31_新应用Mail_PS_飞书_Figma刷数据/raw/假阴性回归_1124/prod/` 里，48×32，整张都是绿色通道填满之后的 (120, 255, 200)。题面要的就是这个颜色。PARAMS 里没有 `allowed`。副本库 `_shared_tightened_1124_b` 把它打成 0，原因是整张只有一种颜色（`flat`、`sample-dots`）。同一道题 selftest 里原来当作正例的那张图，这次也是 0。空文件、颜色不对的假文件仍是 0。

`ps-2-11-mask-disable-apply` 的真导出是左红右蓝。同一套库打出来是 1。这道题的假文件也是 0。

题面这边，剪贴蒙版 `ps-2-11-clipping-mask` 写了种子图和要另存的 PSD。PARAMS 只查导出的 PNG。字体 `ps-2-17-ps-text-font` 写了字号 18，PARAMS 里没有 18 这个数。另存 TIFF 的 `ps-2-25-ps-save-as-format` 只查文件是不是以 `II*` 开头，种子 PSD 不在判据里，所以这道标 L1，其余 45 道可评分题标 L2。

## 怎么跑

只给题包目录。报告打在终端上。

```bash
python3 "/Users/zhangyingying/CUA/评测集建设/实验/E31_新应用Mail_PS_飞书_Figma刷数据/scripts/verify_gate.py" "/Users/zhangyingying/CUA/评测集建设/maccua-tasks/zyy-e31-gen-v4p"
```

要落成文件，后面加 `--out` 和一个路径。11-24 这次的全文在 `/Users/zhangyingying/CUA/评测集建设/实验/E31_新应用Mail_PS_飞书_Figma刷数据/analysis/verify_gate_实跑_1124.md`。

手工题（`kind` 是 `manual`）只标 L0，三道门不跑。v4p 是 63 道。

## 三道门判什么

评分函数来自 `/Users/zhangyingying/CUA/评测集建设/maccua-tasks/_shared_tightened_1124_b/`。PARAMS 里如果写了 `allowed`，库会按它放行题面允许的纯色；没写这个键，整张一种颜色就是 0。v4p 的题现在都没写 `allowed`，脚本不会替它们补上。

假产物。每道题自己的 `selftest.py` 里，期望分数写的是 0 的那些用例（空文件、不署名、颜色或尺寸不对，各题名字不完全一样）。脚本用副本库里的 `fixturelib` 把这些用例再打一遍。全部是 0 才算通过。selftest 里期望是 1 的那条叫对照，单独记一笔，不拿来判这道门：有的对照本身就是整张纯色，收紧之后变成 0，这是旧正例被挡住，不是假文件拿了 1 分。

真产物。在下面四个目录里按文件名找这道题的成品，配套的种子也要能对上才打分。对上了而且分数是 1，算通过。对上了但是 0，算失败。目录里没有这份文件，算未覆盖，不把它算成评分把真文件打错了。

- `/Users/zhangyingying/CUA/评测集建设/实验/E31_新应用Mail_PS_飞书_Figma刷数据/raw/figma导出图_1124`
- `/Users/zhangyingying/CUA/评测集建设/实验/E31_新应用Mail_PS_飞书_Figma刷数据/raw/假阴性回归_1124/prod`
- `/Users/zhangyingying/CUA/评测集建设/实验/E31_新应用Mail_PS_飞书_Figma刷数据/raw/假阴性回归_1124/seed`
- `/Users/zhangyingying/CUA/评测集建设/实验/E31_新应用Mail_PS_飞书_Figma刷数据/raw/psd真文件_1124`

文件名以「结束截图」开头的不打。Figma 那些导出的题号不在 v4p 里，所以这次 v4p 用不上它们；换一份含 Figma 题的包，同一条命令会去对。

题面。不调模型。从题面正文里抽出路径、格式词（PNG、JPEG、TIFF、PSD、PDF、SVG，以及带后缀的 txt）、宽×高、括号里或「RGB」后面的三个颜色数、`#RRGGBB`、字号、点数、ppi、质量、单独写的宽或高。PARAMS 里没有同名文件、对应格式，或没有这个数，就算失败。同一个数只记一次。年份、1/30 这种分数、菜单名、字体名、「纯黑」这种没有写出数字的话，不抽。数字只要在 PARAMS 的某个整数里出现就算有，不核对它是不是落在「字号」那一格；字号 18 被记下来，是因为整份 PARAMS 里都没有 18。

## L 级

按 Fable 11-24 那份验证流程里的定义，脚本最高写到 L2。

- L0：手工题，评分固定返回 0。
- L1：PARAMS 里只有文件能不能解析这一层（魔数、后缀或署名），没有尺寸、抽样、正文或图层条件。v4p 里只有另存 TIFF 那一道。
- L2：PARAMS 里有书面条件。现在这 45 道在这里。
- L3 要同时核到功能语义，和「是这次新做的」（基线、唯一记号或时间戳至少一样）。L4 还要另一批人用真文件和假文件量过误判。这两级脚本不标。题里就算写了基线路径，这次也停在 L2，因为没有拿旧文件和新文件各打一遍，也没有人工对照。

## 11-24 对 v4p 跑出来的数

可评分 46 道。逐题在实跑那份里。

| 门 | 通过 | 失败 | 未覆盖 |
|---|---:|---:|---:|
| 假产物 | 46 | 0 | 0 |
| 真产物 | 1 | 1 | 44 |
| 题面 | 9 | 37 | 0 |

假产物 46 道都是 0。另外 28 道的对照夹具从期望的 1 变成了 0，不在这 46 个通过里面重复计失败。真产物只对上两道：蒙版停用是 1，通道是 0。其余 44 道本机没有可以打的成品。题面 37 道对不上，前 10 道的原因在实跑里，多半是种子路径、要另存的 PSD，或说明 txt 没有进 PARAMS。

评分库 SHA-256 前 12 位：`e31_grade.py` 是 `d59fa9c6649a`，`e31_grade_ext.py` 是 `36a0cda51bd7`，`fixturelib.py` 是 `2061119ad50c`。拦住的 osascript 次数是 0。

## 这次没跑

- 规格门：人先定产物和判据，脚本不代写。
- `tasks validate`。
- 按旧库再对一遍 selftest 原来的五项期望。假产物门只看期望 0 的用例在副本库下是不是 0。
- 归属门。`write_draft_baseline` 和 `write_flag_seal` 要在生产机上写基线，这次没跑。
- 题面的模型对照。11-24 那份是另一个模型读题面和 PARAMS 写的，这份脚本不调用它。
- 真机冒烟、停机之后成品还在不在、人工金标准。

脚本不改题包，不改 `/Users/zhangyingying/CUA/评测集建设/maccua-tasks/_shared_tightened_1124`，也不改 `_shared_tightened_1124_b`。
