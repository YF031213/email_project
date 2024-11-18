# server/user_manager.py
import sqlite3
import os
import logging
import hashlib

logger = logging.getLogger('user_manager')

def hash_password(password):
    """对密码进行哈希处理"""
    return hashlib.sha256(password.encode('utf-8')).hexdigest()

class UserManager:
    def __init__(self, config):
        self.config = config
        self.db_path = self.config['server']['user_data_file']
        if not os.path.exists(self.db_path):
            logger.warning("用户数据文件未找到，正在创建新的用户数据库。")
            self.create_user_db()
        else:
            logger.info("用户数据文件已找到。")
        self.users = {}  # 用于缓存用户信息

    def create_user_db(self):
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT NOT NULL UNIQUE,
                email TEXT NOT NULL UNIQUE,
                password TEXT NOT NULL
            )
        ''')
        conn.commit()
        conn.close()
        logger.info("用户数据库创建成功。")

    def load_users(self):
        """从数据库中加载用户数据"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('SELECT username, email, password FROM users')
        rows = cursor.fetchall()
        self.users = {}
        for row in rows:
            username, email, password = row
            self.users[username] = {
                'email': email,
                'password': password
            }
        conn.close()
        logger.info("用户数据加载成功。")

    def save_users(self):
        """保存用户数据（对于 SQLite，不需要实现此方法）"""
        pass  # 数据库操作在每次增删改时已经提交

    def create_user(self, username, email, password):
        """创建用户"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        hashed_password = hash_password(password)
        try:
            cursor.execute('INSERT INTO users (username, email, password) VALUES (?, ?, ?)',
                           (username, email, hashed_password))
            conn.commit()
            logger.info(f"用户 {username} 添加成功。")
            # 更新缓存
            self.users[username] = {
                'email': email,
                'password': hashed_password
            }
        except sqlite3.IntegrityError:
            logger.error(f"用户 {username} 已存在。")
        finally:
            conn.close()

    def delete_user(self, username):
        """删除用户"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('DELETE FROM users WHERE username = ?', (username,))
        conn.commit()
        conn.close()
        logger.info(f"用户 {username} 已删除。")
        # 更新缓存
        if username in self.users:
            del self.users[username]

    def authenticate(self, username, password):
        """认证用户"""
        user = self.users.get(username)
        if user and user['password'] == hash_password(password):
            logger.info(f"用户 {username} 认证成功。")
            return True
        else:
            logger.warning(f"用户 {username} 认证失败。")
            return False

    def add_test_users(self):
        """添加测试用户"""
        self.create_user('sender', 'sender@example.com', 'test_password')
        self.create_user('receiver', 'receiver@example.com', 'test_password')

    # 可根据需要添加其他方法，例如更新用户信息等
