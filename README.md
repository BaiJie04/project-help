# Project Workflow Skill

`project-workflow` 是一个面向个人开发项目的可移植项目管理 skill。它把项目目标、里程碑、迭代、工作项、依赖、风险、决策和完成证据保存为结构化 JSON，同时生成便于阅读的 Markdown 视图。

同一套方法、状态格式和核心提示词可以用于支持 Skill 的 AI 软件、只能读取文件的 AI，以及纯聊天模型。Python、Git 和平台专属工具都是可选增强，不是核心依赖。

## 版本范围

v0.1.0 支持：

- 初始化个人项目状态。
- 规划里程碑、迭代、backlog、依赖和验收标准。
- 更新任务、阻塞、风险、决策和完成证据。
- 审查进度并生成下一步行动。
- 关闭里程碑或项目并记录复盘。
- revision 冲突保护、原子写入和确定性 Markdown 生成。
- Git 感知但必须确认后提交，永不自动 push。

团队权限、企业预算、多项目组合看板以及外部系统双向同步不属于 v0.1.0。

## 仓库结构

```text
project-help/
|-- SKILL.md
|-- agents/openai.yaml
|-- references/
|-- templates/
|-- examples/personal-project/
|-- scripts/project_state.py
`-- tests/
```

`SKILL.md` 是跨平台入口。`references/` 保存按需加载的方法、状态契约和工作流。`scripts/project_state.py` 是只依赖 Python 标准库的可选工具。

## Installation

### Skill Mode

把整个仓库放入目标 AI 软件的 skill 目录，或将仓库内容复制为该软件的本地 skill。平台应能发现 `SKILL.md`，并在需要时读取其中的 references。

安装后可以直接提出：

```text
为这个项目建立项目管理状态。
把下一阶段拆成里程碑、迭代和工作项。
检查当前迭代的阻塞和风险。
```

### File Mode

如果平台不能发现 skill，但可以读取仓库：

1. 将 `SKILL.md` 设置为系统提示词、自定义指令或项目指令。
2. 允许模型读取 `references/`、`templates/` 和目标项目的 `.project/`。
3. 按 `SKILL.md` 中的路由选择工作流。

### Chat Mode

如果平台不能访问文件：

1. 粘贴 `SKILL.md` 的核心契约。
2. 粘贴完整的当前 `project.json`。
3. 说明要执行的 `init`、`plan`、`update`、`review` 或 `close` 操作。
4. 模型必须返回完整的候选 JSON，并明确说明没有直接写入文件或 Git。

## 受管理项目布局

```text
<project-root>/
`-- .project/
    |-- project.json
    `-- PROJECT.md
```

`project.json` 是唯一事实源。`PROJECT.md` 是生成视图，不应手工修改。

## CLI 使用

需要 Python 3.10 或更高版本。Windows 可使用 `py` 代替 `python`。

```bash
python scripts/project_state.py init --root /path/to/project --name "Project" --summary "Outcome" --success "Observable result"
python scripts/project_state.py validate --root /path/to/project
python scripts/project_state.py apply --root /path/to/project --expected-revision 1 --file candidate.json
python scripts/project_state.py render --root /path/to/project
python scripts/project_state.py summary --root /path/to/project
```

`apply` 要求候选状态的 revision 等于 `expected-revision + 1`。校验失败时不会覆盖现有状态。

## Git 行为

- 写文件前先展示状态影响并获得确认。
- Git 提交需要再次确认。
- 默认只提交 `.project/project.json` 和 `.project/PROJECT.md`。
- 不修改无关工作区文件。
- 提交消息使用 `project(init|plan|update|review|close): <summary>`。
- 本 skill 永不自动 push。

## 测试

```bash
python -m unittest discover -s tests -v
python scripts/project_state.py validate --root examples/personal-project
```

测试不依赖第三方包。Windows 上可使用 `py -m unittest discover -s tests -v`。

## GitHub Upload

本地验证完成后，先创建 GitHub 空仓库，再执行：

```bash
git remote add origin https://github.com/<your-account>/<repository>.git
git push -u origin master
git push origin v0.1.0
```

如果先上传功能分支，将最后一条命令中的 `master` 替换为 `feat/project-workflow-v0.1.0`。推送由用户执行，本项目不会自动 push。

## 设计文档

- 设计规格：`docs/superpowers/specs/2026-09-20-project-workflow-design.md`
- 实施计划：`docs/superpowers/plans/2026-09-20-project-workflow-v0.1.0.md`

## License

MIT License，详见 `LICENSE`。

