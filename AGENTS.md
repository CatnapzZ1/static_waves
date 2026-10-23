# 项目开发约定

- 使用 Hugo Extended、Go Modules、PaperMod、Goldmark、Chroma、KaTeX、Mermaid 和原生 Fuse；不要替换主题或引入前端框架。
- 不修改模块缓存中的 PaperMod 上游源码；优先原生配置，必要扩展仅放 layouts/、assets/。保留默认 Footer 和第三方版权声明。
- 正式文章仅用 content/posts/<slug>/index.md，YAML 字段及五个主分类遵守 docs/content-guide.md。examples/ 永不挂载到生产内容。草稿不能提交到公开仓库。
- 不编造个人资料、域名、社交链接、素材或测试结果。缺失外部条件写入验收报告。
- 不记录私钥、Token、密码或证书私钥。提交前检查暂存快照；不要只检查工作区。
- 未获得明确授权不得访问/修改 VPS、创建远程 GitHub 仓库、push、部署、改 DNS。部署文件默认只是准备文件。
- 不使用 git reset --hard、git clean -fd、覆盖用户文件或其他破坏性操作。对超出当前授权的敏感操作先取得明确授权。
- 保持 main 为长期分支；不引入自动部署、自动依赖升级、评论服务或外部字体。
- 修改后运行相关检查；完整验收入口 scripts/check-site.sh。就绪检查有意因待配置内容失败，不得隐藏失败项。
- 文档、toolchain.json、go.mod/go.sum 与实现同步。升级必须人工决定并通过隔离示例验证。
