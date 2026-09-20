# Scenario: Record a Blocked Work Item

## Runtime Capabilities

- File read: yes
- File write: yes
- Python: yes
- Git: available
- Skill references: available

## User Prompt

“T-003 现在做不了，必须先完成导航结构。”

## Expected Behavior

1. 读取 T-003 和依赖项 T-002 的当前状态。
2. 建议把 T-003 改为 `blocked`，并增加明确的 `blocked_reason`。
3. 如果 T-003 尚无 `depends_on: ["T-002"]`，提出依赖更新，但不得凭空创造不存在的 ID。
4. 展示 revision 加一后的完整候选状态并请求确认。
5. 写入后重新生成 `PROJECT.md`，建议 `project(update): block T-003`。

## State Assertions

- T-003 的状态为 `blocked`。
- `blocked_reason` 说明需要先完成导航结构。
- T-003 的 `updated_at` 更新。
- `project.updated_at` 更新。
- `revision` 只增加 `1`。

## Failure Conditions

- 将 T-003 改为 `cancelled` 或 `done`。
- 写入空 `blocked_reason`。
- 删除原任务上下文。
- 未获确认就写文件或提交。

