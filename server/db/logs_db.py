# db/logs_db.py
import logging
import os

class LogManager:
    def __init__(self, log_dir='db/logs'):
        self.log_dir = log_dir
        if not os.path.exists(self.log_dir):
            os.makedirs(self.log_dir)
        
        # SMTP log
        self.smtp_log = os.path.join(self.log_dir, 'smtp_logs.log')
        # POP3 log
        self.pop3_log = os.path.join(self.log_dir, 'pop3_logs.log')
        # System log
        self.system_log = os.path.join(self.log_dir, 'system_logs.log')
    
    def log_smtp(self, message):
        """记录SMTP相关日志"""
        with open(self.smtp_log, 'a') as f:
            f.write(message + '\n')

    def log_pop3(self, message):
        """记录POP3相关日志"""
        with open(self.pop3_log, 'a') as f:
            f.write(message + '\n')

    def log_system(self, message):
        """记录系统日志"""
        with open(self.system_log, 'a') as f:
            f.write(message + '\n')

    def clear_logs(self):
        """清空所有日志"""
        open(self.smtp_log, 'w').close()
        open(self.pop3_log, 'w').close()
        open(self.system_log, 'w').close()
        logging.info("Logs cleared.")
