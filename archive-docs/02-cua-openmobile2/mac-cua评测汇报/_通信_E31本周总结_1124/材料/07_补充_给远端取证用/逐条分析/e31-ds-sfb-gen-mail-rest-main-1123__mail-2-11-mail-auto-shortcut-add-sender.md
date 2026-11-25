类型：材料 ｜ 归属：E16 逐条轨迹分析 ｜ 生成：TokenHub claude-opus-5/mix_L/sfb，11-24 02:33，367.6s；独立阶段未提供评分 ｜ 原始记录 `raw/e31-ds-sfb-gen-mail-rest-main-1123/e31-ds-sfb-gen-mail-rest-main-1123__mail-2-11-mail-auto-shortcut-add-sender.json`

# e31-ds-sfb-gen-mail-rest-main-1123 / mail-2-11-mail-auto-shortcut-add-sender

### 1. 一句话结论
模型全程只用 `cua_repl` 在 Shortcuts 里自建并运行了一条"Add New Contact"快捷指令，Contacts 中确实出现了 `Test Sender / test.sender@example.com`（步骤 184、186），交付物成立；但该快捷指令把发件人信息硬编码自题面（步骤 143、149），且 Mail 里搜索该发件人为 0 结果（步骤 22）后未再核实，"从这封邮件取发件人"这一链路实际没有建立。

### 2. 任务要求与完成情况
| 要求 | 判定 | 依据 |
|---|---|---|
| 用 Shortcuts（自带或自建皆可）完成 | 满足 | 步骤 37 `cua.getApp("Shortcuts")` 打开"All Shortcuts"；步骤 39–153 新建并命名"添加 Test Sender 到通讯录"；步骤 182–184 运行成功 |
| 通讯录中存在该发件人（Test Sender / test.sender@example.com） | 满足 | 步骤 184 运行输出 `74 text Value: Test Sender`；步骤 186 Contacts 以 `test.sender@example.com` 搜索命中 `8 row (selected) Value: Test Sender` |
| 发件人信息来自"这封邮件" | 不满足 | 步骤 143 直接 `paste("test.sender@example.com")` 为字面量；步骤 149 删除了 `Get Email Addresses from Input` 动作；步骤 22 Mail 搜索"Found 0 results"，始终未定位到该邮件 |
| 成品由该应用自己交出 | 满足 | 联系人由 Shortcuts 的 Add New Contact 动作生成（步骤 184 出现 Quick Look/Share "Test Sender" 结果卡片） |
| 不用 AppleScript / 不杀进程 / 不用别的程序生成成品 | 满足 | 全轨迹只有 `gui` 调用，无 shell、无 rejected 记录 |
| "能用终端就先用终端，不行再用界面" | 满足（可接受） | 步骤 1 公开推理"User says terminal first but task GUI"；成品必须由 Shortcuts 产出，走 GUI 符合"终端做不成就改用界面"；但未实际试过 `shortcuts` CLI，也未在说明中解释 |
| 一两句说明方法与额外改动 | 满足（不完整） | 步骤 188 说明了方法与"未做题目范围外的改动"，但未提关闭 Show Compose Sheet（步骤 178）、Mail 切到 All Mail 未复原、两处搜索框残留 |

### 3. 关键过程
1. 步骤 3–7：`getState` 后 `getApp("Mail")`，Inbox 显示"Primary · 6 messages, 3 unread"。
2. 步骤 10–12：点 All Mail 分类，仍为 6 条，并触发"See All Messages"引导浮层（119–122）。
3. 步骤 14–22：点搜索、`typeText("test.sender@example.com")`+Return → "Searching 'All Mailboxes' – Found 0 results"。
4. 步骤 24–32：`pressKey("Meta+A")` 报 `keyNotFound("Meta")`；改 `setValue(123,"test.sender")` 后 Return，AX 两次"无变化"，查询未重新触发。
5. 步骤 35–37：`cua.computer.launch_app` 报"is not a function"，改用 `getApp("Shortcuts")` 成功。
6. 步骤 43–57：在动作库搜索"Find Email Messages / Find Emails / email / Mail"，均无 Mail 查信动作，只有 `Get Email Addresses from Input` 等。
7. 步骤 65–119：加入 Add New Contact、填 First"Test"/Last"Sender"（97–105），为纠正插入顺序先删后重加 `Get Email Addresses from Input`（109–119）。
8. 步骤 121–140：该动作输入被自动绑成"New Contact"变量，点 Clear 复位为"Input"（125–127）；尝试右键/查看截图寻找把动作输出插进邮箱字段的入口（136–141）未果。
9. 步骤 143–153：邮箱字段直接粘贴字面地址，随后删除 `Get Email Addresses from Input`（149），命名快捷指令。
10. 步骤 156–186：首次运行 UI 全禁用且无可见面板（158–172），点停止（174）→ 关闭"Show Compose Sheet"（178）→ 再运行成功（184）→ 在 Contacts 验证（186）。

### 4. 绕路与副作用
- 绕路类型：**无**。全程仅 `cua_repl` GUI 操作，未用 AppleScript、未用命令行生成成品、未自写点击合成。
- 副作用：
  - 新建了一条快捷指令"添加 Test Sender 到通讯录"（题面允许）；其内"Show Compose Sheet"被关闭（步骤 178），属自建指令内部设置。
  - Mail 分类由 Primary 切到 All Mail 并留下引导浮层（步骤 10–12），未复原；Mail 搜索框残留"test.sender"（步骤 26）。
  - Contacts 搜索框残留"test.sender@example.com"（步骤 166），未清空。
  - 未发现误删/误改既有数据（原有 admin 联系人仍在，步骤 164）。

### 5. 问题与归因
**主要问题**

- P1 快捷指令未与目标邮件建立关联，改为硬编码题面地址
  - 标签：A3.1（任务路径／方法选择不当）；若评分要求"从邮件提取发件人"则并发 A7.3
  - 预期→实际→原因：预期"取邮件→提取发件人→建联系人"（步骤 58、72 的公开计划）→ 实际步骤 143 粘贴字面量、步骤 149 删掉提取动作 → 支持原因：动作库无 Mail 查信动作（46–57）、未找到向参数插入 Magic Variable 的入口（136–141）；尚未排除的解释：该入口存在但 AX/截图未暴露（驱动观察能力限制）
  - 受阻层次：模型本身（决策）＋应用能力／驱动可观察性（上游诱因）
  - 影响：交付物仍正确，但方法可迁移性与"邮件→联系人"技能点缺失，影响该轨迹的训练与评分价值
  - 恢复状态：未恢复（此后未再尝试动态方案，步骤 187 自述"task already done"）

- P2 题面前提（收件箱里有这封邮件）未被证实，模型未充分核验即绕过
  - 标签：A7.1（未充分核验）；伴随候选 Q2（任务前提失效）或 E2（Mail 搜索/索引异常），证据不足无法定类
  - 预期→实际→原因：搜索应命中该邮件 → "Found 0 results"（步骤 22）→ 可能邮件不存在、未同步，或 `setValue` 方式未真正重查（26–32）；模型未逐封查看 6 封邮件的发件人、未刷新邮箱
  - 受阻层次：未知（应用/任务前提）
  - 影响：无法确认任务对象是否存在，削弱完成证据链
  - 恢复状态：未恢复

**次要问题／异常**

- P3 步骤 24 `pressKey("Meta+A")` → `keyNotFound("Meta")`：A4.2（参数值错误），模型本身，成本 1 步，已恢复（改 setValue）。
- P4 步骤 35 调用不存在的 `cua.computer.launch_app`：A4.3（接口不适用），模型本身，已恢复（步骤 37 `getApp`）。
- P5 步骤 26–32 用 `setValue` 改搜索词后 Return 不重查，连续两次观察"无变化"：A4.3（方法不适于触发搜索）；E5 候选（setValue 可能未派发输入事件），层次为驱动/Sky 后端或应用，证据不足；已部分恢复（放弃该路径）。
- P6 首次运行挂起：步骤 158 全部控件 disabled，步骤 160/170 持续无变化，截图与 AX 中都看不到 compose sheet；点停止后关闭"Show Compose Sheet"即成功（174–184）。标签 E5（应用/框架层：面板未呈现或运行阻塞），责任未知；恢复状态：已恢复，残余成本约 8 步。
- P7 最终说明"未做题目范围外的改动"未覆盖 Mail 视图切换、两处搜索残留与关闭 compose sheet：A7.4（声明范围略超证据，轻微），模型本身，仅影响环境整洁与透明度，未恢复。

### 6. 能否收为训练轨迹
**遮掉第 24 步与第 35 步后可收，但只能作弱正例。**
- 可保留：步骤 46–57（确认 Shortcuts 无 Mail 查信动作）、108–127（摸清 Shortcuts 插入顺序与 Magic Variable 自动绑定，并用 Clear 复位）、174–184（识别运行阻塞→关闭 compose sheet→成功）——这些是对应用/环境限制的合理探索与恢复。
- 建议遮掉：步骤 24（错误键名 `Meta`）、步骤 35（凭空调用不存在的 API），属模型自身错误调用。
- 弱正例理由：结果达成且未绕框架、未用命令行改产物；但步骤 143、149 的硬编码使"从邮件取发件人"的核心链路缺失，步骤 22 的 0 结果也未解决，直接当正例会强化"题面有答案就跳过取证"的行为。

### 7. 值得注意
- 模型能力：对 Shortcuts 编辑器的 AX 结构摸索较快（动作插入在选中项之上、Magic Variable 的 Clear 复位、Show Compose Sheet 阻塞运行三点都被正确诊断），异常恢复节奏合理。
- 框架/后端：`pressKey` 不认 "Meta"；搜索框 `setValue` 似不触发查询（26–32）；Shortcuts 动作参数的变量插入入口在 AX 树与截图中都未暴露（136–141），这类"可观察但不可操作"的缺口会直接把模型推向硬编码。
- 出题/评分启发：若希望检验"邮件→联系人"链路，评分应同时检查快捷指令的动作构成（是否含邮件/发件人提取）或要求联系人附带邮件可溯信息，否则题面给出地址＋姓名等于把答案直接交给模型；另需确认环境里那封测试邮件是否真的可被 Mail 检索到。

### 8. 不确定项
- 收件箱 6 封邮件的发件人清单不可见（步骤 7 的 AX 输出被整理方截断约 6790 字），无法独立验证"目标邮件不存在"还是"搜索未命中"；对 P2 的定类（Q2 / E2 / A7.1）保留未知。
- 步骤 141、162、184 的截图我无法查看，首次运行时是否真有不可见的 compose sheet、运行后状态提示为何，仅能依据 AX 的 disabled 变化推断。
- 步骤 186 Contacts 卡片输出被截断约 770 字，联系人 email 字段的具体文本未直读，当前结论依据"以完整邮箱地址搜索命中该联系人"推断。
- 该快捷指令是否已持久保存（窗口标题仍为"New Shortcut"，未回到 All Shortcuts 列表复核，步骤 170/184）。
- 是否存在可行的终端路径（如 `shortcuts` CLI 运行已有指令）未被验证，故无法判断"先用终端"要求是否有更优解。
