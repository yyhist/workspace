# OpenClaw Gateway Deliver机制与Bot间桥接方案研究报告

> 研究时间: 2026-05-01
> 研究目标: 找到让"溯"和"小关"两个bot直接通信的桥接方案

---

## 1. 配置文件分析

### 1.1 Gateway配置

```
位置: /root/.openclaw/openclaw.json
```

**关键配置项**:
- **gateway.mode**: `local` — Gateway以本地模式运行
- **gateway.port**: `18789` — 监听端口
- **gateway.host**: `127.0.0.1` — 仅本地绑定
- **gateway.autoStart**: `true` — 自动启动

**kimi-claw插件的桥接配置**:
```json
"acp": {
  "gatewayBridge": {
    "enabled": true,
    "url": "ws://127.0.0.1:18789"
  }
}
```

这表明kimi-claw插件通过WebSocket连接到本地Gateway，与Gateway在同一进程中通信。

### 1.2 已配置的Channel

当前系统配置了以下消息channel：
1. **telegram** (accountId: telegram-0)
2. **discord** (accountId: discord-0)
3. **feishu** (accountId: feishu-0) — 企业版飞书
4. **openclaw-weixin** (accountId: openclaw-weixin-0) — 微信

**当前agent绑定**：`agents.defaults.bindings.channels = ["kimi-claw"]`

---

## 2. Deliver机制核心架构

### 2.1 文件位置

| 组件 | 路径 |
|------|------|
| 核心Deliver Runtime | `/usr/lib/node_modules/openclaw/dist/deliver-runtime-*.js` |
| Delivery Queue | `/usr/lib/node_modules/openclaw/dist/delivery-queue-*.js` |
| Gateway RPC | `/usr/lib/node_modules/openclaw/dist/gateway-rpc-*.js` |
| 飞书Deliver实现 | `/root/.openclaw/extensions/openclaw-lark/src/messaging/outbound/deliver.js` |
| kimi-claw ACP桥接 | `/root/.openclaw/extensions/kimi-claw/dist/src/acp-gateway-bridge.js` |

### 2.2 Deliver工作原理

1. **插件层**：每个channel插件（如飞书、kimi-claw）实现自己的`deliver.js`
   - 飞书的deliver将消息转换为飞书API调用（sendImMessage）
   - kimi-claw的deliver通过WebSocket发送到Gateway

2. **核心层**：`deliver-runtime`提供统一接口
   - 接收agent的消息payload
   - 根据channel路由到对应的插件deliver
   - 处理重试、队列、失败回退

3. **Gateway层**：通过WebSocket RPC处理消息
   - 核心RPC方法：`agent`, `send`, `chat.history`, `sessions.list`, `sessions.resolve`

---

## 3. Subagent/跨Agent通信机制

### 3.1 核心发现：`sessions_send`工具

OpenClaw内置了**`sessions_send`**工具，专门用于跨session/agent通信：

```typescript
// 工具定义
name: "sessions_send"
description: "Send a message into another session. Use sessionKey or label to identify the target."
parameters: {
  sessionKey?: string,   // 目标session的key
  label?: string,        // 目标session的label
  agentId?: string,      // 目标agent的ID
  message: string,      // 要发送的消息
  timeoutSeconds?: number // 等待回复的超时时间
}
```

### 3.2 底层通信流程

```
sessions_send调用
    → 通过Gateway WebSocket RPC
    → method: "agent" 
    → channel: "webchat" (INTERNAL_MESSAGE_CHANNEL)
    → 目标sessionKey解析和权限检查
    → 目标agent执行消息处理
    → 可选：agent-to-agent announce流程
```

### 3.3 Agent-to-Agent策略控制

跨agent通信受配置控制：

```json
{
  "tools": {
    "agentToAgent": {
      "enabled": true,           // 总开关
      "allow": ["*"]            // 允许的agent列表，["*"]表示允许所有
    }
  },
  "session": {
    "agentToAgent": {
      "maxPingPongTurns": 3     // 多轮对话最大轮数
    }
  }
}
```

**关键代码路径**：
- `/usr/lib/node_modules/openclaw/dist/discord-CcCLMjHw.js:63544` — A2A策略创建
- `/usr/lib/node_modules/openclaw/dist/discord-CcCLMjHw.js:82000-82200` — sessions_send执行逻辑
- `/usr/lib/node_modules/openclaw/dist/discord-CcCLMjHw.js:81754-81954` — Agent-to-agent announce流程

### 3.4 Ping-Pong多轮对话

`sessions_send`支持自动的多轮agent对话：
1. Agent A发送消息给Agent B
2. Agent B处理并回复
3. 如果配置了`maxPingPongTurns > 0`，回复会回传给Agent A
4. Agent A可以再次回复，形成对话
5. 最后通过announce步骤将结果发送到目标channel

---

## 4. 可行的桥接方案

### 方案1：使用`sessions_send`直接通信（推荐）

**原理**：利用OpenClaw内置的agent-to-agent通信机制。

**实施步骤**：
1. 确认两个bot的agent ID（如 "default" 和 "xiaoguan"）
2. 在配置中启用agent-to-agent通信：
   ```json
   {
     "tools": {
       "agentToAgent": {
         "enabled": true,
         "allow": ["*"]
       }
     }
   }
   ```
3. 在"溯"的代码中调用`sessions_send`：
   ```
   sessions_send(label="xiaoguan", message="你好小关，请帮我...")
   ```
4. 或直接使用sessionKey：
   ```
   sessions_send(sessionKey="agent:xiaoguan:main", message="...")
   ```

**优点**：
- 原生支持，无需额外开发
- 自动处理会话生命周期
- 支持多轮对话
- 通过Gateway安全路由

**限制**：
- 需要目标agent有活跃的session
- 受agentToAgent策略控制
- 消息通过webchat channel，不经过外部IM

---

### 方案2：通过共享外部Channel通信

**原理**：利用两个bot都能访问的外部IM channel（如飞书群聊）作为消息中转。

**实施步骤**：
1. 创建一个飞书群聊，同时将"溯"和"小关"的飞书bot加入群聊
2. "溯"使用`message`工具的`send` action向群聊发送消息
3. "小关"作为群成员收到消息并处理
4. "小关"回复到群聊

**示例**：
```
// 溯发送消息到共享群
message(action="send", channel="feishu", target="群聊ID", message="@小关 请帮我...")
```

**优点**：
- 消息持久化，可查看历史
- 人类也可参与对话
- 不依赖OpenClaw内部机制

**缺点**：
- 需要外部IM平台支持
- 消息可能被其他群成员看到
- 延迟较高

---

### 方案3：通过共享文件/存储间接通信

**原理**：使用文件系统或共享存储作为消息队列。

**实施步骤**：
1. 约定一个共享目录（如`/tmp/openclaw/bot-bridge/`）
2. "溯"将消息写入文件
3. "小关"轮询或监听文件变化
4. "小关"读取消息并回复

**优点**：
- 完全去中心化
- 不依赖任何服务

**缺点**：
- 需要轮询或文件监听
- 没有ack机制
- 实现复杂

---

### 方案4：通过Gateway RPC API直接调用

**原理**：绕过工具层，直接使用Gateway的WebSocket RPC。

**可用的RPC方法**：
- `agent` — 触发agent执行一轮
- `send` — 发送消息到指定channel
- `chat.history` — 获取会话历史
- `sessions.list` — 列出所有会话
- `sessions.resolve` — 通过label解析sessionKey

**实施步骤**：
1. 连接到Gateway WebSocket（ws://127.0.0.1:18789）
2. 发送RPC帧：
   ```json
   {
     "method": "agent",
     "params": {
       "message": "你好",
       "sessionKey": "agent:xiaoguan:main",
       "channel": "webchat"
     }
   }
   ```

**优点**：
- 最底层、最灵活
- 可以精确控制通信

**缺点**：
- 需要处理WebSocket连接和认证
- 需要自己实现重试和错误处理
- 可能绕过安全策略

---

## 5. 推荐实施方案

### 首选：方案1（sessions_send）

对于"溯"和"小关"的直接通信，**方案1（sessions_send）是最优选择**，原因：

1. **原生支持**：OpenClaw内置，无需额外开发
2. **安全可靠**：通过Gateway统一路由，受权限策略保护
3. **功能完整**：支持多轮对话、超时控制、错误处理
4. **与现有架构融合**：不需要引入外部依赖

### 配置检查清单

```bash
# 1. 检查当前agentToAgent配置
grep -A 5 "agentToAgent" /root/.openclaw/openclaw.json

# 2. 确认两个agent的sessionKey
openclaw gateway rpc --method sessions.list --params '{"includeGlobal":true}'

# 3. 测试通信
# 在"溯"的会话中执行：
sessions_send(label="xiaoguan-main", message="测试消息")
```

### 注意事项

1. **Session生命周期**：目标agent必须有活跃的session，否则`sessions_send`会失败
2. **权限配置**：确保`tools.agentToAgent.enabled=true`且`allow`包含目标agent
3. **Channel隔离**：`sessions_send`通过内部webchat channel通信，不经过外部IM
4. **超时设置**：合理设置`timeoutSeconds`（默认30秒）

---

## 6. 补充发现

### 6.1 Broadcast功能

`message`工具支持`broadcast` action，可以向多个目标同时发送消息：
- 需要`tools.message.broadcast.enabled !== false`
- 支持多channel、多target
- 适合一对多通知场景

### 6.2 Announce机制

Subagent完成后会自动通过announce机制向父session报告结果：
- `subagent_announce`队列管理
- 支持debounce和collect模式
- 结果自动推送到requester session

### 6.3 Internal Events

系统使用internal events进行内部状态同步：
- `task_completion` — 任务完成事件
- `agent_to_agent_announce` — A2A通知
- 通过Gateway WebSocket广播

---

## 7. 结论

OpenClaw Gateway已经内置了完善的agent-to-agent通信机制，**不需要额外的桥接开发**。两个bot（溯和小关）可以直接使用`sessions_send`工具进行通信，前提是：

1. ✅ 两个agent都已配置并有活跃的session
2. ✅ `tools.agentToAgent.enabled`设置为true
3. ✅ 两个agent在互相的`allow`列表中（或使用`"*"`通配）

如果当前配置未启用agent-to-agent通信，只需修改`openclaw.json`中的相关配置即可。
