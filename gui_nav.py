import os
import re
import shutil
import sys
import tkinter as tk
from tkinter import ttk, messagebox
from typing import Dict, List, Optional, Set, Any, Tuple
import customtkinter as ctk
import yaml

# ================= 配置常量 (Config) =================
class Config:
    # PyInstaller 兼容：_MEIPASS 是打包后的临时解压目录
    if getattr(sys, 'frozen', False):
        BASE_DIR = os.path.dirname(sys.executable)
    else:
        BASE_DIR = os.path.dirname(os.path.abspath(__file__))

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
        except OSError as e:
            print(f"Scan disk error in {path}: {e}")
        return res

    def _parse_yaml_structure(self) -> List[Dict]:
        """使用 pyyaml 解析 mkdocs.yml 的 nav 部分"""
        if not os.path.exists(Config.CONFIG_FILE):
            return []

        try:
            with open(Config.CONFIG_FILE, 'r', encoding='utf-8-sig') as f:
                config = yaml.safe_load(f)
        except yaml.YAMLError as e:
            print(f"YAML Parse Error: {e}")
            return []

        if not config or 'nav' not in config:
            return []

        return self._convert_nav_to_tree(config['nav'])

    def _convert_nav_to_tree(self, nav_items) -> List[Dict]:
        """将 yaml 解析出的 nav 列表转换为内部树形结构"""
        result = []
        for item in nav_items:
            if isinstance(item, dict):
                for key, value in item.items():
                    name = str(key)
                    if isinstance(value, list):
                        result.append({
                            'name': name, 'path': None,
                            'children': self._convert_nav_to_tree(value)
                        })
                    elif isinstance(value, str):
                        result.append({
                            'name': name, 'path': value, 'children': []
                        })
                    else:
                        result.append({
                            'name': name, 'path': None, 'children': []
                        })
            elif isinstance(item, str):
                result.append({'name': item, 'path': item, 'children': []})
        return result

    def save_to_yaml(self, ui_tree_helper) -> bool:
        """保存逻辑：构建 nav 数据结构后用 pyyaml 序列化"""
        if not os.path.exists(Config.CONFIG_FILE):
            return False

        # 1. 从 UI 树构建 nav 数据结构
        roots = ui_tree_helper.get_roots()
        nav_data = []
        for r in roots:
            node = self._build_nav_node(r, ui_tree_helper)
            if node:
                nav_data.append(node)

        # 2. 生成 nav 部分的 YAML（带缩进）
        nav_yaml = yaml.dump(nav_data, allow_unicode=True, default_flow_style=False, sort_keys=False)
        nav_lines = ['    ' + line for line in nav_yaml.split('\n') if line]

        # 3. 备份旧文件
        bak_path = Config.CONFIG_FILE + '.bak'
        shutil.copy(Config.CONFIG_FILE, bak_path)

        # 4. 读取旧文件并替换 nav 部分
        with open(Config.CONFIG_FILE, 'r', encoding='utf-8-sig') as f:
            old_lines = f.readlines()

        new_lines = []
        in_nav = False
        nav_inserted = False

        for line in old_lines:
            stripped = line.strip()
            if stripped.startswith('nav:'):
                in_nav = True
                nav_inserted = True
                new_lines.append('nav:\n')
                new_lines.extend([l + '\n' for l in nav_lines])
                continue

            if in_nav and stripped and not line.startswith(' '):
                in_nav = False

            if not in_nav:
                new_lines.append(line)

        if not nav_inserted:
            new_lines.append('\nnav:\n')
            new_lines.extend([l + '\n' for l in nav_lines])

        # 5. 写入文件
        with open(Config.CONFIG_FILE, 'w', encoding='utf-8') as f:
            f.writelines(new_lines)
        return True

    def _build_nav_node(self, item_id, tree_helper):
        """构建用于 yaml.dump 的 nav 节点（dict 或 str）"""
        meta = self.meta_map.get(item_id)
        if not meta:
            return None

        name = meta['name']

        if meta['type'] == 'file':
            display = os.path.splitext(name)[0] if name.endswith('.md') else name
            if name == 'index.md' or display == '首页':
                return {'首页': item_id}
            return {display: item_id}

        if meta['type'] == 'dir':
            children = tree_helper.get_children(item_id)

            # 优化逻辑：单文件文件夹展平
            if len(children) == 1:
                child_id = children[0]
                child_meta = self.meta_map.get(child_id)
                if child_meta and child_meta['type'] == 'file':
                    return {name: child_id}

            children_list = []
            for kid in children:
                child_node = self._build_nav_node(kid, tree_helper)
                if child_node:
                    children_list.append(child_node)

            return {name: children_list}

        return None

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
            except tk.TclError:
                pass

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
