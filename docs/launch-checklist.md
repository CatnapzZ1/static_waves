# 首次上线检查

本地开发成功不代表正式上线就绪。执行 `./scripts/check-launch-readiness.sh`：关键条件不满足时返回 1。PASS 是已执行通过；FAIL 是未通过；MANUAL 是尚需实际人工验证；N/A 是当前不适用。人工项目未签字时不得宣称全面就绪。

## 自动检查

- [ ] baseURL 为真实 HTTPS 根域名，清除 your-domain.invalid/example.com 等占位符。
- [ ] title、params.label.text、description、homeInfoParams 和 about.md 填写真实信息。
- [x] 实际 Logo、头像、全部 Favicon 存在且构建引用正确。
- [x] 未知社交链接未渲染，目前只有 RSS；添加后检查 URL 格式并人工访问。
- [x] 正式构建排除草稿/未来/过期文章；示例不进入正式内容、索引或 Feed。
- [x] YAML/分类/标签/slug/aliases 规范通过。
- [x] 核心页面、RSS、Sitemap、JSON 生成并通过站内链接检查。
- [x] 源码 MIT、文章 CC BY-NC-SA 4.0、素材例外与上游版权文件存在。
- [x] 完整暂存快照秘密信息与草稿检查通过（仍非完整泄密防护）。
- [ ] Cloudflare Web Analytics：当前未配置、未启用，需人工验证真实统计接收。

目前没有正式文章属于 N/A，不是阻断原因。配置脚本中为教学保留的占位符不能机械全文替换；部署前另外完成以下人工项目。`--config-only` 只检查配置和仓库，不代替正式产物检查，供 deploy.sh 在构建前使用。

## 需要真实环境的人工检查

- [ ] 根域名 A/AAAA 与实际服务一致；不要保留不可达 IPv6。
- [ ] 真正的 GitHub Public 仓库只含可公开源码和已授权素材；正确设置只读 Deploy Key。
- [ ] 确认 VPS 普通用户名、Ubuntu 版本、架构和固定 Hugo/Go 安装。
- [ ] source/scripts/logs/releases/current 权限正确，www-data 无写权限。
- [ ] Nginx 已安装；HTTP Webroot challenge 可公网访问；nginx -t 通过。
- [ ] Let's Encrypt 证书已签发，切换 HTTPS 模板；HTTPS 证书链和域名正确。
- [ ] Certbot timer/cron 实际存在，renew --dry-run 与成功后 reload 正常。
- [ ] 确认实际 SSH 端口、当前 UFW、云防火墙与第二条 SSH 会话后再启用 UFW。
- [ ] 浏览器验证桌面/手机、明暗/系统主题/刷新记忆、导航、复制、公式、图表、封面、Favicon 和搜索结果跳转。
- [ ] Cloudflare dashboard 配置 beacon，生产浏览器收到脚本，后台出现数据；本地仍不加载。
- [ ] 执行首次手动部署、失败自动回滚和手动历史回滚演练。
- [ ] 查看部署日志、Nginx 日志及日志轮转；确认成功部署后仅保留当前加四个历史 release。
- [ ] 再次审阅 backup/rebuild 边界，未提交草稿不受 GitHub 保护。

本次未执行任何 VPS、DNS、正式 HTTPS、远程 GitHub 或发布操作。
