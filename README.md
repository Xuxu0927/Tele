# Tele

通信圣经   来自旭虎 加油

## 本地 Python 环境

本项目使用项目内的标准虚拟环境 env，Python 版本统一记录在 .python-version（当前为 3.14.7），自动发布流程也读取此文件。已验证 MkDocs、Material 主题、实际配置的全部插件，以及 CustomTkinter 导航编辑器。

在 Tele 项目目录中运行：

~~~powershell
# 可选：激活环境
.\env\Scripts\Activate.ps1

# 本地预览站点
.\env\Scripts\python.exe -m mkdocs serve

# 本地构建，不发布网站
.\env\Scripts\python.exe -m mkdocs build

# 打开导航编辑器
.\env\Scripts\python.exe gui_nav.py

# 运行导航与评论回归测试
.\env\Scripts\python.exe -m unittest discover -s tests -v
~~~

直接指定 env 内的 Python 时无需激活。编辑器默认解释器已设置为 env/Scripts/python.exe；如果编辑器记住了以前的解释器选择，请手动选择一次此解释器。

使用已安装的独立 Python 重建环境：

~~~powershell
& 'C:/Users/28890/AppData/Local/Python/pythoncore-3.14-64/python.exe' -m venv env
.\env\Scripts\python.exe -m pip install -r requirements.txt
.\env\Scripts\python.exe -m pip check
~~~

依赖文件用途：

- requirements.txt：项目直接使用的依赖，已固定验证过的版本。
- requirements.lock.txt：本次 Windows + Python 3.14 环境全部依赖的精确版本；同平台、同 Python 版本复现时可安装此文件。
- CI 与本地使用 .python-version 指定的 Python 版本，安装 requirements.txt，并在发布前执行依赖检查和回归测试。升级 Python 时应同步重建本地 env。

## 文章与网站目录

网站使用 Awesome Nav 自动生成目录。日常在 docs 中新增、删除或移动 Markdown 后，直接预览或构建即可，无需先运行 exe 同步。文章内部的相对链接需要随文件位置调整。

需要调整顺序或显示名称时，双击 gui_nav.exe：

- 拖拽调整同级项目的先后顺序。
- 双击项目或点击“修改名称”，修改网站显示的名称，不改动文件名和文章内容。
- 点击“保存更新”后，下次预览或构建生效。绿色项目已经会自动出现在网站上，保存只是固定当前顺序和名称。

各目录的 .nav.yml 保存本层顺序和名称；docs/.nav.yml 设置全站自动收录、自然排序及单篇目录展平。新增文章自动排在该层已固定项目后。也可以直接编辑这些配置文件，保存时会生成 .bak 备份。

编辑器支持常规顺序、名称以及目录级隐藏和排序设置。如果手写了带筛选条件的复杂通配规则，请直接编辑对应的 .nav.yml；exe 会在保存前提示并保留原文件，避免隐藏内容被意外收录。

mkdocs.yml 只管理主题和插件，不再存放逐篇文章列表。hooks/auto_navigation.py 在构建时略过已经删除或移动的旧入口，不会改写 Markdown 或保存的排序规则。

## 重新打包导航编辑器

修改 gui_nav.py 后，需要重新打包才能让双击运行的 gui_nav.exe 使用新逻辑。先关闭正在运行的导航编辑器，再执行以下命令；打包工具仅用于生成 exe，不是网站运行依赖。

~~~powershell
.\env\Scripts\python.exe -m pip install pyinstaller==6.22.3
.\env\Scripts\python.exe -m PyInstaller --noconfirm --onefile --windowed --collect-all customtkinter --collect-all mkdocs_awesome_nav --distpath . --workpath build/pyinstaller --specpath build --name gui_nav gui_nav.py
~~~
