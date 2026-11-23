# 有 XML 才跑端到端

日期：2026-09-21。合作方微信原话：

> 没有的就不用测端到端  
> 只测有 xml 的就行  
> 没有的都是直接模型判断

## 怎么执行

| 测试集里有没有 `.xml` | 做什么 |
|---|---|
| 有 | 真机端到端：点到同类页 → `ux-detect --mode=slide`（截图 + dump + layout + 滑动） |
| 没有 | **不**连真机跑 layout/滑动。这条交给检测模型直接判断，run-log 写「无 XML，不端到端」 |

XML 目前全在 `测试集/整理/*_xml_normal/<app>/g0x/*.xml`。  
`image_truncated` 正例 **150 条都没有 XML**（含美团 g04/g05 酒店筛选项）。不要继续按 truncated 队列硬测。

查法：同 app / 同组 / 同屏在 `*_xml_normal/` 下有 `.xml` 才端到端。catalog 里 `xml_rel == null` 就是没有。

入口也会指到这里：根目录 `README.md`、`AGENTS.md`、`docs/给AI.md`、`docs/给人看.md`、`docs/合作与测试队列.md`。
