# ArkUI Layout-first 字形裁切验证报告

- Verifier: `1.5.0-unbound-overlay-empty-input-20260805`
- Overall: **ok**
- Result: `all_candidates_filtered`
- 说明：所有模型候选均被布局树排除为非文本截断。
- 总问题数：**1**
- 真截断：**0**
- 非文本截断：**1**
- 无法静态确定：**0**

## 结果概览

| Issue | 文本/槽位 | Binding | Verdict | Subtype | Confidence | 下一步 |
|---|---|---|---|---|---|---|
| `issue_1` | 7天无理由退货 · 运费险 · 48小时发货 | `structural_text` | `not_truncation` | `continuous_scroll_glyph_clipping_recoverable` | `high` | `do_not_report_as_text_truncation` |

## issue_1

- Verdict: `not_truncation`
- Subtype: `continuous_scroll_glyph_clipping_recoverable`
- Confidence: `high`
- Rationale: 模型 bbox 是包含被裁切文字的文本区域。该区域中的裁剪 owner 位于同轴连续滚动视口边界；滚动会移动整个 Text，使被切到的字符完整进入视口，因此不是真实截断。
- Recommended next step: `do_not_report_as_text_truncation`

```json
{
  "definition": "visible_glyph_partial_clipping",
  "model_bbox_contract": "bbox localizes a suspected clipped text region; it may contain multiple Text nodes or an entire clipped line",
  "binding_kind": "structural_text",
  "target": {
    "node_index": 76,
    "type": "Text",
    "identifier": "1683",
    "accessibilityId": "1683",
    "id": "",
    "key": "",
    "text": "7天无理由退货 · 运费险 · 48小时发货",
    "bounds": [
      384,
      2459,
      1158,
      2473
    ],
    "orig_bounds": [
      384,
      2459,
      1158,
      2573
    ],
    "hierarchy": "ROOT30,0,0,1,0,1,0,0,0,0,0,4,0,0,0,2,0,1,0,0",
    "scrollable": false,
    "clip": false,
    "signature": {
      "type": "Text",
      "text": "7天无理由退货 · 运费险 · 48小时发货",
      "id": "",
      "key": "",
      "identifier": "1683",
      "accessibilityId": "1683",
      "hierarchy": "ROOT30,0,0,1,0,1,0,0,0,0,0,4,0,0,0,2,0,1,0,0",
      "hostWindowId": "30",
      "bundleName": "com.joker.coolmall",
      "pagePath": "view/EntryPage",
      "ancestor_identifiers": [
        "Row:ibest_cell_right_1737",
        "Column:ibest_cell_1737"
      ],
      "type_path": [
        "Stack",
        "Column",
        "List",
        "ListItem",
        "Column",
        "Column",
        "Column",
        "Column",
        "Row",
        "Row",
        "Row",
        "Text"
      ]
    }
  },
  "model_region_analysis": {
    "enabled": true,
    "model_bbox_contract": "bbox localizes a suspected clipped text region; it may contain multiple Text nodes or an entire clipped line",
    "accepted": true,
    "ambiguous": false,
    "region_text_candidates": [
      {
        "node_index": 76,
        "type": "Text",
        "text": "7天无理由退货 · 运费险 · 48小时发货",
        "id": "",
        "key": "",
        "bounds": [
          384,
          2459,
          1158,
          2473
        ],
        "orig_bounds": [
          384,
          2459,
          1158,
          2573
        ],
        "geometry_score": 5.2558,
        "query_coverage": 0.1422,
        "node_coverage": 1,
        "iou": 0.1422,
        "dynamic_slot_node_index": null,
        "hidden_extents_px": {
          "left": 0,
          "right": 0,
          "top": 0,
          "bottom": 100
        },
        "single_full_visible_glyph_gate": false,
        "directional_boundary_evidence": [
          {
            "direction": "bottom",
            "hidden_extent_px": 100,
            "score": 96.6778,
            "boundary": {
              "node_index": 11,
              "depth": 8,
              "component_type": "List",
              "identifier": "1357",
              "bounds": [
                0,
                137,
                1256,
                2473
              ],
              "direction": "bottom",
              "axis": "vertical",
              "edge_coordinate": 2473,
              "edge_distance_to_visible": 0,
              "overflow_extent": 100,
              "clip": true,
              "scrollable": true,
              "behavior": "continuous_content_scroll",
              "inferred_axis": "vertical",
              "axis_source": "geometry:content_overflow",
              "same_axis": true,
              "kind": "continuous_scroll_viewport",
              "bbox_edge_distance_to_boundary": 0,
              "bbox_crosses_boundary": true,
              "bbox_alignment_tolerance_px": 6,
              "bbox_aligned": true,
              "required_layout_overflow": true
            },
            "boundary_candidates": [
              {
                "node_index": 69,
                "depth": 3,
                "component_type": "Column",
                "identifier": "ibest_cell_1737",
                "bounds": [
                  42,
                  2417,
                  1214,
                  2473
                ],
                "direction": "bottom",
                "axis": "vertical",
                "edge_coordinate": 2473,
                "edge_distance_to_visible": 0,
                "overflow_extent": 100,
                "clip": true,
                "scrollable": false,
                "behavior": "unknown",
                "inferred_axis": null,
                "axis_source": null,
                "same_axis": false,
                "kind": "local_clip",
                "bbox_edge_distance_to_boundary": 0,
                "bbox_crosses_boundary": true,
                "bbox_alignment_tolerance_px": 6,
                "bbox_aligned": true,
                "required_layout_overflow": true
              },
              {
                "node_index": 50,
                "depth": 4,
                "component_type": "Column",
                "identifier": "1633",
                "bounds": [
                  42,
                  2122,
                  1214,
                  2473
                ],
                "direction": "bottom",
                "axis": "vertical",
                "edge_coordinate": 2473,
                "edge_distance_to_visible": 0,
                "overflow_extent": 100,
                "clip": true,
                "scrollable": false,
                "behavior": "unknown",
                "inferred_axis": null,
                "axis_source": null,
                "same_axis": false,
                "kind": "local_clip",
                "bbox_edge_distance_to_boundary": 0,
                "bbox_crosses_boundary": true,
                "bbox_alignment_tolerance_px": 6,
                "bbox_aligned": true,
                "required_layout_overflow": true
              },
              {
                "node_index": 11,
                "depth": 8,
                "component_type": "List",
                "identifier": "1357",
                "bounds": [
                  0,
                  137,
                  1256,
                  2473
                ],
                "direction": "bottom",
                "axis": "vertical",
                "edge_coordinate": 2473,
                "edge_distance_to_visible": 0,
                "overflow_extent": 100,
                "clip": true,
                "scrollable": true,
                "behavior": "continuous_content_scroll",
                "inferred_axis": "vertical",
                "axis_source": "geometry:content_overflow",
                "same_axis": true,
                "kind": "continuous_scroll_viewport",
                "bbox_edge_distance_to_boundary": 0,
                "bbox_crosses_boundary": true,
                "bbox_alignment_tolerance_px": 6,
                "bbox_aligned": true,
                "required_layout_overflow": true
              }
            ],
            "rejected_as_single_full_visible_glyph": false
          }
        ]
      },
      {
        "node_index": 73,
        "type": "Text",
        "text": "服务",
        "id": "",
        "key": "",
        "bounds": [
          98,
          2459,
          378,
          2473
        ],
        "orig_bounds": [
          98,
          2459,
          378,
          2516
        ],
        "geometry_score": 4.488,
        "query_coverage": 0.0515,
        "node_coverage": 1,
        "iou": 0.0515,
        "dynamic_slot_node_index": null,
        "hidden_extents_px": {
          "left": 0,
          "right": 0,
          "top": 0,
          "bottom": 43
        },
        "single_full_visible_glyph_gate": false,
        "directional_boundary_evidence": [
          {
            "direction": "bottom",
            "hidden_extent_px": 43,
            "score": 93.7521,
            "boundary": {
              "node_index": 11,
              "depth": 8,
              "component_type": "List",
              "identifier": "1357",
              "bounds": [
                0,
                137,
                1256,
                2473
              ],
              "direction": "bottom",
              "axis": "vertical",
              "edge_coordinate": 2473,
              "edge_distance_to_visible": 0,
              "overflow_extent": 43,
              "clip": true,
              "scrollable": true,
              "behavior": "continuous_content_scroll",
              "inferred_axis": "vertical",
              "axis_source": "geometry:content_overflow",
              "same_axis": true,
              "kind": "continuous_scroll_viewport",
              "bbox_edge_distance_to_boundary": 0,
              "bbox_crosses_boundary": true,
              "bbox_alignment_tolerance_px": 6,
              "bbox_aligned": true,
              "required_layout_overflow": true
            },
            "boundary_candidates": [
              {
                "node_index": 69,
                "depth": 3,
                "component_type": "Column",
                "identifier": "ibest_cell_1737",
                "bounds": [
                  42,
                  2417,
                  1214,
                  2473
                ],
                "direction": "bottom",
                "axis": "vertical",
                "edge_coordinate": 2473,
                "edge_distance_to_visible": 0,
                "overflow_extent": 43,
                "clip": true,
                "scrollable": false,
                "behavior": "unknown",
                "inferred_axis": null,
                "axis_source": null,
                "same_axis": false,
                "kind": "local_clip",
                "bbox_edge_distance_to_boundary": 0,
                "bbox_crosses_boundary": true,
                "bbox_alignment_tolerance_px": 6,
                "bbox_aligned": true,
                "required_layout_overflow": true
              },
              {
                "node_index": 50,
                "depth": 4,
                "component_type": "Column",
                "identifier": "1633",
                "bounds": [
                  42,
                  2122,
                  1214,
                  2473
                ],
                "direction": "bottom",
                "axis": "vertical",
                "edge_coordinate": 2473,
                "edge_distance_to_visible": 0,
                "overflow_extent": 43,
                "clip": true,
                "scrollable": false,
                "behavior": "unknown",
                "inferred_axis": null,
                "axis_source": null,
                "same_axis": false,
                "kind": "local_clip",
                "bbox_edge_distance_to_boundary": 0,
                "bbox_crosses_boundary": true,
                "bbox_alignment_tolerance_px": 6,
                "bbox_aligned": true,
                "required_layout_overflow": true
              },
              {
                "node_index": 11,
                "depth": 8,
                "component_type": "List",
                "identifier": "1357",
                "bounds": [
                  0,
                  137,
                  1256,
                  2473
                ],
                "direction": "bottom",
                "axis": "vertical",
                "edge_coordinate": 2473,
                "edge_distance_to_visible": 0,
                "overflow_extent": 43,
                "clip": true,
                "scrollable": true,
                "behavior": "continuous_content_scroll",
                "inferred_axis": "vertical",
                "axis_source": "geometry:content_overflow",
                "same_axis": true,
                "kind": "continuous_scroll_viewport",
                "bbox_edge_distance_to_boundary": 0,
                "bbox_crosses_boundary": true,
                "bbox_alignment_tolerance_px": 6,
                "bbox_aligned": true,
                "required_layout_overflow": true
              }
            ],
            "rejected_as_single_full_visible_glyph": false
          }
        ]
      }
    ],
    "owner_candidates": [
      {
        "node_index": 76,
        "type": "Text",
        "text": "7天无理由退货 · 运费险 · 48小时发货",
        "id": "",
        "key": "",
        "bounds": [
          384,
          2459,
          1158,
          2473
        ],
        "orig_bounds": [
          384,
          2459,
          1158,
          2573
        ],
        "geometry_score": 5.2558,
        "query_coverage": 0.1422,
        "node_coverage": 1,
        "iou": 0.1422,
        "dynamic_slot_node_index": null,
        "direction": "bottom",
        "hidden_extent_px": 100,
        "owner_score": 96.6778,
        "boundary": {
          "node_index": 11,
          "depth": 8,
          "component_type": "List",
          "identifier": "1357",
          "bounds": [
            0,
            137,
            1256,
            2473
          ],
          "direction": "bottom",
          "axis": "vertical",
          "edge_coordinate": 2473,
          "edge_distance_to_visible": 0,
          "overflow_extent": 100,
          "clip": true,
          "scrollable": true,
          "behavior": "continuous_content_scroll",
          "inferred_axis": "vertical",
          "axis_source": "geometry:content_overflow",
          "same_axis": true,
          "kind": "continuous_scroll_viewport",
          "bbox_edge_distance_to_boundary": 0,
          "bbox_crosses_boundary": true,
          "bbox_alignment_tolerance_px": 6,
          "bbox_aligned": true,
          "required_layout_overflow": true
        },
        "boundary_candidates": [
          {
            "node_index": 69,
            "depth": 3,
            "component_type": "Column",
            "identifier": "ibest_cell_1737",
            "bounds": [
              42,
              2417,
              1214,
              2473
            ],
            "direction": "bottom",
            "axis": "vertical",
            "edge_coordinate": 2473,
            "edge_distance_to_visible": 0,
            "overflow_extent": 100,
            "clip": true,
            "scrollable": false,
            "behavior": "unknown",
            "inferred_axis": null,
            "axis_source": null,
            "same_axis": false,
            "kind": "local_clip",
            "bbox_edge_distance_to_boundary": 0,
            "bbox_crosses_boundary": true,
            "bbox_alignment_tolerance_px": 6,
            "bbox_aligned": true,
            "required_layout_overflow": true
          },
          {
            "node_index": 50,
            "depth": 4,
            "component_type": "Column",
            "identifier": "1633",
            "bounds": [
              42,
              2122,
              1214,
              2473
            ],
            "direction": "bottom",
            "axis": "vertical",
            "edge_coordinate": 2473,
            "edge_distance_to_visible": 0,
            "overflow_extent": 100,
            "clip": true,
            "scrollable": false,
            "behavior": "unknown",
            "inferred_axis": null,
            "axis_source": null,
            "same_axis": false,
            "kind": "local_clip",
            "bbox_edge_distance_to_boundary": 0,
            "bbox_crosses_boundary": true,
            "bbox_alignment_tolerance_px": 6,
            "bbox_aligned": true,
            "required_layout_overflow": true
          },
          {
            "node_index": 11,
            "depth": 8,
            "component_type": "List",
            "identifier": "1357",
            "bounds": [
              0,
              137,
              1256,
              2473
            ],
            "direction": "bottom",
            "axis": "vertical",
            "edge_coordinate": 2473,
            "edge_distance_to_visible": 0,
            "overflow_extent": 100,
            "clip": true,
            "scrollable": true,
            "behavior": "continuous_content_scroll",
            "inferred_axis": "vertical",
            "axis_source": "geometry:content_overflow",
            "same_axis": true,
            "kind": "continuous_scroll_viewport",
            "bbox_edge_distance_to_boundary": 0,
            "bbox_crosses_boundary": true,
            "bbox_alignment_tolerance_px": 6,
            "bbox_aligned": true,
            "required_layout_overflow": true
          }
        ],
        "full_visible_glyph_gate": false
      },
      {
        "node_index": 73,
        "type": "Text",
        "text": "服务",
        "id": "",
        "key": "",
        "bounds": [
          98,
          2459,
          378,
          2473
        ],
        "orig_bounds": [
          98,
          2459,
          378,
          2516
        ],
        "geometry_score": 4.488,
        "query_coverage": 0.0515,
        "node_coverage": 1,
        "iou": 0.0515,
        "dynamic_slot_node_index": null,
        "direction": "bottom",
        "hidden_extent_px": 43,
        "owner_score": 93.7521,
        "boundary": {
          "node_index": 11,
          "depth": 8,
          "component_type": "List",
          "identifier": "1357",
          "bounds": [
            0,
            137,
            1256,
            2473
          ],
          "direction": "bottom",
          "axis": "vertical",
          "edge_coordinate": 2473,
          "edge_distance_to_visible": 0,
          "overflow_extent": 43,
          "clip": true,
          "scrollable": true,
          "behavior": "continuous_content_scroll",
          "inferred_axis": "vertical",
          "axis_source": "geometry:content_overflow",
          "same_axis": true,
          "kind": "continuous_scroll_viewport",
          "bbox_edge_distance_to_boundary": 0,
          "bbox_crosses_boundary": true,
          "bbox_alignment_tolerance_px": 6,
          "bbox_aligned": true,
          "required_layout_overflow": true
        },
        "boundary_candidates": [
          {
            "node_index": 69,
            "depth": 3,
            "component_type": "Column",
            "identifier": "ibest_cell_1737",
            "bounds": [
              42,
              2417,
              1214,
              2473
            ],
            "direction": "bottom",
            "axis": "vertical",
            "edge_coordinate": 2473,
            "edge_distance_to_visible": 0,
            "overflow_extent": 43,
            "clip": true,
            "scrollable": false,
            "behavior": "unknown",
            "inferred_axis": null,
            "axis_source": null,
            "same_axis": false,
            "kind": "local_clip",
            "bbox_edge_distance_to_boundary": 0,
            "bbox_crosses_boundary": true,
            "bbox_alignment_tolerance_px": 6,
            "bbox_aligned": true,
            "required_layout_overflow": true
          },
          {
            "node_index": 50,
            "depth": 4,
            "component_type": "Column",
            "identifier": "1633",
            "bounds": [
              42,
              2122,
              1214,
              2473
            ],
            "direction": "bottom",
            "axis": "vertical",
            "edge_coordinate": 2473,
            "edge_distance_to_visible": 0,
            "overflow_extent": 43,
            "clip": true,
            "scrollable": false,
            "behavior": "unknown",
            "inferred_axis": null,
            "axis_source": null,
            "same_axis": false,
            "kind": "local_clip",
            "bbox_edge_distance_to_boundary": 0,
            "bbox_crosses_boundary": true,
            "bbox_alignment_tolerance_px": 6,
            "bbox_aligned": true,
            "required_layout_overflow": true
          },
          {
            "node_index": 11,
            "depth": 8,
            "component_type": "List",
            "identifier": "1357",
            "bounds": [
              0,
              137,
              1256,
              2473
            ],
            "direction": "bottom",
            "axis": "vertical",
            "edge_coordinate": 2473,
            "edge_distance_to_visible": 0,
            "overflow_extent": 43,
            "clip": true,
            "scrollable": true,
            "behavior": "continuous_content_scroll",
            "inferred_axis": "vertical",
            "axis_source": "geometry:content_overflow",
            "same_axis": true,
            "kind": "continuous_scroll_viewport",
            "bbox_edge_distance_to_boundary": 0,
            "bbox_crosses_boundary": true,
            "bbox_alignment_tolerance_px": 6,
            "bbox_aligned": true,
            "required_layout_overflow": true
          }
        ],
        "full_visible_glyph_gate": false
      }
    ],
    "rejection_reasons": [],
    "owner_score_margin": 2.9257,
    "clipping_owner_node_index": 76,
    "clipping_owner_text": "7天无理由退货 · 运费险 · 48小时发货",
    "selected_direction": "bottom",
    "first_clipping_boundary": {
      "node_index": 11,
      "depth": 8,
      "component_type": "List",
      "identifier": "1357",
      "bounds": [
        0,
        137,
        1256,
        2473
      ],
      "direction": "bottom",
      "axis": "vertical",
      "edge_coordinate": 2473,
      "edge_distance_to_visible": 0,
      "overflow_extent": 100,
      "clip": true,
      "scrollable": true,
      "behavior": "continuous_content_scroll",
      "inferred_axis": "vertical",
      "axis_source": "geometry:content_overflow",
      "same_axis": true,
      "kind": "continuous_scroll_viewport",
      "bbox_edge_distance_to_boundary": 0,
      "bbox_crosses_boundary": true,
      "bbox_alignment_tolerance_px": 6,
      "bbox_aligned": true,
      "required_layout_overflow": true
    },
    "group_member_node_indexes": [
      76
    ],
    "group_member_texts": [
      "7天无理由退货 · 运费险 · 48小时发货"
    ],
    "original_geometric_best_node_index": 76,
    "selected_owner": {
      "node_index": 76,
      "type": "Text",
      "text": "7天无理由退货 · 运费险 · 48小时发货",
      "id": "",
      "key": "",
      "bounds": [
        384,
        2459,
        1158,
        2473
      ],
      "orig_bounds": [
        384,
        2459,
        1158,
        2573
      ],
      "geometry_score": 5.2558,
      "query_coverage": 0.1422,
      "node_coverage": 1,
      "iou": 0.1422,
      "dynamic_slot_node_index": null,
      "direction": "bottom",
      "hidden_extent_px": 100,
      "owner_score": 96.6778,
      "boundary": {
        "node_index": 11,
        "depth": 8,
        "component_type": "List",
        "identifier": "1357",
        "bounds": [
          0,
          137,
          1256,
          2473
        ],
        "direction": "bottom",
        "axis": "vertical",
        "edge_coordinate": 2473,
        "edge_distance_to_visible": 0,
        "overflow_extent": 100,
        "clip": true,
        "scrollable": true,
        "behavior": "continuous_content_scroll",
        "inferred_axis": "vertical",
        "axis_source": "geometry:content_overflow",
        "same_axis": true,
        "kind": "continuous_scroll_viewport",
        "bbox_edge_distance_to_boundary": 0,
        "bbox_crosses_boundary": true,
        "bbox_alignment_tolerance_px": 6,
        "bbox_aligned": true,
        "required_layout_overflow": true
      },
      "boundary_candidates": [
        {
          "node_index": 69,
          "depth": 3,
          "component_type": "Column",
          "identifier": "ibest_cell_1737",
          "bounds": [
            42,
            2417,
            1214,
            2473
          ],
          "direction": "bottom",
          "axis": "vertical",
          "edge_coordinate": 2473,
          "edge_distance_to_visible": 0,
          "overflow_extent": 100,
          "clip": true,
          "scrollable": false,
          "behavior": "unknown",
          "inferred_axis": null,
          "axis_source": null,
          "same_axis": false,
          "kind": "local_clip",
          "bbox_edge_distance_to_boundary": 0,
          "bbox_crosses_boundary": true,
          "bbox_alignment_tolerance_px": 6,
          "bbox_aligned": true,
          "required_layout_overflow": true
        },
        {
          "node_index": 50,
          "depth": 4,
          "component_type": "Column",
          "identifier": "1633",
          "bounds": [
            42,
            2122,
            1214,
            2473
          ],
          "direction": "bottom",
          "axis": "vertical",
          "edge_coordinate": 2473,
          "edge_distance_to_visible": 0,
          "overflow_extent": 100,
          "clip": true,
          "scrollable": false,
          "behavior": "unknown",
          "inferred_axis": null,
          "axis_source": null,
          "same_axis": false,
          "kind": "local_clip",
          "bbox_edge_distance_to_boundary": 0,
          "bbox_crosses_boundary": true,
          "bbox_alignment_tolerance_px": 6,
          "bbox_aligned": true,
          "required_layout_overflow": true
        },
        {
          "node_index": 11,
          "depth": 8,
          "component_type": "List",
          "identifier": "1357",
          "bounds": [
            0,
            137,
            1256,
            2473
          ],
          "direction": "bottom",
          "axis": "vertical",
          "edge_coordinate": 2473,
          "edge_distance_to_visible": 0,
          "overflow_extent": 100,
          "clip": true,
          "scrollable": true,
          "behavior": "continuous_content_scroll",
          "inferred_axis": "vertical",
          "axis_source": "geometry:content_overflow",
          "same_axis": true,
          "kind": "continuous_scroll_viewport",
          "bbox_edge_distance_to_boundary": 0,
          "bbox_crosses_boundary": true,
          "bbox_alignment_tolerance_px": 6,
          "bbox_aligned": true,
          "required_layout_overflow": true
        }
      ],
      "full_visible_glyph_gate": false
    }
  },
  "selected_glyph_clip_direction": "bottom",
  "first_clipping_boundary": {
    "node_index": 11,
    "depth": 8,
    "component_type": "List",
    "identifier": "1357",
    "bounds": [
      0,
      137,
      1256,
      2473
    ],
    "direction": "bottom",
    "axis": "vertical",
    "edge_coordinate": 2473,
    "edge_distance_to_visible": 0,
    "overflow_extent": 100,
    "clip": true,
    "scrollable": true,
    "behavior": "continuous_content_scroll",
    "inferred_axis": "vertical",
    "axis_source": "geometry:content_overflow",
    "same_axis": true,
    "kind": "continuous_scroll_viewport",
    "bbox_edge_distance_to_boundary": 0,
    "bbox_crosses_boundary": true,
    "bbox_alignment_tolerance_px": 6,
    "bbox_aligned": true,
    "required_layout_overflow": true
  },
  "overlay_candidates": [],
  "semantic_text_metadata_not_used_for_verdict": {
    "ellipsis_visible": false,
    "original_text": "7天无理由退货 · 运费险 · 48小时发货",
    "visible_text": "7天无理由退货 · 运费险 · 48小时发货",
    "extra_content": null,
    "original_differs": false,
    "content_differs": false,
    "max_lines": null,
    "overflow": null,
    "constraint_policy_present": false,
    "font_size": null,
    "semantic_content_evidence_used_for_verdict": false,
    "ignored_semantic_signals": []
  },
  "rich_layout": null,
  "scroll_capacity": {
    "status": "known",
    "toward_start": true,
    "toward_end": true,
    "evidence": {
      "viewport": [
        0,
        137,
        1256,
        2473
      ],
      "content_extent": [
        0,
        0,
        1256,
        2615
      ]
    }
  },
  "required_capacity": "toward_end",
  "required_capacity_available": true,
  "suggested_gesture": "up"
}
```
