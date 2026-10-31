import os
import sys
import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
import customtkinter as ctk
from navigation import NavigationModel

# ================= 配置常量 (Config) =================
class Config:
    # PyInstaller 兼容：_MEIPASS 是打包后的临时解压目录
    if getattr(sys, 'frozen', False):
        BASE_DIR = os.path.dirname(sys.executable)
    else:
        BASE_DIR = os.path.dirname(os.path.abspath(__file__))

    DOCS_DIR = os.path.join(BASE_DIR, 'docs')
    CONFIG_FILE = os.path.join(BASE_DIR, 'mkdocs.yml')

    # UI 样式
    THEME_COLOR = "#1f6aa5"
    NEW_ITEM_COLOR = "#2d4a2d"
    FONT_CFG = ("Microsoft YaHei UI", 13)
    ROW_HEIGHT = 40
    WIN_SIZE = "600x700"

# ================= 核心逻辑层 (Model) =================
class MkDocsCore(NavigationModel):
    def __init__(self):
        super().__init__(Config.DOCS_DIR)

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
        self.title("Tele 网站目录管理")
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
        ctk.CTkButton(top_frame, text="修改名称", width=90,
                      command=self.rename_action).pack(side="right", padx=8)

        # 树形列表样式
        style = ttk.Style()
        style.theme_use("default")
        style.configure("Treeview", background="#2b2b2b", foreground="white",
                        fieldbackground="#2b2b2b", rowheight=Config.ROW_HEIGHT, font=Config.FONT_CFG)
        style.map("Treeview", background=[('selected', Config.THEME_COLOR)])

        # 树形控件
        self.tree = DraggableTreeview(self, columns=("path"), show="tree", selectmode="browse")
        self.tree.bind("<Double-1>", self.rename_action)
        self.tree.grid(row=1, column=0, padx=20, pady=0, sticky="nsew")

        sb = ctk.CTkScrollbar(self, command=self.tree.yview)
        sb.grid(row=1, column=1, sticky="ns", pady=0, padx=(0,20))
        self.tree.configure(yscrollcommand=sb.set)
        ctk.CTkLabel(self, text="拖拽调整同级顺序，双击修改名称。绿色项目已自动收录。",
                     text_color="#aaaaaa").grid(row=2, column=0, padx=16, pady=8)

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

        except (OSError, ValueError) as e:
            messagebox.showerror("无法读取目录", str(e))
            sys.exit()

    def _recursive_insert(self, parent_id, node):
        """将节点数据插入 Treeview"""
        node_id = node['id']
        text = node['name']

        # 图标
        icon = self._item_icon(node_id)

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
        try:
            if self.core.save_to_yaml(TreeAdapter(self.tree)):
                messagebox.showinfo("成功", "目录顺序与显示名称已保存，下次预览或构建时生效。")
                self.destroy()
        except (OSError, ValueError) as error:
            messagebox.showerror("保存失败", str(error))

    def _item_icon(self, item_id):
        kind = self.core.meta_map[item_id]['type']
        if kind in ('dir', 'group'):
            return "📁"
        if kind == 'link':
            return "🔗"
        return "🏠" if item_id == 'index.md' or item_id.endswith('/index.md') else "📄"

    def rename_action(self, event=None):
        selected = self.tree.identify_row(event.y) if event else self.tree.focus()
        if not selected:
            return 'break'
        name = simpledialog.askstring("修改显示名称", "网站上显示的名称：",
                    initialvalue=self.core.meta_map[selected]['name'], parent=self)
        if name is not None:
            try:
                for item_id in self.core.rename_item(selected, name):
                    self.tree.item(item_id, text=f"{self._item_icon(item_id)} {self.core.meta_map[item_id]['name']}")
            except ValueError as error:
                messagebox.showerror("名称无效", str(error))
        return 'break'

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
