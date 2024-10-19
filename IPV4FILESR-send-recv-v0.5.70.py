import socket
import os
import time
import hashlib
import zipfile
from threading import Thread
import configparser
import shutil
import msvcrt
import sys

CONFIG_DIR = os.path.join(os.path.expanduser("~"), "ipv4files")
SERVER_CONFIG_PATH = os.path.join(CONFIG_DIR, "server_config.ini")
CLIENT_CONFIG_PATH = os.path.join(CONFIG_DIR, "client_config.ini")

buf_size = 4096
chunk_size = 1024


def print_progress_bar(percent):
    percent = max(0, min(100, percent))
    bar_length = 20
    num_hashes = int(percent / 100 * bar_length)
    progress_bar = '[' + '█' * num_hashes + \
        ' ' * (bar_length - num_hashes) + ']'
    return str(percent) + '%' +progress_bar



class FileDownloadThread(Thread):
    def __init__(self, client_socket, file_name, file_size, download_folder):
        super(FileDownloadThread, self).__init__()
        self.client_socket = client_socket
        self.file_name = file_name
        self.file_size = file_size
        self.download_folder = download_folder

    def run(self):
        file_path = os.path.join(self.download_folder, self.file_name)
        received_size = 0
        start_time = time.time()
        sha1_hash = hashlib.sha1()

        with open(file_path, 'wb') as file:
            while received_size < self.file_size:
                remaining_size = self.file_size - received_size
                read_size = min(chunk_size, remaining_size)
                data = self.recv_all(self.client_socket, read_size)
                received_size += len(data)
                file.write(data)
                sha1_hash.update(data)
                progress = int(received_size / self.file_size * 100)
                elapsed_time = time.time() - start_time

                if elapsed_time > 0:
                    download_speed = received_size / elapsed_time / 1024
                    print('\r下载进度：{}% 下载速度：{:.2f} KB/s    {}'.format(progress, download_speed, print_progress_bar(progress)), end='')
                else:
                    print('\r下载进度：{}%'.format(progress), end='')
            print('下载完成！')

    def recv_all(self, sock, length):
        """接收指定长度的数据"""
        data = b''
        while len(data) < length:
            packet = sock.recv(length - len(data))
            if not packet:
                return None
            data += packet
        return data
WHITE_ON_BLACK = '\033[30;47m'  # 黑字白底
RESET = '\033[0m'  # 重置颜色

def input_box_with_prompt(prompt="请输入内容:", confirm_text="确认", cancel_text="取消"):
    """
    带有提示文本的输入框函数。
    输入:
    - prompt: 提示文本，可以自定义
    - confirm_text: 确认按钮文本
    - cancel_text: 取消按钮文本
    输出:
    - 用户输入的内容（字符串），如果取消则返回 False
    """
    
    while True:
        user_input = ""  # 用户输入的内容
        selected_option = 0  # 0表示“确认”，1表示“取消”
        
        while True:
            # 清屏
            os.system('cls' if os.name == 'nt' else 'clear')

            # 显示提示文本和当前输入内容
            print(f"{prompt}")
            print(f"输入内容: {user_input}")
            print()
            
            # 显示“确认”和“取消”按钮，当前选项加上白字黑底
            if selected_option == 0:
                print(f"{WHITE_ON_BLACK}[{confirm_text}]{RESET}   [ {cancel_text} ]")
            else:
                print(f"  [ {confirm_text} ]   {WHITE_ON_BLACK}[{cancel_text}]{RESET}")
                
            # 捕获键盘输入
            key = msvcrt.getch()

            if key == b'\r':  # Enter 键
                if selected_option == 0:  # 如果当前选项是“确认”
                    if user_input.strip() == "":  # 如果输入内容为空
                        break  # 重新输入
                    else:
                        return user_input  # 返回用户输入的内容
                elif selected_option == 1:  # 如果当前选项是“取消”
                    return False  # 返回 False

            elif key == b'\xe0':  # 方向键
                direction = msvcrt.getch()

                if direction == b'K':  # 左方向键
                    selected_option = (selected_option - 1) % 2
                elif direction == b'M':  # 右方向键
                    selected_option = (selected_option + 1) % 2
            
            elif key == b'\x08':  # 退格键
                user_input = user_input[:-1]  # 删除最后一个字符
                
            else:
                try:
                    # 捕获用户输入的字符，忽略解码错误
                    user_input += key.decode('utf-8', errors='ignore')
                except Exception as e:
                    print(f"解码错误: {e}")

def show_progress_bar(progress, total, bar_length=40):
    """
    在控制台显示进度条。
    输入:
    - progress: 当前进度（整数）
    - total: 总进度（整数）
    - bar_length: 进度条长度（默认40）
    输出:
    - 动态更新的进度条显示
    """
    # 计算进度的百分比
    percent = float(progress) / total
    # 计算进度条中多少是满的
    filled_length = int(bar_length * percent)
    
    # 生成进度条字符串
    bar = '█' * filled_length + '-' * (bar_length - filled_length)
    # 通过覆盖上一行输出，动态显示进度
    sys.stdout.write(f'\r进度: |{bar}| {percent * 100:.1f}% 已完成')
    sys.stdout.flush()

    # 在进度完成时换行
    if progress == total:
        print()
def render_options(input_type, array_size=None, options=None, prompt="选择一个选项", visible_rows=25):
    clear_console()
    text=prompt
    """
    输入:
    - input_type: 1表示普通列表，2表示二维数组
    - array_size: (rows, cols)，二维数组的大小 (仅当 input_type 为 2 时启用)
    - options: 普通列表或二维数组
    - text: 要显示的提示词
    - visible_rows: 最多的显示行数 默认25
    输出:
    - 选择的选项的下标（对于列表）或坐标（对于二维数组）
    """
    def get_max_width(options):
        if isinstance(options[0], list):  # 检查是否为二维数组
            return max(len(item) for row in options for item in row)
        else:
            return max(len(item) for item in options)

    # 初始化选项下标
    selected_row = 0
    selected_col = 0
    scroll_offset = 0  # 当前滚动的偏移量

    max_width = get_max_width(options) + 2  # 获取最大宽度并在两边添加2个空格用于对齐

    # 首次渲染提示文本（仅显示一次）
    rows, cols = array_size if array_size else (len(options), 1)  # 计算行和列
    print(text)  # 只输出一次提示文本
    print()

    # 渲染可见的选项
    def render_page():
        for row in range(scroll_offset, min(scroll_offset + visible_rows, rows)):
            if input_type == 1:
                print("  " + options[row].ljust(max_width))
            elif input_type == 2:
                for col in range(cols):
                    print(f"  {options[row][col].ljust(max_width)}", end="")
                print()

    render_page()

    while True:
        # 使用转义码移动光标到选项部分
        for _ in range(min(visible_rows, rows)):  # 回退到选项部分
            print("\033[F", end="")

        # 重新渲染选项，只更新高亮部分
        if input_type == 1:  # 处理普通列表
            for idx in range(scroll_offset, min(scroll_offset + visible_rows, len(options))):
                padded_option = options[idx].ljust(max_width)  # 使选项左对齐并按最大宽度填充
                if idx == selected_row:
                    print(f"> {WHITE_ON_BLACK}{padded_option}{RESET}")  # 用白字黑底高亮当前选项
                else:
                    print(f"  {padded_option}")

        elif input_type == 2:  # 处理二维数组
            for row in range(scroll_offset, min(scroll_offset + visible_rows, rows)):
                for col in range(cols):
                    padded_option = options[row][col].ljust(max_width)  # 左对齐并按最大宽度填充
                    if row == selected_row and col == selected_col:
                        print(f"  {WHITE_ON_BLACK}{padded_option}{RESET}", end="")  # 用白字黑底高亮当前选项
                    else:
                        print(f"  {padded_option}", end="")
                print()  # 换行

        # 捕获键盘输入
        key = msvcrt.getch()

        if key == b'\r':  # Enter 键
            if input_type == 1:
                return selected_row  # 返回选项下标
            elif input_type == 2:
                return (selected_row, selected_col)  # 返回二维数组坐标

        elif key == b'\xe0':  # 特殊按键（方向键）
            direction = msvcrt.getch()

            if direction == b'H':  # 上方向键
                if selected_row > 0:
                    selected_row -= 1
                if selected_row < scroll_offset:
                    scroll_offset -= 1  # 向上滚动
            elif direction == b'P':  # 下方向键
                if selected_row < rows - 1:
                    selected_row += 1
                if selected_row >= scroll_offset + visible_rows:
                    scroll_offset += 1  # 向下滚动
            elif direction == b'K':  # 左方向键 (仅对二维数组有效)
                if input_type == 2:
                    selected_col = (selected_col - 1) % cols
            elif direction == b'M':  # 右方向键 (仅对二维数组有效)
                if input_type == 2:
                    selected_col = (selected_col + 1) % cols


def compress_folder(folder_path, zip_file_path):
    with zipfile.ZipFile(zip_file_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for root, _, files in os.walk(folder_path):
            for file in files:
                file_path = os.path.join(root, file)
                rel_path = os.path.relpath(file_path, folder_path)
                zipf.write(file_path, rel_path)

def run_server():
    try:
        global server_files_folder
        host = ''
        port = int(server_port)
        print('[Main_Server_Output]Port Opened:'+str(port))
        backlog = 5
        server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_socket.bind((host, port))
        server_socket.listen(backlog)
        print('等待客户端连接...')

        while True:
            client_socket, client_address = server_socket.accept()
            print('[Main_Server_Output]Cilent conntining')
            print('客户端 %s 连接成功！' % client_address[0])
            # 发送文件列表
            file_list = os.listdir(server_files_folder)
            file_names = '\n'.join(file_list)
            client_socket.send(file_names.encode() + b'<<EOF>>')
            print('[Main_Server_Output]Files list sent!')
            # 接收客户端请求的文件或文件夹名称
            folder_name = client_socket.recv(buf_size).decode()

            # 判断是否是文件夹，是则压缩发送
            folder_path = os.path.join(server_files_folder, folder_name)
            if os.path.isdir(folder_path):
                print('[Main_Server_Output]Cilent Download Mode:ZIP')
                # 发送压缩文件的通知
                client_socket.send(b'ZIP')
                print('[Main_Server_Output]Mode sent')

                # 压缩文件夹并发送
                zip_file_path = os.path.join(
                    server_files_folder, f"{folder_name}.zip")
                total_files = sum(len(files)
                                for _, _, files in os.walk(folder_path))
                processed_files = 0

                print('[Main_Server_Output]压缩中...')
                with zipfile.ZipFile(zip_file_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                    for root, _, files in os.walk(folder_path):
                        for file in files:
                            file_path = os.path.join(root, file)
                            rel_path = os.path.relpath(file_path, folder_path)
                            zipf.write(file_path, rel_path)
                            # 更新压缩进度
                            processed_files += 1
                            progress = processed_files / total_files * 100
                            print('\r压缩进度：{}'.format(print_progress_bar(round(progress))), end='')

                print('\n[Main_Server_Output]压缩完成:'+zip_file_path)

                # 发送压缩文件
                print('[Main_Server_Output]Starting Send File...')
                with open(zip_file_path, 'rb') as zip_file:
                    print('[Main_Server_Output]Sending...')
                    file_size = os.path.getsize(zip_file_path)
                    client_socket.send(str(file_size).encode())
                    while True:
                        data = zip_file.read(buf_size)
                        if not data:
                            break
                        client_socket.sendall(data)
                print('[Main_Server_Output]Finshed.')

                # 计算压缩文件的SHA-1值
                with open(zip_file_path, 'rb') as file:
                    file_data = file.read()
                    sha1_hash = hashlib.sha1()
                    sha1_hash.update(file_data)
                    file_sha1 = sha1_hash.hexdigest()

                    # 将SHA-1值发送给客户端
                    print('[Main_Server_Output]Sending SHA-1...')
                    client_socket.send(file_sha1.encode())
                    print('[Main_Server_Output]SHA-1 sent :' + file_sha1)

                # 删除压缩文件
                os.remove(zip_file_path)

            else:
                # 如果不是文件夹，则发送普通文件
                client_socket.send(b'FILE')
                print('[Main_Server_Output]Cilent Download Mode:NORMAL FILE')

                # 发送文件大
                print('[Main_Server_Output]Sending File Size:')
                client_socket.send(str(os.path.getsize(folder_path)).encode())
                print('[Main_Server_Output]Sent!')

                # 发送文件内容
                with open(folder_path, 'rb') as file:
                    print('[Main_Server_Output]Starting Send File...')
                    print('[Main_Server_Output]Sending...')
                    while True:
                        data = file.read(buf_size)
                        if not data:
                            break
                        client_socket.sendall(data)
                print('[Main_Server_Output]Finshed!')
                print("[Main_Server_Output]Getting SHA-1...")
                # 计算文件的SHA-1值
                with open(folder_path, 'rb') as file:
                    file_data = file.read()
                    sha1_hash = hashlib.sha1()
                    sha1_hash.update(file_data)
                    file_sha1 = sha1_hash.hexdigest()
                    print('[Main_Server_Output]Finshed!')
                    # 将SHA-1值发送给客户端
                    print('[Main_Server_Output]Sending SHA-1...')
                    client_socket.send(file_sha1.encode())
                    print('[Main_Server_Output]SHA-1 sent :' + file_sha1)

            client_socket.close()
            print('[Main_Server_Output]Cilent '+client_address[0]+' losted contiune')
    except Exception as e:
        # print('[Main_Server_Output]ERROR!:'+str(e))
        # print('[Main_Server_Output]Press Enter to contiune...')
        # input()
        # print('[Main_Server_Output]Server will restart after 2 secs...')
        server_socket.close()
        # time.sleep(2)
        run_server()


def run_client(server_ip, download_folder):
    try:
        client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_ip_c = server_ip.split(':')[0]
        print(server_ip_c)
        server_port = server_ip.split(':')[1]
        client_socket.connect((server_ip_c, int(server_port)))
        print('已连接至服务器 %s:25565' % server_ip)

        # 接收并打印服务端的文件列表
        print('服务器文件列表：')
        file_list = []  # 初始化为空列表
        while True:
            data = client_socket.recv(buf_size)
            if data.endswith(b'<<EOF>>'):
                # 处理最后一部分数据，去掉结束标记并分割成文件名
                file_list.extend(data.decode()[:-7].splitlines())  # 按行分割并添加到列表中
                break
            else:
                # 将接收到的数据按行分割并添加到列表中
                file_list.extend(data.decode().splitlines())

        print(type(file_list))  # 现在应该是 <class 'list'>
        print(file_list)  # 输出文件名列表
        folder_name_down = render_options(1,options=file_list,prompt="请选择要下载的文件")
        # 输入要下载的文件或文件夹名称
        folder_name = file_list[folder_name_down]
        client_socket.send(folder_name.encode())

        # 接收服务端的响应
        response = client_socket.recv(buf_size).decode()

        if response == 'ZIP':
            print("请稍候服务端正在压缩...")
            # 接收压缩文件大小
            file_size = int(client_socket.recv(buf_size).decode())

            # 创建并启动 FileDownloadThread 线程来接收并解压缩 ZIP 文件
            zip_file_path = os.path.join(download_folder, folder_name + ".zip")
            file_download_thread = FileDownloadThread(
                client_socket, folder_name + ".zip", file_size, download_folder)
            file_download_thread.start()
            file_download_thread.join()
            print("正在计算SHA-1...")
            # 计算 ZIP 文件的 SHA-1 值
            sha1_hash = hashlib.sha1()
            with open(zip_file_path, 'rb') as zip_file:
                while True:
                    data = zip_file.read(buf_size)
                    if not data:
                        break
                    sha1_hash.update(data)
            zip_file_sha1 = sha1_hash.hexdigest()

            # 解压文件到临时文件夹
            temp_extract_folder = os.path.join(download_folder, 'temp_extract')
            with zipfile.ZipFile(zip_file_path, 'r') as zip_ref:
                zip_ref.extractall(temp_extract_folder)

            # 获取压缩文件中的文件结构信息
            files_structure = []
            for root, dirs, files in os.walk(temp_extract_folder):
                for file in files:
                    file_path = os.path.join(root, file)
                    rel_path = os.path.relpath(file_path, temp_extract_folder)
                    files_structure.append((file_path, rel_path))

            # 根据文件结构信息将文件移动到下载文件夹的相应位置
            for file_path, rel_path in files_structure:
                target_path = os.path.join(
                    download_folder+"\\"+folder_name, rel_path)
                os.makedirs(os.path.dirname(target_path), exist_ok=True)


            for file_path, rel_path in files_structure:
                target_path = os.path.join(download_folder+"\\"+folder_name, rel_path)
                os.makedirs(os.path.dirname(target_path), exist_ok=True)


            # 如果目标文件已经存在，重命名文件
            if os.path.exists(target_path):
                base_name, ext = os.path.splitext(target_path)
                index = 1
                while os.path.exists(base_name + f"_{index}" + ext):
                    index += 1
                new_target_path = base_name + f"_{index}" + ext
                print(f"文件 '{target_path}' 已存在，重命名为 '{new_target_path}'")
                os.rename(file_path, new_target_path)
            else:
                os.rename(file_path, target_path)
                # 接收并比较 ZIP 文件的 SHA1 值
                # 接收并比较SHA1值
            print("正在接收服务端SHA-1(服务端可能正在计算)")
            server_sha1 = client_socket.recv(buf_size).decode()
            received_hash = sha1_hash.hexdigest()
            print("服务器发送的SHA-1校验值：" + received_hash +
                "\n"+"客户端计算的SHA-1下载值:"+server_sha1)
            if received_hash == server_sha1:
                print("文件完整性校验通过")
            else:
                print("服务器发送的SHA-1校验值：" + received_hash +
                "\n"+"客户端计算的SHA-1下载值:"+server_sha1)
                print("文件完整性校验失败")

            # 删除临时文件夹和压缩文
            shutil.rmtree(temp_extract_folder)
            os.remove(zip_file_path)

        elif response == 'FILE':
            file_size = int(client_socket.recv(buf_size).decode())
            file_download_thread = FileDownloadThread(
                client_socket, folder_name, file_size, download_folder)
            file_download_thread.start()
            file_download_thread.join()
            print('文件接收完成！')
            sha1_hash = hashlib.sha1()
            print("正在计算SHA-1...")
            with open(os.path.join(download_folder, folder_name), 'rb') as file:
                while True:
                    data = file.read(buf_size)
                    if not data:
                        break
                    sha1_hash.update(data)

            # 接收并比较SHA1值
            server_sha1 = client_socket.recv(buf_size).decode()
            received_hash = sha1_hash.hexdigest()
            print("服务器发送的SHA-1校验值：" + received_hash +
                "\n"+"客户端计算的SHA-1下载值:"+server_sha1)
            if received_hash == server_sha1:
                print("文件完整性校验通过")
            else:
                print("服务器发送的SHA-1校验值：" + received_hash +
                        "\n"+"客户端计算的SHA-1下载值:"+server_sha1)
                
                print("文件完整性校验失败")
    except Exception as e:
        print(f"运行客户端时出错：{e}\n=========================")
        input('Press Enter to restart client')
    finally:
        client_socket.close()
        time.sleep(1)

# 加载服务器配置
def load_server_config():
    config = configparser.ConfigParser()
    if os.path.exists(SERVER_CONFIG_PATH):
        config.read(SERVER_CONFIG_PATH)
        print("Path:"+config["Server"]["upload_folder"])
        print("Path:"+config["Server"]["new_server_port"])
        return config["Server"]["upload_folder"], config["Server"]["new_server_port"]
    else:
        os.makedirs(CONFIG_DIR, exist_ok=True)
        upload_folder = input("请输入服务器上传文件夹路径: ")
        new_server_port = input("请输入新的服务器端口: ")
        config["Server"] = {"upload_folder": upload_folder,"new_server_port": new_server_port}
        with open(SERVER_CONFIG_PATH, "w") as configfile:
            config.write(configfile)
        return upload_folder,new_server_port

# 加载客户端配置
def load_client_config():
    config = configparser.ConfigParser()
    if os.path.exists(CLIENT_CONFIG_PATH):
        config.read(CLIENT_CONFIG_PATH)
        server_ip = config["Client"]["server_ip"]
        download_folder = config["Client"]["download_folder"]
        print(f"客户端Config:\nIP:{server_ip}\nPath_Download:{download_folder}")
    else:
        os.makedirs(CONFIG_DIR, exist_ok=True)
        server_ip = input("请输入连接的服务器IP: ")
        download_folder = input("请输入客户端下载文件夹路径: ")
        config["Client"] = {"server_ip": server_ip, "download_folder": download_folder}
        with open(CLIENT_CONFIG_PATH, "w") as configfile:
            config.write(configfile)
    return server_ip, download_folder
def clear_console():
    """ 清屏，模拟类似 curses 的效果 """
    os.system('cls' if os.name == 'nt' else 'clear')

def get_max_width(options):
    """ 获取二维数组或列表中的最长文本宽度 """
    max_width = 0
    if isinstance(options[0], list):
        for row in options:
            for item in row:
                max_width = max(max_width, len(item))
    else:
        for item in options:
            max_width = max(max_width, len(item))
    return max_width

def display_aligned_text(text_list, alignment='left', padding=2):
    """
    在控制台显示文本，并确保对齐。
    输入:
    - text_list: 字符串列表
    - alignment: 对齐方式，'left'表示左对齐，'right'表示右对齐，默认左对齐
    - padding: 在文本右侧添加的空格，默认是2个空格
    输出:
    - 对齐文本的显示
    """
    max_length = max([len(text) for text in text_list]) + padding

    for text in text_list:
        if alignment == 'left':
            print(text.ljust(max_length))  # 左对齐
        elif alignment == 'right':
            print(text.rjust(max_length))  # 右对齐



def start():
    print('loading')
    time.sleep(1)
    global server_files_folder,server_port
    while True:
        pdyj = str(render_options(1,options=['服务器(发送)', '客户端(接受)' ,'修改配置',"**更新日志**"],prompt='===============\n版本B0.5.7\nGUI TESTING VERISON\nTESTING VER:BUILD - 4\n==============='))
        time.sleep(1)
        if pdyj == '0':
            # total_steps = 100
            # for i in range(total_steps + 1):
            #     show_progress_bar(i, total_steps)
            #     time.sleep(0.01)  # 模拟一些操作
            clear_console()
            server_files_folder = load_server_config()[0]
            server_port = load_server_config()[1]
            run_server()
            start()
        elif pdyj == '1':
            # total_steps = 100
            # for i in range(total_steps + 1):
            #     show_progress_bar(i, total_steps)
            #     time.sleep(0.01)  # 模拟一些操作
            clear_console()
            client_ip, client_download_folder = load_client_config()
            run_client(client_ip, client_download_folder)
            start()
        elif pdyj == '3':
            clear_console()
            config_choice2 = render_options(1,options=["确定"],prompt="Update Log\n更新日志\nVerison:B 0.5.7 GUI_TESTING VER - BUILD 3\n1.全新GUI画面\n2.修复MD5和BASE64编码问题\n3.加入输入框\n4.列表滚动不再闪烁(引用了转义符)")
            
        elif pdyj == '2':
            clear_console()
            config_choice = str(render_options(1,options=["服务器配置","客户端配置"],prompt="要修改服务器配置还是客户端配置？") + 1)
            if config_choice == '1':
                config = configparser.ConfigParser()
                config.read(SERVER_CONFIG_PATH)
                # new_upload_folder = input("请输入新的服务器上传文件夹路径: ")
                # new_server_port = input("请输入新的服务器端口: ")
                new_server_port = input_box_with_prompt(prompt="请输入新的服务器端口: ")
                if(new_server_port == False):
                    render_options(1,options=["确定"],prompt="请重新选择并输入")
                    start()
                new_upload_folder = input_box_with_prompt(prompt="请输入新的服务器上传文件夹路径:\n(若你输的路径带有中文 请输入chinese进行input输入)")
                if(new_upload_folder == False):
                    render_options(1,options=["确定"],prompt="请重新选择并输入")
                    start()
                if(new_upload_folder == "chinese"):
                    new_upload_folder = input("请输入新的服务器上传文件夹路径:")
                
                config["Server"]["new_server_port"] = new_server_port
                config["Server"]["upload_folder"] = new_upload_folder
                
                with open(SERVER_CONFIG_PATH, "w") as configfile:
                    config.write(configfile)
                print("服务器配置已更新")
                start()
            elif config_choice == '2':
                config = configparser.ConfigParser()
                config.read(CLIENT_CONFIG_PATH)
                #new_server_ip = input("请输入新的服务器IP(xxx.xxx.xx.xx:port): ")
                new_server_ip = input_box_with_prompt(prompt="请输入新的服务器IP(xxx.xxx.xx.xx:port):")
                if(new_server_ip == False):
                    render_options(1,options=["确定"],prompt="请重新选择并输入")
                    start()
                new_download_folder = input_box_with_prompt(prompt="请输入新的客户端下载文件夹路径:\n(若你输的路径带有中文 请输入chinese进行input输入)")
                if(new_download_folder == False):
                    render_options(1,options=["确定"],prompt="请重新选择并输入")
                    start()
                if(new_download_folder == "chinese"):
                    new_download_folder = input("请输入新的客户端下载文件夹路径: ")
                print(new_download_folder)
                config["Client"]["server_ip"] = new_server_ip
                config["Client"]["download_folder"] = new_download_folder
                with open(CLIENT_CONFIG_PATH, "w") as configfile:
                    config.write(configfile)
                print("客户端配置已更新")
                start()
            else:
                print('错误数值，请重新输入')
                start()
        else:
            print('错误数值，请重新输入')
            start()
    

start()
