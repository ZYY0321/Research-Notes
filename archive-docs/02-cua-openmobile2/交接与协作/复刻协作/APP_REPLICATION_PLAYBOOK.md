# Browser-Host App 复刻 Playbook v2.0

> **适用对象**：新 AI agent 或开发者，在 MobileGym 框架中从零复刻一个真实 App  
> **前置阅读**：本 Playbook 是对官方文档的补充，不是替代。执行前必须先读：
> - `trial_apps/mobilegym/docs/guides/add-an-app.md`（教程）  
> - `trial_apps/mobilegym/docs/platform/app/module-contract.md`（正式合同）  
>
> **验证标准**：每一步完成后必须过本步的检查列表，才能进入下一步。  
> **参考实现**：`apps/WechatV2/`（有已知缺陷，见文末附录）

---

## 交互路径缺失问题：核心诊断

> **这是最常见的失败模式。** WechatV2 开发过程中，大量路由被声明但没有 UI 元素能触达，
> 大量用例写在文档里但代码里没有实现。根本原因是 Use Case、路由声明、代码实现 **三者完全解耦**。
>
> 解法是**单向追踪链**：每条 Use Case → 对应 Transition ID → 对应 `data-trigger` 属性 → 通过官方工具静态验证。
> 任何一环断裂，工具会报错。  
> 本 Playbook 的 Step 2 和 Step 2.5 专门处理这个问题。

---

## 目录

1. [理解 OS 约束（必须第一步）](#1-理解-os-约束必须第一步)
2. [需求分析 + 可达性矩阵](#2-需求分析--可达性矩阵)
3. [创建目录结构与 manifest](#3-创建目录结构与-manifest)
4. [声明导航 FSM](#4-声明导航-fsm)
5. [设计状态模型与种子数据](#5-设计状态模型与种子数据)
6. [连接 OS（navigation.ts + AppEntry）](#6-连接-osnavigationts--appentry)
7. [编码页面（分层）](#7-编码页面分层)
8. [验收](#8-验收)

---

## 1. 理解 OS 约束（必须第一步）

> **这一步如果跳过，所有页面的 TopBar 都会被状态栏遮挡，按钮点不了。WechatV2 初版就是因此耽误了数小时。**

### 1.1 读官方文档中的约束

在 `module-contract.md` 的 **Cross-cutting rules** 一节，重点：

| 规则 | 内容 | 违反后果 |
|------|------|----------|
| 时间 API | 用 `TimeService.now()` 不能用 `Date.now()` | lint 报错，任务时间线错乱 |
| 手势事件 | 用 `onPointer*`，不能用 `onTouch* + onMouse*` | 混合输入设备行为异常 |
| 状态栏保留 | 页面根元素必须有 `pt-10`（= 40px） | TopBar 被 OS 状态栏遮挡 |
| 底栏键盘 | TabBar 加 `data-hide-on-keyboard`；不能 `position: fixed` | 键盘弹起时布局破坏 |
| URL 驱动 UI | 模态框/抽屉/标签页状态走 `searchParams`，不走 `useState` | 系统返回键穿透，对话框不关 |

### 1.2 建立 App 级常量文件

在 App 目录下创建 `constants.ts`（这里集中 OS 数值，避免散落硬编码）：

```typescript
// apps/<AppName>/constants.ts
/**
 * OS 宿主约束 —— 来源：os/data/simulatorConfig.ts
 * 不要手动改这里，如果 OS 层更新了数值，同步修改。
 */
export const OS = {
  STATUS_BAR_H:  40,    // 顶部状态栏浮层，pt-10 等于此值
  GESTURE_BAR_H: 16,    // 底部手势条浮层
  VIEWPORT_W:    360,
  VIEWPORT_H:    800,
  TOP_BAR_H:     44,    // App 自身 TopBar 高度（非 OS 层）
  TAB_BAR_H:     56,    // App 自身 TabBar 高度（非 OS 层）
} as const;

/**
 * DATA_VERSION —— 每次修改 defaults.json 必须递增。
 * state.ts 的 persistName = `<appId>_v${DATA_VERSION}`
 * 版本变化会清空 localStorage，强制从 defaults.json 重新加载。
 */
export const DATA_VERSION = 1;
```

### ✅ Step 1 检查

- [ ] 已读 `add-an-app.md` 和 `module-contract.md`
- [ ] `constants.ts` 已创建，`OS.STATUS_BAR_H = 40`，`DATA_VERSION = 1`

---

## 2. 需求分析 + 可达性矩阵

### 2.1 特征清单（Feature Inventory）

格式：`docs/<AppName>-replication/01-feature-inventory.md`

每项标注优先级：

| 优先级 | 定义 |
|--------|------|
| P0 | 核心链路，没有它 App 不可用 |
| P1 | 重要功能，影响使用体验 |
| P2 | 完整度功能，可以是 stub |
| wontfix | 需要真实后端/OS API 暂不实现，记录原因 |

### 2.2 用例定义（Use Cases）

格式：`docs/<AppName>-replication/02-use-cases.md`

**每个用例必须同时绑定 `transition-id` 和 `data-action`**。这是建立追踪链的关键。

```markdown
### UC-A01：发送文字消息
- **Transition ID**：`chat.message.send`        ← 对应 navigation.declaration.ts 中的 transition
- **触发元素**：`data-action="chat.message.send"` ← 代码中 UI 元素的属性
- **触发方式**：点击发送按钮（非双击、非长按）   ← 必须写清楚，避免模型自行猜测
- **前置条件**：已登录，在聊天详情页
- **主成功场景**：
  1. 在输入框输入文字
  2. 点击"发送"按钮（`data-action="chat.message.send"`）
- **状态变更**：`chats[id].messages` 新增 `{type:'text', sender:'me', ...}`
- **判题条件**：`last_message.type === 'text' && last_message.sender === 'me'`
- **难度**：L2
```

**为什么必须写"触发方式"**：WechatV2 的拍一拍（UC-A03）应该是双击头像，但因为文档没写清楚，模型实现成了一个专用按钮。这种错误在验收时才发现，损失很大。

`data-action` 命名规范：
```
{页面}.{对象}.{动作}     →  chat.message.send
{页面}.{对象}.{状态}     →  chatList.item.sticky.toggle
{系统}.{流程}.{步骤}     →  auth.login.submit
```

### 2.3 交互可达性矩阵（最关键的交付物）

**在写任何代码之前，先建立这张表。** 它是用例文档和路由声明之间的桥梁，也是最容易验证"交互路径是否完整"的工具。

格式：`docs/<AppName>-replication/03-interaction-matrix.md`

```markdown
# 交互可达性矩阵

> 规则：每条 P0/P1 用例必须在此表中有对应行。
> 状态：⬜未实现 / 🔶部分实现 / ✅已实现 / ❌wontfix

| UC | 用例 | 入口路由 | 触发方式 | Transition ID | 目标路由 | 状态 |
|----|------|---------|---------|---------------|---------|------|
| A01 | 发送文字消息 | `/chat/:id` | 点击"发送"按钮 | `chat.message.send` | `/chat/:id`（原地） | ⬜ |
| A03 | 拍一拍好友 | `/chat/:id` | **双击**对方头像 | `chat.pat.send` | `/chat/:id`（原地） | ⬜ |
| A05 | 置顶会话 | `/` | 左滑会话行 → 点"置顶" | `chatList.item.sticky.toggle` | `/`（原地） | ⬜ |
| B02 | 星标好友 | `/friend-settings/:id` | 点击星标开关 | `friendSettings.starred.toggle` | `/friend-settings/:id`（原地）| ⬜ |
| C01 | 发纯文字朋友圈 | `/moments` | 长按相机图标 | `moments.postText.open` | `/post-text-moment` | ⬜ |
```

**可达性矩阵的使用方法**：
1. **编码前**：先填满这张表，确保每条 P0/P1 用例都有对应行
2. **路由声明时（Step 4）**：表中每一行的 Transition ID 必须出现在 `navigation.declaration.ts`
3. **编码时（Step 7）**：实现一条用例后，把状态改为 ✅，同时确认代码中有对应的 `data-action`
4. **验收时（Step 8）**：矩阵中没有 ⬜ 的 P0 行，才算通过

### 2.4 从矩阵生成路由检查脚本

```python
# assets/validate_matrix.py
"""
验证交互矩阵中的 Transition ID 都在 navigation.declaration.ts 中声明。
"""
import re
from pathlib import Path

ROOT = Path(__file__).parent.parent
nav_text = (ROOT / "navigation.declaration.ts").read_text(encoding="utf-8")

# 从矩阵 markdown 提取 Transition ID（第5列）
matrix_text = (ROOT.parent.parent / f"docs/{ROOT.name}-replication/03-interaction-matrix.md").read_text(encoding="utf-8")

# 提取所有 `code` 格式的 transition id
matrix_ids = set(re.findall(r'`([a-z][a-z0-9.]+)`', matrix_text))
declared_ids = set(re.findall(r"id:\s*'([^']+)'", nav_text))

missing = matrix_ids - declared_ids
print(f"矩阵中的 Transition ID: {len(matrix_ids)}")
print(f"navigation.declaration 中声明: {len(declared_ids)}")
if missing:
    print(f"ERROR: 矩阵中有但未声明的 ID ({len(missing)} 条):")
    for i in sorted(missing): print(f"  {i}")
else:
    print("OK: 矩阵中所有 Transition ID 都已声明")
```

### ✅ Step 2 检查

- [ ] Feature Inventory 已写，每项有优先级
- [ ] Use Cases 已写，每个 P0/P1 用例有 **Transition ID + data-action + 触发方式**
- [ ] 交互可达性矩阵（03-interaction-matrix.md）已建立，P0/P1 全覆盖
- [ ] wontfix 的原因已记录
- [ ] `validate_matrix.py` 可以运行（即使此时输出"矩阵ID未声明"也没关系，Step 4 之后需要全部通过）

---

## 3. 创建目录结构与 manifest

### 3.1 目录结构

```
apps/<AppName>/
├── manifest.ts               ← 必须
├── <AppName>App.tsx           ← 必须，文件名必须以 App.tsx 结尾
├── navigation.declaration.ts  ← 必须
├── navigation.types.ts        ← 必须（复制自已有 App）
├── navigation.ts              ← 必须（复制自已有 App 再修改）
├── state.ts                   ← 必须（有状态的 App）
├── types.ts                   ← 推荐
├── constants.ts               ← 必须（Step 1 已建）
├── res/
│   └── icons.tsx              ← 必须（launcher 图标）
├── data/
│   ├── index.ts               ← 必须
│   └── defaults.json          ← 必须（用 Python 脚本生成）
├── assets/                    ← 图片资源
│   ├── avatars/
│   └── (其他子目录)
├── components/                ← 共享组件
└── pages/                     ← 页面组件
```

### 3.2 manifest.ts

```typescript
// apps/<AppName>/manifest.ts
import type { AppManifest } from '@/os/types/manifest';

// Launcher 图标：SVG inline 最简单，避免图片加载问题
const IcLauncher = `data:image/svg+xml;utf8,<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100">
  <rect width="100" height="100" rx="22" fill="%23<主色>"/>
  <text y=".9em" font-size="80" x="10"><图标 emoji></text>
</svg>`;

export const manifest: AppManifest = {
  id: '<appId>',               // 小写，唯一，也是 localStorage 键
  packageName: 'com.<公司>.<app>',
  displayName: '<中文名>',
  displayNameEn: '<英文名>',
  aliases: ['<搜索别名>'],
  version: '1.0.0',
  versionCode: 1,
  type: 'plugin',
  icon: IcLauncher,
  iconBackground: '#<主色>',
  iconForeground: '#ffffff',
  designViewportWidth: 360,
  theme: {
    colors: {
      primary: '#<主色>',
      primaryDark: '#<深一档主色>',
      background: '#<页面背景色>',
      surface: '#ffffff',
      textPrimary: '#<正文色>',
      textSecondary: '#<辅助文字色>',
      border: '#<分割线色>',
      statusBarForeground: 'dark',  // 或 'light'
      navigationBarForeground: 'dark',
    },
  },
};
```

**注意**：`id` 必须唯一，OS 通过它做 localStorage 键、store 注册键、`__SIM__.getState().apps.<id>`。

#### 外观自检（对齐 pipeline-v3 §10.1，做不到就降级，不是可选）

manifest 的外观字段决定 app 图标和**系统顶栏/导航栏**的呈现，`SystemShell` 据此驱动。填完必须过这几条：

- **A1 图标**：`icon` + `iconBackground` 必填，launcher 里不能是默认纯色方块。SVG inline 最简单，颜色用真机主色。
- **A2 顶栏色对应**（最常漏）：`statusBarForeground` 必须和顶栏背景明暗**相反**——浅色顶栏用 `'dark'`（深色前景），深色顶栏用 `'light'`。判断标准：真机截图里顶栏的时间/信号图标看得清，你的模拟版也要看得清。`navigationBarForeground` 同理。
- **A4 取色来源**：`primary`/`background`/`border` 等**从真机截图取色**，不要沿用 Taobao/Kapi 的色值。取色结果记进 `docs/<app>-replication/design-tokens.md`，注明取自哪张截图。
- **A3 圆角/字号/间距**：编码阶段（§7）对着真机逐页比，明显偏差按铁律②处理，不能只求结构对。

### ✅ Step 3 检查

- [ ] 目录结构符合上面的 layout
- [ ] `manifest.ts` 所有必填字段完整
- [ ] `res/icons.tsx` 存在，导出 `IcLauncher`
- [ ] `manifest.id` 没有与现有 App 冲突（检查 `apps/*/manifest.ts`）

---

## 4. 声明导航 FSM

### 4.1 复制 navigation.types.ts

```bash
cp apps/Wechat/navigation.types.ts apps/<AppName>/navigation.types.ts
```

不需要修改，这个文件在所有 App 间结构相同。

### 4.2 navigation.declaration.ts

每个路由的完整结构（不要省略字段，省略后 OS 静态分析会警告）：

```typescript
// apps/<AppName>/navigation.declaration.ts
import type { NavigationDeclaration } from './navigation.types';

export const NAVIGATION_DECLARATION = {
  app: '<appId>',
  routes: [
    {
      path: '/',
      component: 'HomePage',
      params: {},
      entryPoint: 'home',       // 'home' | 'none' | 'external'
      scrollContainers: [
        { name: 'main', direction: 'vertical', description: '主列表' },
      ],
      uiStates: [
        { id: '<appId>.home.base', search: {}, description: '首页' },
      ],
      queryParams: {},
      description: '首页',
    },
    // 更多路由...
  ],
  transitions: [
    {
      id: '<appId>.home-open',     // 格式：<appId>.<目标页面>-open
      from: '*',
      to: '/',
      search: {},
      searchParams: {},
      mode: 'replace',
      params: {},
      label: '返回首页',
      ui: { placement: 'none', icon: 'back', gesture: 'back' },
    },
    // 更多转换...
  ],
  capabilities: {
    historyBack: true,
  },
} as const satisfies NavigationDeclaration;

export type TransitionId = typeof NAVIGATION_DECLARATION.transitions[number]['id'];
```

### 4.3 路由完整性验证

在 `assets/validate_routes.py` 中：

```python
import re
from pathlib import Path

ROOT = Path(__file__).parent.parent
nav_text = (ROOT / "navigation.declaration.ts").read_text(encoding="utf-8")
app_text = (ROOT / f"{ROOT.name}App.tsx").read_text(encoding="utf-8")

# 声明的路由
declared = set(re.findall(r"path:\s*'([^']+)'", nav_text))
# 注册的路由（React Router）
registered = set(p for p in re.findall(r'path="([^"]+)"', app_text) if not p.startswith("*"))

# Tab 路由由 CSS display 管理，不在 React Router Routes 里
TAB_ROUTES = {"/", "/contacts", "/discover", "/me"}  # 按实际修改
EXEMPT = {"/auth/login", "/auth/register", "/*"} | TAB_ROUTES

missing = declared - registered - TAB_ROUTES
extra   = registered - declared - EXEMPT

print(f"声明: {len(declared)}  已注册: {len(registered)}")
if missing:
    print(f"缺少注册的路由 ({len(missing)} 条):")
    for r in sorted(missing): print(f"  {r}")
else:
    print("OK: 所有声明路由已注册")
```

运行：`python assets/validate_routes.py`

### ✅ Step 4 检查

- [ ] `navigation.types.ts` 已复制
- [ ] `navigation.declaration.ts` 每条路由有完整字段（不是只有 path/name）
- [ ] `validate_routes.py` 运行输出 "OK"（或 MISSING 全是 P2/wontfix）

---

## 5. 设计状态模型与种子数据

### 5.1 types.ts

时间戳规则（重要）：

```typescript
// ✅ 正确：绝对 Unix 毫秒
timestamp: number;  // 例：1749340800000

// ❌ 错误：负数相对偏移
timestamp: number;  // -3600000（1小时前）

// 资源路径规则
avatar: string;  // /@app-assets/<AppName>/avatars/user.jpg
                 // /@app-assets/<AppName>/images/post.jpg
                 // 路径相对于 apps/<AppName>/assets/
```

### 5.2 data/defaults.json 生成脚本

**永远用 Python 脚本生成，不要手动编辑 JSON。**
PowerShell 读写 UTF-8 文件会损坏中文（GBK→UTF-8 重新编码问题）。

```python
# apps/<AppName>/assets/regen_defaults.py
import json
from pathlib import Path

OUT = Path(__file__).parent.parent / "data" / "defaults.json"

# 基准时间（用当前真实时间的某个固定点）
BASE_TS = 1749340800000  # 2026-06-08 08:00 UTC+8
T = lambda h, m=0: BASE_TS + h * 3600000 + m * 60000  # T(8) = 下午4点

# 资源路径前缀（注意：相对于 assets/ 目录）
A = lambda f: f"/@app-assets/<AppName>/avatars/{f}"
I = lambda f: f"/@app-assets/<AppName>/images/{f}"

data = {
  "user": {
    "id": "user001",
    "name": "用户",
    "avatar": A("user.jpg"),
    # ...
  },
  # ...
}

OUT.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding='utf-8')
print(f"OK: defaults.json 生成完毕 ({OUT.stat().st_size} bytes)")
```

### 5.3 装饰性位图资产(商品图/头像/图标)

**优先级(pipeline v3 §5.3 定版)**

1. **用户已提供生图 API + key** → 阶段 3 实现期**尽早批量生图**:复制并适配 `apps/Taobao/assets/gen_item_images.py`,按 `defaults.json` 清单一次性生成全部 PNG(4 并发、幂等可重跑);`regen_defaults.py` 里路径 helper 优先指向已生成的 PNG。
2. **用户未提供** → `regen_defaults.py` 生成 SVG 占位即可,不阻塞 gate。

**纪律**

- 由 **AI 配置环境变量并执行脚本**,不要求操作者自己跑 Python。
- API 与仓库默认不同时改 `IMAGE_GEN_BASE_URL`/`IMAGE_GEN_MODEL`,key 用 `IMAGE_GEN_API_KEY`(兼容 `TOKENHUB_API_KEY`),**禁止提交到 git**。见 `tools/image_gen_client.py`。
- 生图 prompt 只用合成描述,**禁止**上传 `*_images/` 真机截图或含个人信息的照片。
- 参考:`apps/Taobao/assets/regen_defaults.py` 的 `ITEM_IMG()`(有 PNG 用 PNG,否则 SVG)。

### 5.4 data/index.ts

```typescript
// apps/<AppName>/data/index.ts
import defaults from './defaults.json';
import { manifest } from '../manifest';

export const APP_CONFIG = {
  ...defaults,
  appId: manifest.id,
};
```

### 5.5 state.ts

```typescript
// apps/<AppName>/state.ts
import { createAppStoreWithActions } from '@/os/createAppStore';
import { APP_CONFIG } from './data';
import { DATA_VERSION } from './constants';
import type { AppState, AppActions } from './types';

const initialState: AppState = {
  // 从 APP_CONFIG 填充
};

export const useAppStore = createAppStoreWithActions<AppState, AppActions>(
  manifest.id,          // 第一个参数必须等于 manifest.id
  initialState,
  (set, get) => ({
    // actions
  }),
  {
    persistName: `${manifest.id}_v${DATA_VERSION}`,  // 版本化键名，改版本号清空缓存
    partialize: (state) => {
      // 排除 _temp 字段和函数
      const { _temp, ...rest } = state as AppState & AppActions;
      const result: Record<string, any> = {};
      for (const [k, v] of Object.entries(rest)) {
        if (typeof v !== 'function') result[k] = v;
      }
      return result as Partial<AppState>;
    },
  },
);
```

### 5.6 defaults.json 数据验证脚本

```python
# apps/<AppName>/assets/validate_defaults.py
import json, re
from pathlib import Path

data = json.loads((Path(__file__).parent.parent / "data/defaults.json").read_text(encoding='utf-8'))

errors = []

def check(obj, path=''):
    if isinstance(obj, dict):
        for k, v in obj.items():
            check(v, f"{path}.{k}")
    elif isinstance(obj, list):
        for i, v in enumerate(obj):
            check(v, f"{path}[{i}]")
    elif isinstance(obj, (int, float)):
        # 时间戳必须是绝对正整数（> 2020年 = 1577836800000）
        if 1_000_000_000_000 < obj < 9_999_999_999_999:
            pass  # 合法的绝对时间戳
        elif -86400000 < obj < 0:
            errors.append(f"负数时间戳 {path}: {obj}")
    elif isinstance(obj, str):
        # 图片路径必须以 /@app-assets/ 开头
        if re.match(r'\.(jpg|jpeg|png|gif|webp)$', obj, re.I):
            if not obj.startswith('/@app-assets/') and not obj.startswith('http'):
                errors.append(f"图片路径不规范 {path}: {obj}")

check(data)
if errors:
    print(f"ERROR: {len(errors)} 个问题:")
    for e in errors: print(f"  {e}")
else:
    print("OK: defaults.json 验证通过")
```

### ✅ Step 5 检查

- [ ] `types.ts` 中所有 timestamp 字段有注释说明是绝对 Unix 毫秒
- [ ] `defaults.json` 由 Python 脚本生成，不是手动写的
- [ ] `validate_defaults.py` 运行输出 "OK"
- [ ] `state.ts` 的 `persistName` 包含 `DATA_VERSION`

### 5.7 数据分层：构建时种子 vs 运行时写入（对齐 pipeline-v3 §10.3）

两层数据分工明确，别混淆：

| 层 | 位置 | 内容 | 硬要求 |
|----|------|------|--------|
| **构建时种子** | `data/defaults.json` → `state.ts` 注入 | app 首次打开就该有的内置默认数据 | 每个主列表 **≥ 5 条**，且**多样**：日期/金额/分类/状态各不相同，不是复制同一条改个字。图片/头像真实观感，非字母占位。 |
| **运行时写入** | app store 的 action / OS `ContentProvider` | 用户操作（记一笔、发评论、下单）产生的新数据 | 走正常交互写进 store；刷新不丢（除非 `DATA_VERSION` 变更触发重置）。**禁止**把用户产生的数据硬写回 `defaults.json`。 |

- 「构建时 config 好，还是运行时写入？」→ **默认数据构建时 config，用户产生的数据运行时写入**，两者都要。
- 多样性是种子数据的硬指标：单薄/重复的种子会让 agent 学不到真实分布。生成 `defaults.json` 的 Python 脚本（§5.2）里就要刻意铺开分布，而不是最后补。

### 5.8 双语落地（对齐 pipeline-v3 §10.2）

框架已提供 `os/useAppStrings` + `os/locale`，`manifest.displayNameEn` 全 app 已有。**凡有 `displayNameEn` 的 app（即全部）都要接双语**，跟随 OS 语言切换。标准写法：

1. 建 `res/strings.ts`（中文基准）和 `res/strings.en.ts`（英文覆盖，可只覆盖部分键）：

```typescript
// apps/<AppName>/res/strings.ts —— 中文基准，键名语义化
export const strings = {
  navHome: '首页',
  navStats: '统计',
  navMe: '我的',
  emptyList: '还没有记录',
  // ...
};

// apps/<AppName>/res/strings.en.ts —— 英文覆盖（Partial 即可）
import type { strings } from './strings';
export const stringsEn: Partial<Record<keyof typeof strings, string>> = {
  navHome: 'Home',
  navStats: 'Stats',
  navMe: 'Me',
  emptyList: 'No records yet',
};
```

2. 在组件里用 hook 取当前语言的文案：

```tsx
import { useAppStrings } from '@/os/useAppStrings';
import { strings } from '../res/strings';
import { stringsEn } from '../res/strings.en';

function BottomNav() {
  const s = useAppStrings(strings, stringsEn); // 中文返回基准，英文返回覆盖后
  return <span>{s.navHome}</span>;
}
```

- **覆盖优先级**：至少覆盖导航/Tab/主按钮/空态文案（P0 链路上的文案优先），不必一次全量。
- app 内若真机有"语言/外观设置"入口，按铁律①处置（实现切换 / 移除 / 明确"暂未开放"），不留死交互。

---

## 6. 连接 OS（navigation.ts + AppEntry）

### 6.1 navigation.ts

**直接复制 `apps/Wechat/navigation.ts`，只修改引用路径和 `TransitionId`。**

不要自己写这个文件——它实现了完整的 FSM 解析逻辑（条件分支、参数替换、searchParams 管理），手写容易出错。

```bash
cp apps/Wechat/navigation.ts apps/<AppName>/navigation.ts
# 然后修改第3行的 import 路径
```

修改后只改这一行：
```typescript
import { NAVIGATION_DECLARATION, TransitionId } from './navigation.declaration';
```

### 6.2 AppEntry（最简模板）

`<AppName>App.tsx`：

```tsx
import React, { useCallback } from 'react';
import {
  MemoryRouter, Routes, Route, Navigate,
  useLocation, UNSAFE_NavigationContext,
} from 'react-router-dom';
import { useAppNavigationHandler } from '@/os/hooks/useAppNavigationHandler';
import { manifest } from './manifest';
import { useAppNavigate } from './navigation';
// 页面导入...

/**
 * NavigationHandler —— 必须在 MemoryRouter 内部挂载。
 * 负责：① 注册 App navigator；② 处理 OS 返回键；③ 广播生命周期事件。
 */
function AppNavigationHandler() {
  const location = useLocation();
  const { back } = useAppNavigate();

  useAppNavigationHandler(manifest.id, {
    onBack: (): boolean => {
      // 在首页：不拦截，让 OS 退到 launcher
      if (location.pathname === '/' && !location.search) return false;
      back();
      return true;
    },
  });

  return null;
}

function AppShell() {
  const location = useLocation();
  const isMainTab = ['/', '/tab2', '/tab3'].includes(location.pathname);

  return (
    <div className="flex flex-col h-full bg-app-bg">
      {/* 状态栏安全区 —— 必须是第一个子元素，pt-10 = 40px */}
      <div className="h-10 shrink-0" />

      {/* 主内容区 */}
      <div className="flex-1 overflow-hidden relative">
        <Routes>
          <Route path="/" element={<HomePage />} />
          {/* ... 其他路由 */}
        </Routes>
      </div>

      {/* TabBar —— data-hide-on-keyboard 使键盘弹起时自动隐藏 */}
      {isMainTab && (
        <div data-hide-on-keyboard className="shrink-0">
          <TabBar />
        </div>
      )}

      {/* 底部手势条安全区 —— 必须是最后一个子元素 */}
      <div className="h-4 shrink-0" />
    </div>
  );
}

export default function <AppName>App() {
  return (
    <MemoryRouter initialEntries={['/']}>
      <AppNavigationHandler />
      <AppShell />
    </MemoryRouter>
  );
}
```

**重要说明**：
- `AppNavigationHandler` 必须在 `MemoryRouter` 内部，不能放外面
- `h-10`（= 40px）是状态栏安全区，不能省略
- `data-hide-on-keyboard` 让 OS 在键盘弹起时自动隐藏 TabBar
- `h-4`（= 16px）是底部手势条安全区

### ✅ Step 6 检查

- [ ] `navigation.ts` 已复制并修改 import 路径
- [ ] `<AppName>App.tsx` 中 `AppNavigationHandler` 在 `MemoryRouter` 内部
- [ ] 根容器有 `h-10` 安全区 spacer 作为第一个子元素
- [ ] TabBar 有 `data-hide-on-keyboard`
- [ ] 根容器有 `h-4` 安全区 spacer 作为最后一个子元素
- [ ] `npm run dev` 后 App 出现在 launcher，点击能打开

---

## 7. 编码页面（分层）

### 7.1 分层顺序

**每层完成后做两件事再进下一层：**
1. 跑 Step 8 可见性清单（V1–V7）
2. 更新交互可达性矩阵（03-interaction-matrix.md）的状态列

```
Layer 0: AppShell + TabBar（只有骨架，无内容）
Layer 1: P0 页面框架（有 TopBar，内容为空或占位文字）
Layer 2: P0 状态渲染（数据从 store 读取并展示）
Layer 3: P0 交互（对照矩阵，逐行实现）
Layer 4: P1 页面和交互（对照矩阵，逐行实现）
Layer 5: P2 stub 页面（注册路由，内容只有标题，矩阵状态标为 ❌wontfix）
```

### 7.1.1 Layer 3/4 执行规则：逐行对照矩阵

这是防止"交互路径缺失"的核心操作：

```
对于矩阵中的每一行（状态为 ⬜ 的）：

1. 确认"入口路由"页面已存在
2. 在"触发方式"描述的 UI 元素上，加上 data-action="<Transition ID>"
3. 实现触发后的逻辑（导航 or 状态变更）
4. 确认"目标路由"已在 WechatApp.tsx 中注册
5. 把矩阵中这一行的状态改为 ✅

在进入下一行之前，确保当前行的 ✅ 是真实可触达的。
```

**禁止跳行操作**：不允许实现了 A03 但跳过了 A01。矩阵是顺序执行的，跳行意味着某些依赖前置页面还不存在。

### 7.2 页面模板

```tsx
// pages/<PageName>.tsx
import React from 'react';
import { useNavigate } from 'react-router-dom';  // 可以用，在页面里 ok
import * as TimeService from '@/os/TimeService';  // ⚠️ 不用 Date.now()
import { useAppStore } from '../state';
import { TopBar } from '../components/TopBar';

export default function <PageName>() {
  const navigate = useNavigate();
  const data = useAppStore(s => s.someData);  // 用 selector，不用 getState()

  return (
    // 不需要 pt-10，AppShell 已经处理了安全区
    <div className="flex flex-col h-full bg-app-bg">
      <TopBar
        title="页面标题"
        onBack={() => navigate(-1)}
        rightContent={<button data-trigger="...">按钮</button>}
      />
      <div className="flex-1 overflow-y-auto">
        {/* 页面内容 */}
      </div>
    </div>
  );
}
```

### 7.3 交互规范

```tsx
// ✅ 所有可交互元素必须有 data-action 或 data-trigger
<button
  data-action="chat.message.send"    // 触发状态变更
  onClick={handleSend}
>发送</button>

<button
  data-trigger="chatInfo.open"       // 触发导航
  onClick={() => navigate(`/chat/${id}/info`)}
>详情</button>

// ✅ 图片必须有 onError fallback
<img
  src={user.avatar}
  onError={(e) => {
    (e.target as HTMLImageElement).src = 'data:image/svg+xml,...';
  }}
/>

// ✅ 滑动手势用 Pointer 事件
<div
  onPointerDown={e => { e.currentTarget.setPointerCapture(e.pointerId); /* ... */ }}
  onPointerMove={handleMove}
  onPointerUp={handleUp}
/>

// ❌ 不要用 touch 事件
onTouchStart / onTouchMove / onTouchEnd
```

### 7.4 底部面板 / Action Sheet 规范

> ⚠️ 这是一个**高频易错点**，WeChat 的"加号面板"、"长按菜单"均属此类。  
> **绝对不要**把底部展开面板做成"跳转到新页面"，那是完全错误的 UX。

**判断依据（Panel vs. Page）**

| 行为特征 | 正确模式 |
|---|---|
| 在当前页面叠加，背后页面可见 | 底部面板（Panel），不跳路由 |
| 完全替换屏幕内容 | 新路由页面 |
| 关闭后回到原来状态（消息仍可见） | 底部面板 |

**推荐实现：URL SearchParam 控制**（符合 `module-contract.md`）

```tsx
// 打开面板 ——  在当前路由追加 ?panel=more
navigate({ search: '?panel=more' }, { replace: true });

// 读取面板状态
const { search } = useLocation();
const showMorePanel = new URLSearchParams(search).get('panel') === 'more';

// 关闭面板 —— 移除 searchParam，系统返回键也能正确关闭
navigate({ search: '' }, { replace: true });
```

**临时可接受方案（tech debt）**：若 app 暂未接入完整 `navigation.ts`，可用 `useState`，  
但必须在 `ACCEPTANCE.md` 中标注，并在 `navigation.declaration.ts` 的 `ACTIONS` 里声明：  
```ts
{ id: 'chat.morePanel.toggle', description: '切换加号更多功能面板（本地 state，待迁移 URL）' }
```

**`MorePanel` 内每个操作按钮都必须有 `data-action`**，格式为 `chat.more.<feature>`：
```tsx
<button data-action="chat.more.redPacket" onClick={...}>红包</button>
<button data-action="chat.more.photo"     onClick={...}>图片</button>
```

### 7.5 TopBar 组件模板

```tsx
// components/TopBar.tsx
import React from 'react';
import { useNavigate } from 'react-router-dom';

interface TopBarProps {
  title: string;
  showBack?: boolean;
  onBack?: () => void;
  rightContent?: React.ReactNode;
}

export function TopBar({ title, showBack = true, onBack, rightContent }: TopBarProps) {
  const navigate = useNavigate();
  const handleBack = () => onBack ? onBack() : navigate(-1);

  return (
    <div
      data-status-bar-foreground="dark"
      className="flex items-center h-11 bg-app-bg border-b border-app-border shrink-0 px-2"
    >
      <div className="w-16 flex items-center">
        {showBack && (
          <button
            data-action="back"
            onClick={handleBack}
            className="flex items-center gap-1 text-app-primary text-sm cursor-pointer border-none bg-transparent"
          >
            <span className="text-xl">‹</span>
            <span>返回</span>
          </button>
        )}
      </div>
      <div className="flex-1 text-center font-semibold text-base text-app-text">{title}</div>
      <div className="w-16 flex justify-end items-center">{rightContent}</div>
    </div>
  );
}
```

### ✅ Step 7 检查

- [ ] 每个可点击元素有 `data-action` 或 `data-trigger`
- [ ] 没有使用 `Date.now()` 或 `new Date()`（用 `TimeService.now()`）
- [ ] 没有使用 `onTouchStart/End/Move`（用 `onPointer*`）
- [ ] 没有 `position: fixed`（用 flex + `shrink-0`）
- [ ] 所有 `<img>` 有 `onError` fallback
- [ ] store 读取用 selector：`useStore(s => s.xxx)`，不用 `.getState()`

---

## 8. 验收

### 8.1 创建 ACCEPTANCE.md

在 App 目录下建立验收清单（参考 `apps/WechatV2/ACCEPTANCE.md`）。

### 8.2 可见性清单（5 分钟手工验收）

| # | 项目 | 验收标准 |
|---|------|----------|
| V1 | 顶栏可见 | TopBar 不被 OS 状态栏遮挡，标题和返回按钮清晰可见 |
| V2 | 返回按钮有效 | 所有子页面点返回能正确回到上一级 |
| V3 | 头像/图片显示 | 关键图片为真实内容，非字母/图标占位 |
| V4 | 主列表有数据 | 首页列表 ≥ 3 条真实内容 |
| V5 | 内容页有数据 | 次要列表/详情页有内容 |
| V6 | Tab 切换正常 | 所有 Tab 均可切换，切换后内容正确 |
| V7 | P0 链路跑通 | 见下方 UC 验收 |
| V8 | 图标存在（§10.1 A1） | launcher 里 app 图标不是默认纯色方块 |
| V9 | 顶栏色对应（§10.1 A2） | 系统顶栏文字/图标清晰可见，明暗和顶栏背景相反 |
| V10 | 双语可切换（§10.2） | 切换 OS 语言后，导航/Tab/主按钮/空态文案跟随中/英变化 |
| V11 | 种子数据多样（§10.3） | 主列表 ≥ 5 条且内容不重复（日期/金额/分类各异） |

### 8.3 P0 用例验收

逐一执行用例文档中的每条 P0 用例，检查：
1. 能否按步骤操作
2. 状态变更是否正确（在 DevTools 的 `__SIM__.getState().apps.<id>` 中确认）

### 8.4 交互路径完整性检查

**这是防止"交互路径缺失"的最终防线。**

```bash
# 1. 路由注册检查（Step 4 建立的脚本）
python assets/validate_routes.py

# 2. 矩阵 Transition ID 检查（Step 2 建立的脚本）
python assets/validate_matrix.py

# 3. 官方工具：data-trigger 一致性检查
#    扫描代码中所有 data-trigger="xxx"，验证 xxx 都在 navigation.declaration.ts 中声明
node ../../scripts/build_nav_artifacts.mjs <AppName>

# 4. 交互可达性矩阵自查
#    打开 docs/<AppName>-replication/03-interaction-matrix.md
#    P0 行的状态列必须全部为 ✅，不允许有 ⬜
```

**通过标准**：
- `validate_routes.py`：OK（或 MISSING 全是 P2/wontfix）
- `validate_matrix.py`：OK
- `build_nav_artifacts.mjs`：无 ERROR
- 矩阵中 P0 行全部 ✅

### 8.5 TypeScript 类型检查

```bash
npx tsc --noEmit
```

### 8.6 数据重置测试

修改 `constants.ts` 中 `DATA_VERSION`（例如 1 → 2），刷新浏览器，确认数据重置为 `defaults.json` 的内容。

### ✅ Step 8 检查

- [ ] `ACCEPTANCE.md` 已建立
- [ ] V1–V7 全部 ✅
- [ ] P0 用例全部通过
- [ ] 交互可达性矩阵 P0 行全部 ✅（无 ⬜）
- [ ] `validate_routes.py` 通过
- [ ] `validate_matrix.py` 通过
- [ ] `build_nav_artifacts.mjs` 无 ERROR
- [ ] `npx tsc --noEmit` 无错误
- [ ] 数据重置测试通过

---

## 附录 A：WechatV2 已知偏差（参考实现的缺陷）

`apps/WechatV2/` 是本 Playbook 的参考实现，但它有以下已知偏差，新 App **不要沿用**：

| 问题 | WechatV2 的做法（错） | 正确做法 |
|------|----------------------|---------|
| 状态栏安全区 | `<div style={{ height: 40 }} />` 内联样式 | `<div className="h-10" />` Tailwind |
| navigation.ts | 自写了简化版 | 复制 apps/Wechat/navigation.ts |
| 手势事件 | `onTouchStart/Move/End` | `onPointerDown/Move/Up` |
| 时间 API | 未限制 `Date.now()` | 统一用 `TimeService.now()` |
| NavigationHandler | 未用 `useAppNavigationHandler` | 见 Step 6 模板 |
| data-action | 部分元素有，部分没有 | 所有可交互元素必须有 |

---

## 附录 B：文档位置速查

| 文档 | 路径 |
|------|------|
| 添加 App 教程 | `trial_apps/mobilegym/docs/guides/add-an-app.md` |
| App 模块合同（正式规范） | `trial_apps/mobilegym/docs/platform/app/module-contract.md` |
| 导航 FSM 语法 | `trial_apps/mobilegym/docs/platform/navigation/declaration.md` |
| 状态模型 | `trial_apps/mobilegym/docs/platform/state/model.md` |
| OS 服务（时间/位置/网络）| `trial_apps/mobilegym/docs/platform/os/services/` |
| 键盘/输入合同 | `trial_apps/mobilegym/docs/platform/os/services/input-keyboard.md` |
| 添加任务（Benchmark） | `trial_apps/mobilegym/docs/guides/add-a-task.md` |
| 已有 App 参考实现 | `trial_apps/mobilegym/apps/Wechat/`（最完整）|

---

## 附录 C：常见坑速查

| 症状 | 原因 | 解决 |
|------|------|------|
| TopBar 不可见/按钮点不了 | 缺少状态栏安全区 spacer | AppShell 加 `<div className="h-10" />` |
| 修改数据但页面没变 | localStorage 旧数据覆盖 | 递增 `DATA_VERSION` |
| JSON parse error，中文乱码 | PowerShell 读写 UTF-8 损坏 | 用 Python 脚本生成 JSON |
| 图片 404，显示字母占位 | 资源路径格式错误 | `/@app-assets/<AppName>/<relPath>` |
| 返回键无效 | 未用 `useAppNavigationHandler` | 按 Step 6 接入 |
| 滑动手势在 Playwright 失效 | 用了 touch 事件 | 改用 pointer 事件 |
| 键盘弹起时 TabBar 遮挡输入框 | 缺 `data-hide-on-keyboard` | 给 TabBar 容器加属性 |
| 组件不响应状态更新 | 用了 `store.getState()` | 用 `useStore(s => s.xxx)` |
