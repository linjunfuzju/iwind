# rainbow_yu DeepWindF.auto_para_generator 🐋✨
# Date : 2025/7/5 14:43

import os
import glob
import re
import logging
import json
import time
from tqdm import tqdm

from deepwind_app.tool.loader import *
from config_parser import OpenFast5MVAPGConfigParser

class AutoParaGenerator:
    def __init__(
            self,
            base_dir,
            tool = "",
            tool_port = 0,
            server_port = 0,
            config_parser = None,
            description = None,
            name_ignore_list = None,
            keep_param_count = None,
            mode = "debug",
    ):
        """
        工作流：
        ------

            - 赋值base_dir, tool, port, config_parser, description
            - 处理文件名
            - 生成对应目录
            - 生成__init__.py
            - 生成servers的文件
            - 生成tool文件
            - 自动load和register

        参数:
        ------

        :param base_dir:根目录
        :param batch_dir:批量文件夹处理根目录
        :param tool:工具

        """
        self.name_ignore_list = name_ignore_list
        if self.name_ignore_list is None:
            self.name_ignore_list = []

        self.base_dir = base_dir
        self.tool = tool
        self.filename = self.execute_filename(self.base_dir)
        self.file_lst, self.dat_name = self.get_file_list()
        self.file_dict = dict(zip(self.dat_name, self.file_lst))
        self.server_port = server_port
        self.tool_port = tool_port
        self.config_parser = config_parser(self.base_dir,self.file_dict,keep_param_count)
        self.config_parser.parse()
        if description:
            self.description = description
        else:
            self.description = self.filename

        if mode == "debug":
            self.ip = "localhost"
        elif mode == "release":
            self.ip = "frp-pen.com"
        else:
            self.ip = "localhost"

    def __call__(self, *args, **kwargs):
        self.execute()

    def execute(self):
        self.generate_dir()
        self.load()

    def load(self):
        current_dir = os.path.dirname(os.path.abspath(__file__))
        base_dir = os.path.abspath(os.path.join(current_dir, "../"))

        tool_updater = InitUpdater(
            root_dir=f"app/tool/{self.tool}/r_test",
            scan_dirs=[os.path.join(base_dir, f"app/tool/{self.tool}/r_test")],
            mode="init",
            target_file=os.path.join(base_dir, "app/tool/__init__.py")
        )
        servers_updater = InitUpdater(
            root_dir="routers/r_test",
            scan_dirs=[os.path.join(base_dir, f"servers/{self.tool}-server/routers/r_test")],
            mode="module",
            target_file=os.path.join(base_dir, f"servers/{self.tool}-server/main.py")
        )
        tool_updater.scan()
        servers_updater.scan()
        tool_updater.update()
        servers_updater.update()
        print("完成load init")

    def execute_filename(self, base_dir):
        # 提取目录路径中的最后一部分
        last_dir_name = os.path.basename(os.path.normpath(base_dir))
        self.filename = f"{self.tool}_{last_dir_name}"
        return self.filename

    def get_file_list(self):
        """
        获取文件列表，支持忽略指定名称（如下划线后提取的关键字）。
        :return: file_lst 和 dat_name 两个列表
        """
        fst_files = glob.glob(os.path.join(self.base_dir, "*.fst"))
        dat_files = glob.glob(os.path.join(self.base_dir, "*.dat"))

        file_lst = [os.path.basename(fst_files[0])] if fst_files else []
        dat_name = ["fst"] if fst_files else []

        for dat in dat_files:
            filename = os.path.basename(dat)
            match = re.search(r'_([A-Za-z0-9]+)\.dat$', filename)
            if match:
                name = match.group(1).lower()
                if name in self.name_ignore_list:
                    continue  # 忽略匹配的名字
                file_lst.append(filename)
                dat_name.append(name)

        return file_lst, dat_name


    def generate_dir(self):
        # --- servers ---
        servers_path = os.path.join(f"../servers/{self.tool}-server/routers/r_test")
        os.makedirs(servers_path, exist_ok=True)

        py_file_path = os.path.join(servers_path, f"{self.filename}.py")
        with open(py_file_path, 'w', encoding='utf-8') as f:
            content = self.servers_content()
            f.write(content)
        logging.info(f"完成{self.filename}的servers创建")
        print(f"完成{self.filename}的servers创建")

        # --- tool ---
        tool_path = os.path.join(f"../app/tool/{self.tool}/r_test/{self.filename}")
        os.makedirs(tool_path, exist_ok=True)

        init_file_path = os.path.join(tool_path, "__init__.py")
        with open(init_file_path, 'w', encoding='utf-8') as f:
            content = self.init_content()
            f.write(content)
        logging.info(f"完成{self.filename}的init创建")
        print(f"完成{self.filename}的init创建")

        topy_file_path = os.path.join(tool_path, f"{self.filename}.py")
        with open(topy_file_path, 'w', encoding='utf-8') as f:
            content = self.tool_content()
            f.write(content)
        logging.info(f"完成{self.filename}的tool创建")
        print(f"完成{self.filename}的tool创建")

# ------ init_content ------

    def init_content(self):
        """
        init的页面模板
        在下方继承，返回format表达文字
        :return: content
        """
        pass

# ------ servers_content ------

    def servers_content(self):
        """
        servers的页面模板
        在下方继承，返回format表达文字
        :return: content
        """
        pass

# ------ tool_content ------

    def tool_content(self):
        """
        tool的页面模板
        在下方继承，返回format表达文字
        :return: content
        """
        pass

class OpenFast5MVAPG(AutoParaGenerator):
    def __init__(
            self,
            base_dir,
            tool="openfast",
            tool_port=8002,
            server_port=49520,
            config_parser = OpenFast5MVAPGConfigParser,
            description = None,
            name_ignore_list = None,
            keep_param_count = None,
            mode = "debug",
    ):
        super().__init__(
            base_dir,
            tool,
            tool_port,
            server_port,
            config_parser,
            description,
            name_ignore_list,
            keep_param_count,
            mode,
        )

    def init_content(self):
        content = f"""
# rainbow_yu {self.tool}.tool.{self.filename}.init 🐋✨
from .{self.filename} import (
    {self.filename},
)

__all__ = ["{self.filename}"]
"""
        return content

    # --- servers ---

    def servers_content(self):
        content = f"""
# rainbow_yu {self.tool}.servers.{self.filename} 🐋✨

from pathlib import Path
from fastapi import FastAPI, HTTPException, APIRouter
from pydantic import BaseModel
from typing import Dict, Any, Optional
import shutil
import subprocess
import os
import re
from util.utils import find_latest_out, vtp_url, replace_params_in_file
import uuid

router = APIRouter(prefix="/{self.tool}/r_test")

class ParamUpdate(BaseModel):
"""
        for data in self.dat_name:
            content += f"   {data} : Optional[Dict[str, Any]] = {{}} \n"

        content += f"""
# 文件路径配置（示例）
BASE_DIR = "/app/keydata"
BASE_CASE = os.path.join(BASE_DIR, "{os.path.basename(self.base_dir)}")
BASE_DEPEND = os.path.join(BASE_DIR, "5MW_Baseline")
SIMULATION_WORKSPACE = "/app/simulation_runs"
os.makedirs(SIMULATION_WORKSPACE, exist_ok=True)
"""

        content += f"""

@router.post("/{self.filename}")
async def update_and_run(params: ParamUpdate):
    try:
        # === 1. 创建隔离的模拟工作目录 ===
        session_id = uuid.uuid4().hex
        work_dir = os.path.join(SIMULATION_WORKSPACE, session_id)
        os.makedirs(work_dir, exist_ok=True)

        # === 2. 拷贝必要目录（保持原始相对路径结构）===
        case_dir = os.path.join(work_dir, "{os.path.basename(self.base_dir)}")
        depend_dir = os.path.join(work_dir, "5MW_Baseline")
        shutil.copytree(BASE_CASE, case_dir)
        shutil.copytree(BASE_DEPEND, depend_dir)

        # === 3. 构造路径并替换参数 ===
        vtp_dir = os.path.join(case_dir, "vtk")
        
        param_map = {{
"""
        for i in range(len(self.dat_name)):
            part = f"           \"{self.dat_name[i]}\" : os.path.join(case_dir, \"{self.file_lst[i]}\"),\n"
            content += part

        content += f"""
        }}
        for key, file_path in param_map.items():
            value = getattr(params, key, None)
            if value:
                replace_params_in_file(file_path, value)
        
        # 调用OpenFAST执行模拟（示例命令，需根据实际路径和环境调整）
        # 这里假设 openfast 可执行程序在 PATH 中
        # 并且在 BASE_DIR 目录执行，fst文件名为 input.fst
        cmd = [
            "python3",
            "/app/OpenFAST/glue-codes/python/OpenFAST.py",
            "{os.path.basename(self.base_dir)}/{self.file_lst[0]}",
        ]
        process = subprocess.run(
            cmd,
            cwd=work_dir,
            capture_output=True,
            text=True,
            timeout=300,
        )

        if process.returncode != 0:
            return {{
                "status": "error",
                "message": "OpenFAST simulation failed",
                "stderr": process.stderr,
            }}

        # 返回运行成功消息和部分日志
        return {{
            "status": "success",
            "output": find_latest_out(Path(case_dir)),
            "plot_url": vtp_url(vtp_dir, {self.server_port}),
            "message": "Simulation completed successfully",
            "session_id": session_id,
        }}

    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except subprocess.TimeoutExpired:
        raise HTTPException(status_code=504, detail="OpenFAST simulation timed out")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {{str(e)}}")
"""
        return content

    # --- tool ---

    def tool_content(self):
        content = f"""
# rainbow_yu {self.tool}.tool.{self.filename} 🐋✨

from app.tool.base import BaseTool
import requests

_{self.filename}_DESCRIPTION = \"\"\"这个工具是用来：{self.description}在用户调用参数时允许发送空请求，并且模拟结果后对结果进行总结。
\"\"\"

class {self.filename}(BaseTool):
    name: str = "{self.filename}"
    description: str = _{self.filename}_DESCRIPTION
    parameters: dict = {json.dumps(self.config_parser.to_json(), indent=4)}

    async def execute(self, **kwargs):
        try:
            # 包装成服务端预期格式
            payload = {{"updates": {{}}}}
            for module_name in {self.dat_name}:
                if module_name in kwargs:
                    payload["updates"][module_name] = kwargs[module_name]

            url = "http://{self.ip}:{self.tool_port}/{self.tool}/r_test/{self.filename}"
            response = requests.post(url, json=payload, timeout=60)
            response.raise_for_status()
            return {{"result": response.json()}}
        except requests.exceptions.RequestException as e:
            return {{"error": str(e)}}
        except Exception as e:
            return {{"error": f"An unexpected error occurred: {{str(e)}}"}}
        """

        return content

description_dict = {
    "5MW_ITIBarge_DLL_WTurb_WavesIrr": "这是5MW风力发电机在ITIBarge平台上的工具，适用于不规则波浪情况下的动态模拟，尤其适合浮式平台的海上风电场测试。",
    "5MW_Land_DLL_WTurb": "这是5MW风力发电机在陆地平台上的工具，主要用于静态风力机性能评估，适用于陆上风电机组的载荷分析与性能预测。",
    "5MW_Land_ModeShapes": "这是5MW风力发电机在陆地环境下的模式形状工具，用于分析风力机结构的振动模式，帮助优化风机设计以提高稳定性。",
    "5MW_OC3Mnpl_DLL_WTurb_WavesIrr": "这是OC3平台上的5MW风力发电机模型，适用于不规则波浪的动态模拟，用于海上风电场中浮式平台（OC3 Mnpl）的风机性能分析。",
    "5MW_OC3Spar_DLL_WTurb_WavesIrr": "这是OC3 Spar平台上的5MW风力发电机模型，适用于不规则波浪下的动态性能模拟，特别适合深水海域的风电场模拟。",
    "5MW_OC3Trpd_DLL_WSt_WavesReg": "这是OC3平台的5MW风力发电机模型，适用于规则波浪条件下的风力机性能分析，提供标准化的风电场模拟数据。",
    "5MW_OC4Jckt_DLL_WTurb_WavesIrr_MGrowth": "这是OC4 Jacket平台上的5MW风力发电机模型，用于模拟不规则波浪情况下的风力机性能，并考虑了风机的生长因素（如风机负荷随着时间的变化）。",
    "5MW_OC4Jckt_ExtPtfm": "这是OC4 Jacket平台的扩展平台工具，可能用于更复杂的风机平台模拟，包括更大的平台配置或新的模拟环境。",
    "5MW_OC4Semi_WSt_WavesWN": "这是OC4 Semi平台的5MW风力发电机工具，适用于波浪作用下的风力机性能分析，适合半潜式平台（OC4 Semi）的风电场设计。",
    "5MW_TLP_DLL_WTurb_WavesIrr_WavesMulti": "这是TLP平台的5MW风力发电机模型，用于模拟多波浪条件下的风力机性能，尤其适用于TLP（张力腿平台）在复杂海洋条件下的应用。",
}

def openfast_5mv_apg_batch_execute(
        root_dir,
        apg = OpenFast5MVAPG,
        description_dict = None,
        mode = "debug",
        keep_param_count = None,
):
    # 获取所有合法的子目录
    valid_dirs = [
        name for name in os.listdir(root_dir)
        if os.path.isdir(os.path.join(root_dir, name))
           and name.startswith("5MW")
           and "Linear" not in name
           and "BD" not in name
           and "Baseline" not in name
    ]

    for name in tqdm(valid_dirs, desc="Processing OpenFAST Cases"):
        full_path = os.path.join(root_dir, name)
        try:
            description = description_dict.get(name, f"未找到 {name} 的描述信息")
            ofg = apg(
                base_dir=full_path,
                description=description,
                mode=mode,
                tool_port=8002,
                server_port=42615,
                keep_param_count = keep_param_count,
            )
            ofg.execute()
        except Exception as e:
            print(f"❌ 处理 {name} 时出错: {e}")


if __name__ == "__main__":
    root_dir = os.path.abspath("../servers/openfast-server/keydata")
    openfast_5mv_apg_batch_execute(
        root_dir,
        description_dict=description_dict,
        keep_param_count = 5,
    )

