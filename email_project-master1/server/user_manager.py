import pymysql
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
        self.db_config = {
            'host': self.config['db']['host'],
            'user': self.config['db']['user'],
            'password': self.config['db']['password'],
            'database': self.config['db']['database']
        }
        self.users = {}  # 用于缓存用户信息
        self.load_users()

    def load_users(self):
        """从数据库中加载用户数据"""
        connection = None
        try:
            connection = pymysql.connect(**self.db_config)
            with connection.cursor() as cursor:
                cursor.execute('SELECT username, email, password_hash FROM users')
                rows = cursor.fetchall()
                self.users = {}
                for row in rows:
                    username, email, password_hash = row
                    self.users[username] = {
                        'email': email,
                        'password': password_hash
                    }
            logger.info("用户数据加载成功。")
        except Exception as e:
            logger.error(f"加载用户数据时发生错误: {e}")
        finally:
            if connection:
                connection.close()

    def user_exists(self, username):
        """检查用户是否存在"""
        return username in self.users
    
    def create_user(self, username, email, password):
        """创建用户"""
        connection = None
        hashed_password = hash_password(password)
        try:
            connection = pymysql.connect(**self.db_config)
            with connection.cursor() as cursor:
                cursor.execute('INSERT INTO users (username, email, password_hash) VALUES (%s, %s, %s)',
                               (username, email, hashed_password))
                connection.commit()
                logger.info(f"用户 {username} 添加成功。")
                # 更新缓存
                self.users[username] = {
                    'email': email,
                    'password': hashed_password
                }
        except pymysql.IntegrityError:
            logger.error(f"用户 {username} 已存在。")
        except Exception as e:
            logger.error(f"创建用户时发生错误: {e}")
        finally:
            if connection:
                connection.close()

    def delete_user(self, username):
        """删除用户"""
        connection = None
        try:
            connection = pymysql.connect(**self.db_config)
            with connection.cursor() as cursor:
                cursor.execute('DELETE FROM users WHERE username = %s', (username,))
                connection.commit()
                logger.info(f"用户 {username} 已删除。")
                # 更新缓存
                if username in self.users:
                    del self.users[username]
        except Exception as e:
            logger.error(f"删除用户时发生错误: {e}")
        finally:
            if connection:
                connection.close()

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
        self.create_user('test_user', 'test_user@example.com', 'test_password')
