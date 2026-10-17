# 小叶子 · AI伴侣

一个使用 Streamlit 和 DeepSeek 构建的日常陪伴聊天应用。雾绿界面、叶片插画，让聊天留一点轻松的空间。

![小叶子桌面预览](docs/desktop.png)

## 功能

- 流式显示 AI 回复，支持自定义伴侣昵称和性格。
- 本地保存聊天记录，可切换、新建和删除会话。
- 提供三个开场话题，点击后填入输入框，由你确认发送。
- 回复失败时保留用户消息，可以重新请求回复。
- 手机端自动收起侧边栏，适配窄屏阅读。

## 本地运行

已在 Python 3.13、Streamlit 1.65.0、OpenAI Python SDK 3.29.0 下验证。

```powershell
git clone git@github.com:liyu111474/ai-companion.git
cd ai-companion
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python -m streamlit run app.py
```

也可以在 GitHub 点击 **Code → Download ZIP**，完整解压项目后，在项目目录执行安装和启动命令。Windows 用户安装依赖后，可以双击 `启动小叶子.cmd`。

**请保留整个项目结构。** `app.py` 会读取旁边的 `style.css` 和 `static/leaf.svg`，只复制 Python 代码会因缺少资源而无法启动。从项目目录启动，才能加载 `.streamlit/config.toml` 中的主题配置。

## 连接 DeepSeek

打开侧边栏「连接设置」，填写自己的 DeepSeek API 密钥即可聊天。输入框中的密钥只用于当前浏览器会话，不写入聊天记录。

也支持在启动前设置环境变量：

```powershell
$env:DEEPSEEK_API_KEY = "你的 DeepSeek API 密钥"
python -m streamlit run app.py
```

或者使用 `.streamlit/secrets.toml` 中的 `DEEPSEEK_API_KEY` 配置。真实密钥、环境文件和聊天记录已列入 `.gitignore`，应保留在本机。

模型使用 `deepseek-flash`，接入方式见 [DeepSeek 官方文档](https://api-docs.deepseek.com/guides/codex)。

## 项目结构

```text
ai-companion/
├── app.py                 # 页面、会话管理和 AI 回复
├── style.css              # 布局和轻柔阴影
├── requirements.txt       # 依赖版本
├── 启动小叶子.cmd           # Windows 启动入口
├── .streamlit/config.toml  # 颜色、字体和圆角
├── static/leaf.svg        # 欢迎页插画
├── docs/                  # 页面预览
└── tests/test_app.py       # 行为回归测试
```

聊天记录在运行后写入 `sessions/`，该目录不会上传到 GitHub。旧记录只要包含 `messages`、`nick_name` 和 `nature` 字段，就可以复制到该目录继续使用。

## 界面

背景采用雾绿白 `#F5F8F5`，强调色为松针绿 `#315C46`。正文优先使用 Noto Sans SC，欢迎标题优先使用 Noto Serif SC；未安装时使用系统回退字体。

[查看手机预览](docs/mobile.png)

## 测试

```powershell
python -m unittest discover -s tests -v
```

12 项回归测试覆盖会话切换、新建与删除、角色设定、损坏记录、回复失败重试、流式中断和磁盘保存失败。测试使用临时目录和 API 测试替身，不读取真实记录、不调用付费模型。

已使用 Chrome 检查 1440px 桌面和 390px 手机宽度。真实服务连通性需要有效的 DeepSeek 密钥。
