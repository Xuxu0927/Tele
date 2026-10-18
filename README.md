# Tele

通信圣经   来自旭虎 加油

## 本地 Python 环境

本项目已改用项目内的标准虚拟环境 env，基于独立安装的 Python 3.14.7。已验证 MkDocs、Material 主题、实际配置的全部插件，以及 CustomTkinter 导航编辑器。

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
- 现有 CI 使用自己的 Python 版本，继续安装 requirements.txt。

旧的 .conda 环境已由 env 替代。site_env.yaml 仅保留为历史 Conda 导出文件，不再作为当前环境的安装说明。旧环境包清单、原配置备份、迁移状态和构建日志保存在 .environment-migration/20261017/，该目录与 env 均已加入 Git 忽略。
