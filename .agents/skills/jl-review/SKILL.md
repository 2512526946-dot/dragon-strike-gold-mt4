---
name: jl-review
description: Perform a strict read-only review of a 巨龙出击 branch or commit against main. Use after a development or revision branch is pushed. Inspect actual code, tests, Git scope, and safety boundaries. Never modify files, commit, merge, push, or tag.
---

# 巨龙验收

1. 先读取仓库根目录 `AGENTS.md`。
2. 只读审查当前 branch 或用户指定 commit 相对 `main` 的状态。
3. `/review` 可用时优先使用 Review against a base branch，并在当前任务运行，不使用 Detached review。
4. 检查实际 diff、生产代码、测试证明范围、修改范围、Git ancestry、安全语义、输出泄露、能力陈述和 ff-only 条件。
5. 必要时运行测试，但不得修改任何文件。
6. 只允许以下结论：`PASS`、`PASS WITH FOLLOW-UP`、`FIX BEFORE MERGE`、`NO-GO`。
7. 结论为 `FIX BEFORE MERGE` 时，列出精确 findings，生成最小修订工单，明确继续原分支，并将下一 Skill 指向 `$jl-develop`。
8. 结论为 `PASS` 或明确可合并的 `PASS WITH FOLLOW-UP` 时，给出 main、branch HEAD、修改范围和测试基线，生成 merge 工单，并将下一 Skill 指向 `$jl-merge`。
9. 不修改工作树，不 commit、push、merge 或 tag。输出结论后停止。
