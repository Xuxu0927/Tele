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

# 只需要保留核心过滤逻辑
IGNORE_LIST = {
    'assets', 'img', 'images', 'media', 'static', '.git', '.github', 
    'site', 'venv', '__pycache__', 'node_modules', 'mkdocs', 'dist', 'build'
}
IGNORE_SUFFIX = ('.assets', '.images', '_files')

# 样式配置
THEME_COLOR = "#1f6aa5"     
NEW_ITEM_COLOR = "#2d4a2d"  
FONT_CFG = ("Microsoft YaHei UI", 13)
ROW_HEIGHT = 40

class DraggableTreeview(ttk.Treeview):
    """核心组件：支持拖拽的树状列表"""
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
            self.selection_set(item) # 按下即选中
    
    def on_motion(self, event):
        if self.dragging_item: self.configure(cursor="hand2")

    def on_release(self, event):
        self.configure(cursor="")
        if self.dragging_item:
            target = self.identify_row(event.y)
            if target and target != self.dragging_item:
                # 核心约束：仅允许同级节点交换顺序
                if self.parent(self.dragging_item) == self.parent(target):
                    self.move(self.dragging_item, self.parent(self.dragging_item), self.index(target))
            self.dragging_item = None

class App(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("MkDocs 目录管理")
        self.geometry("600x700")
        ctk.set_appearance_mode("Dark")
        
        self.meta_map = {} 
        self.known_paths = set()
        self.first_new_id = None
        
        if not os.path.exists(DOCS_DIR):
            messagebox.showerror("错误", f"找不到 docs 目录: {DOCS_DIR}")
            sys.exit()

        self.setup_ui()
        self.load_data()
        self.after(300, self.auto_focus_new) # 启动后自动定位

    def setup_ui(self):
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)
        
        # 1. 顶部栏 (简化)
        top = ctk.CTkFrame(self, fg_color="transparent")
        top.grid(row=0, column=0, padx=20, pady=10, sticky="ew")
        ctk.CTkLabel(top, text="拖拽排序 (绿色为新增)", font=("Microsoft YaHei UI", 16, "bold")).pack(side="left")
        ctk.CTkButton(top, text="保存更新", width=100, fg_color="#10b981", hover_color="#059669", command=self.save).pack(side="right")

        # 2. 列表区
        style = ttk.Style()
        style.theme_use("default")
        style.configure("Treeview", background="#2b2b2b", foreground="white", fieldbackground="#2b2b2b", 
                        rowheight=ROW_HEIGHT, font=FONT_CFG)
        style.map("Treeview", background=[('selected', THEME_COLOR)])
        style.layout("Treeview", [('Treeview.treearea', {'sticky': 'nswe'})]) # 隐藏表头

        self.tree = DraggableTreeview(self, columns=("path"), show="tree", selectmode="browse")
        self.tree.grid(row=1, column=0, padx=20, pady=0, sticky="nsew")
        
        sb = ctk.CTkScrollbar(self, command=self.tree.yview)
        sb.grid(row=1, column=1, sticky="ns", pady=0, padx=(0,20))
        self.tree.configure(yscrollcommand=sb.set)

    def load_data(self):
        # 第一步：分析 yaml，找出旧文件
        self.parse_yaml_paths()
        
        # 第二步：扫描硬盘，构建内存树
        raw_tree = self.scan_recursive(DOCS_DIR)
        
        # 第三步：读取历史一级顺序
        history_order = self.get_history_order()
        processed = set()
        
        # A. 恢复历史顺序
        for name in history_order:
            if name in raw_tree:
                self.build_ui_tree("", name, raw_tree[name])
                processed.add(name)
        
        # B. 追加新增项
        for name in sorted(raw_tree.keys(), key=self.natural_sort):
            if name not in processed:
                self.build_ui_tree("", name, raw_tree[name])

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
        node_id = data['rel']
        if self.tree.exists(node_id): return

        # 核心：判断是否新增 (文件不在yaml里，或文件夹下全是新文件)
        is_dir = (data['type'] == 'dir')
        is_new = self.check_is_new(node_id, is_dir)
        tag = 'new' if is_new else 'normal'
        
        if is_new and self.first_new_id is None: self.first_new_id = node_id
        
        icon = "📁" if is_dir else "📄"
        if name == 'index.md': icon = "🏠"
        
        try:
            self.tree.insert(parent, "end", iid=node_id, text=f"{icon} {name}", tags=(tag,))
        except tk.TclError: return

        if is_dir:
            children = data['children']
            for k in sorted(children.keys(), key=self.natural_sort):
                self.build_ui_tree(node_id, k, children[k])
            if parent == "": self.tree.item(node_id, open=True)

    def check_is_new(self, path, is_dir):
        if not is_dir: return path not in self.known_paths
        # 文件夹判断：如果known_paths里没有以此开头的路径，说明该文件夹下的文件全是新的
        prefix = path + "/"
        for p in self.known_paths:
            if p.startswith(prefix) or p == path: return False
        return True

    def auto_focus_new(self):
        """自动定位第一个新增项"""
        if self.first_new_id:
            try:
                parent = self.tree.parent(self.first_new_id)
                while parent:
                    self.tree.item(parent, open=True)
                    parent = self.tree.parent(parent)
                self.tree.see(self.first_new_id)
                self.tree.selection_set(self.first_new_id)
                self.tree.focus(self.first_new_id)
            except: pass

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
        if not meta: return ""
        
        name, rel = meta['name'], item_id
        
        if meta['type'] == 'file':
            display = os.path.splitext(name)[0]
            if name == 'index.md': return f"{indent}- 首页: {rel}\n"
            return f"{indent}- {display}: {rel}\n"
        
        if meta['type'] == 'dir':
            kids = self.tree.get_children(item_id)
            # 智能折叠：仅有一个同名文件
            target = f"{rel}/{name}.md".replace("//", "/")
            if len(kids) == 1 and kids[0] == target:
                return f"{indent}- {name}: {target}\n"
            
            block = f"{indent}- {name}:\n"
            for k in kids: block += self.generate_yaml(k, level + 1)
            return block

    def parse_yaml_paths(self):
        if not os.path.exists(CONFIG_FILE): return
        try:
            with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                for line in f:
                    if ':' in line and '#' not in line.split(':')[0]:
                        val = line.split(':', 1)[1].strip()
                        if val: self.known_paths.add(val)
        except: pass

    def get_history_order(self):
        order = []
        if not os.path.exists(CONFIG_FILE): return order
        try:
            with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                in_nav = False
                for line in f:
                    s = line.strip()
                    if s.startswith('nav:'): in_nav = True; continue
                    if in_nav:
                        if s and not line.startswith(' ') and not line.startswith('#'): break
                        m = re.search(r'^\s*-\s+(.*?)(:|$)(.*)', line)
                        if m:
                            key, val = m.group(1).strip(), m.group(3).strip()
                            folder = val.split('/')[0] if val else key
                            if key == '首页' or folder == 'index.md': folder = 'index.md'
                            order.append(folder)
        except: pass
        return order

    def write_yaml(self, content):
        if not os.path.exists(CONFIG_FILE): return False
        shutil.copy(CONFIG_FILE, f"{CONFIG_FILE}.bak")
        with open(CONFIG_FILE, 'r', encoding='utf-8') as f: lines = f.readlines()
        
        new_l, skip, inserted = [], False, False
        for line in lines:
            if line.strip().startswith('nav:'):
                skip = True; inserted = True
                new_l.extend(["nav:\n", content])
                continue
            if skip and (line.strip() and not line.startswith(' ') and not line.startswith('#')):
                skip = False
            if not skip: new_l.append(line)
        
        if not inserted: new_l.extend(["\nnav:\n", content])
        with open(CONFIG_FILE, 'w', encoding='utf-8') as f: f.writelines(new_l)
        return True

    def natural_sort(self, s):
        return [int(text) if text.isdigit() else text.lower() for text in re.split(r'(\d+)', s)]

if __name__ == "__main__":
    app = App()
    app.mainloop()