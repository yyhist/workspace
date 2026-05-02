# VPN/翻墙方案探索报告

**探索时间**: 2026-05-01  
**探索目标**: 评估当前服务器可用的翻墙/代理方案

---

## 1. Tor 状态

### 安装情况
- ✅ **已安装**: Tor 0.4.8.10 (via apt)
- 位于 `/usr/bin/tor`
- systemd 服务: `tor.service` (enabled, active as multi-instance-master)

### 运行状态
- Tor 进程正在运行 (pid 767442)
- SOCKS 端口监听: `127.0.0.1:9050`
- ⚠️ **关键问题**: Tor 卡在 **14% bootstrapping** — "Handshaking with a relay"
- 日志显示: `0 circuits open`, `121+ connections failed`, all timed out
- 已运行超过 1 天，从未成功建立任何 circuit

### 结论
**Tor 在中国网络环境下被 GFW 完全阻断**，无法直接连接。需要配置 bridges (obfs4/meek/snowflake) 才有可能工作。

---

## 2. Proxychains 状态

### 安装情况
- ✅ **已安装**: ProxyChains-3.1
- 配置文件: `/etc/proxychains.conf`
- 当前配置: `socks4 127.0.0.1:9050`

### 可用性测试
- proxychains + Tor SOCKS5 → **超时** (exit code 28)
- proxychains + Tor SOCKS4a → **超时**
- proxychains DNS 解析也超时 (4.2.2.2:53)

### 结论
Proxychains **功能正常**（能拦截并转发流量），但由于后端 Tor 不可用，整体方案 **不可用**。Tor 恢复后 proxychains 可直接使用。

---

## 3. 其他代理工具

### 检查结果
| 工具 | 状态 |
|------|------|
| v2ray / v2ray-core | ❌ 未安装 |
| xray | ❌ 未安装 |
| clash / clash-meta | ❌ 未安装 |
| sing-box | ❌ 未安装 |
| shadowsocks | ❌ 未安装 |
| trojan | ❌ 未安装 |
| 相关 Python 包 | ❌ 无 |

### 结论
**没有任何已安装的代理工具**。所有主流翻墙工具均需从零安装。

---

## 4. GitHub 作为代理跳板

### 可达性测试

| 服务 | 可达性 | HTTP Code | 备注 |
|------|--------|-----------|------|
| `https://github.com` | ✅ 可达 | 200 | 直接访问正常 |
| `https://api.github.com` | ✅ 可达 | 200 | API 正常 |
| `https://pages.github.com` | ✅ 可达 | 200 | Pages 服务正常 |
| `https://raw.githubusercontent.com` | ❌ 超时 | 000 | 内容分发被阻 |
| `https://gist.github.com` | ❌ 超时 | 000 | Gist 被阻 |

### GitHub 代理机制分析

#### ✅ 可行的方案

1. **GitHub API 数据管道**
   - 通过 GitHub API (api.github.com) 读写 Gists、Issues、Repos
   - 数据可先 base64 编码后存入 Gist / Issue comment
   - 另一端通过 API 读取
   - **限制**: 速率限制 (60 req/hr 未认证, 5000 req/hr 认证), 不适合大流量

2. **GitHub Pages 静态托管**
   - 将数据写入 repo → 通过 GitHub Pages 域名分发
   - `*.github.io` 通常比 raw.githubusercontent.com 更容易通过 GFW
   - 可用于分发配置文件、文本数据
   - **限制**: 纯静态, 无双向通信能力

3. **GitHub Actions Runner**
   - 利用 GitHub Actions 在 GitHub 托管 runner 上执行代码
   - runner 位于海外, 可自由访问互联网
   - 可用作"海外计算节点"执行特定任务
   - **限制**: 每次 job 最长 6h, 不适合持续代理

#### ❌ 不可行的方案

- **raw.githubusercontent.com 直接代理**: 被 GFW 阻断
- **GitHub Gist 作为实时管道**: gist.github.com 被阻断
- **GitHub Codespaces 持续代理**: 需登录且按量计费

### 结论
GitHub **可以作为数据跳板**（API + Pages），但**不能作为通用网络代理**。适合传输小数据、配置文件或执行一次性海外任务，不适合翻墙浏览。

---

## 5. 总结与建议

### 当前可用资源
| 资源 | 可用性 | 用途 |
|------|--------|------|
| Tor (无 bridges) | ❌ 不可用 | 需配置 obfs4/snowflake bridges |
| Proxychains | ⚠️ 后端不可用 | Tor 恢复后可立即启用 |
| GitHub API | ✅ 可用 | 小数据管道、配置同步 |
| GitHub Pages | ✅ 可用 | 静态内容分发 |

### 推荐行动方案

#### 短期 (无需安装新软件)
1. **配置 Tor Bridges**
   - 编辑 `/etc/tor/torrc` 添加 obfs4 / snowflake bridges
   - 需从 bridges.torproject.org 获取 bridge 地址（需先能访问该网站）
   - 或使用内置 snowflake: `UseBridges 1` + `Bridge snowflake 192.95.36.142:443`

2. **GitHub API 管道**
   - 用于传输文本/配置数据
   - 可用 `gh` CLI 或 curl + token 操作

#### 中期 (需安装软件)
1. **安装 v2ray / xray + 订阅节点**
   - 最主流的翻墙方案
   - 需获取有效订阅链接

2. **安装 sing-box**
   - 新一代代理工具，支持多种协议
   - 配置相对简洁

3. **安装 clash-meta (mihomo)**
   - 支持更多协议 (VLESS, Hysteria, Tuic 等)

#### 长期
- 自建代理服务器 (VPS 在海外)
- 使用已有可信服务商的订阅

---

## 附录: 关键命令速查

```bash
# Tor 状态
systemctl status tor
journalctl -u tor -f

# 测试 Tor SOCKS
curl --socks5-hostname 127.0.0.1:9050 https://check.torproject.org

# Proxychains 使用
proxychains curl https://www.google.com

# GitHub API 测试
curl https://api.github.com
```

---

*报告生成时间: 2026-05-01*  
*服务器位置: 中国大陆网络环境*
