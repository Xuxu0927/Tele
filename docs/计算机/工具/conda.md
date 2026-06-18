# conda教程

## 常用命令

| 操作                 | 命令                                        |
| -------------------- | ------------------------------------------- |
| 创建新环境           | `conda create -n 环境名 python=3.x`         |
| 激活/切换环境        | `conda activate 环境名`                     |
| 退出当前环境         | `conda deactivate`                          |
| 查看所有环境         | `conda env list` 或 `conda info --envs`     |
| 删除环境             | `conda env remove -n 环境名`                |
| 克隆环境             | `conda create -n 新环境名 --clone 原环境名` |
| 导出环境（用于复现） | `conda env export > environment.yml`        |
| 从 yml 文件创建环境  | `conda env create -f environment.yml`       |

| 操作                   | 命令                              |
| ---------------------- | --------------------------------- |
| 安装包                 | `conda install 包名`              |
| 指定版本安装           | `conda install 包名=版本号`       |
| 从指定 channel 安装    | `conda install -c channel名 包名` |
| 卸载包                 | `conda remove 包名`               |
| 更新包                 | `conda update 包名`               |
| 更新所有包             | `conda update --all`              |
| 查看当前环境已安装的包 | `conda list`                      |
| 搜索可用的包           | `conda search 包名`               |
| 查看包信息             | `conda info 包名`                 |

| 操作                 | 命令                                    |
| -------------------- | --------------------------------------- |
| 清理缓存（释放空间） | `conda clean --all`                     |
| 更新 conda 自身      | `conda update conda`                    |
| 查看 conda 版本      | `conda --version`                       |
| 查看帮助             | `conda --help` 或 `conda 子命令 --help` |





## 配置环境

---

### 第一步：安装 Miniconda / Anaconda

1. [Index of /anaconda/miniconda/ | 清华大学开源软件镜像站 | Tsinghua Open Source Mirror](https://mirrors.tuna.tsinghua.edu.cn/anaconda/miniconda/)
2. 安装时**勾选** “Add Miniconda to my PATH environment variable”
3. 安装完成后，**重启命令行**

---

## 第二步：创建 Conda 虚拟环境

执行：

```bash
conda create -n py_learn python=3.11 -y
```

激活环境：

```bash
conda activate py_learn
```

此时终端提示符前应显示 `(py_learn)`。

---

## 第三步：在 VSCode 中配置使用该环境

1. **打开 VSCode**，打开你的项目文件夹。
2. 安装python扩展
3. **选择 Python 解释器**：
   - 按 `Ctrl+Shift+P`，输入 `Python: Select Interpreter`。
   - 从列表中选择 `py_learn` 环境（路径类似 `C:\Users\你的用户名\miniconda3\envs\py_learn\python.exe`）。
4. **开启终端自动激活环境**：
   - 按 `Ctrl+,` 打开设置，搜索 `python.terminal.activateEnvironment`，勾选为 `true`。
5. **新建终端**（`` Ctrl+` ``），此时应自动激活 `py_learn` 环境（提示符前出现 `(py_learn)`）。

