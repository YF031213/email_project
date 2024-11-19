import asyncio
import aiosmtpd.controller
import logging
from email_manager import EmailManager

logger = logging.getLogger(__name__)

class SMTPHandler:
    def __init__(self, config, user_manager, email_manager):
        self.config = config
        self.user_manager = user_manager
        self.email_manager = email_manager

    async def handle_DATA(self, server, session, envelope):
        mailfrom = envelope.mail_from
        rcpttos = envelope.rcpt_tos
        data = envelope.content.decode('utf-8', errors='replace')
        logger.info(f"Received email from {mailfrom} to {rcpttos}")
        self.email_manager.store_email(mailfrom, rcpttos, data)
        return '250 OK'

class SMTPServer:
    def __init__(self, config, user_manager, email_manager):
        self.config = config
        self.user_manager = user_manager
        self.email_manager = email_manager
        self.hostname = config['server']['server_domain']
        self.port = config['server']['smtp_port']
        self.handler = SMTPHandler(config, user_manager, email_manager)
        self.controller = aiosmtpd.controller.Controller(self.handler, hostname=self.hostname, port=self.port)

    async def run(self):
        logger.info(f"SMTP server is running on {self.hostname}:{self.port}...")
        self.controller.start()

    async def close(self):
        logger.info("Stopping SMTP server...")
        self.controller.stop()
