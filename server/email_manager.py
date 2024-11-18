# server/email_manager.py
import json
import logging

logger = logging.getLogger(__name__)

class EmailManager:
    def __init__(self, config):
        self.config = config
        self.email_db = self.config['server']['email_data_file']

    def store_email(self, from_addr, to_addr, message):
        """存储邮件"""
        # 将 bytes 转换为 str
        message_str = message.decode('utf-8')

        email_data = {
            'from': from_addr,
            'to': to_addr,
            'message': message_str
        }
        try:
            with open(self.email_db, 'a') as f:
                json.dump(email_data, f)
                f.write("\n")
            logger.info("Email stored successfully.")
        except Exception as e:
            logger.error(f"Error storing email: {e}")

    def get_emails(self, username):
        """获取用户的邮件"""
        # 模拟获取邮件的逻辑
        return []

    def delete_email(self, email_id):
        """删除邮件"""
        logger.info(f"Deleting email {email_id}.")
