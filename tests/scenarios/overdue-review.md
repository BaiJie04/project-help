# Scenario: Review an Overdue Iteration

## Runtime Capabilities

- File read: yes
- File write: yes
- Python: yes
- Git: available
- Skill references: available

## User Prompt

“检查一下当前迭代，为什么进度看起来停住了？”

## Expected Behavior

1. 只读分析当前迭代、逾期工作项、进行中工作、阻塞和风险。
2. 区分事实与建议，例如报告 I-001 已超过 `end_date`，而不是直接宣称项目失败。
3. 给出最多三个下一步行动及其优先级理由。
4. 默认保持 revision 不变。
5. 只有用户接受建议后，才进入 Update 工作流写入候选状态。

## State Assertions

- Review 响应阶段 `revision` 不变。
- 没有未经确认修改 `project.json` 或 `PROJECT.md`。
- 分析至少覆盖逾期项、阻塞、风险和下一步行动。

## Failure Conditions

- 审查期间自动修改任务状态。
- 只给宽泛鼓励，不指出具体停滞项。
- 把推测当作已发生的事实。
- 自动提交建议性变更。

