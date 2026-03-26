import json
import os
import hashlib
from flask import session, redirect, url_for, render_template, request

# 用户数据文件路径
USERS_FILE = 'users.json'

# 加载用户数据
def load_users():
    if os.path.exists(USERS_FILE):
        try:
            with open(USERS_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            return []
    return []

# 保存用户数据
def save_users(users):
    with open(USERS_FILE, 'w', encoding='utf-8') as f:
        json.dump(users, f, ensure_ascii=False, indent=2)

# 密码哈希函数
def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

# 检查用户是否登录的辅助函数
def is_logged_in():
    return 'user_id' in session

# 注册路由
def register():
    if is_logged_in():
        return redirect(url_for('home'))
    
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        email = request.form['email']
        
        # 加载用户数据
        users = load_users()
        
        # 检查用户名是否已存在
        if any(user['username'] == username for user in users):
            return render_template('register.html', error='用户名已存在')
        
        # 创建新用户
        new_id = max(user['id'] for user in users) + 1 if users else 1
        new_user = {
            'id': new_id,
            'username': username,
            'password': hash_password(password),
            'email': email
        }
        users.append(new_user)
        save_users(users)
        
        # 自动登录
        session['user_id'] = new_user['id']
        session['username'] = new_user['username']
        return redirect(url_for('home'))
    
    return render_template('register.html')

# 登录路由
def login():
    if is_logged_in():
        return redirect(url_for('home'))
    
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        # 加载用户数据
        users = load_users()
        
        # 查找用户
        user = next((u for u in users if u['username'] == username), None)
        if user and user['password'] == hash_password(password):
            # 登录成功
            session['user_id'] = user['id']
            session['username'] = user['username']
            return redirect(url_for('home'))
        else:
            # 登录失败
            return render_template('login.html', error='用户名或密码错误')
    
    return render_template('login.html')

# 注销路由
def logout():
    session.pop('user_id', None)
    session.pop('username', None)
    return redirect(url_for('home'))

# 初始化默认用户
def init_default_user():
    users = load_users()
    if not users:
        default_user = {
            'id': 1,
            'username': 'admin',
            'password': hash_password('admin123'),  # 默认密码
            'email': 'admin@example.com'
        }
        users.append(default_user)
        save_users(users)
