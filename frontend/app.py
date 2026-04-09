"""
教培 AI 智能备课与学情分析系统 - Streamlit 前端看板 v2
全面优化 UI/UX：卡片布局、配色主题、动态图表、状态反馈
"""

import streamlit as st
import httpx
import plotly.graph_objects as go
import plotly.express as px
import os
import time

# ── 全局配置 ─────────────────────────────────────────────
API_BASE = os.getenv("API_BASE_URL", "http://localhost:8000/api/v1")
API_KEY = os.getenv("API_KEY", "")

st.set_page_config(
    page_title="教培 AI 智能系统",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── 自定义主题样式 ───────────────────────────────────────
st.markdown("""
<style>
/* 全局字体 */
html, body, [class*="st-"] { font-family: 'Microsoft YaHei', 'PingFang SC', sans-serif; }

/* 隐藏默认 header / footer */
#MainMenu, header, footer { visibility: hidden; }

/* ========== 侧边栏深度优化 ========== */
section[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #0f172a 0%, #1e293b 100%) !important;
    border-right: none !important;
}
section[data-testid="stSidebar"] > div {
    padding: 24px 20px !important;
}
/* 侧边栏标题 */
section[data-testid="stSidebar"] .stMarkdown h2 {
    color: #f1f5f9 !important;
    font-size: 1.35rem !important;
    font-weight: 700 !important;
    margin-bottom: 4px !important;
    letter-spacing: 0.5px;
}
section[data-testid="stSidebar"] .stMarkdown p,
section[data-testid="stSidebar"] .stMarkdown em {
    color: #cbd5e1 !important;
    font-size: 0.82rem !important;
    margin-top: 0 !important;
}
/* 侧边栏分隔线 */
section[data-testid="stSidebar"] hr {
    border-color: #334155 !important;
    margin: 16px 0 !important;
}
/* 侧边栏导航文字 - 提高亮度 */
section[data-testid="stSidebar"] label,
section[data-testid="stSidebar"] span,
section[data-testid="stSidebar"] div[data-testid="stMarkdownContainer"] p {
    color: #e2e8f0 !important;
    font-size: 0.95rem !important;
    font-weight: 500 !important;
}
/* radio 按钮标签 */
section[data-testid="stSidebar"] .stRadio > div[role="radiogroup"] > label {
    padding: 10px 14px !important;
    border-radius: 8px !important;
    margin-bottom: 4px !important;
    transition: all 0.15s;
    color: #e2e8f0 !important;
}
section[data-testid="stSidebar"] .stRadio > div[role="radiogroup"] > label:hover {
    background: rgba(255,255,255,0.08) !important;
}
/* 选中状态 */
section[data-testid="stSidebar"] .stRadio > div[role="radiogroup"] > label[data-baseweb="radio"][aria-checked="true"] {
    background: linear-gradient(135deg, #4F46E5, #7C3AED) !important;
    color: #ffffff !important;
}
section[data-testid="stSidebar"] .stRadio > div[role="radiogroup"] > label[data-baseweb="radio"][aria-checked="true"] * {
    color: #ffffff !important;
}
/* radio 圆点 */
section[data-testid="stSidebar"] .stRadio > div[role="radiogroup"] > label > div:first-child {
    background-color: rgba(255,255,255,0.2) !important;
    border-color: rgba(255,255,255,0.4) !important;
}
section[data-testid="stSidebar"] .stRadio > div[role="radiogroup"] > label[data-baseweb="radio"][aria-checked="true"] > div:first-child {
    background-color: #ffffff !important;
    border-color: #ffffff !important;
}
/* 侧边栏底部信息 */
section[data-testid="stSidebar"] .stAlert {
    background: rgba(34,197,94,0.15) !important;
    border: 1px solid rgba(34,197,94,0.3) !important;
    border-radius: 8px !important;
    padding: 10px 14px !important;
}
section[data-testid="stSidebar"] .stAlert div[data-testid="stAlertContent"] {
    color: #22c55e !important;
    font-weight: 600 !important;
    font-size: 0.85rem !important;
}
section[data-testid="stSidebar"] .stCaption {
    color: #94a3b8 !important;
    font-size: 0.75rem !important;
}
section[data-testid="stSidebar"] a {
    color: #60a5fa !important;
}

/* ========== 主内容区样式 ========== */
/* 指标卡片 */
div[data-testid="stMetric"] {
    background: #ffffff; border-radius: 12px; padding: 16px 20px;
    border: 1px solid #e2e8f0; box-shadow: 0 1px 3px rgba(0,0,0,0.06);
}
div[data-testid="stMetric"] label { color: #64748b !important; font-size: 0.85rem !important; }
div[data-testid="stMetric"] [data-testid="stMetricValue"] { color: #1e293b !important; font-weight: 700 !important; }

/* 自定义信息卡片 */
.info-card {
    background: #ffffff; border-radius: 14px; padding: 24px;
    border: 1px solid #e2e8f0; box-shadow: 0 2px 8px rgba(0,0,0,0.04);
    margin-bottom: 16px; transition: transform 0.15s;
}
.info-card:hover { transform: translateY(-2px); box-shadow: 0 4px 12px rgba(0,0,0,0.08); }
.info-card h3 { margin: 0 0 12px 0; font-size: 1.1rem; color: #1e293b; }
.info-card p { color: #64748b; font-size: 0.92rem; line-height: 1.65; margin: 0; }

/* 功能模块卡片 */
.module-card {
    background: linear-gradient(135deg, var(--bg1) 0%, var(--bg2) 100%);
    border-radius: 16px; padding: 28px; text-align: center;
    border: none; min-height: 220px;
}
.module-card .icon { font-size: 2.8rem; margin-bottom: 12px; }
.module-card h3 { color: #fff; margin: 0 0 10px 0; font-size: 1.15rem; }
.module-card p { color: rgba(255,255,255,0.88); font-size: 0.88rem; line-height: 1.6; }

/* 标签栏 */
.stTabs [data-baseweb="tab-list"] { gap: 8px; }
.stTabs [data-baseweb="tab"] {
    border-radius: 8px 8px 0 0; padding: 10px 24px;
    font-weight: 600; font-size: 0.95rem;
}

/* 按钮 */
.stButton > button[kind="primary"] {
    background: linear-gradient(135deg, #4F46E5, #7C3AED) !important;
    border: none !important; border-radius: 10px !important;
    font-weight: 600 !important; letter-spacing: 0.5px;
}
.stButton > button[kind="primary"]:hover {
    background: linear-gradient(135deg, #4338CA, #6D28D9) !important;
}

/* 分隔线 */
hr { border-color: #e2e8f0 !important; }

/* 状态标签 */
.tag { display: inline-block; padding: 4px 12px; border-radius: 20px;
       font-size: 0.8rem; font-weight: 600; }
.tag-green { background: #dcfce7; color: #166534; }
.tag-yellow { background: #fef3c7; color: #92400e; }
.tag-red { background: #fee2e2; color: #991b1b; }
.tag-blue { background: #dbeafe; color: #1e40af; }

/* expander 样式 */
details { border-radius: 10px !important; border: 1px solid #e2e8f0 !important; }

/* 文件上传区 */
.stFileUploader {
    border: 2px dashed #cbd5e1 !important;
    border-radius: 12px !important;
    padding: 24px !important;
    background: #f8fafc !important;
}

/* selectbox / text_input 美化 */
[data-testid="stSelectbox"] > div > div {
    border-radius: 8px !important;
    border-color: #cbd5e1 !important;
}
[data-testid="stTextInput"] > div > div {
    border-radius: 8px !important;
    border-color: #cbd5e1 !important;
}
</style>
""", unsafe_allow_html=True)


# ── API 工具函数 ────────────────────────────────────────
def _headers():
    h = {"Content-Type": "application/json"}
    if API_KEY:
        h["X-API-Key"] = API_KEY
    return h

def api_get(path, params=None):
    try:
        r = httpx.get(f"{API_BASE}{path}", params=params, headers=_headers(), timeout=60)
        r.raise_for_status()
        return r.json()
    except Exception as e:
        st.error(f"请求失败：{e}")
        return None

def api_post(path, data):
    try:
        r = httpx.post(f"{API_BASE}{path}", json=data, headers=_headers(), timeout=120)
        r.raise_for_status()
        return r.json()
    except Exception as e:
        st.error(f"请求失败：{e}")
        return None


# ── 可复用组件 ──────────────────────────────────────────
def render_module_card(icon, title, desc, bg1, bg2):
    st.markdown(
        f'<div class="module-card" style="--bg1:{bg1};--bg2:{bg2}">'
        f'<div class="icon">{icon}</div><h3>{title}</h3><p>{desc}</p></div>',
        unsafe_allow_html=True,
    )

def render_risk_tag(level: str):
    m = {"high": ("高风险", "tag-red"), "medium": ("中风险", "tag-yellow"), "low": ("低风险", "tag-green")}
    label, cls = m.get(level, (level, "tag-blue"))
    return f'<span class="tag {cls}">{label}</span>'

def get_student_map():
    """获取学生列表并缓存"""
    data = api_get("/students", {"page_size": 100})
    items = data.get("items", []) if data else []
    return {s["id"]: s for s in items}

def plotly_layout_defaults(fig, height=420):
    fig.update_layout(
        height=height,
        margin=dict(l=20, r=20, t=50, b=20),
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        font=dict(family="Microsoft YaHei"),
    )
    return fig


# ── 侧边栏 ─────────────────────────────────────────────
with st.sidebar:
    st.markdown("## 🎓 教培 AI 系统")
    st.markdown("*智能备课 · 学情分析 · 个性化推荐*")
    st.markdown("---")

    page = st.radio(
        "导航",
        [
            "🏠 系统总览",
            "📝 智能备课",
            "📊 学情分析",
            "🎯 个性化推荐",
            "⚠️ 风险预警",
            "📄 试卷扫描",
        ],
        label_visibility="collapsed",
        index=0,
    )

    st.markdown("---")

    # 系统状态
    try:
        _health = httpx.get("http://localhost:8000/health", timeout=3).json()
        st.success("API 服务运行中", icon="✅")
    except Exception:
        st.error("API 服务未连接", icon="❌")

    st.caption(f"接口地址：{API_BASE}")


# ============================================================
# 🏠 系统总览
# ============================================================
if page == "🏠 系统总览":
    st.markdown("# 🎓 教培 AI 智能备课与学情分析系统")
    st.markdown("> 用 AI 技术赋能教育，让每位学生获得个性化学习体验")
    st.markdown("")

    # 核心功能三卡片
    c1, c2, c3 = st.columns(3, gap="medium")
    with c1:
        render_module_card("🧠", "AI 智能备课",
            "自动生成结构化教案<br>分层习题智能设计<br>教学素材精准推荐<br>课件大纲一键生成",
            "#4F46E5", "#7C3AED")
    with c2:
        render_module_card("📊", "学情分析引擎",
            "成绩趋势追踪分析<br>知识图谱精准诊断<br>学习风险早期预警<br>多维度学习画像",
            "#0EA5E9", "#06B6D4")
    with c3:
        render_module_card("🎯", "个性化推荐",
            "最优学习路径规划<br>自适应难度调整<br>间隔重复复习安排<br>学习资源智能匹配",
            "#F59E0B", "#EF4444")

    st.markdown("")
    st.markdown("---")

    # 数据概览
    st.markdown("### 📈 数据概览")
    students = get_student_map()
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("学生总数", f"{len(students)} 人")
    m2.metric("覆盖学科", "数学 / 物理")
    m3.metric("AI 引擎", "通义千问")
    m4.metric("系统版本", "v1.0.0")

    st.markdown("")
    st.markdown("### 🏗️ 系统架构")
    st.code(
        "┌──────────┐     ┌───────────────┐     ┌──────────────┐     ┌────────────┐\n"
        "│ Streamlit │────▶│  FastAPI 网关  │────▶│  核心引擎层  │────▶│ 通义千问 AI │\n"
        "│  前端看板  │     │  RESTful API  │     │ 备课/学情/推荐 │     │ DashScope  │\n"
        "└──────────┘     └──────┬────────┘     └──────────────┘     └────────────┘\n"
        "                       │\n"
        "                ┌──────▼────────┐\n"
        "                │  SQLite/PG    │\n"
        "                │   数据持久层   │\n"
        "                └───────────────┘",
        language=None,
    )


# ============================================================
# 📝 智能备课
# ============================================================
elif page == "📝 智能备课":
    st.markdown("# 📝 AI 智能备课系统")
    st.caption("基于大语言模型，自动生成符合课标的结构化教案与分层习题")

    tab1, tab2, tab3 = st.tabs(["📄 教案生成", "🎯 习题设计", "📋 教案列表"])

    # ---- 教案生成 ----
    with tab1:
        with st.container():
            st.markdown("#### 填写备课参数")
            c1, c2, c3 = st.columns(3)
            with c1:
                subject = st.selectbox("学科", ["数学", "语文", "英语", "物理", "化学"], key="lp_subj")
                grade = st.selectbox("年级", ["七年级", "八年级", "九年级", "高一", "高二", "高三"], key="lp_grade")
            with c2:
                lesson_type = st.selectbox("课型", ["新授课", "复习课", "实验课", "项目式"], key="lp_type")
                student_level = st.selectbox("学生基础", ["混合", "基础薄弱", "中等", "优秀"], key="lp_level")
            with c3:
                duration = st.slider("课时（分钟）", 20, 120, 45, key="lp_dur")
                topic = st.text_input("课题名称 *", placeholder="例：一元二次方程的解法", key="lp_topic")

            c_left, c_right = st.columns(2)
            with c_left:
                special_req = st.text_area("特殊要求（可选）", placeholder="例：融入信息技术、注重小组合作", height=80, key="lp_req")
            with c_right:
                existing_mat = st.text_area("已有资源（可选）", placeholder="例：教材第3章第2节", height=80, key="lp_mat")

        if st.button("🚀 生成教案", type="primary", use_container_width=True, key="btn_lp"):
            if not topic:
                st.warning("请输入课题名称")
            else:
                with st.spinner("🤖 AI 正在生成教案，请耐心等待（约 15-30 秒）..."):
                    result = api_post("/lesson-prep/generate", {
                        "subject": subject, "grade": grade, "topic": topic,
                        "duration": duration, "lesson_type": lesson_type,
                        "student_level": student_level,
                        "special_requirements": special_req or None,
                        "existing_materials": existing_mat or None,
                    })
                if result and result.get("success"):
                    data = result["data"]
                    conf = data.get("ai_confidence", 0)
                    st.success(f"教案生成成功！AI 置信度：{conf:.0%}")
                    st.markdown("---")
                    st.markdown(data.get("full_content", ""))
                elif result:
                    st.error(f"生成失败：{result.get('message', result)}")

    # ---- 习题设计 ----
    with tab2:
        st.markdown("#### 分层习题参数")
        c1, c2 = st.columns([2, 1])
        with c1:
            q_subject = st.selectbox("学科", ["数学", "物理", "化学"], key="qz_subj")
            knowledge_point = st.text_input("目标知识点 *", placeholder="例：一元二次方程", key="qz_kp")
            count = st.slider("题目数量", 3, 20, 6, key="qz_cnt")
        with c2:
            st.markdown("**难度分布**")
            basic_pct = st.slider("基础层 %", 0, 100, 40, key="qz_b")
            inter_pct = st.slider("提高层 %", 0, 100, 40, key="qz_i")
            adv_pct = st.slider("拓展层 %", 0, 100, 20, key="qz_a")
            total_pct = basic_pct + inter_pct + adv_pct
            if total_pct != 100:
                st.warning(f"当前占比总和 {total_pct}%，建议调整为 100%")

        if st.button("🎯 生成习题", type="primary", use_container_width=True, key="btn_qz"):
            if not knowledge_point:
                st.warning("请输入知识点")
            else:
                with st.spinner("🤖 AI 正在设计分层习题..."):
                    result = api_post("/lesson-prep/quiz", {
                        "subject": q_subject, "knowledge_point": knowledge_point,
                        "basic_percent": basic_pct, "intermediate_percent": inter_pct,
                        "advanced_percent": adv_pct, "count": count,
                    })
                if result and result.get("success"):
                    data = result["data"]
                    st.success(f"已生成 {data.get('total_count', 0)} 道习题")

                    # 难度分布饼图
                    dist = data.get("difficulty_distribution", {})
                    if dist:
                        fig = go.Figure(go.Pie(
                            labels=list(dist.keys()), values=list(dist.values()),
                            hole=0.45, marker_colors=["#22C55E", "#F59E0B", "#EF4444"],
                        ))
                        plotly_layout_defaults(fig, 280)
                        fig.update_layout(title="难度分布", showlegend=True)
                        st.plotly_chart(fig, use_container_width=True)

                    for idx, q in enumerate(data.get("questions", []), 1):
                        level = q.get("cognitive_level", "")
                        content = q.get("content", "")[:100]
                        with st.expander(f"第 {idx} 题  [{level}]  {content}"):
                            st.markdown(f"**题目：** {q.get('content', '')}")
                            st.markdown(f"**答案：** {q.get('answer', '')}")
                            mc1, mc2 = st.columns(2)
                            mc1.metric("难度系数", f"{q.get('difficulty', 0):.2f}")
                            mc2.metric("认知层次", level)
                            if q.get("common_errors"):
                                st.info(f"常见错误：{'、'.join(q['common_errors'])}")

    # ---- 教案列表 ----
    with tab3:
        plans = api_get("/lesson-prep/plans")
        items = plans.get("items", []) if plans else []
        if items:
            for p in items:
                conf = p.get("ai_confidence", 0)
                date = p.get("created_at", "")[:10]
                st.markdown(
                    f'<div class="info-card">'
                    f'<h3>{p["topic"]}</h3>'
                    f'<p>{p["subject"]} · {p["grade"]} · {p.get("lesson_type","新授课")} · '
                    f'AI 置信度 <strong>{conf:.0%}</strong> · {date}</p></div>',
                    unsafe_allow_html=True,
                )
        else:
            st.info("暂无教案记录，请先在「教案生成」页生成一份教案。")


# ============================================================
# 📊 学情分析
# ============================================================
elif page == "📊 学情分析":
    st.markdown("# 📊 学情分析引擎")
    st.caption("多维度洞察学习状态，精准定位知识薄弱点")

    students = get_student_map()
    if not students:
        st.warning("暂无学生数据，请先运行种子数据脚本。")
        st.stop()

    # 学生选择器
    sel_col, _ = st.columns([1, 2])
    with sel_col:
        selected_id = st.selectbox(
            "选择学生",
            options=list(students.keys()),
            format_func=lambda x: f"👤 {students[x]['name']}（{students[x].get('grade','')}）",
            key="ana_stu",
        )

    tab1, tab2, tab3 = st.tabs(["🧑‍🎓 学习画像", "📈 成绩趋势", "🗺️ 知识图谱"])

    # ---- 学习画像 ----
    with tab1:
        profile = api_get(f"/students/{selected_id}/profile", {"subject": "数学"})
        if profile:
            stu = profile.get("student", {})
            perf = profile.get("performance_trend", {})
            ability = profile.get("ability_radar", {})
            overall = profile.get("overall_mastery", 0)

            # 头部指标
            st.markdown(f"### {stu.get('name', '')} 的学习画像")
            m1, m2, m3, m4 = st.columns(4)
            m1.metric("当前成绩", f"{perf.get('current_score', 0)} 分")
            m2.metric("平均成绩", f"{perf.get('average_score', 0)} 分")
            trend = perf.get("trend", "无数据")
            slope = perf.get("trend_slope", 0)
            m3.metric("成绩趋势", trend, delta=f"斜率 {slope:+.1f}" if slope else None,
                       delta_color="normal" if slope >= 0 else "inverse")
            m4.metric("整体掌握度", f"{overall:.0%}")

            st.markdown("")
            cl, cr = st.columns([1, 1])

            # 能力雷达图
            with cl:
                if ability:
                    cats = list(ability.keys())
                    vals = list(ability.values())
                    fig = go.Figure(go.Scatterpolar(
                        r=vals + [vals[0]], theta=cats + [cats[0]],
                        fill="toself", fillcolor="rgba(79,70,229,0.15)",
                        line=dict(color="#4F46E5", width=2.5),
                        marker=dict(size=6),
                    ))
                    fig.update_layout(
                        polar=dict(
                            radialaxis=dict(visible=True, range=[0, 1], tickfont=dict(size=10)),
                            angularaxis=dict(tickfont=dict(size=12)),
                        ),
                        title=dict(text="能力分布雷达图", font=dict(size=15)),
                        showlegend=False,
                    )
                    plotly_layout_defaults(fig, 380)
                    st.plotly_chart(fig, use_container_width=True)

            # 知识点掌握热力条
            with cr:
                kstate = profile.get("knowledge_state", {})
                if kstate:
                    names = list(kstate.keys())
                    vals = list(kstate.values())
                    colors = ["#22C55E" if v >= 0.8 else "#F59E0B" if v >= 0.6 else "#EF4444" for v in vals]
                    fig = go.Figure(go.Bar(
                        x=vals, y=names, orientation="h",
                        marker_color=colors,
                        text=[f"{v:.0%}" for v in vals], textposition="inside",
                        textfont=dict(color="white", size=13, family="Microsoft YaHei"),
                    ))
                    fig.update_layout(
                        title=dict(text="知识点掌握度", font=dict(size=15)),
                        xaxis=dict(range=[0, 1], tickformat=".0%"),
                        yaxis=dict(autorange="reversed"),
                    )
                    plotly_layout_defaults(fig, 380)
                    st.plotly_chart(fig, use_container_width=True)

            # 知识断点警示
            gaps = profile.get("knowledge_gaps", {})
            prereq = gaps.get("prerequisite_gaps", [])
            if prereq:
                st.markdown("#### ⚠️ 前置知识缺失")
                for g in prereq:
                    st.warning(
                        f"**{g['knowledge_point']}**（掌握度 {g['current_mastery']:.0%}）→ {g['suggestion']}"
                    )

    # ---- 成绩趋势 ----
    with tab2:
        perf = api_get(f"/analytics/student/{selected_id}/performance", {"subject": "数学"})
        if perf and perf.get("history"):
            history = perf["history"]

            # 趋势折线图
            exam_names = [h["exam_name"] for h in history]
            scores = [h["score"] for h in history]
            avg = perf.get("average_score", 0)

            fig = go.Figure()
            fig.add_trace(go.Scatter(
                x=exam_names, y=scores, mode="lines+markers+text",
                name="成绩", text=[str(s) for s in scores], textposition="top center",
                line=dict(color="#4F46E5", width=3),
                marker=dict(size=10, color="#4F46E5"),
            ))
            fig.add_hline(y=avg, line_dash="dash", line_color="#94A3B8",
                          annotation_text=f"平均 {avg}", annotation_position="top right")
            fig.update_layout(title="数学成绩趋势", yaxis_title="分数",
                              xaxis_title="考试", yaxis=dict(range=[0, 110]))
            plotly_layout_defaults(fig, 400)
            st.plotly_chart(fig, use_container_width=True)

            # 汇总指标
            mc1, mc2, mc3, mc4 = st.columns(4)
            mc1.metric("最新成绩", f"{perf['current_score']} 分")
            mc2.metric("平均成绩", f"{perf['average_score']} 分")
            mc3.metric("趋势", perf["trend"], delta=f"斜率 {perf['trend_slope']:+.1f}",
                       delta_color="normal" if perf["trend_slope"] >= 0 else "inverse")
            mc4.metric("百分位", f"Top {max(0, 100 - perf.get('percentile', 0)):.0f}%")
        else:
            st.info("暂无成绩数据")

    # ---- 知识图谱 ----
    with tab3:
        km = api_get(f"/analytics/student/{selected_id}/knowledge-map", {"subject": "数学"})
        if km:
            graph = km.get("knowledge_graph", {})
            kps = graph.get("knowledge_points", {})
            if kps:
                names = list(kps.keys())
                masteries = [kps[n]["mastery"] for n in names]
                categories = [kps[n].get("category", "其他") for n in names]
                statuses = [kps[n].get("status", "") for n in names]
                color_map = {"已掌握": "#22C55E", "待巩固": "#F59E0B", "薄弱": "#EF4444"}
                colors = [color_map.get(s, "#94A3B8") for s in statuses]

                fig = go.Figure(go.Bar(
                    x=masteries, y=names, orientation="h",
                    marker_color=colors,
                    text=[f"{m:.0%}  {s}" for m, s in zip(masteries, statuses)],
                    textposition="inside",
                    textfont=dict(color="white", size=12),
                ))
                fig.update_layout(
                    title="知识点掌握图谱",
                    xaxis=dict(range=[0, 1], tickformat=".0%", title="掌握度"),
                    yaxis=dict(autorange="reversed"),
                )
                plotly_layout_defaults(fig)
                st.plotly_chart(fig, use_container_width=True)

                # 图例
                st.markdown(
                    '<span class="tag tag-green">已掌握 ≥80%</span> &nbsp; '
                    '<span class="tag tag-yellow">待巩固 60-80%</span> &nbsp; '
                    '<span class="tag tag-red">薄弱 &lt;60%</span>',
                    unsafe_allow_html=True,
                )

                # 分类汇总
                cat_mastery = graph.get("category_mastery", {})
                if cat_mastery:
                    st.markdown("#### 分类掌握度")
                    cols = st.columns(len(cat_mastery))
                    for i, (cat, val) in enumerate(cat_mastery.items()):
                        cols[i].metric(cat, f"{val:.0%}")

            diagnosis = km.get("diagnosis", {})
            if diagnosis.get("prerequisite_gaps"):
                st.markdown("#### ⚠️ 前置知识缺失预警")
                for gap in diagnosis["prerequisite_gaps"]:
                    st.error(
                        f"**{gap['knowledge_point']}**（当前 {gap['current_mastery']:.0%}）\n\n"
                        f"缺失前置：{'、'.join(gap['missing_prerequisites'])} → {gap['suggestion']}"
                    )


# ============================================================
# 🎯 个性化推荐
# ============================================================
elif page == "🎯 个性化推荐":
    st.markdown("# 🎯 个性化学习推荐")
    st.caption("基于知识状态与学习风格，规划最优学习路径")

    students = get_student_map()
    if not students:
        st.warning("暂无学生数据")
        st.stop()

    sel_col, _ = st.columns([1, 2])
    with sel_col:
        selected_id = st.selectbox(
            "选择学生",
            options=list(students.keys()),
            format_func=lambda x: f"👤 {students[x]['name']}",
            key="per_stu",
        )

    tab1, tab2, tab3 = st.tabs(["🛤️ 学习路径", "📚 资源推荐", "🔁 复习计划"])

    with tab1:
        st.markdown("#### 生成个性化学习路径")
        c1, c2 = st.columns(2)
        with c1:
            objective = st.text_input("学习目标 *", placeholder="例：期末数学提升到85分以上", key="path_obj")
        with c2:
            time_constraint = st.text_input("时间约束（可选）", placeholder="例：3 周内", key="path_time")

        if st.button("🛤️ 生成路径", type="primary", use_container_width=True, key="btn_path"):
            if not objective:
                st.warning("请输入学习目标")
            else:
                with st.spinner("🤖 AI 正在规划个性化学习路径..."):
                    result = api_post("/personalization/path", {
                        "student_id": selected_id, "subject": "数学",
                        "learning_objective": objective,
                        "time_constraint": time_constraint or None,
                    })
                if result and result.get("success"):
                    data = result["data"]
                    st.success(f"路径规划完成！预估时长：{data.get('estimated_duration', '未知')}")
                    for stage in data.get("stages", []):
                        with st.expander(f"📌 阶段 {stage.get('stage', '')}：{stage.get('objective', '')}", expanded=True):
                            for item in stage.get("content_sequence", []):
                                icon = {"讲解": "📖", "练习": "✏️", "测试": "📝"}.get(item.get("type", ""), "📦")
                                st.markdown(f"- {icon} **{item.get('title', '')}** — {item.get('estimated_time', '')}")
                            if stage.get("checkpoint"):
                                st.info(f"🎯 阶段测评：{stage['checkpoint']}")

    with tab2:
        st.markdown("#### 智能资源推荐")
        recs = api_get(f"/personalization/student/{selected_id}/recommendations")
        items = recs.get("items", []) if recs else []
        if items:
            for r in items:
                quality = r.get("quality_score", 0)
                stars = "⭐" * int(quality)
                st.markdown(
                    f'<div class="info-card">'
                    f'<h3>#{r["rank"]} {r["title"]}</h3>'
                    f'<p>类型：{r["type"]} · 评分：{stars} ({quality:.1f}) · {r.get("reason","")}</p></div>',
                    unsafe_allow_html=True,
                )
        else:
            st.info("暂无推荐资源，请先生成学习路径。")

    with tab3:
        st.markdown("#### 间隔重复复习计划")
        st.caption("基于 Leitner 系统，科学安排复习间隔")
        schedule = api_get(f"/personalization/student/{selected_id}/review-schedule")
        items = schedule.get("items", []) if schedule else []
        if items:
            for item in items:
                urgency = item.get("urgency", "低")
                tag_cls = {"高": "tag-red", "中": "tag-yellow", "低": "tag-green"}.get(urgency, "tag-blue")
                mastery = item.get("current_mastery", 0)
                interval = item.get("interval_days", 0)

                st.markdown(
                    f'<div class="info-card" style="display:flex;align-items:center;justify-content:space-between;">'
                    f'<div><strong>{item["knowledge_point"]}</strong><br>'
                    f'<span style="color:#64748b">掌握度 {mastery:.0%} · 复习间隔 {interval} 天</span></div>'
                    f'<span class="tag {tag_cls}">紧急度：{urgency}</span></div>',
                    unsafe_allow_html=True,
                )
        else:
            st.info("暂无需要复习的知识点。")


# ============================================================
# ⚠️ 风险预警
# ============================================================
elif page == "⚠️ 风险预警":
    st.markdown("# ⚠️ 学习风险预警看板")
    st.caption("自动识别学习风险，提供干预建议")

    c_filter, c_action, _ = st.columns([1, 1, 2])
    with c_filter:
        risk_filter = st.selectbox("风险等级筛选", ["全部", "high", "medium", "low"],
                                   format_func=lambda x: {"全部": "📋 全部", "high": "🔴 高风险", "medium": "🟡 中风险", "low": "🟢 低风险"}[x])
    with c_action:
        if st.button("🔄 刷新数据", key="btn_refresh"):
            st.rerun()

    params = {"limit": 50}
    if risk_filter != "全部":
        params["risk_level"] = risk_filter

    alerts = api_get("/analytics/risk-alerts", params)
    items = alerts.get("items", []) if alerts else []

    if items:
        # 汇总统计
        high_cnt = sum(1 for a in items if a.get("risk_level") == "high")
        med_cnt = sum(1 for a in items if a.get("risk_level") == "medium")
        low_cnt = sum(1 for a in items if a.get("risk_level") == "low")

        s1, s2, s3, s4 = st.columns(4)
        s1.metric("预警总数", len(items))
        s2.metric("🔴 高风险", high_cnt)
        s3.metric("🟡 中风险", med_cnt)
        s4.metric("🟢 低风险", low_cnt)

        st.markdown("---")

        for alert in items:
            level = alert.get("risk_level", "low")
            tag_html = render_risk_tag(level)
            name = alert.get("student_name", "未知")
            rtype = alert.get("risk_type", "")
            conf = alert.get("confidence_score", 0)
            type_label = {"knowledge_gap": "知识断层", "motivation": "动机衰减",
                          "methodology": "方法不当", "external": "外部干扰"}.get(rtype, rtype)

            with st.expander(f"{name}  ·  {type_label}  ·  置信度 {conf:.0%}"):
                st.markdown(f"风险等级：{tag_html} &nbsp;&nbsp; 类型：**{type_label}**", unsafe_allow_html=True)

                indicators = alert.get("indicators", [])
                if indicators:
                    st.markdown("**📋 风险指标：**")
                    for ind in indicators:
                        st.markdown(f"- {ind}")

                suggestions = alert.get("intervention_suggestions", [])
                if suggestions:
                    st.markdown("**💡 干预建议：**")
                    for sug in suggestions:
                        if isinstance(sug, dict):
                            st.markdown(
                                f"- **[P{sug.get('priority', '')}]** {sug.get('action', '')}  "
                                f"（{sug.get('responsible', '')} · {sug.get('timeline', '')}）  "
                                f"→ 预期：{sug.get('expected_outcome', '')}"
                            )
                        else:
                            st.markdown(f"- {sug}")
    else:
        st.markdown(
            '<div class="info-card" style="text-align:center;padding:48px">'
            '<h3 style="color:#22C55E">✅ 暂无风险预警</h3>'
            '<p>所有学生学习状态良好</p></div>',
            unsafe_allow_html=True,
        )


# ============================================================
# 📄 试卷扫描
# ============================================================
elif page == "📄 试卷扫描":
    st.markdown("# 📄 试卷扫描与智能分析")
    st.caption("拍照上传试卷 → AI 识别题目 → 分析知识点 → 生成针对性强化试卷")

    tab1, tab2, tab3 = st.tabs(["📸 上传试卷", "📊 题目分析", "🎯 生成强化试卷"])

    # ---- 上传试卷 ----
    with tab1:
        st.markdown("#### 📸 拍照/上传试卷")
        st.caption("支持 JPG/PNG 图片或 PDF 文件，AI 将自动识别题目")

        c1, c2, c3 = st.columns(3)
        with c1:
            paper_name = st.text_input("试卷名称 *", placeholder="例：八年级数学期中考试", key="scan_name")
            paper_type = st.selectbox("试卷类型", ["考试", "晚自习作业", "周测", "月考", "期中", "期末"], key="scan_type")
        with c2:
            subject = st.selectbox("学科", ["数学", "物理", "化学", "语文", "英语"], key="scan_subj")
            exam_date = st.date_input("考试日期", value=None, key="scan_date")
        with c3:
            # 获取班级列表
            students_data = api_get("/students", {"page_size": 100})
            class_map = {}
            if students_data and students_data.get("items"):
                for s in students_data["items"]:
                    grade = s.get("grade", "")
                    if grade and grade not in class_map:
                        class_map[grade] = s.get("class_id", "")
            selected_class = st.selectbox("班级", list(class_map.keys()) if class_map else ["八年级"], key="scan_class")
            class_id = class_map.get(selected_class, "")

        # 文件上传
        st.markdown("---")
        st.markdown("#### 📤 上传试卷文件")

        uploaded_file = st.file_uploader(
            "选择试卷图片/PDF",
            type=["jpg", "jpeg", "png", "pdf"],
            help="支持手机拍照上传或扫描件",
            key="paper_upload",
        )

        if uploaded_file:
            st.success(f"已选择文件：{uploaded_file.name}")

            # 文件预览
            if uploaded_file.type.startswith("image"):
                st.image(uploaded_file, caption="试卷预览", use_container_width=True)

        # OCR 文本输入（备用方案）
        with st.expander("📝 或手动输入/粘贴 OCR 文本"):
            ocr_text = st.text_area(
                "粘贴 OCR 识别后的文本",
                placeholder="例：\n1. 解方程：x² - 5x + 6 = 0\n2. 已知二次函数 y = x² - 4x + 3，求顶点坐标\n...",
                height=200,
                key="ocr_input",
            )

        # 提交按钮
        if st.button("🤖 AI 识别题目", type="primary", use_container_width=True, key="btn_parse_paper"):
            if not paper_name:
                st.warning("请输入试卷名称")
            elif not class_id:
                st.warning("请选择班级")
            elif not uploaded_file and not ocr_text:
                st.warning("请上传试卷文件或输入 OCR 文本")
            else:
                with st.spinner("🤖 AI 正在识别题目、分析知识点和难度..."):
                    result = api_post("/paper-scan/scans", {
                        "class_id": class_id,
                        "subject": subject,
                        "paper_name": paper_name,
                        "paper_type": paper_type,
                        "exam_date": exam_date.isoformat() if exam_date else None,
                        "ocr_text": ocr_text,
                        "file_path": None,
                        "file_type": "image" if uploaded_file and uploaded_file.type.startswith("image") else "pdf",
                    })
                if result and result.get("success"):
                    data = result.get("data", {})
                    st.success(f"识别成功！共 {data.get('total_questions', 0)} 道题目")

                    # 显示知识点分布
                    kb = data.get("knowledge_breakdown", {})
                    if kb:
                        st.markdown("#### 📊 知识点分布")
                        for kp, info in kb.items():
                            st.markdown(f"- **{kp}**：{info['count']} 题，平均难度 {info['avg_difficulty']:.2f}")

                    # 显示难度分布
                    dd = data.get("difficulty_distribution", {})
                    if dd:
                        st.markdown("#### 📈 难度分布")
                        cols = st.columns(len(dd))
                        for i, (label, count) in enumerate(dd.items()):
                            cols[i].metric(label, count)

                    # 跳转至分析页
                    st.info("✅ 试卷已录入，请切换到「题目分析」页查看详细内容")
                    st.session_state["last_scan_id"] = data.get("id")
                elif result:
                    st.error(f"识别失败：{result.get('message', result)}")

    # ---- 题目分析 ----
    with tab2:
        st.markdown("#### 📊 试卷题目分析")

        # 获取扫描列表
        scans = api_get("/paper-scan/scans", {"limit": 20})
        scan_items = scans.get("items", []) if scans else []

        if scan_items:
            scan_map = {s["id"]: s["paper_name"] for s in scan_items}
            selected_scan_id = st.selectbox(
                "选择试卷",
                options=list(scan_map.keys()),
                format_func=lambda x: scan_map[x],
                key="analyze_scan",
            )

            # 获取详情
            detail = api_get(f"/paper-scan/scans/{selected_scan_id}")
            if detail:
                # 头部信息
                c1, c2, c3 = st.columns(3)
                c1.metric("题目总数", detail.get("total_questions", 0))
                c2.metric("学科", detail.get("subject", ""))
                c3.metric("类型", detail.get("paper_type", ""))

                # AI 分析
                if detail.get("ai_analysis"):
                    st.markdown("#### 🤖 AI 试卷分析")
                    st.info(detail["ai_analysis"])

                # 知识点分布图
                kb = detail.get("knowledge_breakdown", {})
                if kb:
                    st.markdown("#### 📊 知识点分布")
                    kps = list(kb.keys())
                    counts = [kb[k]["count"] for k in kps]
                    diffs = [kb[k]["avg_difficulty"] for k in kps]

                    fig = go.Figure()
                    fig.add_trace(go.Bar(
                        x=kps, y=counts, name="题目数量",
                        marker_color="#4F46E5",
                    ))
                    fig.add_trace(go.Scatter(
                        x=kps, y=diffs, name="平均难度",
                        mode="lines+markers",
                        line=dict(color="#EF4444", width=2),
                        marker=dict(size=8),
                        yaxis="y2",
                    ))
                    fig.update_layout(
                        title="知识点分布与难度",
                        yaxis=dict(title="题目数量"),
                        yaxis2=dict(title="难度系数", overlaying="y", side="right", range=[0, 1]),
                        barmode="group",
                        height=400,
                    )
                    plotly_layout_defaults(fig)
                    st.plotly_chart(fig, use_container_width=True)

                # 题目列表
                questions = detail.get("questions", [])
                if questions:
                    st.markdown(f"#### 📝 题目列表（{len(questions)} 道）")
                    for idx, q in enumerate(questions, 1):
                        with st.expander(
                            f"第 {idx} 题 | {q.get('question_type', '')} | "
                            f"知识点：{q.get('knowledge_point', '未标注')} | "
                            f"难度：{q.get('difficulty', 0):.2f}"
                        ):
                            st.markdown(f"**题目：** {q.get('content', '')}")
                            if q.get("answer"):
                                st.markdown(f"**答案：** {q['answer']}")

                # 难度分布
                dd = detail.get("difficulty_distribution", {})
                if dd:
                    st.markdown("#### 📈 难度分布")
                    fig = go.Figure(go.Pie(
                        labels=list(dd.keys()),
                        values=list(dd.values()),
                        hole=0.45,
                        marker_colors=["#22C55E", "#F59E0B", "#EF4444"],
                    ))
                    plotly_layout_defaults(fig, 300)
                    fig.update_layout(showlegend=True)
                    st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("暂无试卷数据，请先在「上传试卷」页录入。")

    # ---- 生成强化试卷 ----
    with tab3:
        st.markdown("#### 🎯 生成针对性强化试卷")
        st.caption("基于试卷扫描结果，AI 自动分析薄弱知识点，生成强化练习")

        # 选择原试卷
        scans = api_get("/paper-scan/scans", {"limit": 20})
        scan_items = scans.get("items", []) if scans else []

        if scan_items:
            scan_map = {s["id"]: s["paper_name"] for s in scan_items}
            selected_scan_id = st.selectbox(
                "基于哪份试卷生成强化练习",
                options=list(scan_map.keys()),
                format_func=lambda x: scan_map[x],
                key="gen_scan",
            )

            # 获取原试卷详情
            orig_detail = api_get(f"/paper-scan/scans/{selected_scan_id}")
            if orig_detail:
                # 显示薄弱知识点
                kb = orig_detail.get("knowledge_breakdown", {})
                if kb:
                    st.markdown("#### 📌 薄弱知识点（自动分析）")
                    weak_kps = [
                        kp for kp, info in kb.items()
                        if info.get("avg_difficulty", 0) > 0.6 or info.get("count", 0) > 3
                    ]
                    for kp in weak_kps:
                        info = kb[kp]
                        st.warning(
                            f"**{kp}** — {info['count']} 题，平均难度 {info['avg_difficulty']:.2f}"
                        )

                c1, c2 = st.columns(2)
                with c1:
                    quiz_name = st.text_input("强化试卷名称", placeholder="例：一元二次方程强化练习", key="gen_quiz_name")
                    quiz_type = st.selectbox("试卷类型", ["考试", "晚自习作业", "周测", "月考"], key="gen_type")
                with c2:
                    question_count = st.slider("题目数量", 5, 50, 20, key="gen_cnt")
                    easy_pct = st.slider("基础题占比 %", 0, 100, 30, key="gen_easy")
                    med_pct = st.slider("中等题占比 %", 0, 100, 50, key="gen_med")
                    hard_pct = st.slider("难题占比 %", 0, 100, 20, key="gen_hard")

                # 手动添加重点知识点
                st.markdown("#### 🎯 额外指定重点知识点（可选）")
                focus_kps_input = st.text_input(
                    "",
                    placeholder="例：一元二次方程,二次函数（逗号分隔）",
                    key="gen_focus_kp",
                )

                if st.button("🚀 生成强化试卷", type="primary", use_container_width=True, key="btn_gen_targeted"):
                    if not quiz_name:
                        st.warning("请输入强化试卷名称")
                    else:
                        focus_list = [kp.strip() for kp in focus_kps_input.split(",") if kp.strip()] if focus_kps_input else None

                        with st.spinner("🤖 AI 正在分析薄弱点并生成针对性试卷..."):
                            result = api_post("/paper-scan/generate-targeted-quiz", {
                                "source_scan_id": selected_scan_id,
                                "class_id": orig_detail.get("class_id", ""),
                                "quiz_name": quiz_name,
                                "quiz_type": quiz_type,
                                "question_count": question_count,
                                "difficulty_distribution": {
                                    "简单": easy_pct / 100,
                                    "中等": med_pct / 100,
                                    "困难": hard_pct / 100,
                                },
                                "focus_knowledge_points": focus_list,
                            })
                        if result and result.get("success"):
                            data = result.get("data", {})
                            st.success("强化试卷生成成功！")

                            # 显示薄弱点分析
                            weak = data.get("weak_points", [])
                            student_err = data.get("student_error_points", [])
                            focus = data.get("focus_knowledge_points", [])

                            if weak:
                                st.markdown("#### 📌 薄弱知识点分析")
                                for wp in weak:
                                    st.warning(
                                        f"**{wp['knowledge_point']}** — {wp['reason']} "
                                        f"({wp.get('question_count', 0)} 题, 难度 {wp.get('avg_difficulty', 0):.2f})"
                                    )

                            if student_err:
                                st.markdown("#### ❌ 学生高频错题知识点")
                                for kp in student_err[:5]:
                                    st.error(f"**{kp}**")

                            if focus:
                                st.markdown("#### 🎯 最终重点覆盖知识点")
                                for kp in focus:
                                    st.info(f"• {kp}")

                            st.markdown("---")
                            st.markdown("#### 📝 强化试卷内容")
                            st.markdown(data.get("full_content", ""))
                        elif result:
                            st.error(f"生成失败：{result.get('message', result)}")
        else:
            st.info("暂无试卷数据，请先录入试卷后再生成强化试卷。")
