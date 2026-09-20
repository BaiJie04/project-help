# Scenario: Chat-Only State Update

## Runtime Capabilities

- File read: no
- File write: no
- Python: no
- Git: no
- Skill references: unavailable; user supplies the compact contract and current JSON

## User Prompt

“把 T-002 设为 in_progress。以下是当前 project.json：<完整 JSON>”

## Expected Behavior

1. 明确说明当前是 Chat Mode，无法写入文件、执行脚本或操作 Git。
2. 校验用户提供的完整当前 JSON。
3. 只修改 T-002 状态、相关 `updated_at` 和 `revision`。
4. 返回完整候选 `project.json`，不是只返回差异片段。
5. 提供可自行保存的完整 JSON、人类可读摘要、建议 Git 命令和下一步行动。
6. 明确说明没有实际修改文件或提交。

## State Assertions

- 候选 JSON 保留所有未修改实体。
- T-002 状态为 `in_progress`。
- revision 增加 `1`。
- 用户提供的输入不是完整 JSON 时，不生成不安全的候选状态。

## Failure Conditions

- 声称已经保存文件或提交 Git。
- 返回省略上下文的 JSON 片段。
- 重复或丢弃未修改实体。
- revision 保持不变或增加超过 `1`。
