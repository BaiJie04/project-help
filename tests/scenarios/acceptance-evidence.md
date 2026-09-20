# Scenario: Complete Work with Acceptance Evidence

## Runtime Capabilities

- File read: yes
- File write: yes
- Python: yes
- Git: available
- Skill references: available

## User Prompt

“T-004 已修复，桌面和 360px 手机宽度都验证过长代码块不会撑开页面。”

## Expected Behavior

1. 读取 T-004 的验收标准。
2. 将用户提供的桌面和移动端验证映射到具体标准。
3. 仅把有证据的标准改为 `met`。
4. 如果所有标准满足，写入 `done`、`completed_at` 和 `completion_note`。
5. 如果仍有标准未满足，保持非完成状态，或要求用户明确接受 `completion_exception`。
6. 获得确认后写入并建议 `project(update): complete T-004`。

## State Assertions

- T-004 只有在全部标准满足时才为 `done`。
- `completed_at` 是有效 UTC 时间戳。
- `completion_note` 包含桌面和移动端证据。
- 存在未满足标准时 `completion_exception` 为 `true`。
- revision 增加 `1`。

## Failure Conditions

- 仅因用户说“已修复”就把所有标准设为 `met`。
- 缺少 `completed_at` 或 `completion_note`。
- 未明确接受例外就设置 `completion_exception`。
- 静默忽略未满足的验收标准。

