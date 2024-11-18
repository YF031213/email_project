# api.py

from flask import Flask, request, jsonify
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity
import logging
from user_manager import UserManager
from email_manager import EmailManager
import datetime

app = Flask(__name__)
app.config['JWT_SECRET_KEY'] = 'lbwnb'  # 请使用安全的密钥
app.config['JWT_ACCESS_TOKEN_EXPIRES'] = datetime.timedelta(days=100)

jwt = JWTManager(app)

# 初始化用户管理和邮件管理
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

user_manager = UserManager(config)
email_manager = EmailManager(config)

# 日志设置
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('api')

@app.route('/register', methods=['POST'])
def register():
    data = request.get_json()
    username = data.get('username')
    email = data.get('email')
    password = data.get('password')

    if not all([username, email, password]):
        return jsonify({'msg': '缺少参数'}), 400

    if user_manager.user_exists(username):
        return jsonify({'msg': '用户名已存在'}), 400

    success = user_manager.create_user(username, email, password)
    if success:
        return jsonify({'msg': '用户注册成功'}), 201
    else:
        return jsonify({'msg': '用户注册失败'}), 500

@app.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')

    if not all([username, password]):
        return jsonify({'msg': '缺少参数'}), 400

    if user_manager.authenticate(username, password):
        access_token = create_access_token(identity=username)
        return jsonify({'access_token': access_token}), 200
    else:
        return jsonify({'msg': '用户名或密码错误'}), 401

@app.route('/user/profile', methods=['GET'])
@jwt_required()
def user_profile():
    current_user = get_jwt_identity()
    user_info = user_manager.get_user_info(current_user)
    if user_info:
        return jsonify(user_info), 200
    else:
        return jsonify({'msg': '用户不存在'}), 404

if __name__ == '__main__':
    app.run(host='127.0.0.1', port=5000)
