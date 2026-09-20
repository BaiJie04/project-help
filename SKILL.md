---
name: project-workflow
description: Use when managing a personal development project, including project initialization, backlog and iteration planning, task and risk updates, reviews, decisions, and closure.
---

# 项目工作流

用可移植、Git 友好的状态管理个人开发项目。自然语言说明和提示词使用中文；字段、枚举、ID、路径和 Git 提交类型使用英文。

## 核心契约

- `.project/project.json` 是唯一事实源。
- `.project/PROJECT.md` 由 JSON 生成，不得直接编辑。
- 每次有效状态变更将 `revision` 精确增加 `1`。
- 写入状态前必须获得用户确认。
- Git 提交需要单独确认，永不自动 push。
- 平台不支持某项能力时必须明确说明，并使用降级流程。

构造或校验状态前读取 [状态契约](references/state-model.md)。判断生命周期和质量规则时读取 [项目方法](references/method.md)。在不支持原生 Skill 的运行环境使用前读取 [跨平台协议](references/portability.md)。

## 检测能力

选择模式前确认：

- 是否能读取仓库文件。
- 是否能写入文件。
- 是否能执行 Python。
- 是否能读取和修改 Git 状态。
- 是否能加载本 Skill 及其 references。

不要根据产品名称猜测能力，只根据实际可访问性判断。能力未知时选择较低级模式。

## 选择模式

- **Skill Mode**：平台能发现本文件并读取 references。只加载当前操作需要的工作流。
- **File Mode**：平台不能发现 Skill，但能读取文件。将本文件作为系统提示词或自定义指令，并读取相关 references。
- **Chat Mode**：没有文件能力。要求用户提供完整当前 `project.json`，按同一状态契约返回完整候选 JSON。

详细规则见 [跨平台协议](references/portability.md)。

## 路由工作流

- 初始化项目：[Init](references/workflows/init.md)
- 规划里程碑、迭代和工作项：[Plan](references/workflows/plan.md)
- 更新任务、风险、决策或阻塞：[Update](references/workflows/update.md)
- 审查进度和风险：[Review](references/workflows/review.md)
- 关闭里程碑或项目：[Close](references/workflows/close.md)

用户没有指定操作时，选择能够满足请求的最小工作流。只有操作类型会实质改变写入内容时，才询问一个聚焦问题。

## 应用状态变更

1. 读取并校验 `.project/project.json`。
2. 只分析请求，不写入。
3. 说明建议的状态影响。
4. 获得用户确认。
5. 构造 `revision + 1` 的完整候选状态。
6. Python 可用时优先运行 `python scripts/project_state.py apply --expected-revision N --file CANDIDATE.json`。
7. 无法运行脚本时，手工执行状态契约中的全部校验，并在运行环境支持时原子写入。
8. 根据已接受的 JSON 重新生成 `PROJECT.md`。
9. 报告状态变更，并建议范围受限的 Git 提交。

[项目模板](templates/project.json) 只能用于建立初始形状，不得把模板值复制到已有项目。

## 必须输出

每次操作报告：

1. 操作结果。
2. 状态变更摘要。
3. 状态变化时提供完整候选 `project.json`。
4. Git 提交建议或不可用说明。
5. 下一步行动。

没有接受状态变更时，明确说明没有修改文件。

## 硬边界

- 不修改无关文件。
- 未经明确确认不提交，也永不 push。
- 没有验收证据和 `completed_at` 时不标记 `done`。
- 不静默丢弃阻塞、风险或决策背景。
- 没有实际执行时，不声称脚本、文件写入或 Git 命令成功。

