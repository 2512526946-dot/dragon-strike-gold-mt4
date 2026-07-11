---
name: jlgo
description: Read-only project router and planner for the 巨龙出击 repository. Use when the user says continue, next step, status, plan, or asks what to do. Inspect Git and repository evidence, choose exactly one next action, and produce the next command or work order. Never modify files, branches, commits, tags, or the working tree.
---

# 巨龙推进

1. 先读取仓库根目录 `AGENTS.md`。
2. 只读检查工作区、当前分支、`main`、`origin/main`、最近 commits、tags、当前分支相对 `main`、可见 work branches，以及相关 ADR、协议、生产代码和测试基线。
3. 网络可用时可以运行 `git fetch origin --prune --tags`，但不得 checkout、创建或移动分支。
4. 对每个候选工作分支使用 Git ancestry 证据分类，推荐运行：

   ```bash
   git merge-base --is-ancestor <branch-tip> main
   git rev-list --count main..<branch>
   ```

   - 分支 tip 已是 `main` 的 ancestor：视为已合并历史分支并忽略。
   - `main..<branch>` commit 数为 0：视为已合并或没有独立工作并忽略。
   - 只有分支仍包含 `main` 中不存在的 commit，才视为 active unmerged work branch。
   - 已保留但已经合并的 G143、G148、WF-1 等历史工作分支，不得阻止新工单规划。
   - 无法确认 ancestry 时，将状态判定为 checkpoint 异常并停止，不得猜测。
5. 明确区分 policy 已写入 `AGENTS.md`、contract 已定义、tests 已存在、production code 已实现、capability 已接入和 capability 已启用。
6. 不得因为政策已经声明，就声称对应 Gate 或执行能力已经实现。
7. 继续区分 production implementation、tests only、docs only 和 not implemented。
8. 按以下优先级决定唯一下一步：
   - 工作区不干净或 checkpoint 异常：停止。
   - 存在 active unmerged work branch：只建议 review、修订或 merge，不生成新开发工单。
   - 位于干净 `main` 且无待处理分支：规划唯一下一开发工单。
   - 只有用户明确批准 tag 时才建议 release。
9. 下一开发任务需要 Pro 时，输出模型要求后停止，不在低强度下设计关键架构。
10. 每次只输出一个下一动作，不修改文件，不创建分支，不 commit、push、merge 或 tag。

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

## 下一步操作卡

固定输出之后必须追加 `【下一步操作卡】`：

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

- 规划开发工单时，`下一 Skill` 写 `$jl-develop`。
- 规划验收工单时，`下一 Skill` 写 `$jl-review`。
- 规划 fast-forward 合并工单时，`下一 Skill` 写 `$jl-merge`。
- 规划已明确批准的 tag-only release 时，`下一 Skill` 写 `$jl-release`。
- checkpoint 异常、工作区不干净、无安全下一步或应停止时，`下一 Skill` 写 `无`。
- 完整指令必须只调用一个 Skill，并要求下一轮结束时继续输出新的【下一步操作卡】。
- 不得通过完整指令自动越过用户批准，不得自动 merge、tag 或进入下一工单。
