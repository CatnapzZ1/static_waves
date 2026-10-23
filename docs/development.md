# 本地开发

## 已验证环境

| 工具 | 实际版本/要求 |
| --- | --- |
| Hugo | 0.145.0-666444f0a52132f9fec9f71cf25b441cc6a4f355+extended linux/amd64 |
| Go | go1.27.0 linux/amd64；模块最低声明 1.23.0 |
| PaperMod | v0.0.0-20240915081152-a2eb47bb4b80，发布 v8.0 对应提交 |
| Python | 3.14.8；脚本使用 Python 3.10+ 语法 |
| PyYAML | 6.0.3，requirements-dev.txt 固定 |
| Node.js | v24.18.0，仅执行上游 Fuse 测试和 JS 语法检查 |
| Pillow | 12.3.0，仅素材处理时需要，已安装并实际使用 |
| Git | 2.56.0 |
| KaTeX / Mermaid | 固定 CDN 0.19.0 / 11.12.0；本次未在浏览器执行 CDN 渲染 |

没有 Node 前端依赖树，无 npm 构建步骤。Hugo 下载二进制，不需为构建 Hugo 安装 C 编译器；Go 用于 Hugo Modules。Hugo Extended 版本必须精确匹配，Go 校验最低版本，服务器请使用已验证的 Go 1.27.0。

## 首次安装与依赖

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements-dev.txt
./scripts/bootstrap.sh
```

bootstrap 仅支持 Linux amd64/arm64，下载 Hugo 0.145.0 Extended 和官方 checksum 清单并校验，只写项目 `.tools/`、`.cache/`。之后 `go mod download` 根据已提交 go.mod/go.sum 获取锁定模块，不追踪 master、不自动升级。需要联网。其他系统按 [Hugo 官方安装说明](https://gohugo.io/installation/) 安装相同 Extended 版本并放入 PATH。

所有项目 shell 入口自动 source env.sh，使用项目内模块缓存。若直接调用 Hugo/Go，先执行：

```bash
source scripts/env.sh
hugo version
go version
hugo mod graph
hugo mod verify
```

仅首次解析时使用了官方发布提交查询，之后已固定完整伪版本。不要执行 `hugo mod get -u` 或 `go get ...@latest`。空依赖时 Hugo 可能先获取最新开发主题；务必保留 go.mod/go.sum。本次实际遇到并修正了该问题。

## 日常命令

```bash
./scripts/serve.sh
./scripts/serve.sh -D
./scripts/new-post.sh my-new-post
./scripts/build.sh
./scripts/check-content.sh
./scripts/check-site.sh
./scripts/check-precommit.sh
./scripts/check-launch-readiness.sh
```

预览默认只绑定 127.0.0.1:1313，内存渲染、开发环境 noindex、不加载统计。build.sh 生产构建排除草稿、未来/过期文章；不复用预览目录。check-site 在 TemporaryDirectory 中构建正式输出和示例，不向 public 写入示例，退出后自动释放临时目录。

测试包括工具链、模块完整性、YAML 正确性与重复键、路由冲突、HTML 引用与 CSS 资源、核心 JSON/XML、示例/草稿隔离、原生 Fuse 中英文搜索、Archetype、封面、aliases、Git/显式 lastmod、完整 RSS、统计环境门控、反向提交检查、release 文件级模拟、Shell/JS 语法。外部网址连通性和浏览器可视布局不由这些静态测试证明。

## Git

本地 main 仓库已创建，未配置远程；项目使用已有 Git 身份创建初始化提交。启用 Hook：

```bash
git config core.hooksPath .githooks
git config --get core.hooksPath
```

Hook 读取 Git 暂存区 blob，检查整个即将提交的快照，不读工作区替代暂存版本。检查草稿、前置元信息、生成目录、本地环境文件、可识别私钥和明显凭据，失败给出文件和原因，不打印密钥，不改暂存区。删除文件会自然从快照排除；合并冲突被拒绝。

Hook 是本地保护措施，可被绕过，不是完整秘密扫描保障；提交前仍需人工检查。`.gitignore` 不会自动取消已跟踪文件。误跟踪时先审查，再针对单个文件使用 `git rm --cached <path>`；如果秘密已经公开，需要撤销/轮换秘密，单纯删除当前文件无效。不使用破坏性 reset/clean。

## 素材与常见问题

真实素材位于 brand-originals/，原始尺寸 Logo 1254×1254 RGBA、头像 1080×1080 RGB。manifest.json 记录原文件与发布副本 SHA256、大小、Favicon 裁剪范围；源文件未覆盖。图像导入脚本拒绝覆盖已有副本。再次处理先人工备份/迁移旧副本，确认新素材授权，再指定真实路径和裁剪坐标。

如需要重新处理，安装 `requirements-images.txt`。不需要 Pillow 也可直接构建现有网站。

- `hugo: command not found`：使用项目脚本，或 source scripts/env.sh。
- 无网络/DNS：在有网络的自己的终端运行 bootstrap，保留项目 .cache，不绕过环境权限。
- `listen ... operation not permitted`：当前沙箱禁止 socket，在自己的终端启动 serve.sh；本次无法完成浏览器验收。
- Git log 无提交：新仓库先人工创建一个空初始化提交；正式 clone 会自带历史。
- 数学/图表不显示：检查开关、代码围栏和浏览器 CDN 网络请求。不要把源码标为 safeHTML 来绕过问题。
- 本地检查 PASS、上线检查 FAIL：前者证明构建，后者要求真实域名与资料；按 checklist 补齐，不删除检查项。

## 人工升级流程

先开可选的短期功能分支并保存当前版本；查官方发行说明，选择具体稳定版本/提交。手动更新 Hugo 工具和 toolchain.json，精确更新模块版本，运行 hugo mod tidy 并审查 go.mod/go.sum。运行完整 check-site，在浏览器检查深浅色、代码复制、搜索、数学、图表和移动端，复核项目级模板与上游差异。更新版本文档后才提交。

不自动更新主题、不开自动升级 PR。未来有真实仓库后，可用 `go mod edit -module github.com/真实所有者/真实仓库` 修改本地模块标识并重新验证，不影响内容 URL。
