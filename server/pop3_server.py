import socketserver
import threading
import logging
from email.parser import Parser

# 设置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class POP3Handler(socketserver.StreamRequestHandler):
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
            # 从客户端读取一行
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
            # 列出所有消息
            self.wfile.write(f'+OK {len(self.mailbox)} messages:\r\n'.encode('utf-8'))
            for i, msg in enumerate(self.mailbox, 1):
                size = len(msg['raw'])
                self.wfile.write(f'{i} {size}\r\n'.encode('utf-8'))
            self.wfile.write(b'.\r\n')
        elif len(args) == 2:
            # 列出指定消息
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
                # 标记为删除（这里直接删除）
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

class POP3Server(socketserver.ThreadingMixIn, socketserver.TCPServer):
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

# 示例用法
if __name__ == "__main__":
    # 配置
    config = {
        'server': {
            'server_domain': '127.0.0.1',
            'pop3_port': 1110
        }
    }

    # 模拟用户和邮件管理类
    class DummyUserManager:
        def validate_user(self, username, password):
            if username == 'test_user' and password == 'test_password':
                return True
            else:
                return False

    class DummyEmailManager:
        def get_emails_for_user(self, username):
            # 返回模拟的邮件列表
            if username == 'test_user':
                return [
                    {'raw': b'From: alice@example.com\r\nTo: test_user@example.com\r\nSubject: Test Email 1\r\n\r\nThis is the body of email 1.'},
                    {'raw': b'From: bob@example.com\r\nTo: test_user@example.com\r\nSubject: Test Email 2\r\n\r\nThis is the body of email 2.'}
                ]
            else:
                return []

    # 初始化 POP3 服务器
    user_manager = DummyUserManager()
    email_manager = DummyEmailManager()

    pop3_server = POP3ServerWrapper(config, user_manager, email_manager)

    # 保持主线程运行
    try:
        while True:
            pass
    except KeyboardInterrupt:
        pop3_server.shutdown()
