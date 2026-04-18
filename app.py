import streamlit as st
import pandas as pd
import requests
import json

# ================= 页面配置 =================
st.set_page_config(page_title="TikTok Shop 标题精细化优化器", layout="wide", page_icon="🎯")
st.title("🎯 TikTok Shop 标题精细化优化器 (高阶运营版)")

# ================= 侧边栏配置 =================
with st.sidebar:
    st.header("⚙️ 基础配置")
    api_key = st.text_input("OpenRouter API Key", type="password", help="请输入你的 OpenRouter API Key")
    
    # 推荐使用逻辑推理能力较强的模型
    model_choice = st.selectbox(
        "选择 AI 模型", 
        [
            "openai/gpt-4o",                  # 逻辑分析最强，首选
            "anthropic/claude-3.5-sonnet",    # 极其擅长文本细腻度和合规
            "google/gemini-2.5-flash",        # 速度极快，性价比极高
            "google/gemini-1.5-pro",          
            "openai/gpt-4o-mini"
        ]
    )

# ================= 主区域输入 (商品信息) =================
st.header("📦 商品基础特征")
col_info1, col_info2, col_info3 = st.columns([2, 1, 1])

with col_info1:
    original_title = st.text_input("原始商品标题 (必填)", placeholder="例如: Simple Gold Necklace...")
with col_info2:
    category = st.selectbox(
        "饰品类型 (用于防踩雷排错)",
        ["项链", "耳环", "脚链", "戒指", "手环与手链", "首饰吊件及装饰", "身体饰品", "钥匙扣", "首饰套装", "珠宝调节保护工具"]
    )
with col_info3:
    quantity = st.number_input("商品数量 (用于智能前缀)", min_value=1, value=1, step=1)

st.divider()

# ================= 上传区域 (精准十词) =================
st.subheader("📊 上传精准关键词 (推荐 10 个左右)")
uploaded_excel = st.file_uploader("上传 Excel 文件 (.xlsx)", type=["xlsx"])
all_keywords = []

if uploaded_excel:
    try:
        df = pd.read_excel(uploaded_excel)
        # 提取第一列，最多取前 15 个，防止用户不小心传太多
        all_keywords = df.iloc[:, 0].dropna().astype(str).tolist()[:15]
        st.success(f"✅ 成功加载 **{len(all_keywords)}** 个待分析关键词。")
        st.write("待分析列表：", ", ".join(all_keywords))
    except Exception as e:
        st.error(f"读取 Excel 失败: {e}")

st.divider()

# ================= 核心处理逻辑 =================
def analyze_and_generate(api_key, model, original_title, category, quantity, keywords_list):
    url = "https://openrouter.ai/api/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    # 全新的高阶 Prompt：加入类目过滤与数量语义转化逻辑
    system_prompt = f"""
    你是一个资深的 TikTok Shop 跨境电商标题优化专家与数据分析师。
    
    【商品基础信息】
    - 饰品类别：{category}
    - 原始标题：{original_title}
    - 商品数量：{quantity}件
    
    【任务指令】
    请严格按照以下两个步骤执行任务：
    
    **第一步：多维度交叉诊断 (Keyword Diagnosis)**
    分析用户提供的每一个关键词。
    1. 剔除违规词（如大牌变体、无资质的100%纯金等）。
    2. 严格进行类目过滤：如果该关键词与当前【饰品类别：{category}】冲突（例如项链混入了“戒指”、“耳环”、“调节大小”等词），必须将其判定为“低匹配”，防止商品因乱蹭流量被限流。
    3. 给出判定（高、中、低）和极简理由。
    
    **第二步：差异化爆款组装 (Smart Assembly)**
    结合商品原标题，**仅挑选第一步中匹配度为“高”或“中”的关键词**，生成5个符合 TikTok 平台规则的英文标题。
    
    【标题生成公式规则】
    - 如果【商品数量】为 1：[修饰词] + [原始标题名词] + [场景长尾词]
    - 如果【商品数量】> 1：必须在最前面加上符合欧美电商习惯的转化词（如 {quantity} Pcs, Set of {quantity}, {quantity}-Pack 等），如果是2件也可以考虑 Couple, Matching 等词。
    
    【输出格式要求】
    你必须**只返回一个严格的 JSON 对象**，不要包含任何额外的Markdown标记（如 ```json）或解释文字。格式必须如下：
    {{
      "keyword_analysis": [
        {{
          "keyword": "关键词",
          "match_level": "高/中/低",
          "analysis": "匹配理由(20字以内)"
        }}
      ],
      "generated_titles": [
        {{
          "en_title": "英文标题",
          "zh_title": "中文翻译",
          "used_keywords": ["引用的词1", "引用的词2"],
          "score": 爆单潜力分数(0-100的整数),
          "reason": "推荐理由(50字以内)"
        }}
      ]
    }}
    """
    
    payload = {
        "model": model,
        "messages": [
            {
                "role": "system",
                "content": system_prompt
            },
            {
                "role": "user",
                "content": f"本次需要诊断并使用的热搜关键词列表：{', '.join(keywords_list)}"
            }
        ]
    }
    
    response = requests.post(url, headers=headers, json=payload)
    response.raise_for_status()
    return response.json()['choices'][0]['message']['content']

# ================= 触发生成 =================
if st.button("🚀 开始深度诊断与生成", type="primary", use_container_width=True):
    if not api_key:
        st.warning("请先在左侧侧边栏输入 OpenRouter API Key！")
    elif not original_title:
        st.warning("请填写原始商品标题，以便 AI 评估关键词匹配度！")
    elif not all_keywords:
        st.warning("请先上传包含关键词的 Excel 文件！")
    else:
        with st.spinner("AI 正在执行类目防踩雷诊断与数量语义转化，请稍候..."):
            try:
                result_text = analyze_and_generate(
                    api_key, model_choice, original_title, category, quantity, all_keywords
                )
                
                # 清理格式
                result_text = result_text.strip().removeprefix('```json').removesuffix('```').strip()
                result_data = json.loads(result_text)
                
                # ================= 展示第一部分：关键词诊断 =================
                st.subheader("🩺 第一步：关键词深度诊断报告")
                analysis_list = result_data.get("keyword_analysis", [])
                if analysis_list:
                    df_analysis = pd.DataFrame(analysis_list)
                    df_analysis = df_analysis.rename(columns={
                        "keyword": "关键词", 
                        "match_level": "匹配度", 
                        "analysis": "AI 诊断说明"
                    })
                    # 将匹配度高的排在前面方便查看
                    st.dataframe(df_analysis, use_container_width=True, hide_index=True)
                
                st.divider()
                
                # ================= 展示第二部分：生成的标题 =================
                st.subheader("🏆 第二步：智能重组高转化标题")
                titles_list = result_data.get("generated_titles", [])
                
                # 按分数排序
                sorted_titles = sorted(titles_list, key=lambda x: x['score'], reverse=True)
                
                for idx, item in enumerate(sorted_titles):
                    with st.expander(f"🏅 推荐 #{idx+1} | 潜力评分: {item['score']} 分 | {item['en_title']}", expanded=True):
                        st.markdown(f"**🇺🇸 英文标题:** `{item['en_title']}`")
                        st.markdown(f"**🇨🇳 中文释义:** {item['zh_title']}")
                        
                        # 特别展示引用的关键词
                        used_kws = item.get('used_keywords', [])
                        if used_kws:
                            kw_tags = " ".join([f"`🏷️ {kw}`" for kw in used_kws])
                            st.markdown(f"**🎯 成功引用的关键词:** {kw_tags}")
                            
                        st.markdown(f"**💡 推荐理由:** {item['reason']}")
                        
            except json.JSONDecodeError:
                st.error("AI 返回的数据格式有误，未能生成有效的 JSON，请重试。")
                st.code(result_text)
            except Exception as e:
                st.error(f"发生调用错误: {e}")
