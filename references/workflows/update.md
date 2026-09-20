# Update 工作流

## 目标

记录项目执行中的真实状态变化，包括任务推进、阻塞、风险、决策和完成证据。

## 前置条件

- 读取当前状态并记录 revision。
- 确认用户描述的是已经发生或已批准的状态，而不是未经验证的推测。

## 执行步骤

1. 定位需要变化的工作项、风险或决策。
2. 说明建议的状态转换及原因。
3. 对 `blocked` 工作项写入具体 `blocked_reason`。
4. 对 `done` 工作项核对验收标准，写入 `completed_at` 和 `completion_note`。
5. 验收未全部满足时，仅在用户明确接受后设置 `completion_exception: true`。
6. 风险变化时更新 probability、impact、status 或 mitigation，保留背景。
7. 决策变化时记录 context、decision、rationale 和 consequences。
8. 更新 `project.updated_at`，其他被修改实体同步更新 `updated_at`。
9. 将 revision 加 `1`，展示候选变更并请求确认。
10. 写入后重新生成 `PROJECT.md`，建议 `project(update): <summary>` 提交。

## 状态转换保护

- 不得仅因代码、文件或对话存在就把任务标记为 `done`。
- 不得清除阻塞原因来让状态看起来正常。
- 不得静默改写已接受决策；需要替代时使用新的决策和 `supersedes`。

## Chat Mode

返回完整更新后的 JSON 和明确的证据说明。没有用户提供证据时，只提出变更建议，不伪造完成记录。

## 示例

用户请求：“T-003 已完成，搜索在桌面和手机上都能用。”

预期效果：检查 T-003 的验收标准；只有用户提供或可验证的证据满足全部标准时，才写入 `done`、`completed_at` 和 `completion_note`。

