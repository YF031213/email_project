# server/log_manager.py
import logging

logger = logging.getLogger(__name__)

class LogManager:
    def __init__(self):
        self.smtp_log = 'logs/smtp_logs.log'
        self.pop3_log = 'logs/pop3_logs.log'

    def log_smtp(self, message):
        """记录SMTP日志"""
        with open(self.smtp_log, 'a') as f:
            f.write(message + '\n')

    def log_pop3(self, message):
        """记录POP3日志"""
        with open(self.pop3_log, 'a') as f:
            f.write(message + '\n')

    def clear_logs(self):
        """清空日志"""
        open(self.smtp_log, 'w').close()
        open(self.pop3_log, 'w').close()
