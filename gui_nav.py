import os
import re
import shutil
import sys
import tkinter as tk
from tkinter import ttk, messagebox
from typing import Dict, List, Optional, Set, Any, Tuple
import customtkinter as ctk

# ================= 配置常量 (Config) =================
class Config:
    BASE_DIR = os.path.dirname(os.path.abspath(sys.argv[0]))
    DOCS_DIR = os.path.join(BASE_DIR, 'docs')
    CONFIG_FILE = os.path.join(BASE_DIR, 'mkdocs.yml')
    
    # 忽略列表
    IGNORE_NAMES = {
        'assets', 'img', 'images', 'media', 'static', '.git', '.github', 
        'site', 'venv', '__pycache__', 'node_modules', 'mkdocs', 'dist', 'build'
    }
    IGNORE_SUFFIXES = ('.assets', '.images', '_files')

    # UI 样式
    THEME_COLOR = "#1f6aa5"
    NEW_ITEM_COLOR = "#2d4a2d"
    FONT_CFG = ("Microsoft YaHei UI", 13)
    ROW_HEIGHT = 40
    WIN_SIZE = "600x700"

# ================= 核心逻辑层 (Model) =================
class MkDocsCore:
    """处理文件扫描、YAML解析和排序合并逻辑，不涉及任何 UI"""
    
    def __init__(self):
        self.meta_map = {}     # 存储路径对应的元数据 (type, name)
        self.known_paths = set() # 记录 YAML 中已存在的路径
    
    def get_merged_tree_data(self) -> List[Dict]:
        """主入口：获取合并后的树形数据结构"""
        if not os.path.exists(Config.DOCS_DIR):
            raise FileNotFoundError(f"找不到目录: {Config.DOCS_DIR}")

        self.meta_map.clear()
        self.known_paths.clear()

        # 1. 获取两份数据源
        raw_disk = self._scan_disk(Config.DOCS_DIR)
        history_tree = self._parse_yaml_structure()
        
        # 2. 合并数据 (返回排序后的节点列表)
        return self._merge_logic(history_tree, raw_disk)

    def _merge_logic(self, history_list: List[Dict], disk_data: Dict) -> List[Dict]:
        """递归合并算法"""
        result = []
        
        # A. 优先处理历史记录
        for h_item in history_list:
            display_name = h_item['name']
            found_key = self._find_matching_key(display_name, h_item.get('path'), disk_data)
            
            if found_key:
                data = disk_data.pop(found_key) # 消费掉
                node = self._create_node(data['rel'], display_name, data, is_new=False)
                
                if data['type'] == 'dir':
                    node['children'] = self._merge_logic(h_item.get('children', []), data.get('children', {}))
                
                result.append(node)

        # B. 处理新增项 (按自然顺序)
        sorted_keys = sorted(disk_data.keys(), key=self._natural_sort)
        for k in sorted_keys:
            data = disk_data[k]
            # 新增项显示名默认为文件名/文件夹名
            display_name = k 
            node = self._create_node(data['rel'], display_name, data, is_new=True)
            
            if data['type'] == 'dir':
                # 新文件夹内部递归扫描
                node['children'] = self._merge_logic([], data.get('children', {}))
                
            result.append(node)
            
        return result

    def _create_node(self, rel_path, name, data, is_new):
        """构建标准节点对象，并记录元数据"""
        self.meta_map[rel_path] = {'type': data['type'], 'name': name}
        if not is_new:
            self.known_paths.add(rel_path)
            
        return {
            'id': rel_path,
            'name': name,
            'type': data['type'],
            'is_new': is_new,
            'children': []
        }

    def _find_matching_key(self, name: str, path: Optional[str], disk_data: Dict) -> Optional[str]:
        """尝试匹配 YAML 条目和硬盘文件"""
        # 1. 直接 Key 匹配
        if name in disk_data: return name
        
        # 2. 忽略大小写
        for k in disk_data:
            if k.lower() == name.lower(): return k
            
        # 3. 通过路径反查
        if path:
            target = path.replace('\\', '/')
            for k, v in disk_data.items():
                if v['rel'] == target: return k
        return None

    def _scan_disk(self, path: str) -> Dict:
        """递归扫描硬盘"""
        res = {}
        try:
            items = sorted(os.listdir(path), key=self._natural_sort)
            for item in items:
                full = os.path.join(path, item)
                if item.startswith('.') or item in Config.IGNORE_NAMES: continue
                if os.path.isdir(full) and item.endswith(Config.IGNORE_SUFFIXES): continue
                
                rel = os.path.relpath(full, Config.DOCS_DIR).replace("\\", "/")
                
                if os.path.isdir(full):
                    children = self._scan_disk(full)
                    if children: 
                        res[item] = {'type': 'dir', 'children': children, 'rel': rel}
                elif item.endswith('.md'):
                    res[item] = {'type': 'file', 'rel': rel}
        except Exception: pass
        return res

    def _parse_yaml_structure(self) -> List[Dict]:
        """解析 mkdocs.yml 的 nav 部分"""
        if not os.path.exists(Config.CONFIG_FILE): return []
        
        result_tree = []
        stack = [{'indent': -1, 'children': result_tree}]
        in_nav = False
        
        try:
            with open(Config.CONFIG_FILE, 'r', encoding='utf-8-sig') as f:
                for line in f:
                    s = line.strip()
                    if not s or s.startswith('#'): continue
                    
                    if s.startswith('nav:'): 
                        in_nav = True; continue
                    
                    # nav 结束判断
                    if in_nav and not line.startswith(' ') and line[0].isalpha():
                        in_nav = False; break
                        
                    if in_nav:
                        indent = len(line) - len(line.lstrip(' '))
                        m = re.match(r'^\s*-\s*(.*?)(:|$)(.*)', line)
                        if m:
                            name = m.group(1).strip().strip("'").strip('"')
                            val = m.group(3).strip()
                            path = val.split('#')[0].strip().strip("'").strip('"') if val else None
                            
                            item = {'name': name, 'path': path, 'children': []}
                            
                            while len(stack) > 1 and stack[-1]['indent'] >= indent:
                                stack.pop()
                            stack[-1]['children'].append(item)
                            
                            if not path: # 是目录
                                stack.append({'indent': indent, 'children': item['children']})
        except Exception as e: print(f"YAML Parse Error: {e}")
        return result_tree

    def save_to_yaml(self, ui_tree_helper) -> bool:
        """保存逻辑：利用 UI 树的顺序生成 YAML"""
        if not os.path.exists(Config.CONFIG_FILE): return False
        
        # 生成 content
        roots = ui_tree_helper.get_roots()
        content = ""
        for r in roots:
            content += self._generate_yaml_block(r, 1, ui_tree_helper)
            
        # 写入文件
        shutil.copy(Config.CONFIG_FILE, f"{Config.CONFIG_FILE}.bak")
        with open(Config.CONFIG_FILE, 'r', encoding='utf-8') as f: lines = f.readlines()
        
        new_lines = []
        skip, inserted = False, False
        
        for line in lines:
            s = line.strip()
            if s.startswith('nav:'):
                skip = True; inserted = True
                new_lines.extend(["nav:\n", content])
                continue
            if skip and (s and not line.startswith(' ') and not line.startswith('#')):
                skip = False
            if not skip: new_lines.append(line)
            
        if not inserted: new_lines.extend(["\nnav:\n", content])
        
        with open(Config.CONFIG_FILE, 'w', encoding='utf-8') as f:
            f.writelines(new_lines)
        return True

    def _generate_yaml_block(self, item_id, level, tree_helper) -> str:
        indent = "    " * level
        meta = self.meta_map.get(item_id)
        if not meta: return ""
        
        name = meta['name']
        
        # --- 情况 1: 普通文件 ---
        if meta['type'] == 'file':
            display = os.path.splitext(name)[0] if name.endswith('.md') else name
            if name == 'index.md' or display == '首页': return f"{indent}- 首页: {item_id}\n"
            return f"{indent}- {display}: {item_id}\n"
        
        # --- 情况 2: 文件夹 ---
        if meta['type'] == 'dir':
            children = tree_helper.get_children(item_id)
            
            # =========== 新增优化逻辑开始 ===========
            # 如果文件夹下 【只有一个子项】 且该子项是 【文件】
            if len(children) == 1:
                child_id = children[0]
                child_meta = self.meta_map.get(child_id)
                
                # 确认子项存在且是文件
                if child_meta and child_meta['type'] == 'file':
                    # 直接生成: "- 文件夹名: 子文件路径"
                    # 这样就跳过了子文件名的那一层显示
                    return f"{indent}- {name}: {child_id}\n"
            # =========== 新增优化逻辑结束 ===========

            # 常规逻辑：有多项，或者子项是文件夹，则生成嵌套结构
            block = f"{indent}- {name}:\n"
            for kid in children:
                block += self._generate_yaml_block(kid, level + 1, tree_helper)
            return block
        
        
    @staticmethod
    def _natural_sort(s):
        return [int(t) if t.isdigit() else t.lower() for t in re.split(r'(\d+)', s)]

# ================= UI 组件层 (View) =================
class DraggableTreeview(ttk.Treeview):
    """支持拖拽的 Treeview 组件"""
    def __init__(self, master, **kw):
        super().__init__(master, **kw)
        self.bind("<Button-1>", self.on_press)
        self.bind("<B1-Motion>", self.on_motion)
        self.bind("<ButtonRelease-1>", self.on_release)
        self.dragging_item = None
        self.tag_configure('new', background=Config.NEW_ITEM_COLOR, foreground="white")
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
    
    # 辅助方法供 Core 调用
    def get_roots(self): return self.get_children()
    def get_children_of(self, item): return self.get_children(item)

class App(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.core = MkDocsCore() # 实例化逻辑核心
        self.setup_window()
        self.setup_ui()
        self.load_data()

    def setup_window(self):
        self.title("MkDocs 目录管理 (Refactored)")
        self.geometry(Config.WIN_SIZE)
        ctk.set_appearance_mode("Dark")
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

    def setup_ui(self):
        # 顶部工具栏
        top_frame = ctk.CTkFrame(self, fg_color="transparent")
        top_frame.grid(row=0, column=0, padx=20, pady=10, sticky="ew")
        
        ctk.CTkLabel(top_frame, text="MkDocs 目录排序器", font=("Microsoft YaHei UI", 16, "bold")).pack(side="left")
        ctk.CTkButton(top_frame, text="保存更新", width=100, fg_color="#10b981", 
                      hover_color="#059669", command=self.save_action).pack(side="right")

        # 树形列表样式
        style = ttk.Style()
        style.theme_use("default")
        style.configure("Treeview", background="#2b2b2b", foreground="white", 
                        fieldbackground="#2b2b2b", rowheight=Config.ROW_HEIGHT, font=Config.FONT_CFG)
        style.map("Treeview", background=[('selected', Config.THEME_COLOR)])
        
        # 树形控件
        self.tree = DraggableTreeview(self, columns=("path"), show="tree", selectmode="browse")
        self.tree.grid(row=1, column=0, padx=20, pady=0, sticky="nsew")
        
        sb = ctk.CTkScrollbar(self, command=self.tree.yview)
        sb.grid(row=1, column=1, sticky="ns", pady=0, padx=(0,20))
        self.tree.configure(yscrollcommand=sb.set)

    def load_data(self):
        try:
            # 1. 从 Core 获取清洗好的数据
            data_tree = self.core.get_merged_tree_data()
            
            # 2. 渲染 UI
            self.first_new_id = None
            for node in data_tree:
                self._recursive_insert("", node)
                
            # 3. 自动定位到新文件
            self.after(300, self.auto_focus_new)
            
        except FileNotFoundError as e:
            messagebox.showerror("路径错误", str(e))
            sys.exit()

    def _recursive_insert(self, parent_id, node):
        """将节点数据插入 Treeview"""
        node_id = node['id']
        text = node['name']
        
        # 图标
        icon = "📁" if node['type'] == 'dir' else "📄"
        if text == 'index.md' or node_id == 'index.md': icon = "🏠"
        
        # 标签 (颜色)
        tag = 'new' if node['is_new'] else 'normal'
        if node['is_new'] and self.first_new_id is None: 
            self.first_new_id = node_id
            
        self.tree.insert(parent_id, "end", iid=node_id, text=f"{icon} {text}", tags=(tag,))
        
        if node['children']:
            for child in node['children']:
                self._recursive_insert(node_id, child)
            if parent_id == "": 
                self.tree.item(node_id, open=True)

    def auto_focus_new(self):
        if self.first_new_id:
            try:
                self.tree.see(self.first_new_id)
                self.tree.selection_set(self.first_new_id)
                self.tree.focus(self.first_new_id)
            except: pass

    def save_action(self):
        # 将 Treeview 适配器传给 Core，让 Core 去遍历并保存
        adapter = TreeAdapter(self.tree)
        if self.core.save_to_yaml(adapter):
            messagebox.showinfo("成功", "mkdocs.yml 已更新！")
            self.destroy()

# ================= 适配器 (Adapter) =================
class TreeAdapter:
    """
    用于将 Treeview 的操作暴露给 Core，
    这样 Core 不需要直接依赖 tkinter 的具体控件对象
    """
    def __init__(self, tree_widget):
        self.tree = tree_widget
        
    def get_roots(self):
        return self.tree.get_children()
        
    def get_children(self, item_id):
        return self.tree.get_children(item_id)

if __name__ == "__main__":
    app = App()
    app.mainloop()