# api.py

from flask import Flask, request, jsonify
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity
import pymysql
import logging
import datetime

app = Flask(__name__)
app.config['JWT_SECRET_KEY'] = 'lbwnb'  # 请使用更安全的密钥
app.config['JWT_ACCESS_TOKEN_EXPIRES'] = datetime.timedelta(days=100)

jwt = JWTManager(app)

# 数据库配置
db_config = {
    'host': 'localhost',
    'user': 'email_user',
    'password': 'wyf20031213',  # 替换为您的数据库用户密码
    'database': 'email_system'
}

# 服务器和日志配置
config = {
    'server': {
        'smtp_port': 2525,
        'pop3_port': 1110,
        'server_domain': '127.0.0.1',
        'domain': 'test.com',
        'max_mail_size': 10485760,
        'max_user_count': 1000,
        'admin_user': 'admin@test.com',
        'server_name': 'Test Mail Server',
        'user_data_file': 'db/users.db',
        'email_data_file': 'db/emails.db'
    },
    'logs': {
        'log_level': 'INFO',
        'smtp_log_path': 'db/logs/smtp_logs.log',
        'pop3_log_path': 'db/logs/pop3_logs.log',
        'system_log_path': 'db/logs/system_logs.log',
        'log_rotation': {
            'max_size': 10485760,
            'backup_count': 5
        }
    },
    'security': {
        'password_min_length': 6,
        'password_max_length': 12,
        'password_requirements': {
            'lowercase': True,
            'uppercase': True,
            'numbers': True,
            'special_characters': True
        }
    }
}

# 日志设置
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('api')

# 注册用户
@app.route('/register', methods=['POST'])
def register():
    data = request.get_json()
    username = data.get('username')
    email = data.get('email')
    password = data.get('password')

    if not all([username, email, password]):
        return jsonify({'msg': '缺少参数'}), 400

    try:
        connection = pymysql.connect(**db_config)
        with connection.cursor() as cursor:
            # 检查用户名或邮箱是否已存在
            cursor.execute("SELECT * FROM users WHERE username = %s OR email = %s", (username, email))
            if cursor.fetchone():
                return jsonify({'msg': '用户名或邮箱已存在'}), 400
            
            # 创建用户
            cursor.execute(
                "INSERT INTO users (username, email, password_hash) VALUES (%s, %s, %s)",
                (username, email, password)  # 在实际中，建议使用哈希后的密码
            )
            connection.commit()
            return jsonify({'msg': '用户注册成功'}), 201
    except Exception as e:
        logger.error(f"注册时发生错误: {e}")
        return jsonify({'msg': '用户注册失败'}), 500
    finally:
        connection.close()

# 用户登录
@app.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')

    if not all([username, password]):
        return jsonify({'msg': '缺少参数'}), 400

    try:
        connection = pymysql.connect(**db_config)
        with connection.cursor() as cursor:
            # 验证用户
            cursor.execute("SELECT * FROM users WHERE username = %s AND password_hash = %s", (username, password))
            user = cursor.fetchone()
            if user:
                access_token = create_access_token(identity=username)
                return jsonify({'access_token': access_token}), 200
            else:
                return jsonify({'msg': '用户名或密码错误'}), 401
    except Exception as e:
        logger.error(f"登录时发生错误: {e}")
        return jsonify({'msg': '登录失败'}), 500
    finally:
        connection.close()

# 获取用户信息
@app.route('/user/profile', methods=['GET'])
@jwt_required()
def user_profile():
    current_user = get_jwt_identity()

    try:
        connection = pymysql.connect(**db_config)
        with connection.cursor() as cursor:
            # 获取用户信息
            cursor.execute("SELECT username, email, created_at FROM users WHERE username = %s", (current_user,))
            user_info = cursor.fetchone()
            if user_info:
                return jsonify({
                    'username': user_info[0],
                    'email': user_info[1],
                    'created_at': user_info[2]
                }), 200
            else:
                return jsonify({'msg': '用户不存在'}), 404
    except Exception as e:
        logger.error(f"获取用户信息时发生错误: {e}")
        return jsonify({'msg': '获取用户信息失败'}), 500
    finally:
        connection.close()

# 标记邮件为重要
@app.route('/email/mark_important', methods=['POST'])
@jwt_required()
def mark_email_important():
    data = request.get_json()
    email_id = data.get('email_id')
    current_user = get_jwt_identity()

    if not email_id:
        return jsonify({'msg': '缺少参数'}), 400

    try:
        connection = pymysql.connect(**db_config)
        with connection.cursor() as cursor:
            # 获取当前用户的 ID
            cursor.execute("SELECT id FROM users WHERE username = %s", (current_user,))
            user = cursor.fetchone()
            if not user:
                return jsonify({'msg': '用户不存在'}), 404
            user_id = user[0]

            # 更新邮件为重要
            cursor.execute("UPDATE email_metadata SET important = TRUE WHERE email_id = %s", (email_id,))
            connection.commit()
            return jsonify({'msg': '邮件已标记为重要'}), 200
    except Exception as e:
        logger.error(f"标记邮件为重要时发生错误: {e}")
        return jsonify({'msg': '操作失败'}), 500
    finally:
        connection.close()

if __name__ == '__main__':
    app.run(host='127.0.0.1', port=5000)
