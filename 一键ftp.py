import socket
import os
import qrcode
from pyftpdlib.authorizers import DummyAuthorizer
from pyftpdlib.handlers import FTPHandler
from pyftpdlib.servers import FTPServer

def startftp(username,password,port):
    authorizer = DummyAuthorizer()
    if username!='' and password!='':
        authorizer.add_user(username,password, os.getcwd(), perm='elradfmwMT')
    else:
        authorizer.add_user('ss', 'ss', os.getcwd(), perm='elradfmwMT')
        authorizer.add_anonymous(os.getcwd())

    # Instantiate FTP handler class
    handler = FTPHandler
    handler.authorizer = authorizer

    # Define a customized banner (string returned when client connects)
    handler.banner = "pyftpdlib based ftpd ready."

    if port == '':
        port = 21
    address = ('0.0.0.0', port)
    server = FTPServer(address, handler)

    # set a limit for connections
    server.max_cons = 200
    server.max_cons_per_ip = 50

    # start ftp server
    server.serve_forever()
def QR(url):
    img = qrcode.make(url)
    img.show()
    # qr = qrcode.QRCode()
    # qr.add_data(url)
    # qr.print_ascii(invert=True)
    # print(url)
while True:
    try:
        myname = socket.getfqdn(socket.gethostname())
        myaddr = socket.gethostbyname(myname)
        while True:
            username = input("请创建用户名：")
            password = input("请创建密码：")
            if username != '' and password != '' or username == '' and password == '':
                port = input("请输入端口号:")
                break
            print("用户名/密码错误。")
        if username == '' and password == '' and port == '':
            addresss = "ftp://" + myaddr
        elif username == '' and password == '' and port != '':
            addresss = "ftp://" + myaddr + ":" + port
        elif username != '' and password != '' and port == '':
            addresss = "ftp://" + username + ":" + password + "@" + myaddr
        elif username != '' and password != '' and port != '':
            addresss = "ftp://" + username + ":" + password + "@" + myaddr + ":" + port
        QR(addresss)
        startftp(username, password, port)
    except Exception as e:
        print("出错了：")
        print(str(e))