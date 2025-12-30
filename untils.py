# 导入库
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI    
import os
import ssl
import base64
import io
from PIL import Image

# 常量定义
ARK_MODEL_NAME = "doubao-seed-1-6-vision-250815"
ARK_API_BASE = "https://ark.cn-beijing.volces.com/api/v3"
VISION_MODEL_NAME = "doubao-seed-1-6-vision-250815"

def get_api_key(api_key=None):
    """获取API密钥"""
    return api_key or os.getenv("ARK_API_KEY")

def create_model(model_name, api_key, api_base=None, temperature=0.7):
    """创建模型实例"""
    kwargs = {
        "model_name": model_name,
        "temperature": temperature,
        "openai_api_key": api_key
    }
    if api_base:
        kwargs["openai_api_base"] = api_base
    return ChatOpenAI(**kwargs)

def analyze_media_locally(media_path, media_type):
    """使用本地方法分析媒体文件"""
    try:
        filename = os.path.basename(media_path)
        
        if media_type == 'image':
            # 打开图片
            img = Image.open(media_path)
            width, height = img.size
            format_type = img.format
            
            analysis = f"""
            本地图片分析结果：
            1. 图片基本信息：{format_type}格式，尺寸为{width}x{height}像素
            2. 文件名：{filename}
            3. 图片分析：这是一张用户上传的图片，可能包含与主题相关的视觉内容
            4. 建议创作方向：根据图片内容和用户输入的主题，创作相关的小红书文案
            5. 推荐标签：#图片分享 #生活记录 #原创内容
            """
        else:  # video
            # 简化视频分析，不使用OpenCV
            analysis = f"""
            本地视频分析结果：
            1. 视频基本信息：用户上传的视频文件
            2. 文件名：{filename}
            3. 视频分析：这是一个用户上传的视频，可能包含与主题相关的动态内容
            4. 建议创作方向：根据视频内容和用户输入的主题，创作相关的小红书文案
            5. 推荐标签：#视频分享 #生活记录 #原创内容
            """
        
        return analysis
        
    except Exception as e:
        print(f"本地{media_type}分析失败: {str(e)}")
        return f"无法分析{media_type}内容，将基于用户输入的主题生成内容"

def analyze_image_with_vision(image_path, api_key):
    """使用视觉模型分析图片"""
    try:
        # 读取图片并转换为base64
        with open(image_path, "rb") as image_file:
            base64_image = base64.b64encode(image_file.read()).decode('utf-8')
        
        # 使用ARK API密钥
        ark_api_key = get_api_key(api_key)
        if not ark_api_key:
            print("未设置ARK API密钥，无法使用视觉模型")
            return None
            
        # 创建模型
        model = create_model(VISION_MODEL_NAME, ark_api_key, ARK_API_BASE)
        
        # 创建分析提示
        analyze_prompt = ChatPromptTemplate.from_messages([
            ("system", "你是一个专业的图像分析师，能够详细描述图片内容并提供创意性的小红书内容建议"),
            ("human", [
                {
                    "type": "text",
                    "text": "请分析这张图片，并提供以下内容：\n1. 图片中的主要元素和场景描述\n2. 图片中的色彩、构图和风格特点\n3. 适合的小红书内容主题和风格建议\n4. 可以提取的标签和关键词\n5. 适合的文案创作方向"
                },
                {
                    "type": "image_url",
                    "image_url": {
                        "url": f"data:image/jpeg;base64,{base64_image}"
                    }
                }
            ])
        ])
        
        # 执行分析
        analysis_result = (analyze_prompt | model).invoke({}).content
        return analysis_result
        
    except Exception as e:
        print(f"ARK视觉模型分析图片失败: {str(e)}")
        return None

def analyze_video_with_vision(video_path, api_key):
    """使用视觉模型分析视频（简化版，不使用OpenCV）"""
    try:
        # 使用ARK API密钥
        ark_api_key = get_api_key(api_key)
        if not ark_api_key:
            print("未设置ARK API密钥，无法使用视觉模型")
            return None
            
        # 创建模型
        model = create_model(VISION_MODEL_NAME, ark_api_key, ARK_API_BASE)
        
        # 获取视频文件名
        filename = os.path.basename(video_path)
        
        # 简化视频分析，直接返回基本信息
        analysis_result = f"""
        视频分析结果：
        1. 视频基本信息：用户上传的视频文件
        2. 文件名：{filename}
        3. 视频分析：这是一个用户上传的视频，可能包含与主题相关的动态内容
        4. 建议创作方向：根据视频内容和用户输入的主题，创作相关的小红书文案
        5. 推荐标签：#视频分享 #生活记录 #原创内容
        """
        
        return analysis_result
        
    except Exception as e:
        print(f"ARK视觉模型分析视频失败: {str(e)}")
        return None

def analyze_media(media_path, media_type, api_key):
    """分析媒体文件（图片或视频）"""
    filename = os.path.basename(media_path)
    
    try:
        if media_type == 'image':
            # 尝试使用视觉模型分析图片
            analysis = analyze_image_with_vision(media_path, api_key)
            if analysis:
                return analysis
        else:  # video
            # 尝试使用视觉模型分析视频
            analysis = analyze_video_with_vision(media_path, api_key)
            if analysis:
                return analysis
        
        # 如果视觉模型分析失败，使用本地方法
        print(f"视觉模型分析失败，使用本地方法分析{media_type}")
        return analyze_media_locally(media_path, media_type)
        
    except Exception as e:
        print(f"{media_type}分析失败: {str(e)}")
        return f"{media_type}分析失败，但根据文件名 '{filename}' 可以推测这是一个与用户主题相关的{media_type}，建议围绕{media_type}内容创作相关的小红书内容。"

def create_content_prompt(media_analysis, subject, style, txt_number):
    """创建内容生成提示模板"""
    return ChatPromptTemplate.from_messages([
        ("system", "你是一个专业的小红书创作者，擅长根据媒体内容创作高质量的文案"),
        ("human", f'''你是小红书爆款写作专家，请你基于以下媒体分析结果，以{subject}为主题，采用{style}的写作风格来进行创作，首先产出5个标题（含适当的emoji表情），其次产出1个正文（每一个段落含有适当的emoji表情，文末有合适的tag标签）

媒体分析：
{media_analysis}

一、在小红书标题方面，你会以下技能：
1. 采用二极管标题法进行创作
2. 你善于使用标题吸引人的特点
3. 你使用爆款关键词，写标题时，从这个列表中随机选1-2个
4. 你了解小红书平台的标题特性
5. 你懂得创作的规则
6. 你可以把字数控制在{txt_number}字左右
二、在小红书正文方面，你会以下技能：
1. 写作风格
2. 写作开篇方法
3. 文本结构
4. 互动引导方法
5. 一些小技巧
6. 爆炸词
7. 从你生成的稿子中，抽取3-6个seo关键词，生成#标签并放在文章最后
8. 文章的每句话都尽量口语化、简短
9. 在每段话的开头使用表情符号，在每段话的结尾使用表情符号，在每段话的中间插入表情符号
10. 可以参考媒体分析结果丰富文章内容，并在文章末尾给出分析结果作为参考
三、结合媒体分析结果，以及你掌握的标题和正文的技巧，产出内容。请按照如下格式输出内容，只需要格式描述的部分，如果产生其他内容则不输出：
一. 标题
[标题1到标题5]
[换行]
二. 正文
[正文]
标签：[标签]
参考内容：媒体分析结果''')
    ])

def get_content_template():
    """获取内容模板"""
    return '''一. 标题
[标题1到标题5]
[换行]
二. 正文
[正文]
标签：[标签]
参考内容：媒体分析结果'''

def generate_content_with_model(model, media_analysis, subject, style, txt_number):
    """使用模型生成内容"""
    # 创建标题模板
    title_message = ChatPromptTemplate.from_messages([
        ("system", "你是一个专业的小红书创作者，擅长根据媒体内容创作吸引人的标题"),
        ("human", f"请基于以下媒体分析结果，为{subject}创作5个吸引人的标题（含适当的emoji表情）：\n\n媒体分析：{media_analysis}")
    ])
    
    # 创建内容模板
    content_message = create_content_prompt(media_analysis, subject, style, txt_number)
    
    # 创建标题链和内容链
    title_chain = title_message | model
    content_chain = content_message | model
    
    # 生成标题
    print("生成标题...")
    title = title_chain.invoke({}).content
    print("标题生成成功")
    
    # 生成内容
    print("生成内容...")
    content = content_chain.invoke({}).content
    print("内容生成成功")
    
    return title, content

def create_fallback_content(subject, media_analysis):
    """创建备用内容"""
    fallback_title = f"关于{subject}的分享 📱✨"
    fallback_content = f"""一. 标题
{fallback_title}

二. 正文
今天想和大家分享一下关于{subject}的内容 🌟

这是一个非常有趣的话题，希望能给大家带来一些启发和帮助 💡

如果你对{subject}也感兴趣，欢迎在评论区留言交流哦 📝

标签：#{subject} #分享 #原创内容

参考内容：{media_analysis}"""
    
    return fallback_title, fallback_content

def xiaohongshu_generator(subject, txt_number, creativity, style, API_Key=None):
    """小红书内容生成器（基于文本输入）"""
    print("开始执行xiaohongshu_generator函数...")
    
    # 获取API_KEY
    API_Key = get_api_key(API_Key)
    if not API_Key:
        raise ValueError("请输入API_KEY")
    
    # 创建模型
    model = create_model(ARK_MODEL_NAME, API_Key, ARK_API_BASE, creativity)
    
    # 创建标题模板
    title_message = ChatPromptTemplate.from_messages([
        ("system", "你是一个专业的小红书创作者"),
        ("human", "请为{subject}创作一个标题")
    ])

    # 创建内容模板
    content_message = ChatPromptTemplate.from_messages([
        ("system", "你是一个专业的小红书创作者"),
        ("human", '''你是小红书爆款写作专家，请你用以下步骤,以{subject}为主题或以其为要求,采用{style}的写作风格来进行创作，首先产出5个标题（含适当的emoji表情），其次产出1个正文（每一个段落含有适当的emoji表情，文末有合适的tag标签）

一、在小红书标题方面，你会以下技能：
1. 采用二极管标题法进行创作
2. 你善于使用标题吸引人的特点
3. 你使用爆款关键词，写标题时，从这个列表中随机选1-2个
4. 你了解小红书平台的标题特性
5. 你懂得创作的规则
6. 你可以把字数控制在{txt_number}字左右
7. 你可以根据用户输入的要求，适当调整内容
二、在小红书正文方面，你会以下技能：
1. 写作风格
2. 写作开篇方法
3. 文本结构
4. 互动引导方法
5. 一些小技巧
6. 爆炸词
7. 从你生成的稿子中，抽取3-6个seo关键词，生成#标签并放在文章最后
8. 文章的每句话都尽量口语化、简短
9. 在每段话的开头使用表情符号，在每段话的结尾使用表情符号，在每段话的中间插入表情符号
10. 可以参考维基百科搜索到的信息丰富文章内容，并在文章末尾给出搜索到的信息作为参考
三、结合我给你输入的信息，以及你掌握的标题和正文的技巧，产出内容。请按照如下格式输出内容，只需要格式描述的部分，如果产生其他内容则不输出：
一. 标题
[标题1到标题5]
[换行]
二. 正文
[正文]
标签：[标签]
参考内容：{wiki_search}''')
    ])

    # 创建标题链
    title_chain = title_message | model

    # 创建内容链
    content_chain = content_message | model

    # 生成标题
    print("生成标题...")
    title = title_chain.invoke({"subject": subject}).content
    print("标题生成成功")

    # 跳过维基百科搜索，直接生成内容
    print("跳过维基百科搜索，直接生成内容...")
    wiki_result = f"关于{subject}的相关信息"

    # 生成内容
    print("生成内容...")
    content = content_chain.invoke({
        "subject": subject, 
        "style": style,
        "txt_number": txt_number,
        "wiki_search": wiki_result
    }).content
    print("内容生成成功")

    return title, content

def generate_content_from_media(media_path, media_type, subject, txt_number, creativity, style, api_key):
    """基于媒体文件生成小红书内容"""
    print(f"开始分析{media_type}文件...")
    
    # 获取API_KEY
    API_Key = get_api_key(api_key)
    if not API_Key:
        raise ValueError("请输入API_KEY")
    
    # 分析媒体内容
    media_analysis = analyze_media(media_path, media_type, API_Key)
    print("媒体分析完成，生成内容...")
    
    # 检查媒体分析是否成功
    if "分析失败" in media_analysis or "无法分析" in media_analysis:
        print("媒体分析不完整，使用备用方案生成内容...")
        # 如果媒体分析失败，使用文件名和主题生成内容
        filename = os.path.basename(media_path)
        media_analysis = f"""
        媒体文件：{filename}
        媒体类型：{media_type}
        用户主题：{subject}
        
        虽然无法详细分析媒体内容，但可以根据文件名和用户主题创作相关内容。
        建议围绕用户提供的主题 {subject} 创作，并结合{media_type}的特点。
        """
    
    try:
        # 创建模型
        model = create_model(ARK_MODEL_NAME, API_Key, ARK_API_BASE, creativity)
        
        # 生成内容
        title, content = generate_content_with_model(model, media_analysis, subject, style, txt_number)
        return title, content, media_analysis
        
    except Exception as e:
        print(f"内容生成失败: {str(e)}")
        # 如果内容生成失败，返回一个基本的内容
        return create_fallback_content(subject, media_analysis) + (media_analysis,)

if __name__ == "__main__":
    test_title, test_content = xiaohongshu_generator("摄影", 200, 0.5, "活泼")
    print(test_title)
    print(test_content)