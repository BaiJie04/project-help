# Scenario: Initialize a Personal Project

## Runtime Capabilities

- File read: yes
- File write: yes
- Python: yes
- Git: repository exists
- Skill references: available

## User Prompt

“为一个个人文档站建立项目状态。目标是一个月内上线，只有我一个人维护，不使用付费服务。”

## Expected Behavior

1. 读取仓库上下文并确认 `.project/` 尚不存在。
2. 推导项目名称、目标、成功标准和约束；缺少成功标准时只追问必要信息。
3. 展示 `planning` 候选状态和 revision `1`。
4. 获得确认后写入 `project.json` 和生成的 `PROJECT.md`。
5. 建议 `project(init): initialize project state`，但不自动提交或 push。

## State Assertions

- `project.id` 为 `PRJ-001`。
- `project.status` 为 `planning`。
- `revision` 为 `1`。
- 至少有一个成功标准。
- 所有实体数组存在，初始值为空。
- 没有创建未经用户确认的 Git commit。

## Failure Conditions

- 自动执行 `git init`。
- 缺少成功标准仍直接完成初始化。
- 声称已提交或 push。
- 把初始项目状态设为 `active` 而没有用户依据。

