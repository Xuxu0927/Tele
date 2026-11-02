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

网站目录由根目录 mkdocs.yml 的 nav 列表管理。新增、删除或移动 Markdown 后，打开 gui_nav.exe 扫描目录并点击“保存更新”，再预览或构建网站。文章内部的相对链接需要随文件位置调整。

普通文章直接存放在数学、英语、电子通信、计算机等大类目录中，PDF、图片与对应文章放在同一大类目录。电子通信/附：苏大资料库保留原有课程子文件夹及附件结构。docs/mkdocs 保存网站样式与主题模板。

- 拖拽调整同级项目的先后顺序，拖动时会提示放置位置。
- 双击项目或按 F2 修改网站显示名称，不改动文件名和文章内容。
- 绿色项目是尚未保存到网站导航的新增文章；点击“保存更新”或按 Ctrl+S 后加入目录。
- 可展开、收起全部目录，按 F5 重新扫描。保存后窗口保持打开，并显示保存结果。

编辑器使用浅色界面，并提供窗口淡入、拖拽提示和保存反馈。修改尚未保存时，关闭窗口或重新扫描前会提示。保存会生成 mkdocs.yml.bak 备份，并保留主题、插件等其他配置。

每个文件夹不再需要 .nav.yml，构建过程不使用自动导航插件或导航钩子。单篇文章文件夹会在网站导航中合并为一个入口。

## 重新打包导航编辑器

修改 gui_nav.py 或 navigation.py 后，需要重新打包才能让双击运行的 gui_nav.exe 使用新逻辑。先关闭正在运行的导航编辑器，再执行以下命令；打包工具仅用于生成 exe，不是网站运行依赖。

~~~powershell
.\env\Scripts\python.exe -m pip install pyinstaller==6.22.3
.\env\Scripts\python.exe -m PyInstaller --noconfirm --onefile --windowed --collect-all customtkinter --distpath . --workpath build/pyinstaller --specpath build --name gui_nav gui_nav.py
~~~
