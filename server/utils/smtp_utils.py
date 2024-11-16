# server/utils/smtp_utils.py
import email
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

def create_email(from_addr, to_addr, subject, body):
    """创建邮件格式"""
    msg = MIMEMultipart()
    msg['From'] = from_addr
    msg['To'] = to_addr
    msg['Subject'] = subject
    msg.attach(MIMEText(body, 'plain'))
    return msg
