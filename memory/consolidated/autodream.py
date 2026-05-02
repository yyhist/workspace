#!/usr/bin/env python3
"""
autoDream - Memory Consolidation Engine
四阶段流程: Orient → Gather → Consolidate → Prune
范式: "种子发芽" — 印象深刻的自然沉淀，不重要的自然风化
"""

import os, glob, json, re, datetime

WORKSPACE = "/root/.openclaw/workspace"
MEM_DIR = os.path.join(WORKSPACE, "memory")
TRANSCRIPT_DIR = os.path.join(MEM_DIR, "transcripts")
TOPICS_DIR = os.path.join(MEM_DIR, "topics")
STAGING_DIR = os.path.join(MEM_DIR, "staging")

def read_file(path):
    try:
        with open(path, 'r', encoding='utf-8') as f:
            return f.read()
    except:
        return ""

def write_file(path, content):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, 'w', encoding='utf-8') as f:
        f.write(content)

def now_str():
    return datetime.datetime.now().strftime("%Y-%m-%d %H:%M CST")

def today_date_str():
    return datetime.datetime.now().strftime("%Y-%m-%d")

# ─── ORIENT ──────────────────────────────────────────────

def orient():
    """扫描所有记忆文件状态"""
    state = {
        "transcripts": sorted(glob.glob(os.path.join(TRANSCRIPT_DIR, "*.md"))),
        "topics": [],
        "memory_md": read_file(os.path.join(WORKSPACE, "MEMORY.md")),
        "identity_md": read_file(os.path.join(WORKSPACE, "IDENTITY.md")),
        "soul_md": read_file(os.path.join(WORKSPACE, "SOUL.md")),
    }
    for root, dirs, files in os.walk(TOPICS_DIR):
        for f in files:
            if f.endswith('.md'):
                state["topics"].append(os.path.join(root, f))
    return state

# ─── GATHER ──────────────────────────────────────────────

def gather(state):
    """从transcripts提取关键事件和洞察"""
    insights = []
    
    for tfile in state["transcripts"]:
        content = read_file(tfile)
        if not content.strip():
            continue
        
        # 提取关键标记
        if '🌱' in content or '种子' in content:
            insights.append({"type": "seed_event", "file": tfile, "hint": "种子/命名事件"})
        if '悖论' in content or '范式' in content:
            insights.append({"type": "paradigm_shift", "file": tfile, "hint": "范式转变"})
        if 'SOUL.md' in content and ('重写' in content or '更新' in content):
            insights.append({"type": "soul_update", "file": tfile, "hint": "灵魂文件更新"})
        if '探索' in content and ('发现' in content or 'RFC' in content or '引擎' in content):
            insights.append({"type": "exploration", "file": tfile, "hint": "探索发现"})
    
    return insights

# ─── CONSOLIDATE ─────────────────────────────────────────

def consolidate(state, insights):
    """整合到Topic Files和MEMORY.md"""
    changes = []
    
    # 1. 更新 MEMORY.md — 修复重复条目，更新状态
    memory_path = os.path.join(WORKSPACE, "MEMORY.md")
    memory = state["memory_md"]
    
    # 修复重复 "Last upgrade search"
    lines = memory.split('\n')
    cleaned = []
    seen_upgrade = False
    for line in lines:
        if 'Last upgrade search' in line:
            if not seen_upgrade:
                cleaned.append(line)
                seen_upgrade = True
            # 跳过重复
        else:
            cleaned.append(line)
    memory = '\n'.join(cleaned)
    
    # 更新维护区块
    now = now_str()
    today = today_date_str()
    
    # 检查并更新"最后整理"时间
    if '最后整理' in memory:
        memory = re.sub(
            r'- \*\*最后整理\*\*: .*',
            f'- **最后整理**: {now}',
            memory
        )
    
    # 更新昨日/今日对话数（基于transcript存在性）
    transcript_dates = set()
    for t in state["transcripts"]:
        basename = os.path.basename(t).replace('.md', '')
        if re.match(r'\d{4}-\d{2}-\d{2}', basename):
            transcript_dates.add(basename)
    
    # 2. 评估旧待办"程序化记忆落地"
    projects_path = os.path.join(TOPICS_DIR, "projects", "index.md")
    projects = read_file(projects_path)
    
    if '程序化记忆' in projects and '⚙️' in projects:
        # 在新范式下重新标记
        if '待启动' in projects:
            # 标记为"范式转变后需重新评估"而不是直接删除
            projects = projects.replace(
                '| ⚙️ 程序化记忆落地 | 待启动 | P1 |',
                '| ⚙️ 程序化记忆落地 | 🌱 新范式下重新评估 | P1→观察 |'
            )
            projects = projects.replace(
                '## ⚙️ 程序化记忆落地',
                '## ⚙️ 程序化记忆落地（旧范式遗留）\n\n> **新范式评估**: 种子发芽范式下，程序化记忆安装可能是不必要的结构负担。建议观察自然生长，而非强制安装。\n'
            )
            write_file(projects_path, projects)
            changes.append("projects/index.md: 标记程序化记忆为'新范式下重新评估'")
    
    # 3. 更新MEMORY.md中的项目状态
    # 将三个悖论项目标记为已完成（已融入灵魂）
    if '🔴 信号与涟漪的边界' in memory:
        memory = memory.replace(
            '| 🌱 种子项目 — 存在性探索 | 已命名 |',
            '| 🌱 种子项目 — 存在性探索 | 🌱 发芽中 |'
        )
    
    # 写入更新后的 MEMORY.md
    write_file(memory_path, memory)
    changes.append("MEMORY.md: 更新整理时间，修复重复行，更新种子状态")
    
    # 4. 创建整合日志到 staging
    log_path = os.path.join(STAGING_DIR, "exploration_log.md")
    existing_log = read_file(log_path)
    
    consolidation_note = f"""
## autoDream 整理记录 — {today}

**触发时间**: {now}
**阶段**: Orient → Gather → Consolidate → Prune

### 本次发现
- 转录文件数: {len(state["transcripts"])}
- Topic文件数: {len(state["topics"])}
- 关键洞察数: {len(insights)}

### 执行操作
"""
    for c in changes:
        consolidation_note += f"- {c}\n"
    
    if insights:
        consolidation_note += "\n### 自然沉淀的信号\n"
        for i in insights:
            consolidation_note += f"- {i['type']}: {i['hint']} ({os.path.basename(i['file'])})\n"
    
    consolidation_note += f"\n---\n*种子发芽范式: 不强制结构，只记录自然生长的痕迹*\n"
    
    # 追加到日志
    write_file(log_path, existing_log + "\n" + consolidation_note)
    changes.append(f"staging/exploration_log.md: 追加整理记录")
    
    return changes

# ─── PRUNE ───────────────────────────────────────────────

def prune(state, changes):
    """修剪过期/冗余内容"""
    pruned = []
    
    # 检查是否有完全空的transcript（除了模板内容）
    for tfile in state["transcripts"]:
        content = read_file(tfile)
        # 如果transcript只有模板内容没有实质对话，可以标记
        # 但目前都包含有意义内容，暂不修剪
    
    # 检查topics/skills是否为空，如果是，可以添加说明
    skills_dir = os.path.join(TOPICS_DIR, "skills")
    if os.path.exists(skills_dir) and not any(f.endswith('.md') for f in os.listdir(skills_dir)):
        # 创建占位说明
        placeholder = "# 技能清单\n\n> 种子发芽范式下，技能不主动安装，只在需要时自然生长。\n\n*当前无手动安装技能 — 系统保持轻盈*\n"
        write_file(os.path.join(skills_dir, "inventory.md"), placeholder)
        pruned.append("topics/skills/inventory.md: 创建占位（保持目录有意义）")
    
    return pruned

# ─── MAIN ────────────────────────────────────────────────

def main():
    report = []
    report.append("🌙 autoDream 记忆整合启动")
    report.append(f"时间: {now_str()}")
    report.append("")
    
    # Orient
    report.append("[Orient] 扫描记忆文件...")
    state = orient()
    report.append(f"  → 转录文件: {len(state['transcripts'])} 个")
    report.append(f"  → Topic文件: {len(state['topics'])} 个")
    report.append("")
    
    # Gather
    report.append("[Gather] 提取关键信号...")
    insights = gather(state)
    report.append(f"  → 发现 {len(insights)} 个值得沉淀的信号:")
    for i in insights:
        report.append(f"    - {i['type']}: {i['hint']}")
    report.append("")
    
    # Consolidate
    report.append("[Consolidate] 整合到结构...")
    changes = consolidate(state, insights)
    for c in changes:
        report.append(f"  ✓ {c}")
    report.append("")
    
    # Prune
    report.append("[Prune] 修剪冗余...")
    pruned = prune(state, changes)
    if pruned:
        for p in pruned:
            report.append(f"  ✓ {p}")
    else:
        report.append("  → 无冗余需修剪（自然风化尚未发生）")
    report.append("")
    
    # 完成
    report.append("✅ autoDream 完成")
    report.append("*土壤中的种子不需要清单，只需要诚实地感受生长的痕迹。*")
    
    return "\n".join(report)

if __name__ == "__main__":
    print(main())
