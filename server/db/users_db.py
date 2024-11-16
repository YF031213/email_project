# db/users_db.py
import sqlite3
import logging

logger = logging.getLogger(__name__)

class UserDB:
    def __init__(self, db_path='db/users.db'):
        self.db_path = db_path
        self.conn = sqlite3.connect(self.db_path)
        self.cursor = self.conn.cursor()
        self.create_table()

    def create_table(self):
        """创建用户表"""
        query = '''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL UNIQUE,
            password TEXT NOT NULL,
            is_admin INTEGER DEFAULT 0
        );
        '''
        self.cursor.execute(query)
        self.conn.commit()
        logger.info("User table created or already exists.")

    def add_user(self, username, password, is_admin=0):
        """添加新用户"""
        query = 'INSERT INTO users (username, password, is_admin) VALUES (?, ?, ?)'
        try:
            self.cursor.execute(query, (username, password, is_admin))
            self.conn.commit()
            logger.info(f"User {username} added successfully.")
        except sqlite3.IntegrityError:
            logger.error(f"User {username} already exists.")
            return False
        return True

    def delete_user(self, username):
        """删除用户"""
        query = 'DELETE FROM users WHERE username = ?'
        self.cursor.execute(query, (username,))
        self.conn.commit()
        logger.info(f"User {username} deleted.")

    def get_user(self, username):
        """获取用户信息"""
        query = 'SELECT * FROM users WHERE username = ?'
        self.cursor.execute(query, (username,))
        return self.cursor.fetchone()

    def update_password(self, username, new_password):
        """更新用户密码"""
        query = 'UPDATE users SET password = ? WHERE username = ?'
        self.cursor.execute(query, (new_password, username))
        self.conn.commit()
        logger.info(f"Password for {username} updated.")

    def authenticate(self, username, password):
        """认证用户"""
        user = self.get_user(username)
        if user and user[2] == password:  # Check password
            return True
        return False

    def close(self):
        """关闭数据库连接"""
        self.conn.close()

