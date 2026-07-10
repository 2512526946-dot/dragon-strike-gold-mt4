---
name: jl-merge
description: Fast-forward merge one explicitly approved and reviewed 巨龙出击 work branch into main, verify it, and push main. Use only after a PASS review and explicit user approval. Never develop features, rebase, force push, tag, or begin another work order.
---

# 巨龙合并

1. 先读取仓库根目录 `AGENTS.md`。
2. 确认最新 review 为 `PASS` 或明确可合并的 `PASS WITH FOLLOW-UP`、用户已明确批准合并、main checkpoint 明确、branch HEAD 明确；任一条件缺失时停止。
3. 确认工作区干净。
4. 核对 main、branch、commit 数、diff scope 和 merge-base。
5. 只允许运行 `git merge --ff-only`；禁止 rebase、merge commit 和 force push。
6. 合并后运行工单指定验证并确认结果。
7. push `main`，并确认 `origin/main` 指向预期 commit。
8. 不创建 tag，不删除分支，不进入下一开发工单。
9. 汇报后建议用户调用 `$jlgo`，然后停止。
