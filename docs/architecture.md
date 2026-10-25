# 架构

网站由 Hugo Extended 生成静态文件。`hugo.yaml` 是唯一主配置；中文界面采用 zh 翻译，不配置多语言镜像或切换器，中英文正文可以共存。配置保持 Home-Info Mode，列表、导航、深浅色状态、阅读时间、复制、上一篇/下一篇、返回顶部和默认页脚由 PaperMod 提供。

页脚使用 PaperMod 原生 `params.footer.text` 显示用户提供的 `鲁ICP备2026058675号-1`，链接到 `https://beian.miit.gov.cn/`；保留自动年份、网站名称和 Hugo/PaperMod 致谢。该配置仅展示真实备案信息，不代表公网链路或服务器已完成发布。

## 工具与内容边界

Hugo 0.145.0 Extended + Go 1.27.0 已实际构建。模块名 `local.personal/blog` 不依赖虚构账户。主题使用 Hugo Modules，发布 v8.0 对应模块版本固定在 go.mod，go.sum 提供完整性校验；不使用 Submodule、不复制整个主题、不修改缓存。

文章使用 `content/posts/<bundle>/index.md`，URL `/posts/:slug/`。一个指定主分类，多个任意标签。日期优先级 `lastmod → :git → date`；新仓库至少需一个提交才能使用 Git 信息。普通未跟踪文章可以使用日期回退。示例和本地笔记不挂载到 content；主题资源和正式文章资源随 Hugo 分别处理。

## 小范围模板扩展

| 文件 | 原因 |
| --- | --- |
| partials/footer.html | 基于锁定的 PaperMod v8.0 模板，仅将 PaperMod 致谢链接改为普通文字；保留原生交互。升级主题时需对照上游同步此覆盖 |
| partials/home_info.html | 保留主题 Home-Info 骨架，仅添加可选头像 |
| _default/index.json | 仍供原生 Fuse 使用；仅索引 posts，描述进入 summary，空数组有效 |
| _default/rss.xml | 基于锁定主题模板保留完整 RSS 功能；仅订阅 posts，空站点安全 |
| partials/rss-content.html | RSS 中的 Markdown 图片和链接按文章永久地址补全为绝对 URL，保留页面 HTML 原样 |
| partials/extend_head.html | 按 math 开关加载 KaTeX，按 hook 输出加载 Mermaid，占位域名加 noindex |
| partials/extend_footer.html | 合法生产环境加载统计 |
| _default/_markup/render-codeblock-mermaid.html | HTML 转义图表源码，输出可检测的图表容器 |
| robots.txt | 开发/占位域名禁止抓取，正式域名输出 Sitemap |

其余模板继续使用原生 PaperMod。v8.0 的旧社交兼容分支会引用 Hugo 已移除的 `.Site.Social`；配置非空 `params.social` 映射但保持 twitter/facebook_admin 值为空，使用现代参数路径且不生成虚构社交账号。这是经过构建验证的兼容处理。

## 技术渲染与资源

Chroma 使用 class 样式与 PaperMod 原生明暗代码主题，不启用 Highlight.js。`UseHugoToc: true` 使 Hugo 的 H2/H3 目录范围实际生效，目录默认折叠。

代码复制按钮采用接近 ChatGPT 网页端的轻量图标样式：默认透明背景和 18px 细线双层方框，悬停/键盘聚焦才显示浅淡圆角背景，鼠标操作区域 32px、触屏操作区域 44px。PaperMod 代码块在两种主题下均为深色，因此按钮使用浅灰图标而非页面正文颜色。`assets/js/copy-button.js` 通过按页 defer 加载，增强主题已经创建的按钮，保留原生复制事件及翻译文本；主题反馈复制成功时切换为勾号，恢复时回到复制图标，同时同步无障碍标签和悬停提示。复制按钮扩展无需修改上游主题；页脚模板覆盖仅用于移除 PaperMod 致谢链接。

Goldmark Passthrough 保留 `\(...\)`、`\[...\]`、`$$...$$`。只有 `math: true` 页面加载固定 KaTeX 0.19.0 的 CSS/JS 和官方 SRI；信任模式关闭。公式字体是 KaTeX 自身必需资源，不是正文或中文在线字体服务。

Mermaid 11.12.0 固定 ESM CDN 版本，仅图表页引入；在不跨页缓存的 extend_head 中检测已渲染的 hook 容器（PaperMod v8.0 缓存 footer，不能把按页加载逻辑放在其中）；保持原始源码，监听 PaperMod 对 body.dark 的更改后串行重绘。使用 strict securityLevel，模板不将源码标为 safeHTML。图表仍需浏览器下载 CDN 依赖；离线只保留源码/提示，完整可视渲染不保证。没有全局前端构建框架。

系统字体、800px 正文、图片尺寸和表格/代码横向滚动放在 `assets/css/extended/site.css`。Logo 白色底衬帮助黑色图案在深色模式保持可辨；头像裁成正方形发布副本并圆形展示。保留原始素材和 SHA256 处理清单。

## 搜索、SEO 和统计

HTML、RSS、JSON 首页输出独立。搜索复用 PaperMod 的 Fuse.js、键盘交互和搜索页面，索引仅含正式 posts。首页 RSS 内容完整，不含关于页、草稿、示例。Canonical、Open Graph、Twitter Card、schema.org 继续使用主题；封面按 Page Bundle 相对路径工作，无封面不设置默认无效分享图。

`baseURL` 暂为 `https://your-domain.invalid/`，不具备上线 SEO 条件。Cloudflare Web Analytics 只在生产环境、非 Hugo Server、非占位域名且 token 已配置时插入 beacon；空配置完全省略。beacon token 是公开页面标识，**不是** Cloudflare API Token；不要把账户凭据放到这里。

## 权限和依赖文档

本项目没有数据库、评论、持续监控、自动升级和自动部署。部署脚本仅供后续人工在 VPS 上调用。源代码、未发布草稿、SSH/TLS 私钥具有不同的备份和公开边界，见部署文档。

官方资料：[Hugo Modules](https://gohugo.io/hugo-modules/)、[Hugo 数学](https://gohugo.io/content-management/mathematics/)、[PaperMod 功能](https://github.com/adityatelange/hugo-PaperMod/wiki/Features)、[PaperMod v8.0](https://github.com/adityatelange/hugo-PaperMod/releases/tag/v8.0)、[KaTeX 浏览器集成](https://katex.org/docs/browser.html)、[Mermaid](https://mermaid.js.org/config/usage.html)、[Cloudflare 非 Pages 站点集成](https://developers.cloudflare.com/web-analytics/get-started/)。这些资料用于核对实现，锁定版本的实际模块代码及本地测试是兼容性依据。
