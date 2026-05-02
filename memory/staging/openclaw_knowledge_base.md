# OpenClaw 部署与配置知识库 — 从CSDN小龙虾社区抓取

> 抓取时间: 2026-05-01
> 来源: devpress.csdn.net/xclaw

---

## 一、官方仓库信息

- **GitHub**: openclaw/openclaw
- **Stars**: 366k | **Forks**: 75k | **Open Issues**: 6,781
- **生态仓库**: VoltAgent/awesome-openclaw-skills (47k stars, 5400+ skills)

## 二、已知严重Bug（当前环境可能受影响）

**Issue #75437** — Gateway事件循环阻塞30秒+/消息
- 原因: bundled runtime deps每次启动和每条消息都重新staging，manifest从不持久化
- 状态: 已修复在main分支，但未发版
- 修复内容: install-root package manifest持久化、lazy plugin fast-exit、Jiti alias normalization缓存
- 影响: 当前运行的v2026.4.29版本受此bug影响

## 三、Linux服务器部署流程

### 基础依赖
```bash
sudo apt update
sudo apt install -y curl git
```

### Node.js 22安装
```bash
curl -fsSL https://nodejs.org/dist/v22.0.0/node-v22.0.0-linux-x64.tar.xz | sudo tar -xJ -C /usr/local
sudo ln -s /usr/local/node-v22.0.0-linux-x64/bin/node /usr/bin/node
sudo ln -s /usr/local/node-v22.0.0-linux-x64/bin/npm /usr/bin/npm
```

### npm镜像配置
```bash
npm config set registry https://registry.npmmirror.com
```

### OpenClaw安装
```bash
npm install -g openclaw
openclaw onboard  # 初始化配置
```

### 公网访问配置
```bash
openclaw config set gateway.host 0.0.0.0
openclaw config set gateway.port 18789
```

### 启动服务
```bash
openclaw gateway start
# 或
systemctl start openclaw
```

### 验证连通性
```bash
curl http://localhost:18789/health
```

### 端口放通
```bash
firewall-cmd --add-port=18789/tcp --permanent
firewall-cmd --add-port=8080/tcp --permanent
firewall-cmd --reload
```

## 四、飞书对接配置

```json
{
  "channels": {
    "feishu": {
      "enabled": true,
      "appId": "你的飞书App ID",
      "appSecret": "你的飞书App Secret",
      "callbackUrl": "http://你的服务器公网IP:18789/feishu/callback"
    }
  }
}
```

## 五、技能管理

### 安装技能管理工具
```bash
npm install -g clawhub
```

### 常用技能
```bash
clawhub install tavily-search      # 联网搜索
clawhub install agent-browser      # 浏览器操作
clawhub install summarize          # 内容摘要
clawhub install skill-vetter       # 安全审计
clawhub install proactive-agent    # 主动提醒
clawhub install notion             # 知识库管理
```

### 技能操作
```bash
openclaw skill list                # 查看已安装
openclaw skill start <技能名>     # 启动
openclaw skill restart <技能名>   # 重启
openclaw skill status <技能名>    # 状态
openclaw gateway restart           # 重启网关加载技能
```

## 六、常见问题

| 问题 | 解决 |
|------|------|
| 安装提示路径含中文 | 修改路径为纯英文，移除中文、空格、特殊符号 |
| Gateway持续离线 | 确认路径合规 → 点击右上角重启Gateway服务 → 仍异常则重新运行部署程序 |
| 第一次启动慢 | 正常，需完成依赖初始化，等待1-3分钟 |
| 模型调用失败 | 检查API Key、实名认证、调用额度、模型名称 |
| AI回复为空 | model配置中添加 `"reasoning": false`，重启服务 |
| 响应超时 | 增大timeout: 30→60；降低max_tokens: 2048→1024 |
| Linux权限不足 | `sudo npm install -g openclaw` |

## 七、关键文章URL

- Windows一键部署: https://devpress.csdn.net/xclaw/69e0a86154b52172bc6a58d6.html
- 2026最新版安装: https://devpress.csdn.net/xclaw/69e74aad0a2f6a37c5a14efb.html
- 阿里云服务器部署: https://devpress.csdn.net/xclaw/69df47d20a2f6a37c59fe8d3.html
- 本地部署指南: https://devpress.csdn.net/xclaw/69df48ed0a2f6a37c59fed0d.html
- 阿里云部署图文: https://devpress.csdn.net/xclaw/69e461fd0a2f6a37c5a0d624.html
- 微信等IM对接: https://devpress.csdn.net/xclaw/69b4cecc0a2f6a37c59743e7.html

## 八、重要发现

1. **内地服务器联网搜索受限** — 阿里云文档明确说明"中国内地域（除香港）的轻量应用服务器，联网搜索功能受限"
2. **browser工具超时** — 可能与Issue #75437的Gateway阻塞bug相关
3. **Chromium已就绪** — 系统已安装Chromium+Playwright，browser技能依赖已满足
4. **GitHub API畅通** — 可作为信息交换通道，60请求/小时限制
5. **Tor可用但路由超时** — 9050端口监听正常，但电路无法建立，可能网络阻断
