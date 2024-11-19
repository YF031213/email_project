import asyncio
import logging
import threading
from email_manager import EmailManager
from user_manager import UserManager
from socketserver import ThreadingMixIn, TCPServer, StreamRequestHandler

logger = logging.getLogger('pop3_server')

class POP3Handler(StreamRequestHandler):
    def handle(self):
        self.user_manager = self.server.user_manager
        self.email_manager = self.server.email_manager
        self.username = None
        self.authenticated = False
        self.mailbox = []

        # 发送初始问候语
        self.wfile.write(b'+OK POP3 server ready\r\n')
        logger.info("Client connected")

        while True:
            data = self.rfile.readline().strip()
            if not data:
                break  # 客户端断开连接
            command = data.decode('utf-8')
            logger.info(f"Received command: {command}")

            if command.upper().startswith('USER'):
                self.handle_USER(command)
            elif command.upper().startswith('PASS'):
                self.handle_PASS(command)
            elif command.upper().startswith('STAT'):
                self.handle_STAT()
            elif command.upper().startswith('LIST'):
                self.handle_LIST(command)
            elif command.upper().startswith('RETR'):
                self.handle_RETR(command)
            elif command.upper().startswith('DELE'):
                self.handle_DELE(command)
            elif command.upper().startswith('QUIT'):
                self.handle_QUIT()
                break
            else:
                self.wfile.write(b'-ERR Unknown command\r\n')

    def handle_USER(self, command):
        self.username = command[5:].strip()
        self.wfile.write(b'+OK User accepted\r\n')

    def handle_PASS(self, command):
        password = command[5:].strip()
        if self.user_manager.validate_user(self.username, password):
            self.authenticated = True
            self.mailbox = self.email_manager.get_emails_for_user(self.username)
            self.wfile.write(b'+OK Authenticated\r\n')
            logger.info(f"User {self.username} authenticated")
        else:
            self.wfile.write(b'-ERR Authentication failed\r\n')
            logger.warning(f"Authentication failed for user {self.username}")

    def handle_STAT(self):
        if not self.authenticated:
            self.wfile.write(b'-ERR Not authenticated\r\n')
            return
        num_messages = len(self.mailbox)
        total_size = sum(len(msg['raw']) for msg in self.mailbox)
        response = f'+OK {num_messages} {total_size}\r\n'.encode('utf-8')
        self.wfile.write(response)

    def handle_LIST(self, command):
        if not self.authenticated:
            self.wfile.write(b'-ERR Not authenticated\r\n')
            return
        args = command.split()
        if len(args) == 1:
            self.wfile.write(f'+OK {len(self.mailbox)} messages:\r\n'.encode('utf-8'))
            for i, msg in enumerate(self.mailbox, 1):
                size = len(msg['raw'])
                self.wfile.write(f'{i} {size}\r\n'.encode('utf-8'))
            self.wfile.write(b'.\r\n')
        elif len(args) == 2:
            msg_num = int(args[1])
            if 1 <= msg_num <= len(self.mailbox):
                size = len(self.mailbox[msg_num - 1]['raw'])
                self.wfile.write(f'+OK {msg_num} {size}\r\n'.encode('utf-8'))
            else:
                self.wfile.write(b'-ERR No such message\r\n')
        else:
            self.wfile.write(b'-ERR Invalid LIST command\r\n')

    def handle_RETR(self, command):
        if not self.authenticated:
            self.wfile.write(b'-ERR Not authenticated\r\n')
            return
        args = command.split()
        if len(args) == 2:
            msg_num = int(args[1])
            if 1 <= msg_num <= len(self.mailbox):
                msg = self.mailbox[msg_num - 1]['raw']
                self.wfile.write(f'+OK {len(msg)} octets\r\n'.encode('utf-8'))
                self.wfile.write(msg)
                self.wfile.write(b'\r\n.\r\n')
                logger.info(f"Message {msg_num} sent to user {self.username}")
            else:
                self.wfile.write(b'-ERR No such message\r\n')
        else:
            self.wfile.write(b'-ERR Invalid RETR command\r\n')

    def handle_DELE(self, command):
        if not self.authenticated:
            self.wfile.write(b'-ERR Not authenticated\r\n')
            return
        args = command.split()
        if len(args) == 2:
            msg_num = int(args[1])
            if 1 <= msg_num <= len(self.mailbox):
                del self.mailbox[msg_num - 1]
                self.wfile.write(f'+OK Message {msg_num} deleted\r\n'.encode('utf-8'))
                logger.info(f"Message {msg_num} deleted by user {self.username}")
            else:
                self.wfile.write(b'-ERR No such message\r\n')
        else:
            self.wfile.write(b'-ERR Invalid DELE command\r\n')

    def handle_QUIT(self):
        self.wfile.write(b'+OK Goodbye\r\n')
        logger.info(f"User {self.username} disconnected")

class POP3Server(ThreadingMixIn, TCPServer):
    allow_reuse_address = True

    def __init__(self, server_address, RequestHandlerClass, user_manager, email_manager):
        super().__init__(server_address, RequestHandlerClass)
        self.user_manager = user_manager
        self.email_manager = email_manager

class POP3ServerWrapper:
    def __init__(self, config, user_manager, email_manager):
        self.config = config
        self.user_manager = user_manager
        self.email_manager = email_manager

        self.hostname = self.config['server']['server_domain']
        self.port = self.config['server']['pop3_port']

        # 启动 POP3 服务器
        server_address = (self.hostname, self.port)
        self.server = POP3Server(server_address, POP3Handler, self.user_manager, self.email_manager)
        self.server_thread = threading.Thread(target=self.server.serve_forever)
        self.server_thread.daemon = True
        self.server_thread.start()

        logger.info(f"POP3 server started at {self.hostname}:{self.port}")

    def shutdown(self):
        self.server.shutdown()
        self.server.server_close()
        logger.info("POP3 server shut down")

    async def run(self):
        """启动 POP3 服务器的异步方法"""
        loop = asyncio.get_running_loop()
        await loop.run_in_executor(None, self.server.serve_forever)
        logger.info(f"POP3 server is running on {self.hostname}:{self.port}...")

    async def shutdown_async(self):
        """关闭 POP3 服务器的异步方法"""
        loop = asyncio.get_running_loop()
        await loop.run_in_executor(None, self.shutdown)
        logger.info("POP3 server shut down")
