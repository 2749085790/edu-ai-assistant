# 🎓 AI Tutor — 结构化教学助手

> 不是 ChatGPT · 是真正懂教学的 AI 老师

**和 ChatGPT 有什么区别？**

| 维度 | ChatGPT | AI Tutor |
|------|---------|---------|
| 有没有教学设计 | ❌ 随机问随机答 | ✅ 入门→进阶→测试三阶段结构化 |
| 有没有用户路径 | ❌ 无状态对话 | ✅ 学习目标→路径规划→反馈闭环 |
| 有没有学情记忆 | ❌ 每次重置 | ✅ 持续追踪知识掌握状态 |
| 能不能评估效果 | ❌ 不知道学没学会 | ✅ 自动出题评估 + 风险预警 |
| 面向谁 | 所有人 | ✅ K12 学生 / 教培机构老师 |

**核心定位**：面向教培行业的 AI 驱动教学 SaaS，为老师提供 AI 备课能力，为学生提供结构化个性化学习路径。

[![Python](https://img.shields.io/badge/Python-3.10+-blue?style=flat-square&logo=python)](https://python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.100+-green?style=flat-square&logo=fastapi)](https://fastapi.tiangolo.com/)
[![License](https://img.shields.io/badge/License-MIT-green?style=flat-square)](LICENSE)

---

## 1. 项目背景

教培行业的核心矛盾：

- **老师**：备课耗时 3-4 小时/天，大量时间花在重复劳动上，没有数据支撑分层教学
- **学生**：不知道自己哪里不会，盲目刷题，效率极低，缺乏即时反馈
- **机构**：无法量化教学效果，学情数据分散，续费转化全靠销售

**解决方案**：用 AI Agent 打通"备课→上课→批改→分析"全链路，让老师提效 70%，让学生学习效率提升 40%。

---

## 2. 用户是谁 & 使用场景

| 用户角色 | 核心诉求 | 典型使用场景 |
|---------|---------|------------|
| 👩‍🏫 **教培机构老师** | 快速备课、了解班级学情、出针对性练习 | 上课前：10分钟生成教案 → 课后：扫描试卷获取学情报告 |
| 🧒 **K12 学生** | 知道自己哪里不会、得到个性化练习 | 课后：完成自适应练习 → 系统自动更新知识掌握图谱 |
| 🏢 **机构管理者** | 量化教学效果、看到学生进步数据 | 月末：查看班级整体学情趋势、风险学生预警 |

---

## 3. 核心功能

### 🗺️ 学生完整使用路径

```
① 设定学习目标
   学生选择学科 / 年级 / 薄弱知识点
          │
          ▼
② AI 规划学习路径
   系统基于知识依赖图谱，生成最优学习顺序
   （先解决前置知识缺失，再攻克薄弱点）
          │
          ▼
③ 分阶段学习（核心差异化）
   ┌──────────────────────────────────┐
   │  入门阶段：基础概念讲解 + 例题精讲  │
   │  进阶阶段：变式练习 + 错误分析      │
   │  测试阶段：自动出题 → 评估掌握程度  │
   └──────────────────────────────────┘
          │
          ▼
④ 即时学习反馈
   做题后立刻获得：错误原因 + 知识点定位 + 下一步建议
          │
          ▼
⑤ 学情持续追踪
   知识图谱实时更新 → 薄弱点自动识别 → 学习风险预警
```

### 🧠 AI 智能备课（教师端）

- **教案自动生成**：输入课题+年级+学科，AI 输出结构化教案（含教学目标/重难点/分层设计）
- **分层习题设计**：基于 SOLO 认知理论，自动生成基础/提高/拓展三层习题
- **学情驱动备课**：读取班级薄弱点数据 → 自动调整本节课的重点和练习方向

### 📊 学情分析引擎

- **知识图谱诊断**：可视化展示每个学生的知识掌握状态，精准定位薄弱点
- **成绩趋势追踪**：自动识别进步/退步趋势，生成可读性强的诊断报告
- **学习风险预警**：多维评估（知识断层 / 动机衰减 / 方法不当），提前干预

### 📄 试卷扫描 & 强化出题

- **OCR 识别上传**：手机拍照或文字粘贴，AI 自动识别题目
- **全班知识点热图**：统计班级错误率，识别高频错题
- **强化练习生成**：基于错题统计，AI 生成针对性强化卷

---

## 4. Agent 设计

### 架构：单 Agent + 多 Tool

```
用户请求（老师/学生）
        │
        ▼
┌───────────────────────────────────┐
│          Tutor Agent              │
│  职责：教学任务的核心调度中枢        │
│  - 意图识别（备课/出题/诊断/推荐）  │
│  - 选择合适的 Tool 组合             │
│  - 注入学情上下文                   │
│  - 保证教学逻辑的连续性             │
└──────────────┬────────────────────┘
               │ 按需调用
    ┌──────────┼──────────────────────┐
    ▼          ▼          ▼           ▼
lesson_     quiz_     analysis_    path_
prep_tool   tool      tool         tool
教案生成    出题评估   学情分析     路径规划
    │          │          │           │
    └──────────┴────┬──────┴───────────┘
                    ▼
           通义千问 qwen-plus
           + SQLite 知识状态库
```

### 核心 Tool 调用示例

```python
# 场景：老师上课前备课（5分钟完成）

# Tool 1: 读取班级学情
class_weak_points = analysis_tool.get_class_weakness(
    class_id="G8-Math-A",
    subject="数学",
    recent_days=14
)
# 输出: {"一元二次方程": 0.68, "因式分解": 0.55}

# Tool 2: 生成学情驱动教案
lesson_plan = lesson_prep_tool.generate(
    topic="一元二次方程的解法",
    grade="初二",
    weak_points=class_weak_points,    # 注入学情！
    duration_min=45
)

# Tool 3: 生成分层练习
exercises = quiz_tool.create_layered(
    knowledge="一元二次方程",
    levels=["基础", "提高", "拓展"],
    focus_on=class_weak_points        # 薄弱点加权
)
```

### Prompt 设计策略

```
┌──────────────────────────────────────────────────────────────┐
│                  Tutor Agent 核心 Prompt                      │
├──────────────────────────────────────────────────────────────┤
│ 角色：你是一位经验丰富的 K12 {subject} 老师，同时是教学设计专家  │
│                                                              │
│ 学生画像注入：                                                │
│   姓名：{student_name}，年级：{grade}                         │
│   当前学习阶段：{stage}（入门/进阶/测试）                       │
│   已掌握：{mastered_points}                                   │
│   薄弱点：{weak_points}（错误率从高到低排序）                   │
│                                                              │
│ 教学规则：                                                    │
│   - 入门阶段：先建立概念，用类比和例子，不出题                  │
│   - 进阶阶段：出变式题，引导学生自己发现错误                    │
│   - 测试阶段：出3-5道评估题，判断是否真正掌握                   │
│                                                              │
│ 输出约束：每次回复聚焦一个知识点，不跑题，给出明确下一步指引     │
└──────────────────────────────────────────────────────────────┘
```

---

## 5. 技术架构

```
edu-ai-assistant/
├── src/
│   ├── core/                          # 核心 Agent 引擎
│   │   ├── lesson_prep/               # 备课模块
│   │   │   ├── content_generator.py   # 教案生成 Tool
│   │   │   ├── material_curator.py    # 素材推荐 Tool
│   │   │   └── quiz_designer.py       # 习题设计 Tool
│   │   ├── analytics/                 # 学情分析引擎
│   │   │   ├── performance_tracker.py # 成绩追踪
│   │   │   ├── knowledge_mapper.py    # 知识图谱构建
│   │   │   └── risk_predictor.py      # 风险预测
│   │   └── personalization/           # 个性化推荐
│   │       ├── learning_path.py       # 路径规划 Tool
│   │       └── adaptive_engine.py     # 自适应难度引擎
│   ├── prompts/                       # 提示词库（YAML + Jinja2）
│   │   ├── lesson_prep/              # 备课相关 Prompt
│   │   ├── analytics/                # 分析相关 Prompt
│   │   └── personalization/          # 个性化 Prompt
│   ├── api/                          # FastAPI 路由层
│   └── db/                           # 数据持久层（SQLite/PG）
├── frontend/app.py                    # Streamlit 看板
└── main.py                            # 服务入口
```

**技术栈**：

| 层级 | 技术 | 说明 |
|------|------|------|
| Web 框架 | FastAPI | 高性能异步 Python |
| 前端看板 | Streamlit | 快速搭建数据看板 |
| AI 引擎 | 通义千问 `qwen-plus` | 教案/出题/诊断 |
| 数据库 | SQLite / PostgreSQL | 知识状态持久化 |
| 提示词管理 | YAML + Jinja2 | 版本化 Prompt 模板 |

---

## 6. 快速开始

```bash
# 1. 克隆项目
git clone https://github.com/2749085790/edu-ai-assistant.git
cd edu-ai-assistant

# 2. 创建虚拟环境
python -m venv .venv
.venv\Scripts\activate    # Windows
# source .venv/bin/activate  # Linux/Mac

# 3. 安装依赖
pip install -r requirements.txt

# 4. 配置 API Key
cp .env.example .env
# 编辑 .env，填入：DASHSCOPE_API_KEY=your_key

# 5. 初始化数据库
python -m src.db.seed

# 6. 启动服务
python -m uvicorn main:app --host 0.0.0.0 --port 8000
python -m streamlit run frontend/app.py --server.port 8501
```

- 前端看板：http://localhost:8501
- API 文档：http://localhost:8000/docs

---

## 7. 产品价值

| 指标 | 传统备课方式 | AI Tutor | 提升幅度 |
|------|------------|---------|---------|
| 教师备课时间 | 3-4小时/天 | 30分钟/天 | **↓ 70%** |
| 学生知识盲点识别 | 靠老师经验 | AI 实时定位 | **精准↑** |
| 个性化程度 | 一刀切 | 每人独立路径 | **质的飞跃** |
| 学情数据可见性 | 月考才知道 | 实时追踪 | **时效↑10x** |

---

## 📄 许可证

MIT License © 2026 杨浩文

---

**项目作者：** [2749085790](https://github.com/2749085790)  
**联系邮箱：** 2749085790@qq.com
