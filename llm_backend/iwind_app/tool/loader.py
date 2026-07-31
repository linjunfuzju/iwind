import os
import re
import ast
from typing import Dict, List, Optional


class InitUpdater:
    def __init__(
            self,
            scan_dirs: List[str],
            mode: str = "init",
            root_dir: Optional[str] = None,
            target_file: Optional[str] = None
    ):
        assert mode in {"init", "module"}, "mode must be 'init' or 'module'"
        self.scan_dirs = [os.path.abspath(p) for p in scan_dirs]
        self.mode = mode
        self.root_dir = root_dir if root_dir else None
        self.target_file = os.path.abspath(target_file) if target_file else None
        self.base_dir = os.path.commonpath(self.scan_dirs + ([self.target_file] if self.target_file else []))

        # mode=="init" 时: class name -> module path（用于 import）
        # mode=="module" 时: module name -> module path（用于 import）
        self.class_module_map: Dict[str, str] = {}
        self.alias_map: Dict[str, str] = {}            # 类名 -> 别名（仅 init 模式下用到）
        self.file_targets: Dict[str, List[str]] = {}   # 目标文件 -> 需要写入的类或模块名列表

    def register(self, class_name: str, alias: Optional[str] = None):
        """注册别名用于 __all__ (仅 init 模式下)"""
        if alias:
            self.alias_map[class_name] = alias

    def _get_classes_from_file(self, filepath: str) -> List[str]:
        with open(filepath, "r", encoding="utf-8") as f:
            tree = ast.parse(f.read())
        return [node.name for node in tree.body if isinstance(node, ast.ClassDef)]

    def _get_module_path(self, full_path: str) -> str:
        if self.root_dir:
            rel_path = self.root_dir.replace("/", ".")
        else:
            rel_path = full_path.replace("/", ".")
        if rel_path.endswith(".py"):
            rel_path = rel_path[:-3]
        if rel_path.endswith(".__init__"):
            rel_path = rel_path[:-9]
        return rel_path

    def _extract_all_from_lines(self, lines: List[str]) -> set:
        all_classes = set()
        inside_all = False
        all_str_lines = []

        for line in lines:
            if not inside_all and line.strip().startswith("__all__"):
                inside_all = True
                idx = line.find("[")
                if idx != -1:
                    all_str_lines.append(line[idx:])
            elif inside_all:
                all_str_lines.append(line)
                if "]" in line:
                    break

        if all_str_lines:
            all_str = "".join(all_str_lines)
            all_classes = set(re.findall(r'["\'](\w+)["\']', all_str))

        return all_classes

    def _extract_existing_imports(self, lines: List[str]) -> set:
        pattern = re.compile(r"from\s+[\w\.]+?\s+import\s+([\w_]+)")
        return set(
            match.group(1) for line in lines if (match := pattern.search(line))
        )

    def scan(self):
        """根据模式扫描类定义和目标更新文件"""
        for root in self.scan_dirs:
            if self.mode == "module":
                # module 模式：只处理顶层 .py 文件（不含 __init__.py）
                filenames = os.listdir(root)
                for filename in filenames:
                    if not filename.endswith(".py") or filename == "__init__.py":
                        continue

                    full_path = os.path.join(root, filename)
                    rel_module_path = self._get_module_path(full_path)
                    module_name = os.path.splitext(filename)[0]

                    # 记录模块名 -> 模块路径
                    self.class_module_map[module_name] = rel_module_path

                    target_path = self.target_file or os.path.join(root, "__init__.py")
                    self.file_targets.setdefault(target_path, []).append(module_name)

            else:
                # init 模式：递归扫描所有 __init__.py
                for dirpath, _, filenames in os.walk(root):
                    for filename in filenames:
                        if filename != "__init__.py":
                            continue

                        full_path = os.path.join(dirpath, filename)
                        rel_module_path = self._get_module_path(full_path)

                        folder_name = os.path.basename(dirpath)
                        self.class_module_map[folder_name] = rel_module_path

                        target_path = self.target_file or full_path
                        self.file_targets.setdefault(target_path, []).append(folder_name)

    def update(self):
        for file_path, name_list in self.file_targets.items():
            if not os.path.exists(file_path):
                print(f"❌ {file_path} 不存在，跳过更新")
                continue

            with open(file_path, "r", encoding="utf-8") as f:
                lines = f.readlines()

            if self.mode == "module":
                # module 模式：更新 from import 和 app.include_router(...)
                existing_imports = set()
                existing_routers = set()
                import_pattern = re.compile(r"from\s+([\w\.]+)\s+import\s+(\w+)")
                router_pattern = re.compile(r"app\.include_router\((\w+)\.router\)")

                for line in lines:
                    if match := import_pattern.search(line):
                        existing_imports.add(match.group(2))
                    if match := router_pattern.search(line):
                        existing_routers.add(match.group(1))

                import_lines = []
                router_lines = []

                for mod in name_list:
                    mod_path = self.class_module_map.get(mod)

                    if mod not in existing_imports:
                        import_lines.append(f"from {mod_path} import {mod}\n")
                    if mod not in existing_routers:
                        router_lines.append(f"app.include_router({mod}.router)")

                # 插入 imports 在文件顶部（跳过注释和空行）
                insert_index = 0
                for i, line in enumerate(lines):
                    if line.strip() and not line.strip().startswith("#"):
                        insert_index = i
                        break

                lines = lines[:insert_index] + import_lines + lines[insert_index:]

                # 插入 router 注册语句在文件底部
                if router_lines:
                    if lines[-1].strip() != "":
                        lines.append("\n")
                    lines.extend(router_lines)

                with open(file_path, "w", encoding="utf-8") as f:
                    f.writelines(lines)

                print(f"✅ 更新 {file_path}：添加 {len(import_lines)} import，{len(router_lines)} 个 include_router")

            else:
                # init 模式：维护 __all__ 和 import
                old_all = self._extract_all_from_lines(lines)
                existing_imports = self._extract_existing_imports(lines)

                all_entries = set(old_all)
                import_lines = []

                for cls in name_list:
                    mod_path = self.class_module_map.get(cls)
                    display_name = self.alias_map.get(cls, cls)

                    if display_name not in all_entries:
                        all_entries.add(display_name)
                    if cls not in existing_imports:
                        import_lines.append(f"from {mod_path} import {cls}\n")

                # 插入 import
                insert_index = 0
                for i, line in enumerate(lines):
                    if line.strip() and not line.strip().startswith("#"):
                        insert_index = i
                        break
                lines = lines[:insert_index] + import_lines + lines[insert_index:]

                # 构建新的 __all__ 块
                new_all_str = (
                    "__all__ = [\n"
                    + ",\n".join(f'    "{cls}"' for cls in sorted(all_entries))
                    + "\n]\n"
                )

                # 替换或追加 __all__
                new_lines = []
                inside_all = False
                replaced = False
                for line in lines:
                    if line.strip().startswith("__all__"):
                        new_lines.append(new_all_str)
                        inside_all = True
                        replaced = True
                    elif inside_all:
                        if "]" in line:
                            inside_all = False
                    else:
                        new_lines.append(line)

                if not replaced:
                    new_lines.append("\n" + new_all_str)

                with open(file_path, "w", encoding="utf-8") as f:
                    f.writelines(new_lines)

                print(f"✅ 更新 {file_path}：类 {len(name_list)} 个，新增 import {len(import_lines)} 行")


# -------------------
# ✅ 使用示例
# -------------------
if __name__ == "__main__":
    current_dir = os.path.dirname(os.path.abspath(__file__))
    base_dir = os.path.abspath(os.path.join(current_dir, "../../"))

    # 示例1：默认行为（只处理 __init__.py，维护 __all__）
    updater1 = InitUpdater(
        scan_dirs=[os.path.join(base_dir, "app/tool/openfast")],
        mode="init"
    )
    updater1.scan()
    updater1.update()

    # 示例2：module 模式，每个模块自动写入同目录下 __init__.py，并自动添加 include_router
    updater2 = InitUpdater(
        scan_dirs=[os.path.join(base_dir, "routers/r_test")],
        mode="module"
    )
    updater2.scan()
    updater2.update()

    # 示例3：module 模式，所有模块写入指定统一文件，自动添加 include_router
    updater3 = InitUpdater(
        scan_dirs=[os.path.join(base_dir, "routers/r_test")],
        mode="module",
        target_file=os.path.join(base_dir, "routers/r_test/__init__.py")
    )
    updater3.scan()
    updater3.update()
