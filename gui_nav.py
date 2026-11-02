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
    FONT_CFG = ("Microsoft YaHei", 16)
    ROW_HEIGHT = 50
    WIN_SIZE = "620x790"

# ================= 核心逻辑层 (Model) =================
class MkDocsCore(NavigationModel):
    def __init__(self):
        super().__init__(Config.DOCS_DIR, Config.CONFIG_FILE)

# ================= UI 组件层 (View) =================
class DraggableTreeview(ttk.Treeview):
    """同级拖拽排序，并提示可以放置的位置。"""
    def __init__(self, master, on_reorder, on_hint, **kwargs):
        super().__init__(master, **kwargs)
        self.on_reorder = on_reorder
        self.on_hint = on_hint
        self.dragging_item = None
        self.drop_target = None
        self.drag_active = False
        self.bind("<ButtonPress-1>", self.on_press, add='+')
        self.bind("<B1-Motion>", self.on_motion)
        self.bind("<ButtonRelease-1>", self.on_release, add='+')
        self.tag_configure('new', background='#eef9f2', foreground='#19734b')
        self.tag_configure('normal', background='white', foreground='#334155')
        self.tag_configure('drop', background='#e8f0ff', foreground='#1d4ed8')
        self.tag_configure('folder', font=('Microsoft YaHei', 16, 'bold'), foreground='#172b4d')

    def on_press(self, event):
        region = self.identify_region(event.x, event.y)
        self.dragging_item = self.identify_row(event.y) if region in ('tree', 'cell') else None
        self.press_position = (event.x, event.y)
        self.drag_active = False

    def _clear_target(self):
        if self.drop_target and self.exists(self.drop_target):
            tags = tuple(tag for tag in self.item(self.drop_target, 'tags') if tag != 'drop')
            self.item(self.drop_target, tags=tags)
        self.drop_target = None

    def on_motion(self, event):
        if not self.dragging_item:
            return
        if abs(event.x - self.press_position[0]) + abs(event.y - self.press_position[1]) < 5:
            return
        self.drag_active = True
        self._clear_target()
        target = self.identify_row(event.y)
        valid = target and target != self.dragging_item and self.parent(target) == self.parent(self.dragging_item)
        self.configure(cursor='hand2' if valid else 'no')
        if valid:
            self.drop_target = target
            self.item(target, tags=('drop',) + tuple(self.item(target, 'tags')))
            box = self.bbox(target)
            after = bool(box and event.y >= box[1] + box[3] / 2)
            self.on_hint('松开鼠标，移到「' + self.item(target, 'text').strip() + ('」之后' if after else '」之前'))
        else:
            self.on_hint('可以在同一层级内调整顺序')
        if event.y < 30:
            self.yview_scroll(-1, 'units')
        elif event.y > self.winfo_height() - 25:
            self.yview_scroll(1, 'units')

    def on_release(self, event):
        item = self.dragging_item
        target = self.identify_row(event.y)
        self._clear_target()
        self.configure(cursor='')
        if self.drag_active and item and target and target != item and self.parent(item) == self.parent(target):
            parent = self.parent(item)
            before = list(self.get_children(parent))
            siblings = [child for child in before if child != item]
            box = self.bbox(target)
            after = bool(box and event.y >= box[1] + box[3] / 2)
            index = siblings.index(target) + int(after)
            self.move(item, parent, index)
            self.selection_set(item)
            self.focus(item)
            if before != list(self.get_children(parent)):
                self.on_reorder()
        self.dragging_item = None
        self.drag_active = False
        self.on_hint('拖拽调整同级顺序 · 双击修改名称')


class App(ctk.CTk):
    BLUE = '#2563eb'
    MUTED = '#8290a5'
    INK = '#172b4d'
    BG = '#f3f5f9'

    def __init__(self):
        ctk.set_appearance_mode('Light')
        super().__init__()
        self.core = MkDocsCore()
        self.dirty = False
        self.ready = False
        self.toast_job = None
        self.setup_window()
        self.setup_ui()
        self.load_data()
        self.bind('<Control-s>', lambda event: self.save_action())
        self.bind('<Control-S>', lambda event: self.save_action())
        self.bind('<F2>', self.rename_action)
        self.bind('<F5>', lambda event: self.refresh_action())
        self.protocol('WM_DELETE_WINDOW', self.close_action)
        self.after(30, self._fade_in)

    def setup_window(self):
        self.title('Tele · 网站目录管理')
        self.geometry(Config.WIN_SIZE)
        self.minsize(580, 650)
        self.configure(fg_color=self.BG)
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(2, weight=1)
        try:
            self.attributes('-alpha', 0)
        except tk.TclError:
            pass

    def _fade_in(self, step=0):
        try:
            self.attributes('-alpha', 1 - (1 - min(step / 10, 1)) ** 3)
            if step < 10:
                self.after(16, lambda: self._fade_in(step + 1))
        except tk.TclError:
            pass

    def _label(self, parent, text, size=14, color=None, bold=False, **kwargs):
        return ctk.CTkLabel(parent, text=text, text_color=color or self.INK,
                            font=('Microsoft YaHei', size, 'bold' if bold else 'normal'), **kwargs)

    def _button(self, parent, text, command, primary=False, width=90):
        return ctk.CTkButton(parent, text=text, command=command, width=width, height=36,
                    corner_radius=8, font=('Microsoft YaHei', 14),
                    fg_color=self.BLUE if primary else '#edf2fa',
                    hover_color='#1d4ed8' if primary else '#dfe8f7',
                    text_color='white' if primary else '#425675')

    def setup_ui(self):
        header = ctk.CTkFrame(self, fg_color='transparent')
        header.grid(row=0, column=0, padx=28, pady=(26, 18), sticky='ew')
        header.grid_columnconfigure(1, weight=1)
        badge = ctk.CTkFrame(header, width=48, height=48, corner_radius=14, fg_color=self.BLUE)
        badge.grid(row=0, column=0, rowspan=2, padx=(0, 14))
        badge.grid_propagate(False)
        self._label(badge, 'T', 26, 'white', True).place(relx=.5, rely=.5, anchor='center')
        self._label(header, '网站目录', 25, bold=True).grid(row=0, column=1, sticky='w')
        self._label(header, 'TELE  /  整理文章与目录', 13, '#64748b').grid(row=1, column=1, sticky='w')
        self.save_button = self._button(header, '保存更新  ↗', self.save_action, primary=True, width=126)
        self.save_button.grid(row=0, column=2, rowspan=2, padx=(12, 0))
        self.save_button.configure(state='disabled')

        stats = ctk.CTkFrame(self, fg_color='transparent')
        stats.grid(row=1, column=0, padx=28, pady=(0, 18), sticky='ew')
        self.stat_values = []
        for index, (title, color) in enumerate([('文章', self.INK), ('文件夹', self.INK), ('待加入目录', '#17875a')]):
            stats.grid_columnconfigure(index, weight=1)
            card = ctk.CTkFrame(stats, fg_color='white', corner_radius=12, height=72)
            card.grid(row=0, column=index, padx=(0 if index == 0 else 6, 0 if index == 2 else 6), sticky='ew')
            card.grid_propagate(False)
            card.grid_columnconfigure(0, weight=1)
            value = self._label(card, '—', 25, color, True)
            value.grid(row=0, column=0, padx=18, pady=(8, 0), sticky='w')
            self._label(card, title, 13, '#64748b').grid(row=1, column=0, padx=18, sticky='w')
            self.stat_values.append(value)

        panel = ctk.CTkFrame(self, fg_color='white', corner_radius=14)
        panel.grid(row=2, column=0, padx=28, sticky='nsew')
        panel.grid_columnconfigure(0, weight=1)
        panel.grid_rowconfigure(1, weight=1)
        tools = ctk.CTkFrame(panel, fg_color='transparent')
        tools.grid(row=0, column=0, columnspan=2, padx=18, pady=(14, 12), sticky='ew')
        tools.grid_columnconfigure(0, weight=1)
        self._label(tools, '内容目录', 15, bold=True).grid(row=0, column=0, sticky='w')
        self._button(tools, '展开全部', lambda: self.set_expanded(True), width=80).grid(row=0, column=1, padx=4)
        self._button(tools, '收起全部', lambda: self.set_expanded(False), width=80).grid(row=0, column=2, padx=4)
        self.rename_button = self._button(tools, '修改名称', self.rename_action, width=80)
        self.rename_button.grid(row=0, column=3, padx=4)
        self._button(tools, '重新扫描', self.refresh_action, width=80).grid(row=0, column=4, padx=(4, 0))

        style = ttk.Style(self)
        style.theme_use('clam')
        style.configure('Tele.Treeview', background='white', fieldbackground='white', foreground='#334155',
                        rowheight=Config.ROW_HEIGHT, font=Config.FONT_CFG, borderwidth=0, relief='flat')
        style.layout('Tele.Treeview', [('Treeview.treearea', {'sticky': 'nswe'})])
        style.map('Tele.Treeview', background=[('selected', '#e3edff')], foreground=[('selected', '#1d4ed8')])
        self.tree = DraggableTreeview(panel, self.mark_dirty, self.set_hint,
                        show='tree', selectmode='browse', style='Tele.Treeview')
        self.tree.column('#0', width=500, minwidth=260, stretch=True)
        self.tree.grid(row=1, column=0, padx=(12, 0), sticky='nsew')
        self.tree.bind('<Double-1>', self.rename_action)
        self.tree.bind('<<TreeviewSelect>>', self.on_select)
        scrollbar = ctk.CTkScrollbar(panel, command=self.tree.yview, fg_color='white',
                                     button_color='#d2dbe8', button_hover_color='#abbdd6', width=12)
        scrollbar.grid(row=1, column=1, padx=(2, 8), sticky='ns')
        self.tree.configure(yscrollcommand=scrollbar.set)
        self.hint_label = self._label(panel, '拖拽调整同级顺序 · 双击修改名称', 12, '#64748b', anchor='w')
        self.hint_label.grid(row=2, column=0, columnspan=2, padx=20, pady=(12, 14), sticky='ew')

        footer = ctk.CTkFrame(self, fg_color='transparent')
        footer.grid(row=3, column=0, padx=28, pady=(14, 18), sticky='ew')
        footer.grid_columnconfigure(0, weight=1)
        self.status_box = ctk.CTkFrame(footer, fg_color='transparent', corner_radius=8)
        self.status_box.grid(row=0, column=0, sticky='w')
        self.status_label = self._label(self.status_box, '●  就绪', 13, '#64748b')
        self.status_label.pack(padx=10, pady=5)
        self._label(footer, 'Ctrl+S 保存 · F2 改名 · F5 扫描', 12, '#64748b').grid(row=0, column=1, sticky='e')
        self.rename_button.configure(state='disabled')

    def set_hint(self, text):
        self.hint_label.configure(text=text)

    def _item_icon(self, item_id):
        kind = self.core.meta_map[item_id]['type']
        if kind in ('dir', 'group'):
            return ''
        return '⌂' if item_id == 'index.md' or item_id.endswith('/index.md') else '·'

    def load_data(self, focus_id=None):
        try:
            roots = self.core.get_merged_tree_data()
        except (OSError, ValueError) as error:
            self.ready = False
            self.save_button.configure(state='disabled')
            messagebox.showerror('无法读取目录', str(error), parent=self)
            return False
        self.tree.delete(*self.tree.get_children())
        self.first_new_id = None
        for node in roots:
            self._recursive_insert('', node)
        items = list(self.core.meta_map.values())
        counts = [sum(n['type'] == 'file' for n in items), sum(n['type'] == 'dir' for n in items),
                  sum(n['type'] == 'file' and n['is_new'] for n in items)]
        for label, value in zip(self.stat_values, counts):
            label.configure(text=str(value))
        self.dirty = False
        self.ready = True
        self.save_button.configure(state='normal')
        self.title('Tele · 网站目录管理')
        self.status_label.configure(text=f'●  {counts[2]} 篇新增文章，保存后加入目录' if counts[2] else '●  目录已同步',
                                    text_color='#17875a' if counts[2] else self.MUTED)
        selected = focus_id if focus_id and self.tree.exists(focus_id) else self.first_new_id
        if selected:
            self.tree.see(selected)
            self.tree.selection_set(selected)
            self.tree.focus(selected)
        self.on_select()
        return True

    def _recursive_insert(self, parent_id, node):
        item_id = node['id']
        tags = ('new' if node['is_new'] else 'normal',)
        if node['type'] in ('dir', 'group'):
            tags += ('folder',)
        self.tree.insert(parent_id, 'end', iid=item_id, text=f"{self._item_icon(item_id)}  {node['name']}",
                         tags=tags, open=not parent_id)
        if node['is_new'] and self.first_new_id is None:
            self.first_new_id = item_id
        for child in node['children']:
            self._recursive_insert(item_id, child)

    def on_select(self, event=None):
        self.rename_button.configure(state='normal' if self.tree.selection() else 'disabled')

    def set_expanded(self, expanded):
        for item_id, meta in self.core.meta_map.items():
            if meta['type'] in ('dir', 'group'):
                self.tree.item(item_id, open=expanded)

    def mark_dirty(self):
        self.dirty = True
        if self.toast_job:
            self.after_cancel(self.toast_job)
            self.toast_job = None
        self.status_box.configure(fg_color='transparent')
        self.status_label.configure(text='●  有未保存的调整', text_color='#b7791f')
        self.title('Tele · 网站目录管理 *')

    def refresh_action(self):
        if self.dirty and not messagebox.askyesno('重新扫描', '重新扫描会放弃尚未保存的排序和名称，是否继续？', parent=self):
            return
        if self.load_data():
            self.show_saved('扫描完成，目录已刷新')

    def save_action(self):
        if not self.ready:
            return
        self.save_button.configure(state='disabled', text='正在保存…')
        self.update_idletasks()
        focus_id = self.tree.focus()
        try:
            self.core.save_to_yaml(TreeAdapter(self.tree))
            if self.load_data(focus_id):
                self.show_saved('已保存到 mkdocs.yml')
        except (OSError, ValueError) as error:
            messagebox.showerror('保存失败', str(error), parent=self)
        finally:
            self.save_button.configure(state='normal' if self.ready else 'disabled', text='保存更新  ↗')

    def show_saved(self, text):
        if self.toast_job:
            self.after_cancel(self.toast_job)
        self.status_label.configure(text='✓  ' + text, text_color='#17875a')
        self._animate_status(0)

    def _animate_status(self, step):
        start, end = (220, 247, 231), (243, 245, 249)
        ratio = min(step / 20, 1)
        rgb = tuple(round(a + (b - a) * ratio) for a, b in zip(start, end))
        self.status_box.configure(fg_color='#%02x%02x%02x' % rgb)
        self.toast_job = self.after(45, lambda: self._animate_status(step + 1)) if step < 20 else None

    def rename_action(self, event=None):
        selected = self.tree.identify_row(event.y) if event and getattr(event, 'num', None) == 1 else self.tree.focus()
        if not selected:
            return 'break'
        self.tree.selection_set(selected)
        name = simpledialog.askstring('修改显示名称', '网站上显示的名称：',
                    initialvalue=self.core.meta_map[selected]['name'], parent=self)
        if name is not None and name.strip() != self.core.meta_map[selected]['name']:
            try:
                for item_id in self.core.rename_item(selected, name):
                    self.tree.item(item_id, text=f"{self._item_icon(item_id)}  {self.core.meta_map[item_id]['name']}")
                self.mark_dirty()
            except ValueError as error:
                messagebox.showerror('名称无效', str(error), parent=self)
        return 'break'

    def close_action(self):
        if self.dirty and not messagebox.askyesno('尚未保存', '有未保存的调整，确定关闭？', parent=self):
            return
        self.destroy()


class TreeAdapter:
    def __init__(self, tree_widget):
        self.tree = tree_widget

    def get_roots(self):
        return self.tree.get_children()

    def get_children(self, item_id):
        return self.tree.get_children(item_id)


if __name__ == '__main__':
    app = App()
    app.mainloop()
