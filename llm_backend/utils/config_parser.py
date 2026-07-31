# rainbow_yu DeepWindF.config_parser 🐋✨
# Date : 2025/7/8 15:12

import os
import re
import random

class OpenFast5MVAPGConfigParser:
    def __init__(self, base_dir, file_dict: dict, keep_param_count=None):
        """
        :param base_dir: 根目录路径
        :param file_dict: dict，如 {"fst": "input.fst", "hydro": "HydroDyn.dat", ...}
        :param keep_param_count: 若为整数，则对非fst模块，仅随机保留该数量的参数
        """
        self.base_dir = base_dir
        self.file_dict = file_dict
        self.keep_param_count = keep_param_count
        self.data = {}

    def parse(self):
        for module_name, filename in self.file_dict.items():
            path = os.path.join(self.base_dir, filename)
            module_props = self._parse_single_file(path)
            if module_props:
                # 如果是 fst 文件，保留所有参数；否则随机保留部分参数
                if module_name == "fst":
                    self.data[module_name] = {
                        "type": "object",
                        "description": f"Parameters extracted from {filename}",
                        "properties": module_props
                    }
                elif self.keep_param_count is not None:
                    # 对非fst文件，随机保留指定数量的参数
                    all_keys = list(module_props.keys())
                    keep_keys = set(random.sample(all_keys, min(self.keep_param_count, len(all_keys))))
                    module_props = {k: v for k, v in module_props.items() if k in keep_keys}
                    self.data[module_name] = {
                        "type": "object",
                        "description": f"Parameters extracted from {filename}",
                        "properties": module_props
                    }

    def _parse_single_file(self, filepath):
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                lines = f.readlines()
        except FileNotFoundError:
            print(f"Error: File {filepath} not found.")
            return None
        except Exception as e:
            print(f"Error reading file {filepath}: {e}")
            return None

        properties = {}
        i = 0

        # 普通参数行格式（值 参数名 - 描述 [枚举]）
        param_pattern = re.compile(r'^\s*(?P<value>".*?"|\S+)\s+(?P<param>\S+)\s+-\s*(?P<desc>.+)$')
        enum_pattern = re.compile(r'\{([^}]+)\}')

        # 带参数+多行矩阵数据的特殊格式，类似：
        #  0   AddF0    - description...
        param_with_matrix_pattern = re.compile(
            r'^\s*(?P<value>[\d\.\+\-Ee]+)\s+(?P<param>\w+)\s+-\s*(?P<desc>.+)$'
        )

        while i < len(lines):
            line = lines[i].strip()

            # 跳过空行和注释
            if not line or line.startswith('-') or line.startswith('#') or line.upper().startswith('END'):
                i += 1
                continue

            # 优先匹配带矩阵的参数格式
            m_mat = param_with_matrix_pattern.match(line)
            if m_mat:
                value = m_mat.group("value")
                param = m_mat.group("param")
                desc = m_mat.group("desc").strip()

                # 尝试读取紧接着的多行数字矩阵数据，直到遇到空行、注释或非数字行
                i += 1
                matrix_data = []
                while i < len(lines):
                    data_line = lines[i].strip()
                    if not data_line or data_line.startswith('!') or data_line.startswith('#') or re.match(r'^[A-Za-z\-]', data_line):
                        break
                    values = re.split(r'\s+', data_line)
                    try:
                        float_values = [float(v) for v in values]
                    except ValueError:
                        break  # 如果非数字，结束矩阵读取
                    matrix_data.append(float_values)
                    i += 1

                if matrix_data:
                    # 解析成功矩阵
                    properties[param] = {
                        "type": "array",
                        "description": desc,
                        "items": {
                            "type": "array",
                            "items": {"type": "number"}
                        },
                    }
                else:
                    # 只有单值，没矩阵数据
                    param_type = self.guess_type(value)
                    properties[param] = {
                        "type": param_type,
                        "description": desc
                    }
                continue  # 处理完当前参数，继续下一行，不用i+=1 因为循环里i已经更新

            # 普通参数行匹配
            match = param_pattern.match(line)
            if match:
                value = match.group("value").strip('"')
                param = match.group("param")
                desc = match.group("desc").strip()

                enum_match = enum_pattern.search(desc)
                if enum_match:
                    enum_raw = enum_match.group(1).strip()

                    # 多种枚举格式判断与解析
                    if '=' in enum_raw:
                        # 例：{0: none=no potential flow, 1: frequency-to-time-domain}
                        enums = []
                        for part in enum_raw.split(';'):
                            if ':' in part:
                                key = part.split(':')[0].strip()
                                try:
                                    key = int(key)
                                except:
                                    pass
                                enums.append(key)
                        param_type = "integer"
                    elif re.match(r'^\s*\d+[:,]', enum_raw):
                        # 例：7: WAMIT file to use; 8: ...
                        enums = []
                        for item in enum_raw.split(';'):
                            m = re.match(r'^(\d+)\s*[:]', item.strip())
                            if m:
                                enums.append(int(m.group(1)))
                        param_type = "integer"
                    elif '/' in enum_raw:
                        enums = [x.strip() for x in enum_raw.split('/')]
                        param_type = "string"
                    elif ',' in enum_raw:
                        enums = [x.strip('" ') for x in enum_raw.split(',')]
                        param_type = "string"
                    else:
                        enums = [x.strip('" ') for x in enum_raw.split(';')]
                        param_type = "string"

                    properties[param] = {
                        "type": param_type,
                        "description": desc,
                        "enum": enums
                    }
                else:
                    param_type = self.guess_type(value)
                    properties[param] = {
                        "type": param_type,
                        "description": desc
                    }
                i += 1
                continue

            # 结构化表格检测（带列头和单位行）
            if '!' in line:
                line = line.split('!')[0].strip()
            if '[' in line:
                line = re.sub(r'\[.*?\]', '', line).strip()
            fields = re.split(r'\s+', line)

            next_line = lines[i + 1].strip() if i + 1 < len(lines) else ''
            units = re.split(r'\s+', next_line) if next_line else []

            if len(fields) >= 2 and len(units) == len(fields):
                i += 2
                data_block = []
                while i < len(lines):
                    data_line = lines[i].strip()
                    if not data_line or re.match(r'^[A-Za-z]', data_line) or data_line.startswith('!'):
                        break
                    values = re.split(r'\s+', data_line)
                    if len(values) != len(fields):
                        break
                    row = []
                    for v in values:
                        v_lc = v.lower()
                        if v_lc in {'true', '.true.'}:
                            row.append(True)
                        elif v_lc in {'false', '.false.'}:
                            row.append(False)
                        else:
                            try:
                                row.append(float(v))
                            except ValueError:
                                row.append(v)
                    data_block.append(row)
                    i += 1

                table_key = '_'.join(fields)
                # 判断每列是否全为bool，进而确定类型
                col_types = []
                for col in zip(*data_block):
                    if all(str(v).lower() in {"true", "false"} for v in col):
                        col_types.append("boolean")
                    else:
                        col_types.append("number")

                properties[table_key] = {
                    "type": "array",
                    "description": f"Table data columns: {', '.join(fields)}",
                    "items": {
                        "type": "object",
                        "properties": {
                            field: {"type": col_type} for field, col_type in zip(fields, col_types)
                        }
                    }
                }
                continue

            i += 1

        return properties

    def guess_type(self, value):
        v = value.lower()
        if v in {"true", "false", ".true.", ".false."}:
            return "boolean"
        elif re.match(r'^-?\d+(\.\d+)?([eE][-+]?\d+)?$', value):
            return "number"
        elif "," in value:
            return "array"
        else:
            return "string"

    def to_json(self):
        return {
            "type": "object",
            "properties": self.data,
            "required": []
        }