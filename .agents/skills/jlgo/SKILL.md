---
name: jlgo
description: Read-only project router and planner for the 巨龙出击 repository. Use when the user says continue, next step, status, plan, or asks what to do. Inspect Git and repository evidence, choose exactly one next action, and produce the next command or work order. Never modify files, branches, commits, tags, or the working tree.
---

# 巨龙推进

1. 先读取仓库根目录 `AGENTS.md`。
2. 只读检查工作区、当前分支、`main`、`origin/main`、最近 commits、tags、当前分支相对 `main`、可见 work branches，以及相关 ADR、协议、生产代码和测试基线。
3. 网络可用时可以运行 `git fetch origin --prune --tags`，但不得 checkout、创建或移动分支。
4. 明确区分 production implementation、tests only、docs only 和 not implemented。
5. 按以下优先级决定唯一下一步：
   - 工作区不干净或 checkpoint 异常：停止。
   - 存在未合并 work branch：只建议 review、修订或 merge，不生成新开发工单。
   - 位于干净 `main` 且无待处理分支：规划唯一下一开发工单。
   - 只有用户明确批准 tag 时才建议 release。
6. 下一开发任务需要 Pro 时，输出模型要求后停止，不在低强度下设计关键架构。
7. 每次只输出一个下一动作，不修改文件，不创建分支，不 commit、push、merge 或 tag。

使用固定输出：

```text
【当前 checkpoint】
【已验证能力】
【尚未实现】
【状态判定】
【唯一下一步】
【模型要求】
【下一 Skill】
【一句执行指令】
```

下一步是开发时，额外输出 `【完整候选工单】`。

下一 Skill 只能是 `$jl-develop`、`$jl-review`、`$jl-merge` 或 `$jl-release`。输出后停止，不自动调用它。
