import os

# ================= 配置区域 =================
# 你的文档根目录文件夹名称
DOCS_DIR = 'docs'

# 1. 完全匹配忽略 (文件夹名完全等于这些时忽略)
IGNORE_EXACT = {
    'assets', 'img', 'images', 'media', 'static', 
    '.git', '.github', '.DS_Store', 'CNAME', 'site'
}

# 2. 后缀匹配忽略 (文件夹名以这些结尾时忽略，专门解决 xxx.assets 问题)
IGNORE_SUFFIX = (
    '.assets', 
    '.images', 
    '_files'
)
# ===========================================

def get_indent(level):
    return "    " * level

def scan_directory(path, level=0):
    output = ""
    try:
        # 获取当前目录下的所有内容并排序
        items = sorted(os.listdir(path))
    except FileNotFoundError:
        return f"错误：找不到目录 {path}，请确认 DOCS_DIR 配置正确。\n"

    dirs = []
    files = []

    for item in items:
        full_path = os.path.join(path, item)
        
        # --- 核心过滤逻辑 ---
        # 1. 忽略隐藏文件/文件夹 (以.开头)
        if item.startswith('.'):
            continue
        # 2. 忽略精准匹配名单
        if item in IGNORE_EXACT:
            continue
        # 3. 忽略特定后缀的文件夹 (比如 xxx.assets)
        if os.path.isdir(full_path) and item.endswith(IGNORE_SUFFIX):
            continue
        # ------------------
        
        if os.path.isdir(full_path):
            dirs.append(item)
        elif item.endswith('.md'):
            files.append(item)

    # 1. 先处理文件
    for f in files:
        file_name = os.path.splitext(f)[0]
        # 获取相对于 DOCS_DIR 的路径，用于 MkDocs 引用
        # 注意：MkDocs 的 nav 路径通常是从 docs 内部开始算的
        # 如果脚本放在项目根目录，docs/A/b.md 在 nav 里应该是 A/b.md
        
        # 计算相对路径：从 path 到 DOCS_DIR 的相对路径 + 文件名
        # 修正路径计算逻辑，确保生成的路径是 MkDocs 友好的
        abs_file_path = os.path.join(path, f)
        abs_docs_dir = os.path.abspath(DOCS_DIR)
        abs_current_file = os.path.abspath(abs_file_path)
        
        rel_path = os.path.relpath(abs_current_file, start=abs_docs_dir)
        rel_path = rel_path.replace("\\", "/") # 兼容 Windows
        
        output += f"{get_indent(level)}- {file_name}: {rel_path}\n"

    # 2. 再处理文件夹 (递归)
    for d in dirs:
        # 预先扫描一下子文件夹，如果子文件夹里全是资源文件，没有任何md，
        # 其实也可以选择不显示这个文件夹目录。
        # 但为了保持简单，这里只要是合法文件夹都显示。
        sub_content = scan_directory(os.path.join(path, d), level + 1)
        
        # 只有当子文件夹里有内容时，才把这个文件夹名字打印出来
        # 这样可以避免出现空的 "- 文件夹:" 
        if sub_content.strip(): 
            output += f"{get_indent(level)}- {d}:\n"
            output += sub_content
        
    return output

if __name__ == "__main__":
    print(f"🔍 正在扫描 {DOCS_DIR} 目录...")
    
    if os.path.exists(DOCS_DIR):
        nav_content = scan_directory(DOCS_DIR)
        
        if not nav_content:
            print("⚠️ 警告：目录下似乎没有找到 Markdown 文件。")
        else:
            final_output = "nav:\n" + nav_content
            
            # 写入文件
            with open("nav_output.yaml", "w", encoding="utf-8") as f:
                f.write(final_output)
                
            print("-" * 30)
            print(final_output)
            print("-" * 30)
            print("✅ 成功！目录已生成到 nav_output.yaml")
            print("✅ 已自动过滤 .assets 等资源文件夹")
    else:
        print(f"❌ 错误：当前目录下找不到 '{DOCS_DIR}' 文件夹。")