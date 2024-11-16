# db/emails_db.py
import sqlite3
import logging

logger = logging.getLogger(__name__)

class EmailDB:
    def __init__(self, db_path='db/emails.db'):
        self.db_path = db_path
        self.conn = sqlite3.connect(self.db_path)
        self.cursor = self.conn.cursor()
        self.create_table()

    def create_table(self):
        """创建邮件表"""
        query = '''
        CREATE TABLE IF NOT EXISTS emails (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            sender TEXT NOT NULL,
            receiver TEXT NOT NULL,
            subject TEXT NOT NULL,
            body TEXT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        );
        '''
        self.cursor.execute(query)
        self.conn.commit()
        logger.info("Email table created or already exists.")

    def store_email(self, sender, receiver, subject, body):
        """存储邮件"""
        query = 'INSERT INTO emails (sender, receiver, subject, body) VALUES (?, ?, ?, ?)'
        self.cursor.execute(query, (sender, receiver, subject, body))
        self.conn.commit()
        logger.info(f"Email from {sender} to {receiver} stored successfully.")

    def get_emails(self, receiver):
        """获取指定收件人的所有邮件"""
        query = 'SELECT * FROM emails WHERE receiver = ? ORDER BY timestamp DESC'
        self.cursor.execute(query, (receiver,))
        return self.cursor.fetchall()

    def delete_email(self, email_id):
        """删除邮件"""
        query = 'DELETE FROM emails WHERE id = ?'
        self.cursor.execute(query, (email_id,))
        self.conn.commit()
        logger.info(f"Email {email_id} deleted.")

    def close(self):
        """关闭数据库连接"""
        self.conn.close()
