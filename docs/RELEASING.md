# GitHub 发布流程

目标仓库：`liyu111474/ai-companion`，公开仓库，现有远程名称为 `origin`，默认分支为 `main`。不要把其他项目的提交号或 `v0.1.0` 状态当成本仓库的状态。

## 先检查现状

```powershell
git status --short --branch
git diff --stat
git remote -v
git tag --list
gh auth status
gh release list --repo liyu111474/ai-companion
```

复用已有配置，不重新初始化或建仓。检查远端是否有新提交；遇到分歧先核对内容，保留工作区，不直接强推。

若 CLI 尚未登录，执行 `gh auth login`，选择 GitHub.com、HTTPS、浏览器登录，并允许 CLI 配置 Git 凭据。设备码、密码、二次验证及浏览器授权由用户本人操作。完成后用 `gh auth status` 复核。已有可用 SSH 远程无需因为 CLI 使用 HTTPS 就改写。

## 准备可审阅的版本

1. 完成 [开发验收](DEVELOPMENT.md)，核对 README 的安装方法、示例和实际验证范围。
2. 按 [PUBLIC_FILES.md](../PUBLIC_FILES.md) 核对文件，检查密钥、个人信息、绝对路径、临时文件和截图元数据；保留许可证。
3. 更新五份公开验证材料，检查 README 和文档的项目内链接。发布包只包含审核过的版本文件，不直接压缩整个工作目录。
4. 检查拟用标签和 Release 是否已存在，准备版本标题与说明。已有标签不能直接覆盖。
5. 把仓库名称、公开性、拟提交的文件范围、`origin/main`、版本号及具体操作交给用户确认。

本地修改、验收、复制到另一本地目录均不表示 GitHub 已更新。提交、推送和发布均在确认范围后执行。

## 获得授权后执行

以下以本仓库首次发布 `v0.1.0` 为例；执行时必须再次确认标签未被使用。只 `git add` 公开清单中已检查的文件，并用 `git diff --cached --stat`、`git diff --cached --check` 复核。

```powershell
git commit -m "Prepare first verified release"
git push origin main
git tag -a v0.1.0 -m "Xiaoyezi AI companion v0.1.0"
git push origin refs/tags/v0.1.0
gh release create v0.1.0 --verify-tag --repo liyu111474/ai-companion --title "v0.1.0 · 小叶子 AI 伴侣" --notes-file docs/RELEASE_NOTES_v0.1.0.md
```

已有 `v0.1.0` 时，为新改动选择新的版本号并创建对应说明文件。推送或发布报错后先读取实际状态，避免重复创建或覆盖已成功的操作。

## 发布后确认

确认远端提交与本地一致，核对公开文件、README 图片和文档链接，查看 `gh release view` 的版本及网页地址。向用户明确报告完成的是提交、推送还是 Release，附实际地址。尚未完成的步骤如实说明。
