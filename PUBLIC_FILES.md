# 公开文件清单

此清单列出本次拟纳入版本管理和公开范围的文件。新增、删除或调整公开范围时，应同步检查 README 链接和验证记录。

## 范围

共 **22 个文件**。`.verification/` 只公开五份已审阅材料：应用审阅记录、浏览器检查结果、桌面截图、手机截图和完整运行资源副本启动截图。

项目本身采用 MIT，第三方资源说明见 [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md)。本地聊天、凭据、虚拟环境、备份、旧截图、压缩包、下载依赖及原始测试日志保持在忽略范围。

`.gitignore` 不会自动停止追踪已提交的文件，也不会在直接压缩整个工作目录时自动筛选文件。发布包应来自已审阅的版本文件。

## 完整列表

下列路径均相对于项目根目录，包含本清单自身。

```text
.gitignore
.streamlit/config.toml
.verification/app-review.md
.verification/desktop-full.png
.verification/installation-full.png
.verification/mobile-full.png
.verification/viewer-checks-full.json
AGENTS.md
LICENSE
PUBLIC_FILES.md
README.md
THIRD_PARTY_NOTICES.md
app.py
docs/DEVELOPMENT.md
docs/RELEASE_NOTES_v0.1.0.md
docs/RELEASING.md
requirements.txt
static/leaf.svg
style.css
tests/test_app.py
tests/test_installation.py
启动小叶子.cmd
```

检查结果与验证边界见 [.verification/app-review.md](.verification/app-review.md)。本地文件变化不代表 GitHub 已更新。
