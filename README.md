# 🎓 教培 AI 智能备课与学情分析系统

> 用 AI 技术赋能教育，让每位学生获得个性化学习体验

## 📖 项目简介

本项目是一个面向教培行业的 AI 驱动智能教育平台，集成了**AI 智能备课**、**学情分析**、**个性化推荐**和**试卷扫描**四大核心模块，帮助教师高效备课、精准分析学生学习状态、提供个性化学习方案。

## ✨ 核心功能

### 🧠 AI 智能备课系统
- **教案自动生成** - 输入课题、年级、学科，AI 自动生成结构化教案
- **分层习题设计** - 基于 SOLO 认知理论，智能设计基础/提高/拓展三层习题
- **教学素材推荐** - 按知识点精准推荐视频、课件、互动资源
- **课件大纲生成** - 一键生成 PPT 课件结构与设计建议

### 📊 学情分析引擎
- **成绩趋势追踪** - 可视化展示学生成绩变化趋势，自动检测进步/退步
- **知识图谱诊断** - 构建学生知识掌握图谱，精准定位薄弱知识点
- **学习风险预警** - 多维度风险评估（知识断层/动机衰减/方法不当）
- **AI 诊断报告** - 自动生成亲切易懂的学习诊断摘要

### 🎯 个性化推荐系统
- **学习路径规划** - 基于知识依赖关系，AI 规划最优学习路径
- **自适应难度调整** - 根据学生表现动态调整题目难度（心流理论）
- **间隔重复复习** - 基于 Leitner 系统科学安排复习间隔
- **学习资源匹配** - 智能推荐适合的学习资源

### 📄 试卷扫描系统（新增）
- **拍照上传识别** - 支持手机拍照上传试卷，AI 自动识别题目
- **题目知识点标注** - AI 自动分析每道题的知识点和难度系数
- **薄弱点分析** - 统计全班知识点掌握情况，识别高频错题
- **强化试卷生成** - 基于错题统计，AI 生成针对性强化练习

## 🏗️ 技术架构

```
┌──────────┐     ┌───────────────┐     ┌──────────────┐     ┌────────────┐
│ Streamlit │────▶│  FastAPI 网关  │────▶│  核心引擎层  │────▶│ 通义千问 AI │
│  前端看板  │     │  RESTful API  │     │ 备课/学情/推荐 │     │ DashScope  │
└──────────┘     └──────┬────────┘     └──────────────┘     └────────────
                       │
                ┌──────▼────────┐
                │  SQLite/PG    │
                │   数据持久层   │
                └───────────────┘
```

### 技术栈
| 层级 | 技术选型 | 说明 |
|------|----------|------|
| Web 框架 | FastAPI | 高性能异步 Python 框架 |
| 前端看板 | Streamlit | Python 原生快速构建数据看板 |
| 关系数据库 | PostgreSQL / SQLite | 核心业务数据持久化 |
| AI 引擎 | 通义千问 API | 教案生成、题目分析、学情诊断 |
| 数据验证 | Pydantic v2 | 请求/响应数据校验 |
| 提示词管理 | YAML + Jinja2 | 版本化提示词模板 |

## 🚀 快速开始

### 环境要求
- Python 3.10+
- PostgreSQL（可选，本地开发默认使用 SQLite）

### 安装步骤

1. **克隆项目**
```bash
git clone https://github.com/2749085790/edu-ai-assistant.git
cd edu-ai-assistant
```

2. **创建虚拟环境**
```bash
python -m venv .venv
# Windows
.venv\Scripts\activate
# Linux/Mac
source .venv/bin/activate
```

3. **安装依赖**
```bash
pip install -r requirements.txt
```

4. **配置环境变量**
```bash
# 复制环境变量模板
cp .env.example .env

# 编辑 .env 文件，填入通义千问 API Key
# DASHSCOPE_API_KEY=your_api_key_here
```

5. **初始化数据库**
```bash
# 运行种子数据脚本（自动创建 SQLite 数据库）
python -m src.db.seed
```

6. **启动服务**

**启动 FastAPI 后端：**
```bash
python -m uvicorn main:app --host 0.0.0.0 --port 8000
```

**启动 Streamlit 前端：**
```bash
python -m streamlit run frontend/app.py --server.port 8501
```

7. **访问系统**
- 前端看板：http://localhost:8501
- API 文档：http://localhost:8000/docs

## 📂 项目结构

```
edu-ai-assistant/
├── src/
│   ├── core/                          # 核心引擎
│   │   ├── lesson_prep/               # 备课模块
│   │   │   ├── content_generator.py   # 教案生成
│   │   │   ├── material_curator.py    # 素材精选
│   │   │   └── quiz_designer.py       # 习题设计
│   │   ├── analytics/                 # 学情分析
│   │   │   ├── performance_tracker.py # 成绩追踪
│   │   │   ├── knowledge_mapper.py    # 知识图谱
│   │   │   └── risk_predictor.py      # 风险预测
│   │   └── personalization/           # 个性化推荐
│   │       ├── learning_path.py       # 路径规划
│   │       └── adaptive_engine.py     # 自适应引擎
│   ├── prompts/                       # 提示词库（YAML）
│   │   ├── lesson_prep/
│   │   ├── analytics/
│   │   ├── personalization/
│   │   └── system/
│   ├── api/                           # API 层
│   │   ├── routes/                    # 路由
│   │   ├── models/schemas.py          # Pydantic 模型
│   │   └── middleware/auth.py         # 认证中间件
│   ├── db/
│   │   ├── models.py                  # ORM 模型
│   │   ├── database.py                # 数据库连接
│   │   └── seed.py                    # 种子数据
│   ├── services/ai_client.py          # AI 客户端
│   └── utils/                         # 工具函数
├── frontend/app.py                    # Streamlit 前端
├── data/                              # 数据文件
│   ├── knowledge_graphs/              # 知识图谱
│   └── curriculum_standards/          # 课标数据
├── tests/                             # 单元测试
├── config.yaml                        # 全局配置
└── main.py                            # FastAPI 入口
```

## 🎯 使用示例

### 1. AI 生成教案
1. 进入「智能备课」页面
2. 选择学科（数学/物理等）、年级、课型
3. 输入课题名称（如"一元二次方程的解法"）
4. 点击"生成教案"，AI 自动生成完整教案

### 2. 试卷扫描与强化练习
1. 进入「试卷扫描」页面
2. 上传试卷图片或粘贴 OCR 文本
3. AI 自动识别题目并标注知识点
4. 查看知识点分布和难度分析
5. 点击"生成强化试卷"，AI 生成针对性练习

### 3. 学情分析
1. 进入「学情分析」页面
2. 选择学生
3. 查看学习画像雷达图、成绩趋势图、知识图谱
4. 查看 AI 诊断摘要和风险预警

## 🔧 开发指南

### 运行测试
```bash
python -m pytest tests/ -v
```

### API 开发
所有 API 路由位于 `src/api/routes/`，使用 FastAPI 自动生成的 Swagger 文档：
- 交互式文档：http://localhost:8000/docs
- ReDoc 文档：http://localhost:8000/redoc

### 提示词定制
提示词模板位于 `src/prompts/`，使用 YAML 格式，支持 Jinja2 变量注入：
```yaml
system: |
  你是一位{{ subject }}学科专家...
user: |
  课题：{{ topic }}
  年级：{{ grade }}
```

## 📊 数据库模型

核心数据表：
- `students` - 学生信息
- `class_groups` - 班级
- `teachers` - 教师
- `lesson_plans` - 教案
- `questions` - 习题
- `student_performances` - 成绩记录
- `knowledge_states` - 知识掌握状态
- `error_records` - 错题记录
- `learning_paths` - 学习路径
- `risk_alerts` - 风险预警
- `test_paper_scans` - 试卷扫描记录
- `targeted_quizzes` - 针对性强化试卷

## 🤝 贡献指南

欢迎提交 Issue 和 Pull Request！

## 📄 许可证

本项目采用 MIT 许可证。

## 🙏 致谢

- 通义千问 API 提供 AI 能力支持
- FastAPI、Streamlit、SQLAlchemy 等开源项目

---

**项目作者：** [2749085790](https://github.com/2749085790)  
**联系邮箱：** 2749085790@qq.com
