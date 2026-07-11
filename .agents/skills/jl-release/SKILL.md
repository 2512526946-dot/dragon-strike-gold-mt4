---
name: jl-release
description: Create one explicitly approved annotated milestone tag for 巨龙出击 after validating a clean synchronized main branch. Use only when the user specifies and approves the exact tag. Never develop features, merge branches, or invent a tag.
---

# 巨龙发布

1. 先读取仓库根目录 `AGENTS.md`。
2. 确认用户明确指定并批准了唯一 tag 名；不得创造或替换 tag。
3. 确认当前位于干净 `main`，且 `main` 与 `origin/main` 一致。
4. 确认本地和远端均不存在同名 tag。
5. 运行该阶段要求的完整测试。
6. 创建用户批准的 annotated tag，并确认它指向预期 commit。
7. push tag，并验证远端 tag 指向。
8. 不修改业务代码，不 merge，不规划或进入下一工单。汇报后停止。

## 下一步操作卡

发布工单结束后必须输出：

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

- annotated tag 创建、push 并验证成功后，`下一 Skill` 写 `$jlgo`。
- tag 已存在、checkpoint 异常、测试失败、push 失败或工作区不干净时，`下一 Skill` 写 `无`，并说明必须先处理阻断。
- 完整指令必须要求 `$jlgo` 只读判断唯一下一步，不得直接进入开发、merge 或下一业务工单。
- 完整指令必须只调用一个 Skill，并要求下一轮结束时继续输出新的【下一步操作卡】。
- 不得通过操作卡自动调用 `$jlgo`；必须等待用户显式批准。
