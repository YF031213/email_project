# server/server.py
import json
import os
import logging
from smtp_server import SMTPServer
from pop3_server import POP3ServerWrapper
from user_manager import UserManager
from email_manager import EmailManager
import asyncio
import multiprocessing
from api import app
import datetime

# 设置日志记录
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class MailServer:
    def __init__(self):
        # 加载配置
        config_path = os.path.join(os.path.dirname(__file__), 'config', 'server_config.json')
        if not os.path.exists(config_path):
            logger.error(f"配置文件未找到: {config_path}")
            raise FileNotFoundError(f"配置文件未找到: {config_path}")
        
        with open("server/config/server_config.json", "r") as f:
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
        logs_dir = os.path.join(os.path.dirname(__file__), 'logs')
        if not os.path.exists(logs_dir):
            os.makedirs(logs_dir)
            logger.info(f"日志目录已创建: {logs_dir}")
        else:
            logger.info(f"日志目录已存在: {logs_dir}")
    
    def load_user_data(self):
        """加载用户数据"""
        logger.info("正在加载用户数据...")
        self.user_manager.load_users()
        if not self.user_manager.users:
            logger.info("没有用户数据，添加测试用户...")
            self.user_manager.add_test_users()
            self.user_manager.load_users()

    async def run(self):
        """启动邮件服务器"""
        logger.info("邮件服务器正在启动...")
        self.load_user_data()
        try:
            await asyncio.gather(
                self.smtp_server.run(),
                self.pop3_server.run()
            )
        except asyncio.CancelledError:
            logger.info("邮件服务器已被用户停止。")
            await self.shutdown()

    async def shutdown(self):
        """关闭邮件服务器"""
        logger.info("正在关闭邮件服务器...")
        await self.smtp_server.close()
        await self.pop3_server.shutdown()

    def add_test_users(self):
        """添加测试用户"""
        self.add_user('test_user', 'test_user@example.com', 'test_password')
        
def run_flask_app():
    """运行 Flask API 服务器"""
    # 为了在独立进程中运行 Flask，设置适当的主机和端口
    app.run(host='127.0.0.1', port=5000)


if __name__ == "__main__":
    server = MailServer()
    # 启动 Flask API 服务器作为子进程
    api_process = multiprocessing.Process(target=run_flask_app)
    api_process.start()
    logger.info("Flask API 服务器已启动。")
    
    try:
        # 启动邮件服务器（异步调用）
        asyncio.run(server.run())
    except KeyboardInterrupt:
        logger.info("收到中断信号，正在关闭服务器...")
    finally:
        # 关闭邮件服务器
        asyncio.run(server.shutdown())
        
        # 终止 Flask API 服务器进程
        if api_process.is_alive():
            api_process.terminate()
            api_process.join()
            logger.info("Flask API 服务器已停止。")
