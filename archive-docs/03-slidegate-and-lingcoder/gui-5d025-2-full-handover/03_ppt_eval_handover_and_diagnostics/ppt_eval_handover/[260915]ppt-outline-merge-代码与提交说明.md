# ppt-outline-merge 合并与提交说明

## 合并关系

测试分支为 `test/ppt-outline-merge`，以 `dev/wangbo/ppt-outline-template` 为基础，合入 `dev/tzk/ppt-v2`。

原始 merge commit：`cc8c1e010b3c6184b353fd34dd9b06a35959a8c4`。

本次后续改造的目标是让 `outline.md` 成为唯一的大纲事实来源。流程只解析、预检和传递 `outline.md`，不再生成或依赖 `outline_contract.json`、`outline_source.txt`、`outline_selected.txt`，也不再使用旧的 `source_sha256`、`check_contract` 入口。

## 当前代码状态

仓库位置：`/home/gui-5d025-2/zyy/aipptx-templates`。

当前 follow-up 改动集中在以下实际目录：

```text
skills/agent-3.0/ppt-maker/
skills/agent-3.0/ppt-no-template-mode/
skills/agent-3.0/ppt-template-mode/
skills/agent-3.0/ppt-creative-mode/
```

注意：目录名是 `ppt-no-template-mode`，不是 `ppt-no-template`。

旧契约检查：

```bash
git grep -n -E \
  'outline_contract|outline_source|outline_selected|source_sha256|check_contract' \
  -- skills/agent-3.0
```

无输出表示没有旧契约引用，是正常结果。

## 测试步骤

```bash
cd ~/zyy/aipptx-templates

python3 -m pytest -q \
  skills/agent-3.0/tests/ppt-maker/test_user_outline.py \
  skills/agent-3.0/tests/ppt-maker/test_merged_outline_pipeline.py \
  skills/agent-3.0/tests/ppt-no-template-mode/test_outline_render.py
```

重点测试通过后，再运行：

```bash
python3 -m pytest -q skills/agent-3.0/tests
git diff --check
git diff --stat
```

## 提交步骤

先查看状态：

```bash
git status --short --branch
```

只暂存本次改造涉及的目录，不使用 `git add .`：

```bash
git add -A \
  skills/agent-3.0/ppt-maker \
  skills/agent-3.0/ppt-no-template-mode \
  skills/agent-3.0/ppt-template-mode \
  skills/agent-3.0/ppt-creative-mode
```

检查暂存区：

```bash
git diff --cached --check
git diff --cached --stat
git diff --cached --name-status
```

确认删除的旧测试、新增的新测试以及代码改动都正确后，创建 follow-up commit：

```bash
git commit -m "refactor(ppt): make outline.md the sole outline contract"
```

提交后验证：

```bash
git status --short --branch
git show --stat --oneline HEAD
git log --graph --oneline --decorate -5
```

## 推送

当前本地分支的 upstream 指向 `origin/dev/wangbo/ppt-outline-template`，所以不要直接运行 `git push`。如果需要推送到测试分支，应显式指定：

```bash
git push -u origin HEAD:refs/heads/test/ppt-outline-merge
```
