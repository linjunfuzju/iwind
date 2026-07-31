#!/usr/bin/env python3
"""
ZWind 一键批量仿真脚本（跨平台版）

支持: Windows, macOS, Linux
需要: Docker Desktop 已安装

用法:
    python run_simulation.py

Windows 用户:
    1. 安装 Docker Desktop: https://docs.docker.com/desktop/install/windows-install/
    2. 打开 PowerShell 或 CMD
    3. 进入本脚本所在目录
    4. 运行: python run_simulation.py
"""

import subprocess
import sys
import os
import shutil
import platform
import signal
import threading
import socket
import time
from datetime import datetime

IMAGE_NAME = "zwind-reproduce:v4"
RESULTS_DIR = "./simulation_runs"

# 全局变量：容器 ID
container_id = None
container_lock = threading.Lock()

# API 端口范围
API_START_PORT = 8005
API_MAX_PORT = 8010


def detect_os():
    """检测操作系统"""
    system = platform.system().lower()
    if system == "windows":
        return "windows"
    elif system == "darwin":
        return "macos"
    elif system == "linux":
        return "linux"
    return "unknown"


def run_command(cmd, description="", check=True):
    """运行命令并显示输出"""
    print(f"[执行] {description}...")
    print(f"[命令] {' '.join(cmd) if isinstance(cmd, list) else cmd}")
    result = subprocess.run(cmd, shell=isinstance(cmd, str))
    return result.returncode == 0 if check else True


def check_docker():
    """检查 Docker 是否安装并运行"""
    docker_path = shutil.which("docker")
    if not docker_path:
        print("[错误] Docker 未安装或不在 PATH 中")
        print("")
        print("请先安装 Docker:")
        print("  Windows: https://docs.docker.com/desktop/install/windows-install/")
        print("  macOS:   https://docs.docker.com/desktop/install/mac-install/")
        print("  Linux:   https://docs.docker.com/desktop/install/linux-install/")
        return False

    try:
        subprocess.run(["docker", "info"], capture_output=True, check=True)
    except subprocess.CalledProcessError:
        print("[错误] Docker 未运行")
        print("请启动 Docker Desktop 后重试")
        return False

    print("[OK] Docker 已就绪")
    return True


def is_port_in_use(port):
    """检查端口是否被占用"""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        return s.connect_ex(('localhost', port)) == 0


def find_available_port(start_port=API_START_PORT, max_attempts=10):
    """查找可用端口"""
    for port in range(start_port, start_port + max_attempts):
        if not is_port_in_use(port):
            return port
    return None


def cleanup_containers_on_port(port):
    """清理占用指定端口的容器"""
    try:
        # 查找占用端口的容器
        result = subprocess.run(
            ["docker", "ps", "--format", "{{.ID}} {{.Ports}}"],
            capture_output=True, text=True
        )
        for line in result.stdout.strip().split('\n'):
            if not line:
                continue
            parts = line.split()
            if len(parts) >= 2:
                container_id = parts[0]
                ports_info = ' '.join(parts[1:])
                if f":{port}->" in ports_info or f"{port}/tcp" in ports_info:
                    print(f"[清理] 停止占用端口 {port} 的旧容器: {container_id[:12]}")
                    subprocess.run(["docker", "stop", container_id],
                                 capture_output=True, stderr=subprocess.DEVNULL)
                    subprocess.run(["docker", "rm", container_id],
                                 capture_output=True, stderr=subprocess.DEVNULL)
                    return True
    except Exception as e:
        print(f"[警告] 清理容器时出错: {e}")
    return False


def cleanup_stale_containers():
    """清理所有处于 Created 或 Exited 状态的 zwind 容器"""
    try:
        result = subprocess.run(
            ["docker", "ps", "-a", "--format", "{{.ID}} {{.Names}} {{.Status}}"],
            capture_output=True, text=True
        )
        for line in result.stdout.strip().split('\n'):
            if not line:
                continue
            parts = line.split()
            if len(parts) >= 3:
                container_id = parts[0]
                container_name = parts[1]
                status = ' '.join(parts[2:])

                # 只清理 zwind 容器
                if "zwind" not in container_name.lower():
                    continue

                # 清理 Created 或 Exited 状态的容器
                if "Created" in status or "Exited" in status:
                    print(f"[清理] 删除旧容器: {container_name} ({status})")
                    subprocess.run(["docker", "rm", container_id],
                                 capture_output=True, stderr=subprocess.DEVNULL)
    except Exception as e:
        print(f"[警告] 清理旧容器时出错: {e}")


def generate_container_name():
    """生成带时间戳的容器名称"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    return f"zwind_{timestamp}"


def find_image_file():
    """自动查找当前目录下的 .tar.gz 镜像文件"""
    import glob
    tar_files = glob.glob("*.tar.gz")
    if not tar_files:
        print("[错误] 未找到任何 .tar.gz 镜像文件")
        print("请确保镜像文件在当前目录下")
        return None
    if len(tar_files) > 1:
        print(f"[警告] 发现多个 tar.gz 文件，使用第一个: {tar_files[0]}")
    # 优先使用 _fixed 版本
    for tf in tar_files:
        if "_fixed" in tf:
            print(f"[信息] 优先使用修复版镜像: {tf}")
            return tf
    return tar_files[0]


def load_image():
    """加载 Docker 镜像"""
    image_file = find_image_file()
    if not image_file:
        return False
    print(f"[信息] 找到镜像文件: {image_file}")

    try:
        subprocess.run(["docker", "image", "inspect", IMAGE_NAME],
                      capture_output=True, check=True)
        print("[OK] 镜像已存在，跳过加载")
        return True
    except subprocess.CalledProcessError:
        pass

    print(f"[加载] 正在加载 Docker 镜像 (~450MB)...")
    try:
        # 使用二进制模式兼容 Windows
        import gzip
        with open(image_file, "rb") as f:
            gzip_file = gzip.GzipFile(fileobj=f)
            load_process = subprocess.Popen(
                ["docker", "load"],
                stdin=gzip_file,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT
            )
            for line in iter(load_process.stdout.readline, b""):
                print(line.decode("utf-8", errors="replace").rstrip())
            load_process.wait()
        print("[OK] 镜像加载完成")
        return True
    except Exception as e:
        print(f"[错误] 加载镜像失败: {e}")
        return False


def prepare_dirs():
    """创建结果目录"""
    os.makedirs(RESULTS_DIR, exist_ok=True)
    results_path = os.path.abspath(RESULTS_DIR)
    print(f"[OK] 结果目录: {results_path}")
    return results_path


def cleanup(signum=None, frame=None):
    """清理函数：停止 Docker 容器（保留容器以便恢复）"""
    global container_id
    print("")
    print("[中断] 收到停止信号，正在清理...")
    if container_id:
        print(f"[停止] 停止 Docker 容器 ({container_id[:12]})...")
        subprocess.run(["docker", "stop", container_id],
                      capture_output=True, stderr=subprocess.DEVNULL)
        print(f"[提示] 容器已停止，可用 'docker start {container_id}' 恢复运行")
    print("[完成] 脚本已退出")
    sys.exit(130)


def setup_signal_handler():
    """设置信号处理器"""
    signal.signal(signal.SIGINT, cleanup)
    signal.signal(signal.SIGTERM, cleanup)


def find_available_api_port_in_container(container_id, start_port=8005, max_attempts=10):
    """在容器内查找可用端口启动 API 服务"""
    for port in range(start_port, start_port + max_attempts):
        # 测试容器内端口是否可用
        test_cmd = [
            "docker", "exec", container_id, "bash", "-c",
            f"python3 -c \"import socket; s=socket.socket(); s.bind(('0.0.0.0',{port})); s.close()\""
        ]
        result = subprocess.run(test_cmd, capture_output=True)
        if result.returncode == 0:
            return port
    return start_port  # 默认返回 8005


def run_simulation(results_path):
    """运行批量仿真"""
    global container_id

    print("")
    print("==============================================")
    print("[运行] 开始批量仿真 (336组工况)")
    print("预计时间: 约48小时 (可 Ctrl+C 中断)")
    print("==============================================")
    print("")

    # 设置信号处理器
    setup_signal_handler()

    # 清理旧容器
    print("[清理] 清理旧容器...")
    cleanup_stale_containers()

    # 环境变量配置
    env = os.environ.copy()
    env["CONFIGURED_CASE_TYPES"] = "Typhoon_V40,Typhoon_V60,Earthquake_1g,Earthquake_2g"

    # 查找可用端口
    available_port = find_available_port(API_START_PORT, API_MAX_PORT - API_START_PORT + 1)
    if not available_port:
        print(f"[错误] 无法找到可用端口 ({API_START_PORT}-{API_MAX_PORT})")
        return

    if available_port != API_START_PORT:
        print(f"[提示] 端口 {API_START_PORT} 已被占用，使用端口 {available_port}")

    # 先清理目标端口的旧容器
    cleanup_containers_on_port(available_port)

    # 生成容器名称
    container_name = generate_container_name()

    # 启动容器（使用 sleep infinity 保持容器运行）
    print("[启动] 创建 Docker 容器...")
    create_cmd = [
        "docker", "run", "-d",
        "--name", container_name,
        "-v", f"{results_path}:/app/simulation_runs",
        "-p", f"{available_port}:8005",
        "-e", f"CONFIGURED_CASE_TYPES={env['CONFIGURED_CASE_TYPES']}",
        IMAGE_NAME,
        "sleep", "infinity"
    ]

    try:
        result = subprocess.run(create_cmd, capture_output=True, text=True, env=env)
        if result.returncode != 0:
            # 容器创建失败，尝试清理后重试
            print(f"[警告] 创建容器失败，尝试清理...")
            cleanup_containers_on_port(available_port)
            result = subprocess.run(create_cmd, capture_output=True, text=True, env=env)
            result.check_returncode()

        container_id = result.stdout.strip()
        print(f"[容器] 容器已启动: {container_id[:12]} (名称: {container_name})")
    except subprocess.CalledProcessError as e:
        print(f"[错误] 创建容器失败: {e.stderr}")
        print("[提示] 请手动运行 'docker ps -a' 查看容器状态")
        return

    # 在容器内启动服务并运行仿真
    # 使用找到的端口启动 API 服务
    exec_cmd = [
        "docker", "exec", container_id, "bash", "-c",
        f"echo '[启动] 启动 API 服务 (端口 {available_port})...' && "
        f"python3 -m uvicorn main:app --host 0.0.0.0 --port 8005 & "
        "echo '[等待] 等待 API 服务就绪...' && "
        "sleep 5 && "
        "echo '[运行] 开始批量仿真...' && "
        "exec python3 -m tools.zwind_batch_runner"
    ]

    print(f"[命令] 在容器 {container_id[:12]} 中启动批量仿真")
    print("")
    print("开始执行批量任务，按 Ctrl+C 可中断...")
    print("=" * 60)

    try:
        subprocess.run(exec_cmd, env=env)
    except KeyboardInterrupt:
        cleanup()
    finally:
        # 正常结束时停止容器（保留以便恢复）
        if container_id:
            print(f"[停止] 停止容器 {container_id[:12]}...")
            subprocess.run(["docker", "stop", container_id],
                          capture_output=True, stderr=subprocess.DEVNULL)
            print(f"[提示] 容器已停止，可用 'docker start {container_id}' 恢复运行")
            container_id = None


def main():
    print("==============================================")
    print(" ZWind 批量仿真 (336组工况)")
    print("==============================================")
    print(f"[系统] {detect_os().upper()}")
    print("")

    # 检查 Docker
    if not check_docker():
        sys.exit(1)

    # 加载镜像
    if not load_image():
        sys.exit(1)

    # 创建结果目录
    results_path = prepare_dirs()

    # 运行仿真
    run_simulation(results_path)

    print("")
    print("==============================================")
    print("完成！")
    print(f"结果目录: {results_path}")
    print("==============================================")


if __name__ == "__main__":
    main()
