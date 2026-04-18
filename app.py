import streamlit as st
import pandas as pd
import requests
import json
import random

# ================= 页面配置 =================
st.set_page_config(page_title="TikTok Shop 爆款标题优化工具", layout="wide", page_icon="🛍️")
st.title("🛍️ TikTok Shop 爆款标题优化工具 (纯文本极速版)")

# ================= 侧边栏配置 (全局设置) =================
with st.sidebar:
    st.header("⚙️ 基础配置")
    api_key = st.text_input("OpenRouter API Key", type="password", help="请输入你的 OpenRouter API Key")
    
    # 因为不需要图片了，推荐使用速度更快、成本极低的文本/轻量模型
    model_choice = st.selectbox(
        "选择 AI 模型", 
        [
            "google/gemini-2.5-flash",        # 强烈推荐，性价比极高
            "openai/gpt-4o-mini",             # 便宜且聪明
            "anthropic/claude-3-haiku",       # 速度极快
            "google/gemini-1.5-pro",
            "openai/gpt-4o",
            "google/gemini-3.1-pro-preview"
        ]
    )
    
    sample_size = st.slider("每次抽取的关键词数量", min_value=10, max_value=100, value=40, step=10, 
                            help="从你上传的 Excel 中随机抽取的关键词数量喂给 AI。不建议超过100，避免 AI 注意力分散。")

# ================= 主区域输入 (商品信息) =================
st.header("📦 商品基本信息")
col_info1, col_info2, col_info3 = st.columns([2, 1, 1])

with col_info1:
    original_title = st.text_input("原始商品标题 (必填)", placeholder="例如: Simple Gold Necklace for Women...")
with col_info2:
    category = st.selectbox(
        "饰品类型",
        ["项链", "耳环", "脚链", "戒指", "手环与手链", "首饰吊件及装饰", "身体饰品", "钥匙扣", "首饰套装", "珠宝调节保护工具"]
    )
with col_info3:
    quantity = st.number_input("商品数量 (Pack/Set)", min_value=1, value=1, step=1)

st.divider()

# ================= 上传区域 (仅关键词) =================
st.subheader("📊 上传热度关键词库")
uploaded_excel = st.file_uploader("上传包含上千个关键词的 Excel 文件 (.xlsx)", type=["xlsx"])
all_keywords = []

if uploaded_excel:
    try:
        # 读取 Excel，假设关键词在第一列
        df = pd.read_excel(uploaded_excel)
        # 清理空值并转换为字符串列表
        all_keywords = df.iloc[:, 0].dropna().astype(str).tolist()
        st.success(f"✅ 成功加载本地词库！共读取到 **{len(all_keywords)}** 个关键词。")
        with st.expander("预览词库前 10 个词"):
            st.write(", ".join(all_keywords[:10]))
    except Exception as e:
        st.error(f"读取 Excel 失败: {e}")

st.divider()

# ================= 核心处理逻辑 =================
def generate_titles(api_key, model, original_title, category, quantity, keywords_list):
    url = "https://openrouter.ai/api/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    # 纯文本的 Prompt 提示词
    system_prompt = f"""
    你是一个资深的 TikTok Shop 跨境电商标题优化专家。请根据提供的原始标题、饰品类别、商品数量以及本轮抽取的热搜关键词，生成5个具备爆单潜力的全新商品标题。
    
    【商品基础信息】
    - 饰品类别：{category}
    - 原始标题：{original_title}
    - 商品数量：{quantity}件 （如果数量>1，请务必在标题英文中自然体现，如 "{quantity} Pcs", "Set of {quantity}" 等）
    
    【合规与优化要求（至关重要）】
    1. 严格遵守 TikTok Shop 商品上架规则。
    2. 绝对禁止侵权词汇（如大牌名称的变体、仿冒暗示）。
    3. 绝对禁止虚假宣传（如无证据的“100%纯金”、“包治百病”等）。
    4. 标题需符合东南亚和欧美用户的搜索习惯。
    5. 在保留原标题核心属性的基础上，巧妙、自然地融入提供的热搜关键词。
    
    【输出格式要求】
    你必须**只返回一个严格的 JSON 数组**，不要包含任何额外的Markdown标记（如 ```json）或解释文字。格式如下：
    [
      {{
        "en_title": "英文标题",
        "zh_title": "中文翻译",
        "score": 爆单潜力分数(0-100的整数),
        "reason": "推荐理由(50字以内)"
      }}
    ]
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
                "content": f"本轮供你使用的热搜关键词：{', '.join(keywords_list)}"
            }
        ]
    }
    
    response = requests.post(url, headers=headers, json=payload)
    response.raise_for_status()
    return response.json()['choices'][0]['message']['content']

# ================= 触发生成 =================
if st.button("🚀 开始生成爆款标题 (每次点击都会随机融入不同关键词)", type="primary", use_container_width=True):
    if not api_key:
        st.warning("请先在左侧侧边栏输入 OpenRouter API Key！")
    elif not original_title:
        st.warning("请填写原始商品标题（因为没有图片了，AI 必须依赖原标题来知道商品是什么）！")
    elif not all_keywords:
        st.warning("请先上传有效的关键词 Excel 文件！")
    else:
        # 核心优化：动态随机抽取关键词
        current_sample_size = min(sample_size, len(all_keywords))
        sampled_keywords = random.sample(all_keywords, current_sample_size)
        
        st.info(f"🎲 正在从词库中随机抽取 **{current_sample_size}** 个词： {', '.join(sampled_keywords[:5])}...")
        
        with st.spinner("AI 正在深度重组标题，马上就好..."):
            try:
                result_text = generate_titles(
                    api_key, model_choice, original_title, category, quantity, sampled_keywords
                )
                
                # 清理返回结果可能带有的 Markdown 格式
                result_text = result_text.strip().removeprefix('```json').removesuffix('```').strip()
                
                # 解析 JSON 并排序
                titles_data = json.loads(result_text)
                sorted_titles = sorted(titles_data, key=lambda x: x['score'], reverse=True)
                
                st.success("🎉 生成完毕！以下是按爆单潜力分数倒序排列的标题：")
                
                # 展示结果
                for idx, item in enumerate(sorted_titles):
                    with st.expander(f"🏆 推荐 #{idx+1} | 潜力评分: {item['score']} 分 | {item['en_title']}", expanded=True):
                        st.markdown(f"**🇺🇸 英文标题:** `{item['en_title']}`")
                        st.markdown(f"**🇨🇳 中文释义:** {item['zh_title']}")
                        st.markdown(f"**💡 推荐理由:** {item['reason']}")
                        
            except json.JSONDecodeError:
                st.error("AI 返回的数据格式有误，未能生成有效的 JSON，请重试。")
                st.code(result_text) # 显示错误文本以便排查
            except Exception as e:
                st.error(f"发生调用错误: {e}")
