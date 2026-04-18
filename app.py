import streamlit as st
import pandas as pd
import requests
import json
import base64

# ================= 页面配置 =================
st.set_page_config(page_title="TikTok Shop 爆款标题优化工具", layout="wide", page_icon="🛍️")
st.title("🛍️ TikTok Shop 爆款标题优化工具 (云端版)")

# ================= 侧边栏配置 =================
with st.sidebar:
    st.header("⚙️ 基础配置")
    api_key = st.text_input("OpenRouter API Key", type="password", help="请输入你的 OpenRouter API Key")
    
    # 常用支持视觉的模型列表
    model_choice = st.selectbox(
        "选择 AI 模型 (必须支持图片)", 
        ["anthropic/claude-3.5-sonnet", "openai/gpt-4o", "google/gemini-1.5-pro"]
    )
    
    category = st.selectbox(
        "选择饰品类型",
        ["耳环", "脚链", "戒指", "手环与手链", "项链", "首饰吊件及装饰", "身体饰品", "钥匙扣", "首饰套装", "珠宝调节保护工具"]
    )

# ================= 主区域输入 =================
col1, col2 = st.columns(2)

with col1:
    st.subheader("1. 上传热度关键词 (Excel)")
    uploaded_excel = st.file_uploader("请上传包含关键词的 Excel 文件 (.xlsx)", type=["xlsx"])
    keywords = []
    if uploaded_excel:
        try:
            df = pd.read_excel(uploaded_excel)
            # 假设关键词在第一列，提取前20个避免Token超载
            keywords = df.iloc[:, 0].dropna().astype(str).tolist()[:20] 
            st.success(f"成功提取 {len(keywords)} 个关键词！例如: {', '.join(keywords[:3])}...")
        except Exception as e:
            st.error(f"读取 Excel 失败: {e}")

with col2:
    st.subheader("2. 上传商品图片")
    uploaded_image = st.file_uploader("请上传商品主图 (JPG/PNG)", type=["jpg", "jpeg", "png"])
    if uploaded_image:
        st.image(uploaded_image, caption="商品预览", use_container_width=True)

# ================= 核心处理逻辑 =================
def encode_image_to_base64(image_file):
    return base64.b64encode(image_file.getvalue()).decode('utf-8')

def generate_titles(api_key, model, category, keywords_list, image_base64):
    url = "https://openrouter.ai/api/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    # 构建严谨的 Prompt 提示词
    system_prompt = f"""
    你是一个资深的 TikTok Shop 跨境电商标题优化专家。请根据提供的商品图片、饰品类别（{category}）以及热搜关键词列表，生成5个具备爆单潜力的商品标题。
    
    【合规要求（至关重要）】
    1. 严格遵守 TikTok Shop 商品上架规则。
    2. 绝对禁止侵权词汇（如大牌名称的变体、仿冒暗示）。
    3. 绝对禁止虚假宣传（如“100%纯金”若无证据、“包治百病”等）。
    4. 标题需符合东南亚和欧美用户的搜索习惯。
    
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
                "content": [
                    {
                        "type": "text",
                        "text": f"提供的热搜关键词：{', '.join(keywords_list)}"
                    },
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/jpeg;base64,{image_base64}"
                        }
                    }
                ]
            }
        ]
    }
    
    response = requests.post(url, headers=headers, json=payload)
    response.raise_for_status()
    return response.json()['choices'][0]['message']['content']

# ================= 触发生成 =================
if st.button("🚀 开始生成爆款标题", type="primary"):
    if not api_key:
        st.warning("请先在左侧侧边栏输入 OpenRouter API Key！")
    elif not keywords:
        st.warning("请先上传有效的关键词 Excel 文件！")
    elif not uploaded_image:
        st.warning("请先上传商品图片！")
    else:
        with st.spinner("AI 正在深度分析商品与关键词，生成合规爆款标题中..."):
            try:
                base64_img = encode_image_to_base64(uploaded_image)
                result_text = generate_titles(api_key, model_choice, category, keywords, base64_img)
                
                # 清理返回结果可能带有的 Markdown 格式
                result_text = result_text.strip().removeprefix('```json').removesuffix('```').strip()
                
                # 解析 JSON 并排序
                titles_data = json.loads(result_text)
                sorted_titles = sorted(titles_data, key=lambda x: x['score'], reverse=True)
                
                st.success("生成完毕！以下是按爆单潜力分数倒序排列的标题：")
                
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
                st.error(f"发生错误: {e}")
