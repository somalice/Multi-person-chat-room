import threading

import wx,time
from socket import socket,AF_INET,SOCK_STREAM

class Server(wx.Frame):
    def __init__(self):
        wx.Frame.__init__(self, None, id=1002, title='服务器端界面',pos=wx.DefaultPosition, size=wx.Size(400, 450))
        # 窗口放一个面板
        pl=wx.Panel(self)
        # 面板上放一个盒子
        box=wx.BoxSizer(wx.VERTICAL) # 垂直向上自动排版
        # 可伸缩的网格布局
        fgz1 = wx.FlexGridSizer(wx.HSCROLL) # 水平方向布局

        start_server_btn=wx.Button(pl,size=(133,40),label='启动服务')
        record_btn = wx.Button(pl, size=(133, 40), label='保存聊天记录')
        stop_server_btn = wx.Button(pl, size=(133, 40), label='停止服务')

        # 按钮放到可伸缩的网格布局中
        fgz1.Add(start_server_btn,1,wx.TOP)
        fgz1.Add(record_btn,1,wx.TOP)
        fgz1.Add(stop_server_btn,1,wx.TOP)

        # 将可伸缩的网格放到box中
        box.Add(fgz1,1,wx.ALIGN_CENTER)

        # 只读的多行文本框
        self.show_text = wx.TextCtrl(pl, size=(400, 410), style=wx.TE_MULTILINE | wx.TE_READONLY)
        box.Add(self.show_text, 1, wx.ALIGN_CENTER)

        # 把box放到面板中
        pl.SetSizer(box)
        '''---------------------------以上为界面绘制代码-----------------------------'''

        self.isOn=False # 存储服务器的启动状态，默认没有启动
    # 服务器端绑定的IP和端口
        self.host_port=('',8000) # '' 空字符代表本机的所有IP
        # 创建socket对象
        self.server_socket = socket(AF_INET,SOCK_STREAM)
        # 绑定IP和端口
        self.server_socket.bind(self.host_port)
        # 监听
        self.server_socket.listen(5)
        # 创建一个字典，存储与客户端对话的会话线程
        self.session_thread_dict={} # key-value {客户端的名称key:会话线程value}

        # 当光标点击“启动服务”按钮时，要执行的操作
        self.Bind(wx.EVT_BUTTON,self.start_server,start_server_btn)
        # 当光标点击“保存聊天记录”按钮时，要执行的操作
        self.Bind(wx.EVT_BUTTON, self.start_server, record_btn)
        # 为“断开”按钮绑定事件
        self.Bind(wx.EVT_BUTTON, self.stop_server, stop_server_btn)

    def stop_server(self,event):
        print('服务器已停止服务')
        self.isOn=False

    def save_record(self,event):
        # 获取只读文本框中的内容
        record_data=self.show_text.GetValue()
        with open('record.log','w',encoding='utf-8') as file:
            file.write(record_data)


    def start_server(self,event):
        # 判断服务器是否已经启动，服务器没启动时才启动
        if not self.isOn: # 等价于 self.isOn==False
            # 启动服务器
            self.isOn=True
            # 创建主线程对象
            main_thread=threading.Thread(target=self.do_work)
            # 设置为守护线程，父线程执行结束(窗体界面)，子线程也自动关闭
            main_thread_daemon=True
            # 启动主线程
            main_thread.start()

    def do_work(self):
        # 判断isOn的值
        while self.isOn:
            # 接收客户端的连接请求
            sesion_socket,client_addr=self.server_socket.accept()
            # 客户端发送连接请求之后，发送过来的第一条数据为客户端的名称，去作为字典的键
            user_name=sesion_socket.recv(1024).decode('utf-8')
            # 创建一个会话线程对象
            sesstion_thread=SesstionThread(sesion_socket,user_name,self)
            # 存储到字典中
            self.session_thread_dict[user_name]=sesstion_thread
            # 启动会话线程
            sesstion_thread.start()
            # 输出服务器的提示信息
            self.show_info_and_send_client('服务器通知',f'欢迎{user_name}进入聊天室！',time.strftime('%Y-%m-%d %H:%M:%S',time.localtime()))
        # 当self.isOn的值为False时，执行关闭socket对象
        self.server_socket.close()

    def show_info_and_send_client(self,data_source,data,date_time):
        # 字符串拼接操作
        send_data=f'{data_source}:{data}\n时间：{date_time}'
        # 只读文本框
        self.show_text.AppendText('-'*40+'\n'+send_data+'\n')
        # 每一个客户端都发送一次
        for client in self.session_thread_dict.values():
            # 判断当前会话是否是开启状态
            if client.isOn:
                client.client_socket.send(send_data.encode('utf-8'))

# 服务器端会话线程的类
class SesstionThread(threading.Thread):
    def __init__(self,client_socket,user_name,server):
        # 调用父类的初始化方法
        threading.Thread.__init__(self)
        self.client_socket=client_socket
        self.user_name=user_name
        self.server=server
        self.isOn=True # 会话线程是否启动，当创建SesstionThread对象时会话线程即启动

    def run(self)->None:
        print(f'客户端：{self.user_name}已经和服务器连接成功，服务器启动一个会话线程')
        while self.isOn:
            # 从客户端接收数据，存储到data中
            data=self.client_socket.recv(1024).decode('utf-8')
            # 如果客户端点击断开按钮，先给服务器发送一句话
            if data=='disconnect':
                self.isOn=False
                # 发送一条服务器通知
                self.server.show_info_and_send_client('服务器通知',f'{self.user_name}离开了聊天室',time.strftime('%Y-%m-%d %H:%M:%S',time.localtime()))
            else:
                # 其它聊天信息显示给所有客户端，包括服务器端
                self.server.show_info_and_send_client(self.user_name,data,time.strftime('%Y-%m-%d %H:%M:%S',time.localtime()))
        # 关闭socket
        self.client_socket.close()


if __name__ == '__main__':
    # 初始化App()
    app = wx.App()
    # 创建服务器端界面对象
    server = Server()
    server.Show()

    # 循环刷新显示
    app.MainLoop()