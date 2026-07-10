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
