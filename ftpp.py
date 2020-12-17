import wx
import pyperclip
import socket
import logging
import configparser
from pyftpdlib.authorizers import DummyAuthorizer
from pyftpdlib.handlers import FTPHandler
from pyftpdlib.servers import FTPServer
import threading
import qrcode
import time

class MainFrame(wx.Frame):  # 记住一定要从wx.Frame派生出主窗口类
    def __init__(self, p, t):
        """ p: 父亲窗口
        t:  窗口标题
        """
        wx.Frame.__init__(self, id=-1, parent=p, title=t, size=(-1,-1))
        # 该panel的父亲就是该窗口， id=-1就表示任意ID
        panel = wx.Panel(self, -1)
        cf = configparser.ConfigParser()
        cf.read("resources/set.conf")
        self.username0 = wx.StaticText(panel, -1, "创建用户:")
        self.username1 = wx.TextCtrl(panel, -1, cf.get("default", "username"), size=wx.DefaultSize)
        # basicText.SetInsertionPoint(0)
        self.password0 = wx.StaticText(panel, -1, "创建密码:")
        self.password1 = wx.TextCtrl(panel, -1, cf.get("default", "password"), size=wx.DefaultSize, style=wx.TE_PASSWORD)

        self.noname = wx.CheckBox(parent=panel,id=-1,label=u"匿名登录",pos=(220, 0),size = wx.DefaultSize)
        self.perm1 = wx.CheckBox(parent=panel, id=-1, label=u"允许读", pos=(220, 40), size=wx.DefaultSize)
        self.perm2 = wx.CheckBox(parent=panel, id=-1, label=u"允许写", pos=(220, 60), size=wx.DefaultSize)
        self.url="ftp://"
        self.urlText = wx.StaticText(panel, -1, self.url,pos=(0,185),size=wx.DefaultSize)
        self.urlText.Shown=False
        self.urlText.SetForegroundColour("blue")
        # self.copyurl = wx.Button(panel, -1, u"复制链接",pos=(220, 120))
        # self.Bind(wx.EVT_BUTTON, self.copyaddress, self.copyurl)

        self.noname.SetValue(cf.get("default", "noname")=='True')
        self.perm1.SetValue(cf.get("default", "read")=='True')
        self.perm2.SetValue(cf.get("default", "write")=='True')
        self.port0 = wx.StaticText(panel, -1, "开放端口:")
        self.port1 = wx.TextCtrl(panel, -1, cf.get("default", "port"), size=wx.DefaultSize)
        self.PathButton0 = wx.StaticText(panel, -1, "共享目录:")
        self.PathButton1= wx.Button(panel, -1, './')
        self.path=r''+cf.get("default", "path")
        self.PathButton1.SetLabel(self.path)
        print(self.path)
        self.Bind(wx.EVT_BUTTON, self.ChoosePath, self.PathButton1)

        self.runftp = wx.Button(panel, -1, u"启动FTP")
        self.Bind(wx.EVT_BUTTON, self.OnClick, self.runftp)
        self.shownLog = wx.Button(panel, -1, u"查看日志")
        self.Bind(wx.EVT_BUTTON, self.ShownLog, self.shownLog)
        self.urladd = wx.Button(panel, -1, "高级链接")
        self.urladd.Enabled = False
        self.Bind(wx.EVT_BUTTON, self.urladdfun, self.urladd)
        self.copyurl = wx.Button(panel, -1, "复制地址")
        self.copyurl.Enabled = False
        self.Bind(wx.EVT_BUTTON, self.copyurlfun, self.copyurl)
        pilimg = qrcode.make('url').resize((100,100))
        wximage=wx.Bitmap.FromBuffer(pilimg.size[0],pilimg.size[1],pilimg.convert("RGB").tobytes())
        self.qrBmp = wx.StaticBitmap(panel, -1, wximage, pos=(220, 100))
        self.qrBmp.Shown=False
        self.Bind(wx.EVT_CLOSE, self.OnClose) #######
        sizer = wx.FlexGridSizer(cols=2, hgap=6, vgap=6)
        sizer.AddMany([self.username0, self.username1, self.password0, self.password1,
                       self.port0,self.port1,
                       self.PathButton0,self.PathButton1,self.runftp,self.shownLog,
                       self.urladd,self.copyurl])
        panel.SetSizer(sizer)

        self.runftp.SetDefault()
        self.isrun=0
        time.sleep(1)
        self.Refresh()
    def OnClose(self,e):
        try:
            self.server.close_all()
            wx.Exit()
        except:
            pass
            wx.Exit()
    def getUrl(self,addPassword=False):
        try:
            self.myaddr = socket.gethostbyname(socket.gethostname()) #socket.gethostbyname(socket.getfqdn(socket.gethostname()))
        except:
            self.myaddr='0.0.0.0'
        if addPassword==False:
            self.url = 'ftp://' + self.myaddr
            if self.port1.GetValue() != '21':
                self.url += ':' + str(self.port1.GetValue())
        elif addPassword==True:
            self.url = 'ftp://' + self.username1.GetValue() + ":" + self.password1.GetValue() + "@" + self.myaddr
            if self.port1.GetValue() != '21':
                self.url += ':' + str(self.port1.GetValue())
        self.urlText.SetLabel(self.url)
        pilimg = qrcode.make(self.url).resize((100, 100))
        wximage = wx.Bitmap.FromBuffer(pilimg.size[0], pilimg.size[1], pilimg.convert("RGB").tobytes())
        self.qrBmp.SetBitmap(wximage)
    def urladdfun(self,event):
        if self.urladd.GetLabel()=="高级链接":
            self.urladd.SetLabel("普通链接")
            self.getUrl(True)
        else:
            self.urladd.SetLabel("高级链接")
            self.getUrl(False)
    def copyurlfun(self,event):
        pyperclip.copy(self.url)

    def ShownLog(self, event):
        import subprocess
        t = threading.Thread(target=subprocess.Popen, args=('notepad resources/ftpp.log',))
        t.start()
    def OnClick(self, event):

        if self.isrun == 0:
            self.perm=''
            if self.perm1.GetValue()==True:
                self.perm+='elr'
            if self.perm2.GetValue()==True:
                self.perm+='adfmwMT'
            self.getUrl(False)

            t = threading.Thread(target=self.startftp, args=(self.username1.GetValue(), self.password1.GetValue(),
                     self.port1.GetValue(), self.path, self.perm, self.noname.GetValue()))
            t.start()

            self.reverse()
            self.runftp.SetLabel(u"停止FTP" )
            self.isrun = 1
        else:
            self.server.close_all()
            self.reverse()
            self.runftp.SetLabel(u"启动FTP")
            self.isrun = 0


    def reverse(self):
        self.username0.Enabled = not self.username0.Enabled
        self.password0.Enabled = not self.password0.Enabled
        self.port0.Enabled = not self.port0.Enabled
        self.PathButton0.Enabled = not self.PathButton0.Enabled
        self.username1.Enabled = not self.username1.Enabled
        self.password1.Enabled = not self.password1.Enabled
        self.port1.Enabled = not self.port1.Enabled
        self.PathButton1.Enabled = not self.PathButton1.Enabled
        self.noname.Enabled = not self.noname.Enabled
        self.perm1.Enabled = not self.perm1.Enabled
        self.perm2.Enabled=not self.perm2.Enabled
        self.urlText.Shown=not self.urlText.Shown
        self.qrBmp.Shown=not self.qrBmp.Shown
        self.urladd.Enabled=not self.urladd.Enabled
        self.copyurl.Enabled=not self.copyurl.Enabled
    def ChoosePath(self, event):
        """"""
        dlg = wx.DirDialog(self, u"选择文件夹", defaultPath=self.path,style=wx.DD_DEFAULT_STYLE)
        if dlg.ShowModal() == wx.ID_OK:
            self.PathButton1.SetLabel(dlg.GetPath())
            self.path=r''+dlg.GetPath()
        dlg.Destroy()

    def startftp(self,username, password, port, path, perm, noname):
        logging.basicConfig(filename='resources/ftpp.log', level=logging.INFO)
        logging.info('\n\n' + time.asctime(time.localtime(time.time())))
        try:
            authorizer = DummyAuthorizer()
            authorizer.add_user(username, password, path, perm=perm)
            if noname == True:
                authorizer.add_anonymous(path)
            # Instantiate FTP handler class
            handler = FTPHandler
            handler.authorizer = authorizer
            # Define a customized banner (string returned when client connects)
            handler.banner = "pyftpdlib based ftpd ready."
            address = ('0.0.0.0', port)

            self.server = FTPServer(address, handler)
            # set a limit for connections
            self.server.max_cons = 500
            self.server.max_cons_per_ip = 50
            # start ftp server
            self.server.serve_forever(timeout=999999999)
        except Exception as e:
            self.reverse()
            self.runftp.SetLabel(u"启动失败")
            time.sleep(1)
            self.runftp.SetLabel(u"启动FTP")
            self.isrun = 0
            logging.info('\n'+str(e) )

if __name__ == "__main__":
    # 创建应用程序
    app = wx.App(False)
    # frame就是应用程序的主窗口
    frame = MainFrame(None, "FTP")
    icon_obj = wx.Icon(name="./resources/ftp.ico", type=wx.BITMAP_TYPE_ICO)
    frame.SetIcon(icon_obj)
    frame.Show(True)  # 显示该窗口
    app.MainLoop()  # 进入消息循环