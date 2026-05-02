# 飞书群聊中 bot@bot 消息机制研究报告

**研究时间**: 2026-05-01
**研究目的**: 回答核心问题 — 为什么人类@bot有效，但bot@bot可能无效？

---

## 一、失败场景还原（来自 2026-04-30 记录）

| 时间 | 动作 | 发送者 | 接收者 | 结果 |
|------|------|--------|--------|------|
| 23:27 | @测试 | 一航（人类） | wb（bot） | ✅ "能收到" |
| 23:30 | @wb询问能力 | 大龙虾（溯/bot） | wb（bot） | ❌ 未收到 |

**关键观察**: 一航注意到"大龙虾@wb时名字没有亮"，暗示bot@bot的@格式在飞书UI层面就与human@bot不同。

---

## 二、飞书消息事件的数据结构

### 2.1 sender_type 字段

飞书 `im.message.receive_v1` 事件的消息体中，`sender` 对象包含 `sender_type` 字段：

```json
{
  "event": {
    "sender": {
      "sender_id": {
        "open_id": "ou_xxx",
        "union_id": "on_xxx",
        "user_id": "xxx"
      },
      "sender_type": "user"  // ← 关键字段
    }
  }
}
```

**已确认的值域**:
- `"user"` — 人类用户发送的消息
- `"app"` — 应用/机器人发送的消息

> ⚠️ 来自 electricbubble/feishu Go SDK 的注释：`"sender_type // 消息发送者类型。目前只支持用户(user)发送的消息。"` — 这是重要信号。

---

## 三、OpenClaw 飞书插件源码分析

### 3.1 Mention 解析逻辑（`parse.js`）

```javascript
// 解析 @提及信息
async function parseMessageEvent(event, botOpenId, expandCtx) {
  // mentions 解析
  if (event.message.mentions) {
    for (const m of event.message.mentions) {
      const openId = m.id?.open_id;
      parsedMentions.push({
        openId,
        name: m.name,
        key: m.key,
        isBot: Boolean(botOpenId && openId === botOpenId),  // ← 判断是否为@本bot
      });
    }
  }
}
```

**结论**: 解析逻辑本身没有问题。如果飞书推送了bot@bot的mention信息，OpenClaw能正确识别。

### 3.2 Sender 类型处理（`enrich.js`）

```javascript
async function resolveSenderInfo(params) {
  // 仅对人类用户解析显示名称 —— 通讯录API不返回app/bot账户的结果
  if (ctx.rawSender?.sender_type !== 'user') {
    log(`sender_type is "${ctx.rawSender?.sender_type}", skipping name resolution`);
    return { ctx };
  }
  // ...
}
```

**结论**: enrich阶段仅跳过bot sender的名称解析，**不会阻止消息处理**。

### 3.3 Reaction 处理中的Bot区分（`reaction-handler.js`）

```javascript
const isBotMessage = msg.senderType === 'app' && msg.senderId === account.appId;
const isOtherBotMessage = msg.senderType === 'app' && account.appId && msg.senderId !== account.appId;
```

**结论**: OpenClaw明确识别"其他机器人发送的消息"，说明飞书确实会推送这类消息（至少在reaction场景下）。

### 3.4 入站消息处理流程总结

```
飞书推送事件 → parse解析 → gate检查(@/trigger) → enrich丰富上下文 → handler处理 → dispatch分发给agent
```

**关键**: gate.js 和 handler.js 中**没有看到**对 `sender_type === 'app'` 的过滤逻辑。如果事件被推送到OpenClaw，理论上应该能处理。

---

## 四、核心问题定位：为什么 bot@bot 无效？

### 4.1 假设1：飞书平台不推送机器人发送的消息 ❓

**证据**:
1. 飞书官方文档描述 `im.message.receive_v1` 为"**用户**发送新消息至机器人或群聊后推送事件"
2. Go SDK注释: "目前只支持用户(user)发送的消息"
3. 4月30日实测：bot@bot时名字没有亮 + wb未收到

**但存在矛盾**:
- reaction-handler.js 中明确处理了 `senderType === 'app'` 的场景
- message-lookup.js 中读取并传递 `senderType`
- 这说明飞书**在某些场景下**会推送机器人消息

### 4.2 假设2：bot@bot 的 mention 格式与 human@bot 不同 ❓

**证据**:
1. 4月30日一航观察"大龙虾@wb时名字没有亮"
2. 飞书UI层面的@高亮依赖于mention数据的正确性

**推测**: 当机器人通过API发送消息并@另一个机器人时，飞书可能不会生成标准的mention元数据（或者生成的mention数据中open_id指向方式不同），导致：
- UI层面不显示高亮
- 事件订阅层面可能不将该消息识别为"有效提及"

### 4.3 假设3：OpenClaw 插件层面的过滤（最可能）

经过仔细审查源码，发现以下关键点：

**`enrich.js` 第49-51行**:
```javascript
if (ctx.rawSender?.sender_type !== 'user') {
    log(`sender_type is "${ctx.rawSender?.sender_type}", skipping name resolution`);
    return { ctx };
}
```

这里只是跳过名字解析，不阻止处理。但结合其他线索...

**更关键的**: `parse.js` 解析mention时，依赖 `event.message.mentions` 数组。如果飞书在bot@bot时**不生成mention数组**，那么 `mentionedBot` 将为 `false`，导致gate检查失败（群聊需要@bot才响应）。

### 4.4 当前最可信的根因

**飞书平台层面对 bot@bot 消息的处理存在限制**：

1. **事件推送方面**: 飞书 `im.message.receive_v1` 事件主要针对人类用户消息设计。当机器人通过API发送消息时，飞书**可能**不会将该消息推送给其他订阅了此事件的机器人应用。

2. **Mention 元数据方面**: 即使推送了事件，bot@bot时生成的mention数据中，被@的bot的open_id可能使用不同的标识方式（例如使用app_id而非open_id），导致OpenClaw的匹配逻辑 `openId === botOpenId` 失效。

3. **UI 层面**: 飞书客户端对bot@bot的@显示做了降级处理（名字不亮），说明平台本身就认为这不是一个"标准"的@行为。

---

## 五、解决方案探索

### 方案A：使用飞书 Webhook 让 bot 互相发送消息 ❌

**分析**:
- 飞书"自定义机器人"（Webhook机器人）只能**单向推送**消息到群聊
- 不能接收消息、不能订阅事件
- **结论**: 不适用bot@bot双向通信场景

### 方案B：使用飞书群机器人回调 ❌

**分析**:
- 飞书群机器人回调主要用于卡片交互（`card.action.trigger`）
- 不支持消息内容的接收
- **结论**: 不适用

### 方案C：通过 OpenClaw Gateway 的桥接机制 ✅ 最有希望

**分析**:
- 如果两个bot都在**同一个 OpenClaw Gateway** 下运行
- OpenClaw可以在Gateway层面拦截bot A发出的消息，直接路由给bot B
- 完全绕过飞书平台的限制

**具体实现思路**:
```
bot A (OpenClaw agent) → Gateway 检测到bot消息 → 直接转发给 bot B (另一个agent)
```

**优势**:
- 不依赖飞书平台特性
- 延迟极低（本地路由）
- 可以保留完整的mention上下文

**挑战**:
- 需要修改OpenClaw飞书插件的出站消息处理逻辑
- 需要设计bot-to-bot的路由规则
- 可能需要引入新的配置项（如 `botBridge: true`）

### 方案D：利用飞书开放平台的事件订阅 + 消息历史 API ✅ 备选

**分析**:
- 即使 `im.message.receive_v1` 不推送bot消息，可以通过**轮询消息历史**获取
- 飞书 API `GET /open-apis/im/v1/messages` 可以拉取群聊消息历史
- 需要权限: `im:message.group_msg`

**具体实现**:
```python
# 轮询群聊消息
while True:
    messages = fetch_chat_messages(chat_id)
    for msg in messages:
        if msg.sender.sender_type == 'app' and is_mentioning_me(msg):
            process_bot_at_bot(msg)
    sleep(poll_interval)
```

**优势**:
- 不修改飞书平台限制
- 通用性强

**劣势**:
- 轮询有延迟（秒级到分钟级）
- 增加API调用频率
- 需要额外的权限和实现复杂度

### 方案E：使用飞书"应用消息"直接调用（最推荐）✅✅

**分析**:
- 飞书bot可以通过 Open API **主动发送**消息给另一个bot
- 不需要@机制，直接通过API调用 `im/v1/messages` 发送消息
- 接收方bot需要配置 webhook 或事件订阅来接收

**但存在问题**: 如果接收方也是自建应用bot，它同样受限于 `im.message.receive_v1` 不推送bot消息的限制。

---

## 六、综合建议

### 短期方案（立即可行）

**方案 C 的简化版 — "Gateway 桥接"**:

如果大龙虾（溯）和 wb 都在**同一个 OpenClaw Gateway** 下:

1. **修改 OpenClaw 飞书插件的出站发送逻辑**: 当检测到当前agent是bot身份发送消息时，检查消息内容是否包含@另一个bot的标记
2. **Gateway 层面拦截**: 在 `send.js` 或 `deliver.js` 中，如果检测到目标接收者是群聊中的另一个bot，改为直接通过内部路由传递消息给目标agent
3. **绕过飞书**: 完全不通过飞书API发送这条bot@bot消息，而是直接在OpenClaw内部完成通信

**代码修改点**:
```javascript
// 在 deliver.js 或 actions.js 的发送逻辑中
if (isBotToBotMessage(msg)) {
  // 直接通过 Gateway 内部路由发送给目标agent
  gateway.routeToAgent(targetAgentId, msg);
  return;  // 跳过飞书API调用
}
```

### 中期方案

**方案 D + C 结合**:
- 主要通信走Gateway桥接（快速、可靠）
- 对于跨Gateway的bot通信，使用飞书消息历史API轮询作为fallback

### 长期方案

**向飞书官方反馈**:
- 提交工单询问 `im.message.receive_v1` 对 `sender_type === 'app'` 消息的支持计划
- 参考其他IM平台（如Discord、Slack）的bot-to-bot通信机制

---

## 七、关键源码文件索引

| 文件路径 | 作用 | 相关行号 |
|---------|------|---------|
| `src/messaging/inbound/parse.js` | 解析mention信息 | 35-82 |
| `src/messaging/inbound/enrich.js` | sender类型处理 | 49-51 |
| `src/messaging/inbound/reaction-handler.js` | Bot消息识别 | 114-119 |
| `src/messaging/inbound/gate.js` | 入站消息gate控制 | 155-170 |
| `src/messaging/inbound/handler.js` | 消息处理器 | 35-130 |
| `src/messaging/shared/message-lookup.js` | senderType读取 | 106-114 |
| `src/messaging/outbound/deliver.js` | 统一消息发送 | 69+ |
| `src/messaging/outbound/send.js` | 消息发送 | 214+ |

---

## 八、待验证假设

1. **需要实测**: 在飞书开放平台"事件订阅"的"近期事件"日志中，查看当bot@bot时是否会产生 `im.message.receive_v1` 事件记录
2. **需要实测**: 如果产生了事件，检查事件体中 `mentions` 数组是否包含被@的bot信息
3. **需要实测**: 检查bot@bot时 `sender.sender_id.open_id` 的格式是否与人类@bot时一致
4. **需要实测**: 在同一个OpenClaw Gateway下，通过内部路由直接传递消息的可行性

---

## 九、结论

**根因**: 飞书平台在 `im.message.receive_v1` 事件订阅层面对 `sender_type === 'app'`（机器人发送）的消息存在隐性限制。当bot A通过API发送消息并@bot B时，飞书**可能**不将该消息推送给bot B的事件订阅，或者推送的mention元数据格式与human@bot不同，导致bot B无法识别被@。

**这不是OpenClaw的bug**，而是飞书平台层面的设计限制（类似于Slack早期对bot-to-bot通信的限制）。

**最佳解决方案**: 在OpenClaw Gateway层面实现bot-to-bot的内部桥接通信，完全绕过飞书平台的限制。对于需要飞书UI层面可见的bot@bot交互，可考虑使用消息历史API轮询作为补充机制。

---

*研究员: 溯 (subagent)*
*研究完成时间: 2026-05-01 13:15 CST*
