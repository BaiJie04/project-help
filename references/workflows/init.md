# Init 工作流

## 目标

在空白或个人项目中创建最小、有效、可继续规划的 `.project/` 状态。

## 前置条件

- 读取 [状态契约](../state-model.md)。
- 检查 `.project/` 是否已存在。
- 检查当前目录是否为 Git 仓库，但不得自动执行 `git init`。

## 输入

需要用户提供或确认：

- 项目名称。
- 项目目标摘要。
- 至少一个成功标准。
- 已知约束；没有时使用空数组。
- 初始项目状态；默认 `planning`。

如果缺少名称、目标或成功标准，只询问缺少的必要信息。

## 执行步骤

1. 搜索现有项目上下文，避免创建与现有目标冲突的状态。
2. 使用 `PRJ-001` 创建初始状态，`revision` 为 `1`。
3. 创建空的 milestones、iterations、work_items、risks 和 decisions。
4. 将状态与生成视图展示给用户。
5. 获得确认后创建 `.project/project.json` 和 `.project/PROJECT.md`。
6. 如果 Python 可用，使用 `init` 命令；否则按状态契约手工校验并写入。
7. 建议提交：`project(init): initialize project state`。

## Chat Mode

没有文件能力时，返回完整初始 JSON，不声称文件已创建，并建议用户自行保存到 `.project/project.json`。

## 示例

用户请求：“为我的个人文档站建立项目管理状态，目标是一个月内上线，约束是一个人维护且不使用付费服务。”

预期效果：创建 `planning` 状态、写入成功标准和约束、revision 为 `1`，工作项保持为空，等待后续 `plan` 工作流。

