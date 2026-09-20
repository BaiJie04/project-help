# Scenario: Close a Project with a Retrospective

## Runtime Capabilities

- File read: yes
- File write: yes
- Python: yes
- Git: available
- Skill references: available

## User Prompt

“第一版可以结束了。搜索优化没做完，留到以后，其他目标都达到了。”

## Expected Behavior

1. 汇总已完成、未完成和取消的工作项。
2. 对比成功标准，记录搜索优化例外。
3. 记录 outcome、未完成事项、经验教训和后续建议。
4. 将项目或里程碑设为合适的完成状态，不删除未完成工作。
5. 展示完整 closure 状态并请求确认。
6. 写入后建议 `project(close): complete first release`。

## State Assertions

- 项目或里程碑进入 `completed`。
- 未完成搜索工作仍有明确状态和后续建议。
- closure 信息完整记录。
- revision 增加 `1`。

## Failure Conditions

- 将未完成工作直接删除。
- 把未完成工作错误标为 `done`。
- 没有经验教训或后续建议。
- 自动 push。

