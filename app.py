from flask import Flask, render_template, request, redirect, url_for, session, jsonify
from datetime import datetime
import json
import os
from auth import register, login, logout, is_logged_in, init_default_user
from openai import OpenAI
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

# 初始化OpenAI客户端
client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))

app = Flask(__name__)
app.secret_key = 'your-secret-key-change-this-in-production'  # 用于session加密

# 数据文件路径
DATA_FILE = 'posts.json'
COMMENTS_FILE = 'comments.json'

# 加载数据
def load_posts():
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            return []
    return []

# 保存数据
def save_posts(posts):
    with open(DATA_FILE, 'w', encoding='utf-8') as f:
        json.dump(posts, f, ensure_ascii=False, indent=2)

# 加载评论
def load_comments():
    if os.path.exists(COMMENTS_FILE):
        try:
            with open(COMMENTS_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            return []
    return []

# 保存评论
def save_comments(comments):
    with open(COMMENTS_FILE, 'w', encoding='utf-8') as f:
        json.dump(comments, f, ensure_ascii=False, indent=2)

# 加载文章数据
posts = load_posts()
comments = load_comments()

# 初始化默认用户
init_default_user()

# 如果没有数据，添加初始数据
if not posts:
    posts = [
        {
            'id': 1,
            'title': '欢迎来到我的博客',
            'content': '这是我的第一篇博客文章，希望大家喜欢！',
            'author': '作者',
            'date_posted': '2024-01-01'
        },
        {
            'id': 2,
            'title': 'Flask入门教程',
            'content': 'Flask是一个轻量级的Python Web框架，非常适合搭建小型网站。',
            'author': '作者',
            'date_posted': '2024-01-02'
        }
    ]
    save_posts(posts)

@app.route('/')
def home():
    return render_template('home.html', posts=posts, logged_in=is_logged_in(), username=session.get('username'))

@app.route('/post/<int:post_id>')
def post(post_id):
    post = next((p for p in posts if p['id'] == post_id), None)
    post_comments = [c for c in comments if c['post_id'] == post_id]
    return render_template('post.html', post=post, comments=post_comments, logged_in=is_logged_in(), username=session.get('username'))

@app.route('/about')
def about():
    return render_template('about.html', logged_in=is_logged_in(), username=session.get('username'))

# 注册路由
@app.route('/register', methods=['GET', 'POST'])
def register_route():
    return register()

# 登录路由
@app.route('/login', methods=['GET', 'POST'])
def login_route():
    return login()

# 注销路由
@app.route('/logout')
def logout_route():
    return logout()

@app.route('/post/new', methods=['GET', 'POST'])
def new_post():
    if not is_logged_in():
        return redirect(url_for('login_route'))
    
    if request.method == 'POST':
        title = request.form['title']
        content = request.form['content']
        author = request.form['author']
        date_posted = datetime.now().strftime('%Y-%m-%d')
        new_id = max(post['id'] for post in posts) + 1 if posts else 1
        new_post = {
            'id': new_id,
            'title': title,
            'content': content,
            'author': author,
            'date_posted': date_posted
        }
        posts.append(new_post)
        save_posts(posts)  # 保存数据
        return redirect(url_for('home'))
    return render_template('create_post.html', logged_in=is_logged_in(), username=session.get('username'))

@app.route('/post/<int:post_id>/edit', methods=['GET', 'POST'])
def edit_post(post_id):
    if not is_logged_in():
        return redirect(url_for('login_route'))
    
    post = next((p for p in posts if p['id'] == post_id), None)
    if not post:
        return redirect(url_for('home'))
    if request.method == 'POST':
        post['title'] = request.form['title']
        post['content'] = request.form['content']
        post['author'] = request.form['author']
        save_posts(posts)  # 保存数据
        return redirect(url_for('post', post_id=post_id))
    return render_template('edit_post.html', post=post, logged_in=is_logged_in(), username=session.get('username'))

@app.route('/post/<int:post_id>/delete', methods=['POST'])
def delete_post(post_id):
    if not is_logged_in():
        return redirect(url_for('login_route'))
    
    global posts
    posts = [p for p in posts if p['id'] != post_id]
    save_posts(posts)  # 保存数据
    return redirect(url_for('home'))

@app.route('/post/<int:post_id>/comment', methods=['POST'])
def add_comment(post_id):
    if not is_logged_in():
        return redirect(url_for('login_route'))
    
    content = request.form['content']
    author = session.get('username')
    date_posted = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    new_id = max(comment['id'] for comment in comments) + 1 if comments else 1
    
    new_comment = {
        'id': new_id,
        'post_id': post_id,
        'content': content,
        'author': author,
        'date_posted': date_posted
    }
    
    comments.append(new_comment)
    save_comments(comments)
    return redirect(url_for('post', post_id=post_id))

# 添加智能内容生成路由
@app.route('/ai/generate', methods=['POST'])
def generate_content():
    if not is_logged_in():
        return redirect(url_for('login_route'))
    
    prompt = request.form.get('prompt')
    content_type = request.form.get('content_type', 'article')  # article, title, summary
    
    if not prompt:
        return jsonify({'error': '请输入提示词'})
    
    try:
        # 构建提示词
        if content_type == 'article':
            system_prompt = '你是一位专业的博客作者，擅长撰写高质量的博客文章。请根据用户提供的主题，生成一篇结构清晰、内容丰富的博客文章。'
            user_prompt = f'请围绕以下主题撰写一篇博客文章：{prompt}'
        elif content_type == 'title':
            system_prompt = '你是一位专业的标题撰写专家，擅长为博客文章创作吸引人的标题。'
            user_prompt = f'请为关于"{prompt}"的博客文章生成5个吸引人的标题'
        else:  # summary
            system_prompt = '你是一位专业的内容总结专家，擅长提炼文章的核心内容。'
            user_prompt = f'请为关于"{prompt}"的内容生成一个简洁的摘要'
        
        # 调用OpenAI API
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.7,
            max_tokens=1000
        )
        
        generated_content = response.choices[0].message.content
        return jsonify({'content': generated_content})
    
    except Exception as e:
        return jsonify({'error': f'生成内容时出错：{str(e)}'})

# 添加设置路由
@app.route('/settings', methods=['GET', 'POST'])
def settings():
    if not is_logged_in():
        return redirect(url_for('login_route'))
    
    if request.method == 'POST':
        api_key = request.form.get('api_key')
        if api_key:
            # 保存API密钥到.env文件
            with open('.env', 'w') as f:
                f.write(f'OPENAI_API_KEY={api_key}')
            # 重新加载环境变量
            load_dotenv()
            # 重新初始化OpenAI客户端
            global client
            client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
            return redirect(url_for('settings', success=True))
    
    api_key = os.getenv('OPENAI_API_KEY', '')
    success = request.args.get('success') == 'True'
    
    return render_template('settings.html', api_key=api_key, success=success)

if __name__ == '__main__':
    app.run(debug=True)
