from flask import Flask, render_template, request, jsonify
import os
import sys
import json
import uuid
from werkzeug.utils import secure_filename

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from untils import xiaohongshu_generator, generate_content_from_media

app = Flask(__name__)

# 配置上传文件夹
UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'bmp', 'webp', 'mp4', 'avi', 'mov', 'mkv', 'webm'}
MAX_CONTENT_LENGTH = 50 * 1024 * 1024  # 50MB

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = MAX_CONTENT_LENGTH

# 检查文件扩展名
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/generate', methods=['POST'])
def generate():
    try:
        data = request.json
        subject = data.get('subject', '')
        txt_number = int(data.get('txt_number', 200))
        creativity = float(data.get('creativity', 0.5))
        style = data.get('style', '活泼')
        api_key = data.get('api_key', '')
        
        title, content = xiaohongshu_generator(subject, txt_number, creativity, style, api_key)
        
        return jsonify({
            'success': True,
            'title': title,
            'content': content
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        })

@app.route('/analyze_media', methods=['POST'])
def analyze_media():
    try:
        # 检查是否有文件上传
        if 'file' not in request.files:
            return jsonify({
                'success': False,
                'error': '没有上传文件'
            })
        
        file = request.files['file']
        
        # 检查文件名是否为空
        if file.filename == '':
            return jsonify({
                'success': False,
                'error': '没有选择文件'
            })
        
        # 检查文件类型
        if not allowed_file(file.filename):
            return jsonify({
                'success': False,
                'error': '不支持的文件类型'
            })
        
        # 获取表单数据
        data_str = request.form.get('data', '{}')
        data = json.loads(data_str)
        
        subject = data.get('subject', '上传的媒体内容')
        txt_number = int(data.get('txt_number', 200))
        creativity = float(data.get('creativity', 0.5))
        style = data.get('style', '活泼')
        api_key = data.get('api_key', '')
        
        # 保存上传的文件
        filename = secure_filename(file.filename)
        unique_filename = str(uuid.uuid4()) + '_' + filename
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], unique_filename)
        file.save(file_path)
        
        # 分析媒体文件类型
        file_type = 'image' if file.content_type and file.content_type.startswith('image/') else 'video'
        
        # 生成基于媒体的内容
        title, content, media_analysis = generate_content_from_media(
            file_path, file_type, subject, txt_number, creativity, style, api_key
        )
        
        # 删除临时文件
        try:
            os.remove(file_path)
        except:
            pass
        
        return jsonify({
            'success': True,
            'title': title,
            'content': content,
            'media_analysis': media_analysis
        })
    except ValueError as ve:
        # 处理API密钥相关错误
        return jsonify({
            'success': False,
            'error': str(ve),
            'error_type': 'api_key'
        })
    except Exception as e:
        # 处理其他错误
        error_msg = str(e)
        error_type = 'general'
        
        # 检查是否是API认证错误
        if 'AuthenticationError' in error_msg or 'API key' in error_msg:
            error_type = 'authentication'
            error_msg = 'API密钥认证失败，请检查您的API密钥是否正确'
        
        return jsonify({
            'success': False,
            'error': error_msg,
            'error_type': error_type
        })

if __name__ == '__main__':
    # 可以通过环境变量PORT设置端口号，默认为5000
    port = int(os.environ.get('PORT', 5000))
    app.run(debug=True, port=port)