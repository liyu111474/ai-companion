# 第三方依赖与资源

项目自身代码、叶片 SVG 插画和文档采用 [MIT License](LICENSE)。依赖及可选字体分别遵循各自许可证。

| 项目 | 用途 | 许可证及来源 |
| --- | --- | --- |
| Streamlit | 页面、控件和聊天界面 | [Apache-2.0](https://github.com/streamlit/streamlit/blob/develop/LICENSE) |
| OpenAI Python SDK | 调用 DeepSeek 兼容接口 | [Apache-2.0](https://github.com/openai/openai-python/blob/main/LICENSE) |
| Noto Sans SC / Noto Serif SC | 可选中文字体 | SIL Open Font License：[Sans](https://github.com/notofonts/noto-cjk/blob/main/Sans/LICENSE)、[Serif](https://github.com/notofonts/noto-cjk/blob/main/Serif/LICENSE) |

依赖通过 `requirements.txt` 安装，其发行包保留上游许可文件。本仓库没有打包这些依赖的源代码或字体文件；使用未安装 Noto 字体的电脑时会回退到系统字体。Streamlit 提供的图标由其自身发行与加载机制处理。

今后如随项目复制第三方图片、字体、文档、脚本或其他资源，须同时保留其许可与署名，并更新此文件和公开清单。
