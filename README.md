# 个人技术博客

基于 Hugo Extended + PaperMod Home-Info 的中文技术博客。支持中英文文章、固定 slug、分类/标签、归档、Fuse 搜索、完整 RSS、SEO、Chroma、KaTeX 和 Mermaid。当前没有正式文章，示例仅放在 `examples/`。已经接入用户提供的猫咪 Logo 和头像。

本地工程已通过构建与自动检查；正式域名、博客名称和个人资料尚未填写，网站未上线。VPS 未修改。详细结果见 [验收报告](docs/acceptance.md)。

## 快速开始

需要 Bash、Git、Go、Python 3、Node.js（仅用于搜索测试，不用于站点打包）。首次联网准备：

```bash
cd /home/catnap/projects/static_blog/personal-blog
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements-dev.txt
./scripts/bootstrap.sh
./scripts/serve.sh
```

在浏览器打开 `http://localhost:1313/`。当前机器已由用户安装工具和模块，现有系统 PyYAML 也可使用；不必重复安装。沙箱可能禁止监听本地端口，此时在自己的终端启动预览。

```bash
./scripts/serve.sh -D
./scripts/new-post.sh understanding-transformers
./scripts/build.sh
./scripts/check-site.sh
./scripts/check-precommit.sh
./scripts/check-launch-readiness.sh
```

`build.sh` 输出到 `public/`，使用全新构建目录，之前由脚本生成的产物保存在忽略的 `.test-output/previous-public-*`，防止草稿预览遗留混入发布。自定义目标须为空（部署 release 标记除外）。不识别的旧 public/ 会拒绝覆盖。测试全部在临时目录构建，不污染正式内容。

就绪检查发现占位资料时返回非零，这是预期且真实的阻断，不等同于本地开发失败。不要发布开发预览目录。

## 版本和目录

已验证 Hugo Extended **0.145.0**、Go **1.27.0**、PaperMod **v0.0.0-20240915081152-a2eb47bb4b80**（发布 v8.0 对应提交）。具体依赖见 `toolchain.json`、`go.mod`、`go.sum`。

| 路径 | 用途 |
| --- | --- |
| hugo.yaml | 网站配置、首页简介、导航、社交链接、技术渲染 |
| content/posts/ | 正式 Leaf Page Bundle；初始只有栏目索引 |
| content/about.md | 待填写的关于页面 |
| archetypes/posts.md | 新建草稿模板 |
| examples/ | 隔离的基础与技术示例 |
| layouts/、assets/ | 项目级模板、CSS、JS 扩展 |
| static/images/site/ | 实际 Logo 和头像发布副本 |
| brand-originals/ | 原始素材及处理清单，不作为网站静态输出 |
| scripts/、.githooks/ | 校验、构建、预览和提交保护 |
| deploy/ | 未来 VPS 脚本、Nginx、Certbot、日志轮转模板 |
| docs/ | 开发、写作、架构、部署、验收说明 |

## 开发与版权

安装本地 Hook：`git config core.hooksPath .githooks`（本工作区已配置）。保留单一长期 main 分支，没有配置 GitHub 远程仓库。草稿只在本地；发布前将 `draft` 改为 `false`，完成检查后再暂存提交。

原创项目代码采用 [MIT](LICENSE)。已明确授权的原创文章采用 [CC BY-NC-SA 4.0](LICENSE-CONTENT.md)。Logo、头像及第三方素材不在默认开源许可范围内。项目中基于 PaperMod 的少量模板保留 [上游 MIT 声明](LICENSE-PAPERMOD)。

## 文档索引

- [架构](docs/architecture.md)
- [内容写作](docs/content-guide.md)
- [本地开发与升级](docs/development.md)
- [未来 VPS 部署与恢复](docs/deployment.md)
- [首次上线清单](docs/launch-checklist.md)
- [实际验收报告](docs/acceptance.md)
