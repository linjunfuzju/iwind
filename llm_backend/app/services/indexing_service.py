import os
import asyncio
import logging
from pathlib import Path
from typing import Optional, Dict, Any, List
import mimetypes
import shutil
import uuid
import traceback

import graphrag.api as api
from graphrag.config.load_config import load_config
from graphrag.config.enums import IndexingMethod
from graphrag.logger.rich_progress import RichProgressLogger

from app.core.config import settings
from app.core.logger import get_logger

logger = get_logger(service="indexing")

class IndexingService:
    def __init__(self):
        """初始化索引服务"""
        self.project_dir = settings.GRAPHRAG_PROJECT_DIR
        self.data_dir_name = settings.GRAPHRAG_DATA_DIR
        self.data_dir = os.path.join(self.project_dir, self.data_dir_name)
        self.default_config = 'settings.yaml'
        
        # 初始化文件类型到配置的映射
        self.config_mapping = {
            'application/pdf': 'pdf_config.yaml',
            'application/vnd.openxmlformats-officedocument.wordprocessingml.document': 'docx_config.yaml',
            'application/vnd.openxmlformats-officedocument.presentationml.presentation': 'pptx_config.yaml',
            'text/plain': 'text_config.yaml',
            'text/markdown': 'markdown_config.yaml',
            'text/html': 'html_config.yaml'
        }
        
        # 确保目录存在
        self._ensure_directories_exist()

    def _ensure_directories_exist(self):
        """确保必要的目录结构存在"""
        required_dirs = [
            self.data_dir,
            os.path.join(self.data_dir, "input"),
            os.path.join(self.data_dir, "output")
        ]
        
        for dir_path in required_dirs:
            os.makedirs(dir_path, exist_ok=True)
            logger.debug(f"确保目录存在: {dir_path}")

    def _get_file_type(self, file_path: str) -> str:
        """获取标准化的文件类型"""
        mime_type, _ = mimetypes.guess_type(file_path)
        if mime_type is None:
            # 根据扩展名补充常见类型
            ext = os.path.splitext(file_path)[1].lower()
            if ext == '.md':
                return 'text/markdown'
            return 'application/octet-stream'
        return mime_type

    def _get_config_file(self, file_type: str) -> str:
        """安全获取配置文件"""
        config_file = self.config_mapping.get(file_type, self.default_config)
        config_path = os.path.join(self.data_dir, config_file)
        
        if not os.path.exists(config_path):
            logger.warning(f"配置文件 {config_file} 不存在，使用默认配置")
            return self.default_config
        return config_file

    def _check_existing_index(self, file_path: str, output_dir: str) -> bool:
        """增强的索引检查"""
        try:
            file_name = Path(file_path).stem
            index_path = os.path.join(output_dir, f"{file_name}_index")
            return os.path.exists(index_path) and os.listdir(index_path)
        except Exception as e:
            logger.warning(f"检查索引时出错: {str(e)}")
            return False

    def _prepare_user_directories(self, user_id: int) -> tuple:
        """安全的目录准备"""
        try:
            user_uuid = str(uuid.uuid5(uuid.NAMESPACE_DNS, f"user_{user_id}"))
            
            user_input_dir = os.path.join(self.data_dir, "input", user_uuid)
            user_output_dir = os.path.join(self.data_dir, "output", user_uuid)
            
            os.makedirs(user_input_dir, exist_ok=True)
            os.makedirs(user_output_dir, exist_ok=True)
            
            # 设置合理权限 (Linux系统)
            if os.name == 'posix':
                os.chmod(user_input_dir, 0o755)
                os.chmod(user_output_dir, 0o755)
            
            return user_input_dir, user_output_dir
        except Exception as e:
            logger.error(f"创建用户目录失败: {str(e)}")
            raise RuntimeError(f"无法创建用户目录: {str(e)}")

    def _copy_file_to_input_dir(self, file_path: str, input_dir: str) -> str:
        """安全的文件复制"""
        try:
            if not os.path.exists(file_path):
                raise FileNotFoundError(f"源文件不存在: {file_path}")
                
            file_name = os.path.basename(file_path)
            dest_path = os.path.join(input_dir, file_name)
            
            # 避免文件名冲突
            if os.path.exists(dest_path):
                base, ext = os.path.splitext(file_name)
                counter = 1
                while os.path.exists(dest_path):
                    dest_path = os.path.join(input_dir, f"{base}_{counter}{ext}")
                    counter += 1
            
            shutil.copy2(file_path, dest_path)
            logger.info(f"文件复制成功: {file_path} -> {dest_path}")
            return dest_path
        except Exception as e:
            logger.error(f"文件复制失败: {str(e)}")
            raise RuntimeError(f"无法复制文件: {str(e)}")

    async def process_file(self, file_info: Dict[str, Any]) -> Dict[str, Any]:
        """增强的文件处理方法"""
        result_template = {
            'status': 'error',
            'file_path': '',
            'error': '',
            'original_file_path': '',
            'input_file_path': '',
            'file_type': '',
            'config_used': '',
            'is_update': False,
            'user_id': 0,
            'input_dir': '',
            'output_dir': ''
        }
        
        try:
            # 验证输入
            if 'path' not in file_info:
                raise ValueError("缺少必要参数: path")
                
            file_path = file_info['path']
            result_template.update({
                'original_file_path': file_path,
                'user_id': file_info.get('user_id', 0)
            })
            
            # 获取文件类型
            file_type = self._get_file_type(file_path)
            result_template['file_type'] = file_type
            
            logger.info(f"开始处理文件: {file_path} (类型: {file_type})")

            # 准备目录
            input_dir, output_dir = self._prepare_user_directories(file_info.get('user_id', 0))
            result_template.update({
                'input_dir': input_dir,
                'output_dir': output_dir
            })
            
            # 复制文件
            input_file_path = self._copy_file_to_input_dir(file_path, input_dir)
            result_template['input_file_path'] = input_file_path
            
            # 获取配置
            config_file = self._get_config_file(file_type)
            result_template['config_used'] = config_file
            config_path = os.path.join(self.data_dir, config_file)
            
            # 检查索引
            is_update = self._check_existing_index(input_file_path, output_dir)
            result_template['is_update'] = is_update
            
            # 加载配置
            config_overrides = {
                'input.base_dir': input_dir,
                'output.base_dir': output_dir,
                'input.file_pattern': f".*{os.path.basename(input_file_path)}$$"
            }
            graphrag_config = load_config(
                Path(self.data_dir),
                Path(config_path),
                config_overrides
            )
            
            # 构建索引
            progress_logger = RichProgressLogger(prefix="graphrag-index")
            index_result = await api.build_index(
                config=graphrag_config,
                method=IndexingMethod.Standard,
                is_update_run=is_update,
                memory_profile=False,
                progress_logger=progress_logger
            )
            
            # 处理结果
            result_template['status'] = 'success'
            errors = []
            
            for workflow_result in index_result:
                if workflow_result.errors:
                    errors.extend(workflow_result.errors)
            
            if errors:
                result_template.update({
                    'status': 'partial_success',
                    'errors': errors
                })
                logger.warning(f"索引构建完成但有错误: {errors}")
            
            return result_template
            
        except Exception as e:
            logger.error(f"文件处理失败: {str(e)}", exc_info=True)
            result_template.update({
                'error': str(e),
                'traceback': traceback.format_exc()
            })
            return result_template

    async def process_directory(self, directory_path: str, user_id: int = 0) -> Dict[str, Any]:
        """增强的目录处理方法"""
        result = {
            'status': 'success',
            'processed_files': 0,
            'successful': 0,
            'failed': 0,
            'results': [],
            'errors': []
        }
        
        try:
            if not os.path.isdir(directory_path):
                raise NotADirectoryError(f"路径不是目录: {directory_path}")
                
            for root, _, files in os.walk(directory_path):
                for file in files:
                    try:
                        file_path = os.path.join(root, file)
                        file_result = await self.process_file({
                            'path': file_path,
                            'user_id': user_id
                        })
                        
                        result['processed_files'] += 1
                        if file_result['status'] == 'success':
                            result['successful'] += 1
                        else:
                            result['failed'] += 1
                            result['errors'].append({
                                'file': file_path,
                                'error': file_result.get('error', 'unknown')
                            })
                            
                        result['results'].append(file_result)
                        
                    except Exception as e:
                        logger.error(f"处理文件 {file} 时出错: {str(e)}")
                        result['failed'] += 1
                        result['errors'].append({
                            'file': os.path.join(root, file),
                            'error': str(e)
                        })
            
            if result['failed'] > 0:
                result['status'] = 'partial_success' if result['successful'] > 0 else 'error'
            
            return result
            
        except Exception as e:
            logger.error(f"目录处理失败: {str(e)}", exc_info=True)
            return {
                'status': 'error',
                'error': str(e),
                'traceback': traceback.format_exc()
            }
# import os
# import asyncio
# import logging
# from pathlib import Path
# from typing import Optional, Dict, Any
# import mimetypes
# import shutil
# import uuid

# import graphrag.api as api
# from graphrag.config.load_config import load_config
# from graphrag.config.enums import IndexingMethod
# from graphrag.logger.rich_progress import RichProgressLogger
# from graphrag.index.typing.pipeline_run_result import PipelineRunResult

# from app.core.config import settings
# from app.core.logger import get_logger

# logger = get_logger(service="indexing")

# class IndexingService:
#     def __init__(self):
#         self.project_dir = settings.GRAPHRAG_PROJECT_DIR
#         self.data_dir_name = settings.GRAPHRAG_DATA_DIR
#         self.data_dir = os.path.join(self.project_dir, self.data_dir_name)
        

#         # 默认配置文件
#         self.default_config = 'settings.yaml'
        
#     def _get_file_type(self, file_path: str) -> str:
#         """获取文件MIME类型"""
#         mime_type, _ = mimetypes.guess_type(file_path)
#         return mime_type or 'application/octet-stream'
    
#     def _get_config_file(self, file_type: str) -> str:
#         """根据文件类型获取对应的配置文件"""
#         return self.config_mapping.get(file_type, self.default_config)
    
#     def _check_existing_index(self, file_path: str, output_dir: str) -> bool:
#         """检查文件是否已经建立索引"""
#         file_name = Path(file_path).stem
#         index_path = os.path.join(output_dir, f"{file_name}_index")
#         return os.path.exists(index_path)
    
#     def _prepare_user_directories(self, user_id: int) -> tuple:
#         """为用户准备输入和输出目录"""
#         # 生成用户UUID
#         user_uuid = str(uuid.uuid5(uuid.NAMESPACE_DNS, f"user_{user_id}"))
        
#         # 创建用户输入目录
#         user_input_dir = os.path.join(self.data_dir, "input", user_uuid)
#         os.makedirs(user_input_dir, exist_ok=True)
        
#         # 创建用户输出目录
#         user_output_dir = os.path.join(self.data_dir, "output", user_uuid)
#         os.makedirs(user_output_dir, exist_ok=True)
        
#         return user_input_dir, user_output_dir
    
#     def _copy_file_to_input_dir(self, file_path: str, input_dir: str) -> str:
#         """将文件复制到用户的输入目录"""
#         file_name = os.path.basename(file_path)
#         dest_path = os.path.join(input_dir, file_name)
        
#         # 复制文件
#         shutil.copy2(file_path, dest_path)
#         logger.info(f"已将文件复制到输入目录: {dest_path}")
        
#         return dest_path
    
#     async def process_file(self, file_info: Dict[str, Any]) -> Dict[str, Any]:
#         """处理单个文件的索引构建"""
#         try:
#             file_path = file_info['path']
#             file_type = self._get_file_type(file_path)
#             user_id = file_info.get('user_id', 0)  # 获取用户ID，默认为0
            
#             logger.info(f"开始处理文件: {file_path}, 类型: {file_type}, 用户ID: {user_id}")
            
#             # 准备用户目录
#             user_input_dir, user_output_dir = self._prepare_user_directories(user_id)
            
#             # 复制文件到输入目录
#             input_file_path = self._copy_file_to_input_dir(file_path, user_input_dir)
            
#             # 获取配置文件
#             config_file = self._get_config_file(file_type)
#             logger.info(f"使用配置文件: {config_file}")
            
#             # 检查是否需要增量更新
#             is_update = self._check_existing_index(input_file_path, user_output_dir)
            
#             # 准备配置
#             config_path = os.path.join(self.data_dir, config_file)
#             if not os.path.exists(config_path):
#                 logger.warning(f"配置文件不存在: {config_path}，使用默认配置")
#                 config_path = os.path.join(self.data_dir, self.default_config)
            
#             # 设置配置覆盖
#             config_overrides = {
#                 'input.base_dir': user_input_dir,
#                 'output.base_dir': user_output_dir,
#                 # 更新文件匹配模式以匹配文件名
#                 'input.file_pattern': f".*{os.path.basename(input_file_path)}$$"
#             }
            
#             # 加载配置
#             graphrag_config = load_config(
#                 Path(self.data_dir),
#                 Path(config_path),
#                 config_overrides
#             )
            
#             # 创建进度记录器
#             progress_logger = RichProgressLogger(prefix="graphrag-index")
            
#             logger.info(f"开始{'增量更新' if is_update else '构建'}索引: {input_file_path}")
#             logger.info(f"输入目录: {user_input_dir}")
#             logger.info(f"输出目录: {user_output_dir}")
            
#             # 执行索引构建
#             index_result = await api.build_index(
#                 config=graphrag_config,
#                 method=IndexingMethod.Standard,
#                 is_update_run=is_update,
#                 memory_profile=False,
#                 progress_logger=progress_logger
#             )
            
#             # 处理结果
#             result_info = {
#                 'original_file_path': file_path,
#                 'input_file_path': input_file_path,
#                 'file_type': file_type,
#                 'config_used': config_file,
#                 'is_update': is_update,
#                 'status': 'success',
#                 'user_id': user_id,
#                 'input_dir': user_input_dir,
#                 'output_dir': user_output_dir
#             }
            
#             # 检查是否有错误
#             for workflow_result in index_result:
#                 if workflow_result.errors:
#                     result_info['status'] = 'error'
#                     result_info['errors'] = workflow_result.errors
#                     logger.error(f"索引构建失败: {workflow_result.errors}")
            
#             return result_info
            
#         except Exception as e:
#             logger.error(f"处理文件时发生错误: {str(e)}", exc_info=True)
#             return {
#                 'file_path': file_path,
#                 'status': 'error',
#                 'error': str(e)
#             }
    
#     async def process_directory(self, directory_path: str, user_id: int = 0) -> Dict[str, Any]:
#         """处理整个目录的索引构建"""
#         try:
#             results = []
#             for root, _, files in os.walk(directory_path):
#                 for file in files:
#                     file_path = os.path.join(root, file)
#                     file_info = {
#                         'path': file_path,
#                         'original_name': file,
#                         'user_id': user_id
#                     }
#                     result = await self.process_file(file_info)
#                     results.append(result)
            
#             return {
#                 'status': 'success',
#                 'processed_files': len(results),
#                 'results': results
#             }
            
#         except Exception as e:
#             logger.error(f"处理目录时发生错误: {str(e)}", exc_info=True)
#             return {
#                 'status': 'error',
#                 'error': str(e)
#             }