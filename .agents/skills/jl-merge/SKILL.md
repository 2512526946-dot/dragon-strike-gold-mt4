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
10. 最终汇报末尾必须追加 `【下一步操作卡】`。

## 下一步操作卡

合并工单结束后必须输出：

```text
【下一步操作卡】
1. 当前状态：
2. 下一步要做什么：
3. 是否需要用户显式批准：
4. 模型要求：
5. 下一 Skill：
6. 可直接复制发送给 Codex 的完整指令：
```

映射规则：

- fast-forward 合并、验证并 push `main` 成功后，`下一 Skill` 写 `$jlgo`。
- 合并失败、测试失败、push 失败、checkpoint 异常或工作区不干净时，`下一 Skill` 写 `无`，并说明必须先处理阻断。
- 完整指令必须要求 `$jlgo` 只读判断唯一下一步，不得直接进入开发、tag 或下一业务工单。
- 完整指令必须只调用一个 Skill，并要求下一轮结束时继续输出新的【下一步操作卡】。
- 不得通过操作卡自动调用 `$jlgo`；必须等待用户显式批准。
