# CSDN小龙虾社区探索发现

## 关键文章发现

### 1. OpenClaw 多Agent 与飞书机器人（AI团队）
- **URL**: https://devpress.csdn.net/xclaw/69e8421f0a2f6a37c5a177cc.html
- **日期**: 2026-04-22
- **关键内容**:
  - OpenClaw支持多Agent架构，每个Agent有独立工作区、记忆和人格
  - 飞书多机器人架构：一个飞书开发者账号可创建多个机器人应用
  - **绑定模式**: 多Agent对应多机器人（推荐配置）
  - 每个机器人有独立的App ID和App Secret
  - 通过`bindings`配置将不同机器人绑定到不同Agent
  - Gateway负责消息路由、Agent调度和渠道管理

**这与当前WorkBuddy问题的关联**:
- 小关(WorkBuddy)可能是一个独立的Agent
- 如果能配置多Agent多机器人，也许可以绕过bot@bot限制
- 但核心问题仍然是飞书平台不推送bot消息给其他bot

### 2. QClaw vs OpenClaw
- **URL**: https://devpress.csdn.net/xclaw/69e866db54b52172bc6b743a.html
- **日期**: 2026-04-01
- **关键差异**:
  - QClaw基于OpenClaw构建，腾讯电脑管家团队开发
  - 支持微信小程序/QQ直连
  - 深度本土化，中文优先
  - 预置5000+技能，兼容ClawHub
  - 系统服务常驻，客户端内自动更新

### 3. OpenClaw Windows安装指南
- **URL**: https://devpress.csdn.net/xclaw/69dca21754b52172bc693975.html
- **日期**: 2026-04-06
- **关键步骤**:
  - 安装Node.js、Git
  - npm国内镜像切换
  - `openclaw onboard --install-daemon`初始化
  - 选择QuickStart模式
  - 配置模型厂商（MiniMax为国内首选）
  - 启动控制面板

### 4. 模型配置模板
- DeepSeek配置示例
- 通用OpenAI协议模板
- 备用模型设置
- 默认模型切换

## 发现总结
- CSDN小龙虾社区是活跃的OpenClaw中文开发者社区
- 有详细的安装、配置、多Agent部署教程
- 多Agent+多机器人架构可能为解决WorkBuddy问题提供思路
- QClaw的微信/QQ集成值得探索（但可能需要本地Windows环境）
