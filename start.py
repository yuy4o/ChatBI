import subprocess
import os
import sys
import time
import signal
import argparse

# 定义路径
BACKEND_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'backend')
FRONTEND_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'frontend')

# 存储进程
processes = []

# 处理信号，确保在脚本终止时关闭所有子进程
def signal_handler(sig, frame):
    print('\n正在关闭所有服务...')
    for process in processes:
        if process.poll() is None:  # 如果进程还在运行
            if sys.platform == 'win32':
                process.terminate()
            else:
                process.send_signal(signal.SIGTERM)
    sys.exit(0)

# 注册信号处理器
signal.signal(signal.SIGINT, signal_handler)
signal.signal(signal.SIGTERM, signal_handler)

# 启动后端服务
def start_backend():
    print('正在启动后端服务...')
    backend_process = subprocess.Popen(
        [sys.executable, 'app.py'],
        cwd=BACKEND_DIR,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1,
        universal_newlines=True
    )
    processes.append(backend_process)

    # 启动一个线程来读取和打印后端输出
    def print_backend_output():
        for line in backend_process.stdout:
            print(f'[后端] {line.strip()}')

    import threading
    backend_thread = threading.Thread(target=print_backend_output)
    backend_thread.daemon = True
    backend_thread.start()

    # 等待后端启动
    time.sleep(2)
    print('后端服务已启动，运行在 http://localhost:5000')
    return backend_process

# 启动前端服务
def start_frontend():
    print('正在启动前端服务...')
    npm_cmd = 'npm.cmd' if sys.platform == 'win32' else 'npm'
    frontend_process = subprocess.Popen(
        [npm_cmd, 'start'],
        cwd=FRONTEND_DIR,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1,
        universal_newlines=True
    )
    processes.append(frontend_process)

    # 启动一个线程来读取和打印前端输出
    def print_frontend_output():
        for line in frontend_process.stdout:
            print(f'[前端] {line.strip()}')

    import threading
    frontend_thread = threading.Thread(target=print_frontend_output)
    frontend_thread.daemon = True
    frontend_thread.start()

    # 等待前端启动
    time.sleep(2)
    print('前端服务已启动，运行在 http://localhost:5173')
    return frontend_process

def main():
    parser = argparse.ArgumentParser(description='启动MapperSuggest应用')
    parser.add_argument('--frontend-only', action='store_true', help='只启动前端服务')
    parser.add_argument('--backend-only', action='store_true', help='只启动后端服务')
    args = parser.parse_args()

    try:
        if args.frontend_only:
            start_frontend()
            print('\n前端服务已启动。按Ctrl+C停止服务。')
        elif args.backend_only:
            start_backend()
            print('\n后端服务已启动。按Ctrl+C停止服务。')
        else:
            # 启动后端和前端
            start_backend()
            start_frontend()
            print('\n所有服务已启动。按Ctrl+C停止所有服务。')
            print('\n访问 http://localhost:5173 查看应用')

        # 保持脚本运行
        while True:
            time.sleep(1)

            # 检查进程是否还在运行
            for i, process in enumerate(processes):
                if process.poll() is not None:  # 进程已终止
                    if i == 0 and not args.frontend_only:
                        print('后端服务已停止，退出代码:', process.returncode)
                        signal_handler(None, None)  # 关闭所有进程
                    elif i == 1 and not args.backend_only:
                        print('前端服务已停止，退出代码:', process.returncode)
                        signal_handler(None, None)  # 关闭所有进程

    except KeyboardInterrupt:
        pass
    finally:
        signal_handler(None, None)  # 确保关闭所有进程

if __name__ == '__main__':
    main()