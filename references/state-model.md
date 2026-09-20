# 项目状态契约

## 权威来源

受管理项目使用以下目录：

```text
.project/
|-- project.json
`-- PROJECT.md
```

`project.json` 是唯一事实源。`PROJECT.md` 是从 JSON 确定性生成的阅读视图。任何状态变更都必须先修改完整候选 JSON，再重新生成 Markdown。

## 顶层结构

```json
{
  "schema_version": 1,
  "revision": 1,
  "project": {},
  "milestones": [],
  "iterations": [],
  "work_items": [],
  "risks": [],
  "decisions": []
}
```

- `schema_version` 当前固定为 `1`。
- `revision` 从 `1` 开始，每次有效更新只增加 `1`。
- 所有时间戳使用 UTC 的 ISO 8601 格式，例如 `2026-09-20T00:00:00Z`。
- 候选状态的 `revision` 必须等于用户读取时的 revision 加一。

## ID 规则

- 项目：`PRJ-001`
- 里程碑：`M-001`
- 迭代：`I-001`
- 工作项：`T-001`
- 风险：`R-001`
- 决策：`D-001`
- 验收标准：`AC-001`

ID 在各自集合中唯一，永不复用。生成新 ID 时，取该命名空间现有最大数字后缀加一。

## 项目字段

`project` 必须包含：

- `id`、`name`、`summary`
- `status`
- `constraints` 字符串数组
- `success_criteria` 字符串数组
- `created_at`、`updated_at`

项目状态枚举：

- `planning`
- `active`
- `paused`
- `completed`
- `archived`

## 里程碑

必填字段：`id`、`title`、`description`、`status`、`created_at`、`updated_at`。

可选字段：`target_date`、`completed_at`、`completion_note`。

状态枚举：`planned`、`active`、`completed`、`cancelled`。

## 迭代

必填字段：`id`、`title`、`goal`、`status`、`created_at`、`updated_at`。

可选字段：`start_date`、`end_date`、`completed_at`、`completion_note`。

状态枚举：`planned`、`active`、`completed`、`cancelled`。

## 工作项

必填字段：

- `id`、`type`、`title`、`description`
- `status`、`priority`
- `acceptance_criteria`
- `created_at`、`updated_at`

可选字段：

- `milestone_id`、`iteration_id`、`parent_id`
- `depends_on`
- `due_date`、`blocked_reason`
- `completed_at`、`completion_note`、`completion_exception`

类型枚举：`epic`、`story`、`task`、`bug`、`spike`。

状态枚举：`backlog`、`ready`、`in_progress`、`blocked`、`review`、`done`、`cancelled`。

优先级枚举：`p0`、`p1`、`p2`、`p3`。

验收标准格式：

```json
{
  "id": "AC-001",
  "text": "可观察的验收结果",
  "status": "pending"
}
```

验收标准状态为 `pending` 或 `met`，同一工作项内 ID 唯一。

## 关系与约束

- `milestone_id` 必须引用现有里程碑。
- `iteration_id` 必须引用现有迭代。
- `parent_id` 必须引用现有工作项。
- `depends_on` 中的每个 ID 必须存在。
- 工作项不能依赖自身，依赖图不能出现环。
- `blocked` 工作项必须提供非空 `blocked_reason`。
- 决策的 `supersedes` 必须引用现有决策。

## 完成规则

工作项进入 `done` 时必须：

- 所有验收标准为 `met`；或者用户明确接受未满足项。
- 存在 `completed_at`。
- 存在 `completion_note`，记录验收证据或例外原因。
- 如果仍有 `pending` 验收标准，`completion_exception` 必须为 `true`。

非 `done` 工作项不能把 `completion_exception` 设为 `true`。

## 风险

必填字段：`id`、`title`、`description`、`probability`、`impact`、`status`、`mitigation`、`created_at`、`updated_at`。

- `probability` 和 `impact`：`low`、`medium`、`high`。
- `status`：`open`、`mitigated`、`accepted`、`closed`。

风险状态变化时保留原始背景和缓解措施，不删除历史语义。

## 决策

必填字段：`id`、`title`、`context`、`decision`、`rationale`、`consequences`、`status`、`created_at`、`updated_at`。

状态枚举：`proposed`、`accepted`、`rejected`、`superseded`。

被替代的决策保留原记录，通过新决策的 `supersedes` 建立关系。

## PROJECT.md 生成规则

生成内容必须包含：

1. 项目摘要与状态。
2. 成功标准与约束。
3. 当前里程碑与迭代。
4. 下一步行动。
5. 阻塞工作与活动风险。
6. 里程碑和迭代摘要。
7. 按优先级与规划顺序排列的工作项。
8. 已接受决策。

生成文件必须包含“不得直接编辑”的提示。无法执行脚本时，模型必须根据同一规则生成等价 Markdown。

