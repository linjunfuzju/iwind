from deepwind_app.tool.base import BaseTool
import aiohttp
import base64
import os
import asyncio
from io import BytesIO
import uuid
from typing import Dict, List

_yolo_DESCRIPTION = """这个工具用于风机损伤检测的图像识别，输入图片URL列表，
                    返回检测结果和标记后的图片。"""

class YoloDetection(BaseTool):
    name: str = "detection"
    description: str = _yolo_DESCRIPTION
    
    parameters: dict = {
        "type": "object",
        "properties": {
            "image_paths": {  # 修改了参数名以更准确地表示本地文件路径
                "type": "array",
                "items": {"type": "string"},
                "description": "需要检测的图片本地文件路径列表"
            },
        },
        "required": ["image_paths"]  # 更新为新的参数名
    }

    async def execute(self, **kwargs):
        print("\n=== 开始执行 YOLO 检测 ===")
        print(f"接收到的参数类型: {type(kwargs)}")
        print(f"完整参数内容: {kwargs}")
        
        try:
            # 1. 参数验证 - 使用新的参数名 image_paths
            print("\n[调试] 开始参数验证...")
            if "image_paths" not in kwargs:
                print("[错误] 缺少 image_paths 参数")
                raise ValueError("必须提供 image_paths 参数")
            
            print(f"[调试] image_paths 存在，类型: {type(kwargs['image_paths'])}")
            
            if not isinstance(kwargs["image_paths"], list):
                print(f"[错误] image_paths 不是列表，实际类型: {type(kwargs['image_paths'])}")
                raise ValueError("image_paths 必须是列表")
            
            print(f"[调试] image_paths 是列表，长度: {len(kwargs['image_paths'])}")
            print(f"[调试] 第一个文件路径示例: {kwargs['image_paths'][0] if kwargs['image_paths'] else '空列表'}")
            
            # 2. 读取本地文件并转换为base64
            base64_images = []
            for path in kwargs["image_paths"]:
                # 去除可能的文件协议前缀
                cleaned_path = path.replace("file://", "")
                
                if not os.path.exists(cleaned_path):
                    raise FileNotFoundError(f"文件不存在: {cleaned_path}")
                
                print(f"[调试] 正在读取文件: {cleaned_path}")
                with open(cleaned_path, "rb") as image_file:
                    image_bytes = image_file.read()
                    base64_str = base64.b64encode(image_bytes).decode('utf-8')
                    base64_images.append(base64_str)
            
            print(f"[调试] 成功转换 {len(base64_images)} 张图片为base64格式")
            
            # 3. 构建服务端请求
            task_id = self._generate_task_id()
            print(f"\n[调试] 生成任务ID: {task_id}")
            payload = {
                "image_data": base64_images,  # 使用base64编码的图像数据
                "task_id": task_id
            }
            
            # 4. 使用aiohttp发送异步请求
            print("\n[调试] 准备发送请求到检测服务...")
            async with aiohttp.ClientSession() as session:
                print("[调试] 创建ClientSession完成")
                async with session.post(
                    "http://localhost:8004/yolo_detection",
                    json=payload,
                    timeout=600
                ) as response:
                    print(f"[调试] 收到响应，状态码: {response.status}")
                    response.raise_for_status()
                    result = await response.json()
                    print(f"[调试] 响应内容: {result}")
                    print("\n=== 执行成功 ===")
                    return result
            
        except (FileNotFoundError, IOError) as e:
            print(f"\n[错误] 文件操作失败: {str(e)}")
            return {"error": f"文件操作失败: {str(e)}", "debug_info": {"step": "file_io"}}
        except aiohttp.ClientError as e:
            print(f"\n[错误] 网络请求失败: {str(e)}")
            return {"error": f"网络请求失败: {str(e)}", "debug_info": {"step": "network_request"}}
        except ValueError as e:
            print(f"\n[错误] 参数验证失败: {str(e)}")
            return {"error": f"参数验证失败: {str(e)}", "debug_info": {"step": "parameter_validation"}}
        except Exception as e:
            print(f"\n[错误] 未预期错误: {str(e)}")
            import traceback
            traceback.print_exc()
            return {"error": f"处理错误: {str(e)}", "debug_info": {"step": "unexpected_error"}}

    def _generate_task_id(self) -> str:
        """生成唯一任务ID"""
        task_id = f"{uuid.uuid4().hex[:8]}"
        print(f"[调试] 生成任务ID: {task_id}")
        return task_id