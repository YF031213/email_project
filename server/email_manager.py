# server/email_manager.py
import json
import base64
import logging

logger = logging.getLogger(__name__)

class EmailManager:
    def __init__(self, config):
        self.config = config
        self.email_db = self.config['server']['email_data_file']

    def store_email(self, from_addr, to_addr, title, message):
        """存储邮件，使用base64编码raw字段"""
        message_base64 = base64.b64encode(message).decode('utf-8')
        email_data = {
            'sender': from_addr,
            'to': to_addr,
            'title': title,
            'raw': message_base64
        }
        try:
            with open(self.email_db, 'a') as f:
                json.dump(email_data, f)
                f.write("\n")
            logger.info("Email stored successfully.")
        except Exception as e:
            logger.error(f"Error storing email: {e}")

    def get_emails(self, username):
        """获取用户的所有邮件"""
        emails = []
        try:
            with open(self.email_db, 'r') as f:
                for line in f:
                    email = json.loads(line.strip())
                    if email.get("to") == username:
                        email["raw"] = base64.b64decode(email["raw"].encode('utf-8'))
                        emails.append(email)
        except FileNotFoundError:
            logger.error("Email database file not found.")
        except Exception as e:
            logger.error(f"Error retrieving emails: {e}")
        return emails
