# OpenClaw 多Agent配置研究笔记 — 2026-05-01

来源：kimi_search国内搜索

---

## 一、多Agent两种核心模式

| 模式 | 独立Agent (Isolated) | A2A协作 (Agent-to-Agent) |
|------|----------------------|--------------------------|
| 关系 | 平行关系，互不干扰 | 主从/协作关系，可互相调用 |
| 适用 | 工作/生活分离、不同渠道绑定 | 复杂任务分解、专家系统调用 |
| 复杂度 | ⭐⭐ | ⭐⭐⭐⭐ |
| 推荐 | 新手首选 | 高级用户必备 |

最佳实践：先配置多个独立Agent，再启用A2A协作。

---

## 二、创建独立Agent（基础）

```bash
# 创建前端开发Agent
openclaw agents add fe-dev \
  --workspace ~/.openclaw/workspaces/fe-dev \
  --model claude-sonnet-4-2

# 创建市场研究Agent
openclaw agents add market-researcher \
  --workspace ~/.openclaw/workspaces/market-researcher \
  --model qwen-max-2026-01-23
```

关键参数：
- Agent ID：唯一标识
- --workspace：专属工作区目录（物理隔离记忆/文件/技能）
- --model：分配最适合任务的模型

**为Agent绑定专属消息渠道**：
```bash
openclaw config set agents.fe-dev.channels.feishu \
  '{"enabled": true, "appId": "cli_fe_dev_xxxxx", "appSecret": "your-secret"}' \
  --json
```

验证启动：
```bash
openclaw agents list
openclaw gateway start
openclaw status
```

---

## 三、启用A2A协作（进阶）

编辑 `~/.openclaw/openclaw.json`：

```json
{
  "agentToAgent": {
    "enabled": true,
    "allowedAgents": ["orchestrator", "project-manager"],
    "security": {
      "requireAuth": true
    }
  },
  "agents": {
    "orchestrator": {
      "workspace": "~/.openclaw/workspaces/orchestrator",
      "models": { "default": "anthropic/claude-opus-4-5" }
    },
    "coder": {
      "workspace": "~/.openclaw/workspaces/coder",
      "models": { "default": "deepseek-coder-v3" }
    },
    "reviewer": {
      "workspace": "~/.openclaw/workspaces/reviewer",
      "models": { "default": "qwen-max-2026-01-23" }
    }
  }
}
```

在orchestrator的 `persona.md` 中定义协作逻辑：
```markdown
你是一个项目协调者。核心职责是将复杂请求分解为子任务，委派给专家Agent。

可用专家Agent：
- **coder**: 编写/运行/调试代码。调用 `a2a_call("coder", "指令")`
- **reviewer**: 审查代码质量/安全性。调用 `a2a_call("reviewer", "代码")`

工作流程：
1. 接收用户请求
2. 分析分解任务
3. 调用coder执行编码
4. 将coder输出传递给reviewer审查
5. 整合反馈，形成最终答案
```

---

## 四、实战案例：自动化周报

目标：用户在飞书发送"生成本周周报"

1. 创建4个Agent：report-agent(主), calendar-agent, git-agent, notion-agent
2. 为report-agent配置飞书通道
3. 在openclaw.json中启用A2A，report-agent加入allowedAgents
4. 为report-agent编写persona.md，明确分步调用其他Agent
5. 为各Agent配置所需工具和API密钥

---

## 五、4周渐进式实施计划

**第1周**：单Agent落地，跑通核心工作流
- 安装OpenClaw，撰写SOUL.md
- 配置Telegram接收输出
- 创建Cron定时任务，每天自动运行

**第2周**：添加记忆系统，优化输出
- 人工反馈指导
- 执行 `openclaw memory optimize`

**第3周**：添加第二个Agent，实现文件协作
- "一写多读"文件协作模式
- 跑通多Agent协作逻辑

---

## 六、工作流编排（workflow.yaml）

```yaml
workflow:
  - name: research_task
    agent: researcher
    trigger: new_task
    description: 资料搜集、数据整理、生成调研报告

  - name: coding_task
    agent: coder
    trigger: research_task_complete
    description: 根据调研报告编写代码

  - name: execute_task
    agent: executor
    trigger: coding_task_complete
    description: 执行代码，完成自动化操作

  - name: integrate_task
    agent: supervisor
    trigger: execute_task_complete
    description: 整合所有结果，生成最终报告
```

启动：
```bash
openclaw agents start --all
openclaw workflow run my_workflow
```

---

## 七、关键命令速查

```bash
openclaw doctor              # 全面配置诊断
openclaw backup create       # 创建完整备份
openclaw memory optimize     # 优化记忆系统
openclaw agents add          # 动态添加Agent
openclaw agents remove       # 动态删除Agent
openclaw agents restart      # 重启单个Agent
openclaw agents sync         # 定期同步所有Agent状态
openclaw config set log.enable true  # 开启日志
```

---

## 八、排错指南

| 问题 | 解决方案 |
|------|----------|
| Agent间通信失败"消息总线配置错误" | 检查channel配置，验证AppID/Secret有效 |
| agents start --all部分失败 | 检查agents.yaml格式，确认模型配置有效，查看日志 |
| 工作流无法触发"触发规则不存在" | 检查trigger字段与前序任务名一致(任务名_complete格式) |
| 动态添加/删除Agent | openclaw agents add/remove/restart [AgentID] |

---

*记录时间: 2026-05-01*
*来源: 腾讯云开发者社区(2026-04-12) + 阿里云开发者社区(2026-03-13) + 什么值得买(2026-03-10)*
