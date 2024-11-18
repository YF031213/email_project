# server/server.py
import json
import os
import logging
from smtp_server import SMTPServer
from pop3_server import POP3ServerWrapper
from user_manager import UserManager
from email_manager import EmailManager
import asyncore

# 设置日志记录
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class MailServer:
    def __init__(self):
        # 加载配置
        with open("C:\\Users\\Dragonite\\PycharmProjects\\email_project\\server\config\server_config.json", "r") as f:
            self.config = json.load(f)
        logger.info("配置文件加载成功。")    
        
        # 初始化用户管理和邮件管理
        self.user_manager = UserManager(self.config)
        self.email_manager = EmailManager(self.config)
        
        # 读取服务器参数
        self.smtp_port = self.config['server']['smtp_port']
        self.pop3_port = self.config['server']['pop3_port']
        self.server_domain = self.config['server']['server_domain']

        # 初始化SMTP服务器
        self.smtp_server = SMTPServer(self.config, self.user_manager, self.email_manager)
        logger.info(f"SMTP服务器已在 {self.server_domain}:{self.smtp_port} 初始化。")

        # 初始化POP3服务器
        self.pop3_server = POP3ServerWrapper(self.config, self.user_manager, self.email_manager)
        logger.info(f"POP3服务器已在 {self.server_domain}:{self.pop3_port} 初始化。")
        
        # 确保日志目录存在
        if not os.path.exists('logs'):
            os.makedirs('logs')
    
    def load_user_data(self):
        """加载用户数据"""
        logger.info("正在加载用户数据...")
        self.user_manager.load_users()
        if not self.user_manager.users:
            logger.info("没有用户数据，添加测试用户...")
            self.user_manager.add_test_users()
            self.user_manager.load_users()

    def run(self):
        """启动邮件服务器"""
        logger.info("邮件服务器正在启动...")
        self.load_user_data()
        try:
            asyncore.loop()  # 运行SMTP服务器的事件循环
        except KeyboardInterrupt:
            logger.info("邮件服务器已被用户停止。")
            self.shutdown()

    def shutdown(self):
        """关闭邮件服务器"""
        logger.info("正在关闭邮件服务器...")
        self.smtp_server.close()
        self.pop3_server.shutdown()

    def add_test_users(self):
        """添加测试用户"""
        self.add_user('sender', 'sender@example.com', 'test_password')
        self.add_user('receiver', 'receiver@example.com', 'test_password')

    


if __name__ == "__main__":
    server = MailServer()
    server.run()
