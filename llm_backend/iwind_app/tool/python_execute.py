import os
import re
import uuid
import tempfile
import asyncio
from typing import Dict

from deepwind_app.tool.base import BaseTool  # 保持模块结构不变，方便接入系统

class PythonExecute(BaseTool):
    name: str = "python_execute"
    description: str = (
        "Executes Python code. "
        "If matplotlib is used, saves figures and returns a public URL. "
        "Avoids GUI backend by using non-interactive 'Agg' rendering. "
        "图例全部使用英文，避免字体问题。"
    )

    parameters: dict = {
        "type": "object",
        "properties": {
            "code": {
                "type": "string",
                "description": "Python code to execute (use print or matplotlib).",
            },
        },
        "required": ["code"],
    }
    async def execute(
            self,
            code: str,
            timeout: int = 5,
            container_name: str = "opensees-server-opensees_server-1",
            container_code_path: str = None,
            container_image_dir: str = "/app/plots",
        ) -> Dict:
        result = {"observation": "", "status": False, "plot_url": ""}
        image_id = f"{uuid.uuid4().hex}.png"
        if container_code_path is None:
            container_code_path = f"/tmp/{uuid.uuid4().hex}.py"
        container_image_path = f"{container_image_dir}/{image_id}"
        host_code_path = None

        try:
            # 判断是否需要patch matplotlib
            need_patch = "import matplotlib" in code or "plt." in code

            if need_patch:
                print("[PythonExecute] matplotlib detected, processing plt.savefig...")

                # 匹配 plt.savefig(...) 调用，支持单双引号路径和换行
                pattern = re.compile(r"plt\.savefig\((['\"])(.*?)\1\)", flags=re.DOTALL)

                def replace_savefig(match):
                    return f"plt.savefig(r'{container_image_path}')"

                # 替换所有 plt.savefig 调用路径
                new_code, count = pattern.subn(replace_savefig, code)

                if count == 0:
                    # 无保存调用，追加保存和关闭图形代码
                    new_code += f"\nplt.savefig(r'{container_image_path}')\nplt.close()\n"
                else:
                    # 有保存调用，确保最后有 plt.close()
                    if not new_code.strip().endswith("plt.close()"):
                        new_code += "\nplt.close()\n"

                # 添加 Agg 后端和警告过滤头部
                patched_head = (
                    "import matplotlib\n"
                    "matplotlib.use('Agg')\n"
                    "import matplotlib.pyplot as plt\n"
                    "import warnings\n"
                    "warnings.filterwarnings('ignore')\n"
                )
                code = patched_head + "\n" + new_code.strip() + "\n"

            # 写入临时 Python 文件
            with tempfile.NamedTemporaryFile(delete=False, suffix=".py") as f:
                host_code_path = f.name
                f.write(code.encode("utf-8"))
            print(f"[PythonExecute] Code written to temp file: {host_code_path}")

            # 确保容器内图片目录存在
            mkdir_cmd = ["sudo", "docker", "exec", container_name, "mkdir", "-p", container_image_dir]
            proc_mkdir = await asyncio.create_subprocess_exec(
                *mkdir_cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
            )
            stdout_mkdir, stderr_mkdir = await proc_mkdir.communicate()
            if proc_mkdir.returncode != 0:
                result["observation"] = f"[mkdir failed] {stderr_mkdir.decode().strip()}"
                print(f"[PythonExecute] mkdir failed: {result['observation']}")
                return result

            # 拷贝代码文件到容器
            cp_cmd = ["sudo", "docker", "cp", host_code_path, f"{container_name}:{container_code_path}"]
            print(f"[PythonExecute] Running: {' '.join(cp_cmd)}")
            proc_cp = await asyncio.create_subprocess_exec(
                *cp_cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
            )
            stdout_cp, stderr_cp = await proc_cp.communicate()
            if proc_cp.returncode != 0:
                result["observation"] = (
                    f"[Copy Failed] return code {proc_cp.returncode}\n"
                    f"STDOUT: {stdout_cp.decode()}\nSTDERR: {stderr_cp.decode()}"
                )
                print(f"[PythonExecute] Copy failed: {result['observation']}")
                return result
            print(f"[PythonExecute] Code copied to container at {container_code_path}")

            # 执行代码（用python3更通用）
            exec_cmd = ["sudo", "docker", "exec", container_name, "python3", container_code_path]
            print(f"[PythonExecute] Executing: {' '.join(exec_cmd)}")
            proc_exec = await asyncio.create_subprocess_exec(
                *exec_cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.STDOUT,
            )

            try:
                stdout, _ = await asyncio.wait_for(proc_exec.communicate(), timeout=timeout)
                output = stdout.decode("utf-8")
                result["observation"] = output
                result["status"] = proc_exec.returncode == 0
                print(f"[PythonExecute] Execution finished with code {proc_exec.returncode}")
                print(f"[PythonExecute] Output:\n{output}")

                if result["status"] and need_patch:
                    # 返回图片的外部访问URL，请根据你实际部署环境修改
                    # result["plot_url"] = f"http://frp-fun.com:13160/plots/{image_id}"
                    result["plot_url"] = f"http://localhost:8001/plots/{image_id}"
                    print(f"[PythonExecute] Image saved at: {result['image_url']}")

            except asyncio.TimeoutError:
                proc_exec.kill()
                await proc_exec.communicate()
                result["observation"] = f"[Timeout] Execution exceeded {timeout} seconds."
                print(f"[PythonExecute] Timeout after {timeout}s.")

        except Exception as e:
            result["observation"] = f"[Exception] {str(e)}"
            print(f"[PythonExecute] Exception occurred: {e}")

        finally:
            # 清理本地临时文件
            if host_code_path and os.path.exists(host_code_path):
                os.remove(host_code_path)
                print(f"[PythonExecute] Temp file removed: {host_code_path}")

        return result