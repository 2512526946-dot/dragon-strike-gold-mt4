---
name: jl-develop
description: Execute exactly one explicitly approved 巨龙出击 development or revision work order. Use only when the user has supplied or approved a complete scoped work order. Never merge main, create a tag, or continue into another work order.
---

# 巨龙开发

1. 先读取仓库根目录 `AGENTS.md`。
2. 确认用户已明确批准唯一工单。
3. 确认工单至少包含任务名称、main checkpoint、目标分支、允许修改文件、禁止范围、验证命令和提交要求。
4. 工单不完整时停止并指向 `$jlgo`。
5. 判断工单要求从 `main` 新建分支，还是继续现有修订分支。
6. 修订工单明确继续原分支时，不得因为分支存在而停止。
7. 只修改工单允许的范围，并保留所有无关用户改动。
8. 依次运行 targeted tests、相关 regression、必要的 full tests 和 `git diff --check`。
9. 按工单要求 commit，并 push 工作分支。
10. 不 merge，不 tag，不自动 review，不进入下一工单。
11. 只汇报当前工单结果，并建议用户显式调用 `$jl-review`。
