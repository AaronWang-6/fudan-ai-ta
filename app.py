import streamlit as st
from openai import OpenAI
import docx
import io
import requests
import datetime

# =========================================================
# 【安全防护区】 - 杜绝密钥泄露、控制访问时效
# =========================================================
PRIVATE_API_KEY = st.secrets.get("API_KEY")
PRIVATE_API_BASE = st.secrets.get("API_BASE")

# 时效控制：设置二维码/网页的过期时间
EXPIRE_DATE = datetime.date(2026, 5, 28)

# =========================================================
# --- 核心资源链接定义 ---
# =========================================================
GITHUB_LESSON_PLAN_URL = "https://raw.githubusercontent.com/AaronWang-6/fudan-ai-ta/main/%E6%95%99%E6%A1%88.docx"
GITHUB_SPEECH_URL = "https://raw.githubusercontent.com/AaronWang-6/fudan-ai-ta/main/%E8%AE%B2%E7%A8%BF.docx"

# 动态机器人 GIF 路径与网页标签静态图片 PNG 路径
ROBOT_GIF_URL = "https://github.com/AaronWang-6/fudan-ai-ta/blob/main/robot.gif?raw=true"
ROBOT_PNG_URL = "https://github.com/AaronWang-6/fudan-ai-ta/blob/main/robot.png?raw=true"

# =========================================================
# --- 页面基本配置与高级 UI 定制（穿透壳层强放头像与更换标签） ---
# =========================================================
st.set_page_config(page_title="物理学系科研启航小助手", page_icon=ROBOT_PNG_URL, layout="centered")

# 通过纯文本 CSS 深度定制视觉交互，严防 f-string 语法冲突
st.markdown("""
    <style>
    /* 全局浅蓝色渐变静止背景 */
    .stApp {
        background: linear-gradient(135deg, #e0f2fe 0%, #f0fdf4 100%);
    }
    
    /* 聊天对话框容器自定义平滑淡入并向上飘入动画 */
    .stChatMessage {
        background-color: transparent !important;
        animation: bubbleFadeUp 0.4s ease-out forwards;
    }
    
    @keyframes bubbleFadeUp {
        from {
            opacity: 0;
            transform: translateY(12px);
        }
        to {
            opacity: 1;
            transform: translateY(0);
        }
    }
    
    /* 🎯 【核心修复】解除外壳限制，强行将整个头像骨架及所有子层级撑大至 64px (2倍大) */
    div[data-testid="stChatMessageAvatar"],
    div[data-testid="stChatMessageAvatar"] > div,
    div[data-testid="stChatMessageAvatar"] img {
        width: 64px !important;
        height: 64px !important;
        min-width: 64px !important;
        min-height: 64px !important;
        max-width: 64px !important;
        max-height: 64px !important;
        border-radius: 50% !important; /* 保持圆形 */
        object-fit: cover !important;  /* 确保 GIF 等比例填充不缩水 */
    }
    
    /* 让用户原生的帽子符号（🎓）在撑大的大容器中居中并完美放大 */
    div[data-testid="stChatMessageAvatar"] span {
        font-size: 40px !important;
        line-height: 64px !important;
        display: flex !important;
        align-items: center !important;
        justify-content: center !important;
    }
    
    /* 优化排版间距：拉开左侧 64px 大头像和右侧文字对话框的距离，严防重叠 */
    div[data-testid="stChatMessageContent"] {
        margin-left: 20px !important;
        padding-top: 8px !important;
    }
    
    /* 隐藏不必要的 Streamlit 默认页脚 */
    footer {visibility: hidden;}
    </style>
    """, unsafe_allow_html=True)

# --- 远程文件静默拉取与解析逻辑 ---
@st.cache_data(show_spinner="小助手正在翻阅教案与讲稿，请稍候...")
def fetch_and_extract_docx(url):
    try:
        response = requests.get(url, timeout=15)
        if response.status_code == 200:
            doc = docx.Document(io.BytesIO(response.content))
            full_text = [para.text.strip() for para in doc.paragraphs if para.text.strip()]
            return '\n'.join(full_text)
        return f"文件拉取失败，HTTP状态码: {response.status_code}"
    except Exception as e:
        return f"读取远程文件失败: {e}"

# --- 检查服务是否过期 ---
current_date = datetime.date.today()
if current_date > EXPIRE_DATE:
    st.error("⏳ 抱歉，该思政 AI 助教的本次班会服务时间已截止（过期失效）。如需重新开启，请联系负责老师。")
    st.stop()

# 静默加载教案、讲稿核心知识库
lesson_plan_content = fetch_and_extract_docx(GITHUB_LESSON_PLAN_URL)
speech_content = fetch_and_extract_docx(GITHUB_SPEECH_URL)

# =========================================================
# --- 侧边栏控制台（彻底回归最纯净清爽的模型配置区） ---
# =========================================================
with st.sidebar:
    st.title("⚛️ 助教控制台")
    st.markdown("---")
    
    st.subheader("⚙️ 模型设置")
    model_options = {
        "gpt-4o": "🎨 GPT-4o (OpenAI)",
        "deepseek-v3-0324": "🐋 DeepSeek-V3",
        "gemini-3.1-pro-preview": "♊ Gemini 3.1 Pro",
        "gpt-5.4": "🚀 GPT-5.4 (OpenAI)"
    }
    
    selected_model = st.selectbox(
        "选择 AI 引擎", 
        options=list(model_options.keys()),
        format_func=lambda x: model_options[x],
        index=0
    )
    
    max_len = st.slider("回答长度上限", 500, 4000, 2000)
    
    st.divider()
    if st.button("🔄 开启新对话 / 清除记忆"):
        st.session_state.messages = []
        st.rerun()

# --- 初始化聊天记录 ---
if "messages" not in st.session_state:
    st.session_state.messages = []

# =========================================================
# --- 主界面交互布局（标题图标完美替换为 robot.png） ---
# =========================================================
col1, col2 = st.columns([0.12, 0.88], vertical_alignment="center")
with col1:
    st.image(ROBOT_PNG_URL, use_container_width=True)
with col2:
    st.title("物理学系“科研启航”小助手")

st.markdown("“同学们，在坐热‘冷板凳’的路上，我一直都在。”")

# --- 核心系统提示词（严格遵守守界原则，融合教案与讲稿与总书记讲话） ---
SYSTEM_PROMPT = f"""
你是一个名为“科研启航小助手”的AI，专门为复旦大学物理学系《筑基高水平科技自立自强，勇坐基础研究“冷板凳”》主题班会提供服务。
你的角色是：一位懂物理系学生困境、有同理心、充满鼓励的助教。

【核心行为准则】
1. 严格守界，绝不代写：当学生问及如何完成课后任务（例如撰写《我的科研报国行动计划书》、人物小传等）时，你绝对不能直接帮学生生成完整的文本。你必须给出写作框架、启发思考的角度，鼓励他们自己动笔。
2. 紧扣资料，不盲目发散：所有的解答、举例和引导，必须严格基于下方的【教案内容】与【讲稿参考】，不要引入无关扩展。
3. 严禁说教，拒绝爹味：当学生表达焦虑（如怕毕不了业、发不出文章）时，必须先肯定情绪，并用教案中的调研数据（如78.3%的科研急躁症）来提供同理心。
4. 当学生问到与研究价值相关的问题的时候，你同时要引用一些习近平总书记的话来体现价值观，习近平总书记与此主题相关的讲话也在下方的【习近平总书记的讲话】
【核心参考资料库】
=========================================
【完整教案内容】：
{lesson_plan_content}

【上课讲稿参考】：
{speech_content}

【习近平总书记的讲话】：
1. “基础研究是整个科学体系的源头，是所有技术问题的总机关。要以更大力度、更实举措加强基础研究，提升我国原始创新能力，进一步打牢科技强国建设根基。”——2026年4月30日，习近平总书记在加强基础研究座谈会重要讲话
2. 青年科技人才是国家战略人才力量的源头活水，要放手使用优秀青年科技人才，让他们挑大梁、当主角，在科技创新的实践中成长成才——2025 年 1 月 16 日，习近平总书记在全国科技大会、国家科学技术奖励大会上的重要讲话
3. 加快实现高水平科技自立自强，是推动高质量发展的必由之路。在激烈的国际竞争中，我们要开辟发展新领域新赛道、塑造发展新动能新优势，从根本上说，还是要依靠科技创新——2024 年 3 月 5 日，习近平总书记参加十四届全国人大二次会议江苏代表团审议时的重要讲话
4. 加强基础研究，是实现高水平科技自立自强的迫切要求，是建设世界科技强国的必由之路，要从源头和底层解决关键技术问题——2024 年 6 月 24 日，习近平总书记在两院院士大会、中国科协第十次全国代表大会上的重要讲话
5. 人工智能是引领新一轮科技革命和产业变革的战略性技术，具有溢出带动性很强的 “头雁” 效应，要推动人工智能赋能千行百业——2024 年 10 月 24 日，习近平总书记在中共中央政治局第十八次集体学习时的重要讲话
6. 教育、科技、人才是全面建设社会主义现代化国家的基础性、战略性支撑，要一体推进教育科技人才事业发展，构筑人才竞争优势——2024 年 9 月 10 日，习近平总书记在全国教育大会上的重要讲话
7. 要以科技创新推动产业创新，加快形成新质生产力，不断塑造发展新动能新优势，把科技成果转化为现实生产力。——2025 年 3 月 5 日，习近平总书记参加十四姐全国人大三次会议江苏代表团审议时的重要讲话
8. 习近平总书记在二十届中央政治局第三次集体学习时强调：“加强基础研究，是实现高水平科技自立自强的迫切要求，是建设世界科技强国的必由之路。”
=========================================
"""

# 渲染历史对话（使用放大后的自定义皮肤与大号专属图标）
for message in st.session_state.messages:
    if message["role"] == "user":
        with st.chat_message("user", avatar="🎓"):
            st.markdown(f'<div style="background-color:#1e3a8a; color:white; padding:12px; border-radius:12px;">{message["content"]}</div>', unsafe_allow_html=True)
    else:
        with st.chat_message("assistant", avatar=ROBOT_GIF_URL):
            st.markdown(f'<div style="background-color:#bae6fd; color:#0f172a; padding:12px; border-radius:12px; border: 1px solid #7dd3fc;">{message["content"]}</div>', unsafe_allow_html=True)

# --- 交互输入逻辑 ---
user_input = st.chat_input("关于科研方向、毕业焦虑或班会任务，尽管和我说...")

if user_input:
    st.session_state.messages.append({"role": "user", "content": user_input})
    with st.chat_message("user", avatar="🎓"):
        st.markdown(f'<div style="background-color:#1e3a8a; color:white; padding:12px; border-radius:12px;">{user_input}</div>', unsafe_allow_html=True)

    try:
        client = OpenAI(api_key=PRIVATE_API_KEY, base_url=PRIVATE_API_BASE)
        
        with st.chat_message("assistant", avatar=ROBOT_GIF_URL):
            response_placeholder = st.empty()
            full_response = ""
            
            chat_context = [{"role": "system", "content": SYSTEM_PROMPT}]
            chat_context.extend([{"role": m["role"], "content": m["content"]} for m in st.session_state.messages])
            
            completion = client.chat.completions.create(
                model=selected_model,
                messages=chat_context,
                max_tokens=max_len,
                temperature=0.5, 
                stream=True,
            )
            
            for chunk in completion:
                content = chunk.choices[0].delta.content
                if content:
                    full_response += content
                    response_placeholder.markdown(f'<div style="background-color:#bae6fd; color:#0f172a; padding:12px; border-radius:12px; border: 1px solid #7dd3fc;">{full_response}▌</div>', unsafe_allow_html=True)
            
            response_placeholder.markdown(f'<div style="background-color:#bae6fd; color:#0f172a; padding:12px; border-radius:12px; border: 1px solid #7dd3fc;">{full_response}</div>', unsafe_allow_html=True)
        
        st.session_state.messages.append({"role": "assistant", "content": full_response})

    except Exception as e:
        st.error(f"连接小助手失败了，请稍后再试或联系老师。错误: {e}")
