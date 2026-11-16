# 7 月回流：抽 query → 分类打标 → 上传

> 和 1–6 月同一套分类，不是脱敏模型打标。  
> 脱敏全量还在跑（`脱敏_05`），这是另一条线。

## 要对齐以前上传的两份

| 1–6 月 AOSS | 7 月对应 |
|---|---|
| `ppt-query-back/{202601..202606}/` 月度 query | `ppt-query-back/202607/july_202607_queries.jsonl` |
| `ppt-query-back/classify_ppt_query_20260629.jsonl`（Skill 6 维） | `july_202607_skill_classified.jsonl` |
| `ppt-query-back/deep_classify_ppt_query_20260702.jsonl`（深度 14 维） | `july_202607_deep_classified.jsonl` |

`plan_id` = 7 月 `session_id`。覆盖已成功下载的约 3.95 万，缺的 332 条不进包。

## 看进度

```bash
wc -l /data/xhx_return_data_2607/meta/july_classify/july_202607_queries.jsonl
cat /data/xhx_return_data_2607/meta/july_classify/skill_status.txt
cat /data/xhx_return_data_2607/meta/july_classify/deep_status.txt
```

脚本：`extract_july.py`、`classify_july.py`（TokenHub Claude，**额度已满 403**）、`classify_july_flash.py`（同一套提示词，走内网 208，等脱敏全量打完再跑，避免抢同一张卡）。

## 现在到哪了（2026-09-07 11:40）

- query **已抽完**：39,498 / 39,500 有文本（2 条空），`july_202607_queries.jsonl`
- Skill / 深度：Opus 5 已停（太贵，已标约 2k/1.5k 留下）。改走 **Sonnet 4.6**（`config.py` 那把 TokenHub 备用 key，不是额度耗尽的 env Claude）。`cat skill_status.txt` / `deep_status.txt`
- 上传：7.2 传附件用的同一套 ads-cli AK，**现在写什么都 403**（`202607/` 和 `attachments/` 都拒）。密钥还能列目录，不能写。不是 7 月路径写错。要管理员重开写权限或换 AK。
- 上传 `ppt-query-back/202607/`：同一套 ads-cli 对这个新前缀 **403 AccessDenied**，附件目录能写、月份目录不一定有权。要管理员开 `202607/` 或换 AK

## 上传

query / 两份分类 jsonl → `ppt-query-back/202607/`。脚本 `upload_july_jsonl.sh`。  
kernel 整包另说，先传 jsonl。
