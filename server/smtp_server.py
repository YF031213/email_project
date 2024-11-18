0# server/smtp_server.py
import asyncore
import logging
import smtpd

logger = logging.getLogger(__name__)

class SMTPServer(smtpd.SMTPServer):
    def __init__(self, config, user_manager, email_manager):
        self.config = config
        self.user_manager = user_manager
        self.email_manager = email_manager
        self.hostname = config['server']['server_domain']
        self.port = config['server']['smtp_port']
        
        # 初始化SMTP服务器
        super().__init__(('127.0.0.1', self.port), None)
        print(f"SMTP server started at 127.0.0.1:{self.port}")

    def process_message(self, peer, mailfrom, rcpttos, data, **kwargs):
        # 处理邮件的逻辑
        print(f"Received message from {mailfrom} to {rcpttos}")
        print(f"Message data: {data}")
        """处理收到的邮件"""
        logger.info(f"Received email from {mailfrom} to {rcpttos}")
        self.email_manager.store_email(mailfrom, rcpttos, data)
        return '250 OK'

    def start(self):
        logger.info(f"SMTP server is running on {self.hostname}:{self.port}...")
        asyncore.loop()

    def stop(self):
        """停止SMTP服务"""
        logger.info("Stopping SMTP server...")
        asyncore.close_all()
