import os
import re
import shutil
import sys
import tkinter as tk
from tkinter import ttk, messagebox
import customtkinter as ctk

# ================= 核心配置 =================
BASE_DIR = os.path.dirname(os.path.abspath(sys.argv[0]))
DOCS_DIR = os.path.join(BASE_DIR, 'docs')
CONFIG_FILE = os.path.join(BASE_DIR, 'mkdocs.yml')

IGNORE_LIST = {
    'assets', 'img', 'images', 'media', 'static', '.git', '.github', 
    'site', 'venv', '__pycache__', 'node_modules', 'mkdocs', 'dist', 'build'
}
IGNORE_SUFFIX = ('.assets', '.images', '_files')

# 样式
THEME_COLOR = "#1f6aa5"     
NEW_ITEM_COLOR = "#2d4a2d"  
FONT_CFG = ("Microsoft YaHei UI", 13)
ROW_HEIGHT = 40

class DraggableTreeview(ttk.Treeview):
    def __init__(self, master, **kw):
        super().__init__(master, **kw)
        self.bind("<Button-1>", self.on_press)
        self.bind("<B1-Motion>", self.on_motion)
        self.bind("<ButtonRelease-1>", self.on_release)
        self.dragging_item = None
        self.tag_configure('new', background=NEW_ITEM_COLOR, foreground="white")
        self.tag_configure('normal', foreground="white")

    def on_press(self, event):
        item = self.identify_row(event.y)
        if item:
            self.dragging_item = item
            self.selection_set(item)
    
    def on_motion(self, event):
        if self.dragging_item: self.configure(cursor="hand2")

    def on_release(self, event):
        self.configure(cursor="")
        if self.dragging_item:
            target = self.identify_row(event.y)
            if target and target != self.dragging_item:
                if self.parent(self.dragging_item) == self.parent(target):
                    self.move(self.dragging_item, self.parent(self.dragging_item), self.index(target))
            self.dragging_item = None

class App(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("MkDocs 目录管理 (顺序记忆版)")
        self.geometry("900x700")
        ctk.set_appearance_mode("Dark")
        
        self.meta_map = {} 
        self.known_paths = set()
        self.first_new_id = None
        # 新增：存储从 yaml 加载的路径顺序
        self.yaml_path_order = []
        
        if not os.path.exists(DOCS_DIR):
            messagebox.showerror("错误", f"找不到 docs 目录: {DOCS_DIR}")
            sys.exit()

        self.setup_ui()
        self.load_data()
        self.after(300, self.auto_focus_new)

    def setup_ui(self):
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)
        
        top = ctk.CTkFrame(self, fg_color="transparent")
        top.grid(row=0, column=0, padx=20, pady=10, sticky="ew")
        ctk.CTkLabel(top, text="目录排序 (严格读取 yaml 顺序)", font=("Microsoft YaHei UI", 16, "bold")).pack(side="left")
        ctk.CTkButton(top, text="保存更新", width=100, fg_color="#10b981", hover_color="#059669", command=self.save).pack(side="right")

        style = ttk.Style()
        style.theme_use("default")
        style.configure("Treeview", background="#2b2b2b", foreground="white", fieldbackground="#2b2b2b", 
                        rowheight=ROW_HEIGHT, font=FONT_CFG)
        style.map("Treeview", background=[('selected', THEME_COLOR)])
        style.layout("Treeview", [('Treeview.treearea', {'sticky': 'nswe'})])

        self.tree = DraggableTreeview(self, columns=("path"), show="tree", selectmode="browse")
        self.tree.grid(row=1, column=0, padx=20, pady=0, sticky="nsew")
        
        sb = ctk.CTkScrollbar(self, command=self.tree.yview)
        sb.grid(row=1, column=1, sticky="ns", pady=0, padx=(0,20))
        self.tree.configure(yscrollcommand=sb.set)

    def load_data(self):
        # 1. 扫描硬盘数据
        raw_tree = self.scan_recursive(DOCS_DIR)
        
        # 2. 从 yaml 加载路径顺序（必须先于 parse_yaml_paths 调用）
        self.yaml_path_order = self.load_path_order_from_yaml()
        
        # 3. 解析 mkdocs.yml 中所有的路径 (用于判断新旧)
        self.parse_yaml_paths()
        
        # 4. 构建 UI 树，严格按照 yaml 中的顺序
        self.build_ui_from_order(raw_tree)

    def load_path_order_from_yaml(self):
        """
        从 mkdocs.yml 的 nav 部分读取所有路径，按照它们在文件中出现的顺序
        返回一个路径列表
        """
        path_order = []
        if not os.path.exists(CONFIG_FILE):
            return path_order
            
        try:
            with open(CONFIG_FILE, 'r', encoding='utf-8-sig') as f:
                lines = f.readlines()
            
            in_nav = False
            for line in lines:
                stripped = line.strip()
                
                # 检测 nav 开始
                if stripped == 'nav:':
                    in_nav = True
                    continue
                
                # 如果不在 nav 部分，继续查找
                if not in_nav:
                    continue
                    
                # 检测 nav 结束（遇到顶级非空行且不是以空格开头）
                if in_nav and stripped and not line.startswith(' ') and not line.startswith('#') and stripped != 'nav:':
                    break
                
                # 跳过注释行和空行
                if not stripped or stripped.startswith('#'):
                    continue
                
                # 解析路径
                # 匹配格式：- 显示名: 路径
                # 或者：- 显示名: （目录，没有路径）
                # 使用正则匹配更灵活
                
                # 尝试匹配有路径的情况
                path_match = re.search(r':\s*(.*?)(#|$)', line)
                if path_match:
                    path = path_match.group(1).strip()
                    # 清理路径：去除引号，处理可能的锚点
                    path = path.strip("'\"").split('#')[0].strip()
                    if path and path not in path_order:
                        path_order.append(path)
                
                # 对于目录（没有路径的情况），我们需要提取显示名
                # 匹配格式：- 显示名:
                elif ':' in line and not line.strip().startswith('#') and not line.strip().endswith('#'):
                    # 提取显示名作为可能的目录名
                    parts = line.split(':', 1)
                    if len(parts) == 2 and not parts[1].strip():
                        display_name = parts[0].replace('-', '').strip().strip("'\"")
                        if display_name and display_name not in path_order:
                            # 将显示名作为目录路径添加
                            path_order.append(display_name)
                            
        except Exception as e:
            print(f"读取 yaml 路径顺序时出错: {e}")
        
        return path_order

    def build_ui_from_order(self, raw_tree):
        """
        按照 yaml 中的路径顺序构建 UI 树
        """
        # 首先，找出所有在 yaml 顺序中的项目
        processed = set()
        
        # 按顺序处理 yaml 中的路径
        for path in self.yaml_path_order:
            # 尝试直接匹配路径
            matched = False
            
            # 遍历 raw_tree 查找匹配
            for name, data in list(raw_tree.items()):
                if name in processed:
                    continue
                    
                # 检查是否匹配
                if self.is_path_match(path, name, data):
                    self.build_ui_tree("", name, data)
                    processed.add(name)
                    matched = True
                    break
            
            # 如果直接匹配失败，尝试模糊匹配
            if not matched:
                for name, data in list(raw_tree.items()):
                    if name in processed:
                        continue
                        
                    # 尝试通过路径的部分匹配
                    if path in name or name in path:
                        self.build_ui_tree("", name, data)
                        processed.add(name)
                        matched = True
                        break
        
        # 处理剩余的项目（新增项目）
        sorted_keys = sorted([k for k in raw_tree.keys() if k not in processed], key=self.natural_sort)
        for name in sorted_keys:
            self.build_ui_tree("", name, raw_tree[name])

    def is_path_match(self, yaml_path, name, data):
        """
        检查 yaml 中的路径是否匹配硬盘数据
        """
        # 如果 yaml 路径包含扩展名，尝试匹配文件
        if '.' in yaml_path:
            # 可能是文件路径
            if data.get('type') == 'file':
                # 检查文件名是否匹配
                if name == yaml_path or data.get('rel', '') == yaml_path:
                    return True
                
                # 检查不带扩展名的匹配
                if os.path.splitext(name)[0] == os.path.splitext(yaml_path)[0]:
                    return True
        else:
            # 可能是目录
            if data.get('type') == 'dir':
                # 检查目录名是否匹配
                if name == yaml_path:
                    return True
                
                # 检查路径是否匹配
                if data.get('rel', '') == yaml_path:
                    return True
        
        return False

    def scan_recursive(self, path):
        res = {}
        try:
            items = sorted(os.listdir(path), key=self.natural_sort)
            for item in items:
                full = os.path.join(path, item)
                if item.startswith('.') or item in IGNORE_LIST: continue
                if os.path.isdir(full) and item.endswith(IGNORE_SUFFIX): continue
                
                rel = os.path.relpath(full, DOCS_DIR).replace("\\", "/")
                
                if os.path.isdir(full):
                    children = self.scan_recursive(full)
                    if children: 
                        res[item] = {'type': 'dir', 'children': children, 'rel': rel}
                        self.meta_map[rel] = {'type': 'dir', 'name': item}
                elif item.endswith('.md'):
                    res[item] = {'type': 'file', 'rel': rel}
                    self.meta_map[rel] = {'type': 'file', 'name': item}
        except: pass
        return res

    def build_ui_tree(self, parent, name, data):
        # 使用 rel 作为 item_id，确保唯一性
        if 'rel' in data:
            node_id = data['rel']
        else:
            node_id = name
        
        if self.tree.exists(node_id): 
            return

        is_dir = (data['type'] == 'dir')
        is_new = self.check_is_new(node_id, is_dir)
        tag = 'new' if is_new else 'normal'
        
        if is_new and self.first_new_id is None: 
            self.first_new_id = node_id
        
        icon = "📁" if is_dir else "📄"
        if name == 'index.md': 
            icon = "🏠"
        
        try:
            self.tree.insert(parent, "end", iid=node_id, text=f"{icon} {name}", tags=(tag,))
        except tk.TclError: 
            return

        if is_dir:
            children = data['children']
            for k in sorted(children.keys(), key=self.natural_sort):
                self.build_ui_tree(node_id, k, children[k])
            if parent == "": 
                self.tree.item(node_id, open=True)

    def check_is_new(self, path, is_dir):
        if not is_dir: 
            return path not in self.known_paths
        prefix = path + "/"
        for p in self.known_paths:
            if p.startswith(prefix) or p == path: 
                return False
        return True

    def auto_focus_new(self):
        if self.first_new_id:
            try:
                parent = self.tree.parent(self.first_new_id)
                while parent:
                    self.tree.item(parent, open=True)
                    parent = self.tree.parent(parent)
                self.tree.see(self.first_new_id)
                self.tree.selection_set(self.first_new_id)
                self.tree.focus(self.first_new_id)
            except: 
                pass

    def save(self):
        roots = self.tree.get_children()
        yaml_content = ""
        for r in roots:
            yaml_content += self.generate_yaml(r, 1)
            
        if self.write_yaml(yaml_content):
            messagebox.showinfo("成功", "MkDocs 目录已更新！")
            self.destroy()

    def generate_yaml(self, item_id, level):
        indent = "    " * level
        meta = self.meta_map.get(item_id)
        if not meta: 
            return ""
        
        name, rel = meta['name'], item_id
        
        if meta['type'] == 'file':
            display = os.path.splitext(name)[0]
            if name == 'index.md': 
                return f"{indent}- 首页: {rel}\n"
            return f"{indent}- {display}: {rel}\n"
        
        if meta['type'] == 'dir':
            kids = self.tree.get_children(item_id)
            target = f"{rel}/{name}.md".replace("//", "/")
            if len(kids) == 1 and kids[0] == target:
                return f"{indent}- {name}: {target}\n"
            
            block = f"{indent}- {name}:\n"
            for k in kids: 
                block += self.generate_yaml(k, level + 1)
            return block

    def parse_yaml_paths(self):
        if not os.path.exists(CONFIG_FILE): 
            return
        try:
            with open(CONFIG_FILE, 'r', encoding='utf-8-sig') as f:
                for line in f:
                    if ':' in line and '#' not in line.split(':')[0]:
                        val = line.split(':', 1)[1].strip()
                        if val:
                            val = val.strip("'").strip('"')
                            self.known_paths.add(val)
        except: 
            pass

    def write_yaml(self, content):
        if not os.path.exists(CONFIG_FILE): 
            return False
        
        # 备份原文件
        shutil.copy(CONFIG_FILE, f"{CONFIG_FILE}.bak")
        
        # 读取原文件内容
        with open(CONFIG_FILE, 'r', encoding='utf-8') as f: 
            lines = f.readlines()
        
        new_lines = []
        skip = False
        inserted = False
        
        for line in lines:
            if line.strip().startswith('nav:'):
                skip = True
                inserted = True
                new_lines.extend(["nav:\n", content])
                continue
            
            if skip and (line.strip() and not line.startswith(' ') and not line.startswith('#')):
                skip = False
            
            if not skip:
                new_lines.append(line)
        
        # 如果没有找到 nav: 部分，则在文件末尾添加
        if not inserted:
            if new_lines and not new_lines[-1].endswith('\n'):
                new_lines.append('\n')
            new_lines.extend(["\nnav:\n", content])
        
        # 写入新文件
        with open(CONFIG_FILE, 'w', encoding='utf-8') as f: 
            f.writelines(new_lines)
        return True

    def natural_sort(self, s):
        return [int(text) if text.isdigit() else text.lower() for text in re.split(r'(\d+)', s)]

if __name__ == "__main__":
    app = App()
    app.mainloop()