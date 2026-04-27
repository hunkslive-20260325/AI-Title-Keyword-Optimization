import streamlit as st
import pandas as pd
import requests
import json
import re

# ================= 页面配置 =================
st.set_page_config(page_title="TikTok Shop 标题精细化优化器", layout="wide", page_icon="🎯")
st.title("🎯 TikTok Shop 标题精细化优化器 (高阶运营版)")

# ================= 侧边栏配置 =================
with st.sidebar:
    st.header("⚙️ 基础配置")
    api_key = st.text_input("OpenRouter API Key", type="password", help="请输入你的 OpenRouter API Key")
    
    model_choice = st.selectbox(
        "选择 AI 模型", 
        [
            "openai/gpt-4o",                # 逻辑最稳，首选
            "anthropic/claude-3.5-sonnet",    # 文案极其自然
            "google/gemini-2.0-flash",       # 响应极快
            "openai/gpt-4o-mini"
        ]
    )
    
    st.divider()
    st.header("🛡️ 优化策略")
    keep_original = st.slider("原标题词序保留权重", 0, 100, 85, help="数值越高，AI 越倾向于在原标题基础上修饰，而不是重写")

# ================= 主区域输入 (商品信息) =================
st.header("📦 商品基础特征")
col_info1, col_info2, col_info3 = st.columns([2, 1, 1])

with col_info1:
    original_title = st.text_input("原始商品标题 (必填)", placeholder="例如: Simple Gold Necklace for Women")
with col_info2:
    category = st.selectbox(
        "饰品类型",
        ["项链", "耳环", "脚链", "戒指", "手环与手链", "首饰吊件及装饰", "身体饰品", "钥匙扣", "首饰套装", "珠宝调节保护工具"]
    )
with col_info3:
    quantity = st.number_input("商品数量", min_value=1, value=1, step=1)

st.divider()

# ================= 上传区域 (关键词) =================
st.subheader("📊 上传精准关键词")
uploaded_excel = st.file_uploader("上传 Excel 文件 (.xlsx)", type=["xlsx"])
all_keywords = []

if uploaded_excel:
    try:
        df = pd.read_excel(uploaded_excel)
        all_keywords = df.iloc[:, 0].dropna().astype(str).tolist()[:30]
        st.success(f"✅ 成功加载 **{len(all_keywords)}** 个待分析关键词。")
    except Exception as e:
        st.error(f"读取 Excel 失败: {e}")

st.divider()

# ================= 核心处理逻辑 =================
def analyze_and_generate(api_key, model, original_title, category, quantity, keywords_list, weight):
    url = "https://openrouter.ai/api/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    # 核心优化点：在 Prompt 中建立锚点，限制 AI 随意发挥
    system_prompt = f"""
    你是一个资深的 TikTok Shop SEO 标题专家。你的任务是优化原标题，而不是重写一个新产品。
    
    【核心约束 - 必须遵守】
    1. **锚点保留**：原始标题为 "{original_title}"。你必须保留其中的核心产品名词和品牌语序（保留权重：{weight}%）。
    2. **数量前置**：如果数量 > 1（当前数量：{quantity}），必须以 "({quantity}Pcs)" 或 "Set of {quantity}" 开头。
    3. **关键词嵌入**：仅从给定的关键词列表中挑选高匹配词，自然地嵌入到原标题的修饰部分，不要破坏原标题的主体结构。
    4. **TikTok 风格**：地道美式英语，使用符号（如 | , &）增加可读性，禁止全大写。

    【任务流】
    1. 诊断关键词：剔除与【类目：{category}】不符的词。
    2. 智能重组：按照 [数量/营销前缀] + [原始标题核心] + [优选关键词嵌入] + [场景词] 的公式生成 5 个标题。
    
    【输出格式】
    必须只返回一个纯 JSON 对象，格式如下：
    {{
      "keyword_analysis": [
        {{ "keyword": "词", "match_level": "高/中/低", "analysis": "理由" }}
      ],
      "generated_titles": [
        {{
          "en_title": "英文标题",
          "zh_title": "中文翻译",
          "used_keywords": ["引用的词"],
          "score": 评分,
          "reason": "为何保留原标题并如何优化的说明"
        }}
      ]
    }}
    """
    
    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"待分析关键词列表：{', '.join(keywords_list)}"}
        ],
        "response_format": { "type": "json_object" } # 强制部分模型输出 JSON
    }
    
    response = requests.post(url, headers=headers, json=payload)
    response.raise_for_status()
    return response.json()['choices'][0]['message']['content']

# ================= 触发生成 =================
if st.button("🚀 开始深度诊断与生成", type="primary", use_container_width=True):
    if not api_key or not original_title or not all_keywords:
        st.warning("请确保 API Key、原始标题和关键词文件均已就绪！")
    else:
        with st.spinner("AI 正在基于原标题进行精细化嵌入优化..."):
            try:
                raw_response = analyze_and_generate(
                    api_key, model_choice, original_title, category, quantity, all_keywords, keep_original
                )
                
                # 增强型解析：使用正则提取防止 Markdown 干扰
                json_str = re.search(r'\{.*\}', raw_response, re.DOTALL).group()
                result_data = json.loads(json_str)
                
                # --- 展示诊断结果 ---
                st.subheader("🩺 关键词匹配诊断")
                df_analysis = pd.DataFrame(result_data.get("keyword_analysis", []))
                st.dataframe(df_analysis, use_container_width=True, hide_index=True)
                
                st.divider()
                
                # --- 展示生成结果 ---
                st.subheader("🏆 优化后的精细化标题")
                sorted_titles = sorted(result_data.get("generated_titles", []), key=lambda x: x['score'], reverse=True)
                
                for idx, item in enumerate(sorted_titles):
                    with st.expander(f"推荐 #{idx+1} | 匹配评分: {item['score']}", expanded=(idx == 0)):
                        st.markdown(f"**🇺🇸 英文标题:**")
                        st.code(item['en_title'], language='text')
                        st.markdown(f"**🇨🇳 中文释义:** {item['zh_title']}")
                        
                        used_kws = item.get('used_keywords', [])
                        if used_kws:
                            st.write(f"**🎯 嵌入词汇:** {' '.join([f'`{k}`' for k in used_kws])}")
                        
                        st.info(f"💡 **优化逻辑:** {item['reason']}")
                        
            except Exception as e:
                st.error(f"处理失败: {e}")
                with st.expander("查看 AI 原始返回"):
                    st.write(raw_response)
