from flask import Flask, render_template, request, redirect, url_for, session
from datetime import datetime
import json
import os
from auth import register, login, logout, is_logged_in, init_default_user

app = Flask(__name__)
app.secret_key = 'your-secret-key-change-this-in-production'  # 用于session加密

# 数据文件路径
DATA_FILE = 'posts.json'

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

# 加载文章数据
posts = load_posts()

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
    return render_template('post.html', post=post, logged_in=is_logged_in(), username=session.get('username'))

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

if __name__ == '__main__':
    app.run(debug=True)
