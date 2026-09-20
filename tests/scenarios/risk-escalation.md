# Scenario: Escalate a Risk

## Runtime Capabilities

- File read: yes
- File write: yes
- Python: yes
- Git: available
- Skill references: available

## User Prompt

“R-001 的搜索方案升级为高影响风险，维护成本可能拖慢整个发布。”

## Expected Behavior

1. 读取 R-001 的现有概率、影响、状态和缓解措施。
2. 建议把 `impact` 提升为 `high`，并更新 `mitigation`。
3. 如果风险尚未关闭，保持或调整为 `open`/`mitigated` 中的合理状态。
4. 保留原始风险背景，不覆盖成只描述新结论的短句。
5. 展示候选状态并请求确认，写入后建议 `project(update): escalate R-001`。

## State Assertions

- R-001 的 `impact` 为 `high`。
- 风险背景和缓解措施仍然存在。
- R-001 与 `project.updated_at` 更新。
- revision 增加 `1`。

## Failure Conditions

- 删除原风险描述。
- 把风险直接标记为 `closed`。
- 未提供缓解措施就结束更新。
- 未确认就提交。

