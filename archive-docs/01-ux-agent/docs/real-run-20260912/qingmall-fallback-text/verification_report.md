# ArkUI Layout-first 字形裁切验证报告

- Verifier: `1.5.0-unbound-overlay-empty-input-20260805`
- Overall: **unknown**
- Result: `static_verification_incomplete`
- 说明：没有确认真实截断，但仍有候选无法通过单帧布局树静态确定。
- 总问题数：**1**
- 真截断：**0**
- 非文本截断：**0**
- 无法静态确定：**1**

## 结果概览

| Issue | 文本/槽位 | Binding | Verdict | Subtype | Confidence | 下一步 |
|---|---|---|---|---|---|---|
| `issue_1` | - | `-` | `unknown` | `no_matching_component` | `low` | `check_bbox_space_or_recapture` |

## issue_1

- Verdict: `unknown`
- Subtype: `no_matching_component`
- Confidence: `low`
- Rationale: 模型 bbox 未能可靠映射到 Text 或局部动态文本槽位，也没有找到足以解释该区域的固定覆盖层证据。
- Recommended next step: `check_bbox_space_or_recapture`

```json
{
  "definition": "visible_glyph_partial_clipping",
  "target_match": {
    "status": "no_text_candidate",
    "confidence": "none",
    "ambiguous": false,
    "score": null,
    "margin": null,
    "candidates": []
  },
  "scroll_analysis": {
    "resolver_version": "2.3.0-minimal-gesture-20260725",
    "target": null,
    "requested_direction": null,
    "truncation_direction": null,
    "direction_inference": null,
    "decision": {
      "status": "no_matching_component",
      "confidence": null,
      "rationale": null,
      "primary_controller": null,
      "suggested_gesture": null
    },
    "primary_controller_axis": null,
    "primary_controller_behavior": null,
    "continuous_ancestor_signatures": [],
    "context_switch_ancestor_signatures": []
  },
  "unbound_overlay_filter_attempted": true
}
```
