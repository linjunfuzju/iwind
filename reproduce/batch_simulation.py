#!/usr/bin/env python3
"""
ZWind Batch Simulation Script (Cross-platform)

Supports: Windows, macOS, Linux
Requires: Docker Desktop installed

Usage:
    python run_simulation.py

Windows users:
    1. Install Docker Desktop: https://docs.docker.com/desktop/install/windows-install/
    2. Open PowerShell or CMD
    3. Navigate to this script's directory
    4. Run: python run_simulation.py
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

# Global variable: container ID
container_id = None
container_lock = threading.Lock()

# API port range
API_START_PORT = 8005
API_MAX_PORT = 8010


def detect_os():
    """Detect operating system"""
    system = platform.system().lower()
    if system == "windows":
        return "windows"
    elif system == "darwin":
        return "macos"
    elif system == "linux":
        return "linux"
    return "unknown"


def run_command(cmd, description="", check=True):
    """Run command and display output"""
    print(f"[EXEC] {description}...")
    print(f"[CMD] {' '.join(cmd) if isinstance(cmd, list) else cmd}")
    result = subprocess.run(cmd, shell=isinstance(cmd, str))
    return result.returncode == 0 if check else True


def check_docker():
    """Check if Docker is installed and running"""
    docker_path = shutil.which("docker")
    if not docker_path:
        print("[ERROR] Docker is not installed or not in PATH")
        print("")
        print("Please install Docker first:")
        print("  Windows: https://docs.docker.com/desktop/install/windows-install/")
        print("  macOS:   https://docs.docker.com/desktop/install/mac-install/")
        print("  Linux:   https://docs.docker.com/desktop/install/linux-install/")
        return False

    try:
        subprocess.run(["docker", "info"], capture_output=True, check=True)
    except subprocess.CalledProcessError:
        print("[ERROR] Docker is not running")
        print("Please start Docker Desktop and try again")
        return False

    print("[OK] Docker is ready")
    return True


def is_port_in_use(port):
    """Check if port is in use"""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        return s.connect_ex(('localhost', port)) == 0


def find_available_port(start_port=API_START_PORT, max_attempts=10):
    """Find an available port"""
    for port in range(start_port, start_port + max_attempts):
        if not is_port_in_use(port):
            return port
    return None


def cleanup_containers_on_port(port):
    """Clean up containers occupying the specified port"""
    try:
        # Find containers occupying the port
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
                    print(f"[CLEANUP] Stopping old container occupying port {port}: {container_id[:12]}")
                    subprocess.run(["docker", "stop", container_id],
                                 stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                    subprocess.run(["docker", "rm", container_id],
                                 stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                    return True
    except Exception as e:
        print(f"[WARNING] Error during container cleanup: {e}")
    return False


def cleanup_stale_containers():
    """Clean up all zwind containers in Created or Exited state"""
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

                # Only clean zwind containers
                if "zwind" not in container_name.lower():
                    continue

                # Clean Created or Exited containers
                if "Created" in status or "Exited" in status:
                    print(f"[CLEANUP] Removing old container: {container_name} ({status})")
                    subprocess.run(["docker", "rm", container_id],
                                 stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except Exception as e:
        print(f"[WARNING] Error cleaning stale containers: {e}")


def generate_container_name():
    """Generate container name with timestamp"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    return f"zwind_{timestamp}"


def find_image_file():
    """Automatically find Docker image file (.tar.gz) in current directory.

    This function uses multiple strategies to find .tar.gz files:
    1. First tries glob with *.tar.gz (case-sensitive)
    2. Then tries case-insensitive glob for variations
    3. Finally falls back to listing all files and checking extensions manually

    If multiple files are found, it will:
    1. Prioritize files containing "_fixed" in the name
    2. If still multiple, use the first one and warn user

    This ensures the script works regardless of filename changes.
    """
    import glob
    import os

    # Get script directory (works even if script is run from different cwd)
    script_dir = os.path.dirname(os.path.abspath(__file__)) if '__file__' in dir() else os.getcwd()

    def filter_tar_gz(files):
        """Filter out non-.tar.gz files (e.g., .zip files) and return valid ones"""
        valid = []
        for f in files:
            basename = os.path.basename(f).lower()
            # Must end with .tar.gz (exactly)
            if basename.endswith('.tar.gz') and not basename.endswith('.tar.gz.zip'):
                valid.append(f)
        return valid

    # Strategy 1: Try standard glob *.tar.gz
    tar_files = glob.glob(os.path.join(script_dir, "*.tar.gz"))
    tar_files = filter_tar_gz(tar_files)

    # Strategy 2: If nothing found, try case-insensitive patterns
    if not tar_files:
        for pattern in ['*.tar.gz', '*.tar.GZ', '*.TAR.GZ', '*.TAR.gz']:
            tar_files = glob.glob(os.path.join(script_dir, pattern))
            tar_files = filter_tar_gz(tar_files)
            if tar_files:
                print(f"[INFO] Found image file using case-insensitive pattern: {pattern}")
                break

    # Strategy 3: If still nothing, list all files and check manually
    if not tar_files:
        all_files = os.listdir(script_dir)
        for f in all_files:
            f_lower = f.lower()
            if f_lower.endswith('.tar.gz') and not f_lower.endswith('.tar.gz.zip'):
                tar_files.append(os.path.join(script_dir, f))
                print(f"[INFO] Found image file via directory listing: {f}")

    if not tar_files:
        print("[ERROR] No valid .tar.gz image file found in current directory")
        print(f"[INFO] Searched in: {script_dir}")
        print("[INFO] Please ensure the Docker image file (.tar.gz) is in the same directory")
        # List what files ARE there for debugging
        all_files = os.listdir(script_dir)
        tar_like = [f for f in all_files if '.tar' in f.lower() or '.zip' in f.lower()]
        if tar_like:
            print(f"[INFO] Found archive-like files: {tar_like}")
            print("[INFO] Note: Only .tar.gz files are accepted, not .zip or other formats")
        return None

    # Convert to just filenames for display
    tar_basenames = [os.path.basename(f) for f in tar_files]

    if len(tar_files) == 1:
        print(f"[INFO] Found image file: {tar_basenames[0]}")
        return tar_files[0]

    # Multiple files found - prioritize _fixed version
    fixed_files = [f for f in tar_files if "_fixed" in os.path.basename(f).lower()]
    if len(fixed_files) == 1:
        print(f"[INFO] Multiple .tar.gz files found, using _fixed version: {os.path.basename(fixed_files[0])}")
        return fixed_files[0]
    elif len(fixed_files) > 1:
        # Multiple _fixed files - use first one and warn
        print(f"[WARNING] Multiple _fixed versions found, using first: {os.path.basename(fixed_files[0])}")
        print(f"[INFO] Available candidates: {', '.join(tar_basenames)}")
        return fixed_files[0]

    # No _fixed version, use first file and warn
    print(f"[WARNING] Multiple .tar.gz files found, using first: {tar_basenames[0]}")
    print(f"[INFO] Available candidates: {', '.join(tar_basenames)}")
    return tar_files[0]


def load_image():
    """Load Docker image"""
    image_file = find_image_file()
    if not image_file:
        return False
    print(f"[INFO] Image file: {image_file}")

    try:
        subprocess.run(["docker", "image", "inspect", IMAGE_NAME],
                      capture_output=True, check=True)
        print("[OK] Image already exists, skipping load")
        return True
    except subprocess.CalledProcessError:
        pass

    print(f"[LOAD] Loading Docker image (~450MB)...")
    try:
        # Use binary mode for Windows compatibility
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

        if load_process.returncode != 0:
            print(f"[ERROR] Docker load failed with code {load_process.returncode}")
            return False

        # After loading, ensure the image has the correct tag (IMAGE_NAME)
        # The loaded image may have a different tag (e.g., 'latest' or 'v5')
        # We need to find it and tag it correctly
        try:
            # Check if already correctly tagged
            inspect_result = subprocess.run(
                ["docker", "image", "inspect", IMAGE_NAME],
                capture_output=True, text=True
            )
            if inspect_result.returncode == 0:
                print(f"[OK] Image already tagged as {IMAGE_NAME}")
                return True

            # Find the loaded image (any zwind-reproduce image)
            list_result = subprocess.run(
                ["docker", "images", "--format", "{{.Repository}}:{{.Tag}}"],
                capture_output=True, text=True
            )
            loaded_tag = None
            for line in list_result.stdout.strip().split('\n'):
                if line and 'zwind-reproduce' in line.lower():
                    print(f"[INFO] Found loaded image: {line}")
                    loaded_tag = line
                    break

            if loaded_tag and loaded_tag != IMAGE_NAME:
                print(f"[INFO] Tagging {loaded_tag} as {IMAGE_NAME}")
                result = subprocess.run(
                    ["docker", "tag", loaded_tag, IMAGE_NAME],
                    capture_output=True, text=True
                )
                if result.returncode == 0:
                    print(f"[OK] Successfully tagged as {IMAGE_NAME}")
                else:
                    print(f"[WARNING] Tag failed: {result.stderr}")
                    # Try alternative approach - force tag
                    subprocess.run(
                        ["docker", "tag", "-f", loaded_tag, IMAGE_NAME],
                        capture_output=True
                    )
        except Exception as e:
            print(f"[WARNING] Auto-tagging encountered issue: {e}")

        print("[OK] Image loaded successfully")
        return True
    except Exception as e:
        print(f"[ERROR] Failed to load image: {e}")
        return False


def prepare_dirs():
    """Create results directory"""
    os.makedirs(RESULTS_DIR, exist_ok=True)
    results_path = os.path.abspath(RESULTS_DIR)
    print(f"[OK] Results directory: {results_path}")
    return results_path


def cleanup(signum=None, frame=None):
    """Cleanup function: stop Docker container (keep container for recovery)"""
    global container_id
    print("")
    print("[INTERRUPT] Received stop signal, cleaning up...")
    if container_id:
        print(f"[STOP] Stopping Docker container ({container_id[:12]})...")
        subprocess.run(["docker", "stop", container_id],
                      stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        print(f"[HINT] Container stopped. Use 'docker start {container_id}' to resume")
    print("[DONE] Script exited")
    sys.exit(130)


def setup_signal_handler():
    """Setup signal handlers"""
    signal.signal(signal.SIGINT, cleanup)
    signal.signal(signal.SIGTERM, cleanup)


def find_available_api_port_in_container(container_id, start_port=8005, max_attempts=10):
    """Find available port inside container for API service"""
    for port in range(start_port, start_port + max_attempts):
        # Test if port is available inside container
        test_cmd = [
            "docker", "exec", container_id, "bash", "-c",
            f"python3 -c \"import socket; s=socket.socket(); s.bind(('0.0.0.0',{port})); s.close()\""
        ]
        result = subprocess.run(test_cmd, capture_output=True)
        if result.returncode == 0:
            return port
    return start_port  # Default to 8005


def run_simulation(results_path):
    """Run batch simulation"""
    global container_id

    print("")
    print("==============================================")
    print("[RUN] Starting batch simulation (336 cases)")
    print("Estimated time: ~48 hours (Ctrl+C to interrupt)")
    print("==============================================")
    print("")

    # Setup signal handler
    setup_signal_handler()

    # Cleanup old containers
    print("[CLEANUP] Cleaning stale containers...")
    cleanup_stale_containers()

    # Environment config
    env = os.environ.copy()
    env["CONFIGURED_CASE_TYPES"] = "Typhoon_V40,Typhoon_V60,Earthquake_1g,Earthquake_2g"

    # Find available port
    available_port = find_available_port(API_START_PORT, API_MAX_PORT - API_START_PORT + 1)
    if not available_port:
        print(f"[ERROR] Cannot find available port ({API_START_PORT}-{API_MAX_PORT})")
        return

    if available_port != API_START_PORT:
        print(f"[HINT] Port {API_START_PORT} is occupied, using port {available_port}")

    # Cleanup old containers on target port first
    cleanup_containers_on_port(available_port)

    # Generate container name
    container_name = generate_container_name()

    # Start container (using sleep infinity to keep container running)
    print("[START] Creating Docker container...")
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
            # Container creation failed, try cleanup and retry
            print(f"[WARNING] Container creation failed, trying cleanup...")
            cleanup_containers_on_port(available_port)
            result = subprocess.run(create_cmd, capture_output=True, text=True, env=env)
            result.check_returncode()

        container_id = result.stdout.strip()
        print(f"[CONTAINER] Container started: {container_id[:12]} (name: {container_name})")
    except subprocess.CalledProcessError as e:
        print(f"[ERROR] Container creation failed: {e.stderr}")
        print("[HINT] Run 'docker ps -a' to check container status")
        return

    # Start service inside container and run simulation
    # Use the found port to start API service
    exec_cmd = [
        "docker", "exec", container_id, "bash", "-c",
        f"echo '[START] Starting API service (port {available_port})...' && "
        f"python3 -m uvicorn main:app --host 0.0.0.0 --port 8005 & "
        "echo '[WAIT] Waiting for API service...' && "
        "sleep 5 && "
        "echo '[RUN] Starting batch simulation...' && "
        "exec python3 -m tools.zwind_batch_runner"
    ]

    print(f"[CMD] Starting batch simulation in container {container_id[:12]}")
    print("")
    print("Executing batch tasks. Press Ctrl+C to interrupt...")
    print("=" * 60)

    try:
        subprocess.run(exec_cmd, env=env)
    except KeyboardInterrupt:
        cleanup()
    finally:
        # Normal exit - stop container (keep for recovery)
        if container_id:
            print(f"[STOP] Stopping container {container_id[:12]}...")
            subprocess.run(["docker", "stop", container_id],
                          capture_output=True, stderr=subprocess.DEVNULL)
            print(f"[HINT] Container stopped. Use 'docker start {container_id}' to resume")
            container_id = None


def main():
    print("==============================================")
    print(" ZWind Batch Simulation (336 cases)")
    print("==============================================")
    print(f"[SYSTEM] {detect_os().upper()}")
    print("")

    # Check Docker
    if not check_docker():
        sys.exit(1)

    # Load image
    if not load_image():
        sys.exit(1)

    # Create results directory
    results_path = prepare_dirs()

    # Run simulation
    run_simulation(results_path)

    print("")
    print("==============================================")
    print("Done!")
    print(f"Results directory: {results_path}")
    print("==============================================")


if __name__ == "__main__":
    main()
