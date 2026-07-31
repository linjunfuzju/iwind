# rainbow_yu DeepWindF.replace_io 🐋✨
# Date : 2025/7/7 19:14

import os
import re

class ReplaceIo:
    def __init__(
            self,
            base_path,
    ):
        self.base_path = base_path

    def __call__(self, *args, **kwargs):
        self.execute()


    def replace(self, file_path):
        with open(file_path, 'r') as f:
            lines = f.readlines()

        updated, new_lines = self.replace_rule(lines,file_path)

        if updated:
            with open(file_path, 'w') as f:
                f.writelines(new_lines)
            print(f"✅ 文件已更新: {file_path}")
        else:
            print(f"✅ 文件已是最新: {file_path}")

    def replace_rule(self,lines,file_path):
        pass

    def folder_rule(
            self,
            folder_name,
            dir_path,
    ):
        pass

    def file_rule(
            self,
            file_name,
    ):
        pass

    def execute(self):
        for dirpath, dirnames, filenames in os.walk(self.base_path):
            folder_name = os.path.basename(dirpath)
            if self.folder_rule(folder_name,dirpath):
                for fname in filenames:
                    if self.file_rule(fname):
                        file_path = os.path.join(dirpath, fname)
                        self.replace(file_path)

class ReplaceDll(ReplaceIo):
    def __init__(self, base_path):
        super().__init__(base_path)

    def replace_rule(self, lines,file_path):
        updated = False
        new_lines = []
        for line in lines:
            if '.dll' in line:
                match = re.search(r'["\']([^"\']*?)(DISCON[^/\\]*?)\.dll["\']', line)
                if match:
                    dll_name = match.group(2)
                    if dll_name == "DISCON":
                        new_dll_path = f'"../5MW_Baseline/ServoData/DISCON/DISCON.so"'
                    elif dll_name == "DISCON_ITIBarge":
                        new_dll_path = f'"../5MW_Baseline/ServoData/DISCON_ITI/DISCON_ITIBarge.so"'
                    elif dll_name == "DISCON_OC3Hywind":
                        new_dll_path = f'"../5MW_Baseline/ServoData/DISCON_OC3/DISCON_OC3Hywind.so"'
                    else:
                        print(f"⚠️ 未知DLL名称: {dll_name} in {file_path}")
                        continue

                    new_line = re.sub(r'["\']([^"\']*?DISCON[^/\\]*?)\.dll["\']', new_dll_path, line)
                    if new_line != line:
                        print(f"✅ 替换成功: {file_path}")
                        print(f"  OLD: {line.strip()}")
                        print(f"  NEW: {new_line.strip()}")
                        line = new_line
                        updated = True
            new_lines.append(line)

        return updated,new_lines

    def folder_rule(self, folder_name, dirpath):
        return folder_name.startswith("5MW") and "Linear" not in dirpath and "BD" not in dirpath
    def file_rule(self,file_name,):
        file_name.endswith("ServoDyn.dat")


class ReplaceFst(ReplaceIo):
    def __init__(self, base_path):
        super().__init__(base_path)

    def folder_rule(self, folder_name, dirpath):
        return True
    def file_rule(self,file_name,):
        return file_name.endswith(".fst")
    def replace_rule(self, lines, file_path):
        updated = False
        new_lines = []
        for line in lines:
            # 替换 WrVTK 行，保留前导空格
            match = re.match(r'^\s*0\s+WrVTK', line)
            if match:
                # 保留前导空格并替换内容
                new_line = re.sub(r'^\s*0\s+WrVTK', lambda m: m.group(0).replace('0', '2'), line)
                if new_line != line:
                    print(f"✅ 替换成功: {file_path}")
                    print(f"  OLD: {line.strip()}")
                    print(f"  NEW: {new_line.strip()}")
                    updated = True
                line = new_line

            # 替换 OutFileFmt 行，保留前导空格
            match = re.match(r'^\s*0\s+OutFileFmt', line)
            if match:
                # 保留前导空格并替换内容
                new_line = re.sub(r'^\s*0\s+OutFileFmt', lambda m: m.group(0).replace('0', '1'), line)
                if new_line != line:
                    print(f"✅ 替换成功: {file_path}")
                    print(f"  OLD: {line.strip()}")
                    print(f"  NEW: {new_line.strip()}")
                    updated = True
                line = new_line

            new_lines.append(line)

        return updated, new_lines



if __name__ == "__main__":
    base_path = "../servers/openfast-server/keydata"  # 替换为你的实际路径
    rpio = ReplaceFst(base_path)
    rpio.execute()

