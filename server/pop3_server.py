import asyncore
import asynchat
import logging
import base64
from email_manager import EmailManager
from user_manager import UserManager

logger = logging.getLogger(__name__)

class POP3ServerWrapper(asyncore.dispatcher):
    def __init__(self, config, user_manager, email_manager):
        asyncore.dispatcher.__init__(self)
        self.config = config
        self.user_manager = user_manager
        self.email_manager = email_manager
        self.create_socket()
        self.bind(("127.0.0.1", self.config['server']['pop3_port']))
        self.listen(5)
        print(f"POP3 server started at 127.0.0.1:{self.config['server']['pop3_port']}")

    def handle_accepted(self, sock, addr):
        print(f"Accepted connection from {addr}")
        POP3SessionHandler(sock, self.user_manager, self.email_manager)

class POP3SessionHandler(asynchat.async_chat):
    def __init__(self, sock, user_manager, email_manager):
        asynchat.async_chat.__init__(self, sock)
        self.user_manager = user_manager
        self.email_manager = email_manager
        self.set_terminator(b"\r\n")
        self.username = None
        self.in_auth = False
        self.push(b"+OK POP3 server ready")

    def collect_incoming_data(self, data):
        self._collect_incoming_data(data)

    def found_terminator(self):
        command = self._get_data().decode('utf-8').strip()
        if command.startswith("USER"):
            self.handle_user(command)
        elif command.startswith("PASS"):
            self.handle_pass(command)
        elif command.startswith("RETR"):
            self.handle_retr(command)
        elif command.startswith("LIST"):
            self.handle_list()
        elif command == "QUIT":
            self.handle_quit()
        else:
            self.push(b"-ERR Unrecognized command")

    def handle_user(self, command):
        self.username = command.split(" ")[1]
        if self.username:
            self.push(b"+OK User accepted")
        else:
            self.push(b"-ERR Missing username")

    def handle_pass(self, command):
        password = command.split(" ")[1]
        if self.user_manager.verify_user(self.username, password):
            self.in_auth = True
            self.push(b"+OK Password accepted")
        else:
            self.push(b"-ERR Invalid credentials")

    def handle_list(self):
        if not self.in_auth:
            self.push(b"-ERR Not authenticated")
            return

        emails = self.email_manager.get_emails(self.username)
        self.push(f"+OK {len(emails)} messages".encode('utf-8'))
        for i, email in enumerate(emails):
            self.push(f"{i+1} {len(email['raw'])}".encode('utf-8'))

    def handle_retr(self, command):
        if not self.in_auth:
            self.push(b"-ERR Not authenticated")
            return

        try:
            msg_num = int(command.split(" ")[1]) - 1
            emails = self.email_manager.get_emails(self.username)
            if 0 <= msg_num < len(emails):
                email_data = emails[msg_num]["raw"]
                self.push(b"+OK Message follows")
                self.push(email_data)
                self.push(b"\r\n.")
            else:
                self.push(b"-ERR No such message")
        except (IndexError, ValueError):
            self.push(b"-ERR Invalid message number")

    def handle_quit(self):
        self.push(b"+OK POP3 server signing off")
        self.close()
