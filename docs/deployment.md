# Ubuntu VPS 部署与恢复（准备文件，尚未执行）

目标是用户已有 Ubuntu Server 26.04 LTS 64-bit VPS，使用现有普通 SSH 用户人工发布。**本次没有登录 VPS，没有安装 Nginx/Certbot，没有改 DNS/UFW，没有创建 GitHub 仓库或 push，没有签发证书。以下操作只供后续获得明确部署授权后执行。**

## 路径与权限

| 路径 | 用途及权限 |
| --- | --- |
| /opt/blog/source/ | Git 完整源码，普通部署用户所有，0700，不向 Nginx 暴露 |
| /opt/blog/scripts/ | 从 deploy/ 安装的已审阅脚本，普通用户所有，0700 |
| /opt/blog/logs/ | 发布/回滚日志与互斥锁，普通用户所有，0700 |
| /opt/blog/deploy.env | 实际域名及仓库地址，0600，不进 Git |
| /var/www/blog/releases/ | 版本化静态产物，部署用户所有，0755 |
| /var/www/blog/current | 当前版本符号链接，原子替换 |
| /var/www/blog/previous | 上一可回滚版本符号链接，清理保护 |
| /var/www/letsencrypt/ | 独立 ACME HTTP-01 Webroot，root 管理，Nginx 可读 |
| /etc/nginx/sites-available/blog.conf | 管理员安装的实际站点配置 |

Nginx 的 www-data 只需读静态文件和遍历目录，没有源码、脚本或发布目录写权限。构建和切换无需 sudo。禁止 chmod 777。

后续先核实 `id`、`uname -m`、`lsb_release -a`、现有目录所有权；若路径已有其他用途立即停止并安排迁移，不能直接覆盖。以下变量必须填写真实值：

```bash
BLOG_DEPLOY_USER='填写现有普通SSH用户名'
BLOG_DOMAIN='填写真实根域名'
BLOG_REPOSITORY='git@github.com:真实所有者/真实仓库.git'
```

管理员首次准备目录（只能对确认属于本项目的新目录执行）：

```bash
sudo install -d -o "$BLOG_DEPLOY_USER" -g www-data -m 0755 /opt/blog /var/www/blog /var/www/blog/releases
sudo install -d -o "$BLOG_DEPLOY_USER" -g www-data -m 0700 /opt/blog/source /opt/blog/scripts /opt/blog/logs
sudo install -d -o root -g www-data -m 0755 /var/www/letsencrypt
```

日常以该普通用户登录，不新建 blogdeploy，不用 root 运行 deploy.sh。脚本会拒绝 root、异常路径所有者和错误符号链接。

## 软件与固定工具链

由管理员人工安装系统依赖；不在部署脚本执行系统升级：

```bash
sudo apt update
sudo apt install nginx certbot ufw git curl python3 python3-venv ca-certificates logrotate util-linux
```

先查看现有版本，避免覆盖已有 Go。固定已验证版本：Go **1.27.0**、Hugo Extended **0.145.0**。Go 从 [官方发行页](https://go.dev/dl/) 选择与 VPS 架构一致的包，下载后对照官方 SHA256，核对成功后安装到管理员选定的目录并配置 PATH。比如 amd64 文件名为 `go1.27.0.linux-amd64.tar.gz`；ARM 使用 arm64。不要盲目把 archive 解压覆盖已有 /usr/local/go；存在旧版本时先规划保留旧安装目录和回退方式。

Hugo 由项目 bootstrap.sh 安装到 /opt/blog/source/.tools，自动校验官方下载 checksum；Go 模块使用源码内的 go.mod/go.sum。服务器如要完整跑 check-site，还需已验证 Node.js 24.18.0；常规发布只依赖 Hugo/Go/Python/Bash/Git/curl/flock，不需要 Node 前端构建。

安装源码后执行：

```bash
cd /opt/blog/source
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements-dev.txt
./scripts/bootstrap.sh
./scripts/check-toolchain.sh
```

PaperMod 精确锁定 `v0.0.0-20240915081152-a2eb47bb4b80`。版本升级必须先在本地完整测试，再调整服务器工具，不能在服务器追最新开发分支。

## GitHub Public 仓库与只读 Deploy Key

后续由用户创建真实仓库并人工推送本地 main，本次未执行。公开仓库仅存可公开源码、正式文章和有权公开的素材。私钥、证书、未发表草稿不属于公开源码。

在 VPS 以现有普通用户创建专用仓库密钥，先确认目标 key 文件不存在：

```bash
install -d -m 0700 "$HOME/.ssh"
test ! -e "$HOME/.ssh/blog_readonly"
ssh-keygen -t ed25519 -f "$HOME/.ssh/blog_readonly" -C 'blog read-only deploy key'
chmod 600 "$HOME/.ssh/blog_readonly"
```

只把 `.pub` 公钥添加到该仓库 Settings → Deploy keys；**不要勾选 Allow write access**。可为密钥设置口令并用 ssh-agent 管理。不要显示或复制私钥到仓库和日志。首次连接前对照 [GitHub 官方 SSH 指纹](https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/githubs-ssh-key-fingerprints) 验证主机密钥，不关闭 StrictHostKeyChecking。

以真实变量在空 source 目录 clone，并仅给该仓库设置用钥方式：

```bash
GIT_SSH_COMMAND="ssh -i $HOME/.ssh/blog_readonly -o IdentitiesOnly=yes" git clone "$BLOG_REPOSITORY" /opt/blog/source
cd /opt/blog/source
git config core.sshCommand "ssh -i $HOME/.ssh/blog_readonly -o IdentitiesOnly=yes"
git ls-remote origin HEAD
```

clone 应保留完整历史以便 Git lastmod。检查访问为只读，Github SSH 鉴权成功不代表有 shell（不要求获得 GitHub shell）。不要把密钥字符串写到 deploy.env。

## 安装部署脚本与配置

审阅后将以下文件安装到 /opt/blog/scripts，脚本不随 fetch 自动自我更新，后续脚本升级需重新人工审阅安装：

```bash
cd /opt/blog/source
install -m 0700 deploy/deploy.sh deploy/rollback.sh deploy/common.sh deploy/releases.py /opt/blog/scripts/
install -m 0600 deploy/deploy.env.example /opt/blog/deploy.env
```

编辑 /opt/blog/deploy.env，填写 `BLOG_DOMAIN` 和 `BLOG_REPOSITORY`。该文件是被 Bash source 的本地可信配置，只有部署用户/管理员应能修改。同步 hugo.yaml 的真实 HTTPS baseURL，必须与域名完全一致（带根路径 `/`）。在本地填写 title/label/简介/about 等资料并通过就绪检查，提交到源码仓库；不要仅在 VPS 私自改已跟踪文件。

## DNS、Nginx 与首次证书

真实根域名 A/AAAA 必须指向可到达的服务器。只有已准备好 IPv6 才保留 AAAA。HTTP-01 需要公网 80/TCP 通向本机 challenge 路径，云防火墙、UFW 和可能的反向代理均需检查。先使用 HTTP 模板，不能在证书不存在时直接启用 HTTPS 模板。

将 `deploy/nginx/blog-http.conf` 复制为待审阅文件，把 YOUR_DOMAIN 替换为真实域名，安装为 `/etc/nginx/sites-available/blog.conf`。确认现有站点没有 server_name 冲突，再创建 sites-enabled 链接，不覆盖用户现有配置：

```bash
sudo ln -s /etc/nginx/sites-available/blog.conf /etc/nginx/sites-enabled/blog.conf
sudo nginx -t
sudo systemctl reload nginx
```

只有 nginx -t 成功后才能执行下一条 reload。若服务尚未启动则先 `sudo systemctl start nginx`。HTTP 模板只服务 challenge，其余返回 503，避免提前公开未验收内容。

设置真实邮箱变量后申请证书：

```bash
BLOG_CERT_EMAIL='填写真实邮箱'
sudo certbot certonly --webroot -w /var/www/letsencrypt -d "$BLOG_DOMAIN" --email "$BLOG_CERT_EMAIL" --agree-tos
sudo certbot certificates
```

确认 fullchain.pem/privkey.pem 存在，证书名称与域名一致，再把 `blog-https.conf` 中所有 YOUR_DOMAIN 替换后安装为 blog.conf，备份原配置，运行 nginx -t，成功后 reload。如果证书名称带后缀，按 certbot certificates 的实际路径调整，不猜测。

HTTPS 模板根目录 `/var/www/blog/current`，HTTP 重定向到固定 HTTPS 根域名；ACME 路径仍独立开放。静态资源缓存七天，HTML/JSON/XML/发布标识要求重新验证；无效路径返回 404，不做 SPA 回退。设置 nosniff、同源 frame 和 Referrer-Policy；未启用 HSTS preload，首次稳定后才考虑 HSTS。KaTeX/Mermaid 与主题原生 inline script 需要兼容的 CSP，本模板没有未经测试的强制 CSP。

## 续期

安装成功后 reload hook：

```bash
sudo install -m 0755 deploy/certbot/reload-nginx.sh /etc/letsencrypt/renewal-hooks/deploy/blog-reload-nginx
systemctl list-timers --all
systemctl status certbot.timer
sudo certbot renew --dry-run
```

检查系统包实际配置的 timer 或 cron，避免重复调度。如果没有已生效续期机制，再由管理员启用包提供的 certbot.timer：`sudo systemctl enable --now certbot.timer`。证书自动续期符合要求，**不是**系统自动升级。成功续期才由 deploy hook 运行 nginx -t 并 reload；dry-run 默认不会运行 deploy hook，需按已安装 Certbot 版本确认 `--run-deploy-hooks` 支持后再单独验证。

诊断查看 `journalctl -u certbot.service`、`/var/log/letsencrypt/letsencrypt.log`、DNS、80 端口和 webroot 文件访问。本次未运行这些命令，不能宣称证书或续期已成功。[Certbot Webroot/续期官方说明](https://eff-certbot.readthedocs.io/en/stable/using.html#webroot)。

## UFW：先保证 SSH 通路

SSH 端口未知，不能假设 22。先用已有会话查看实际 sshd 配置和监听地址，考虑 systemd socket、NAT/云控制台实际映射；同时检查当前规则和云防火墙。保留当前会话，并准备第二条 SSH 登录验证和云控制台恢复入口。

```bash
sudo sshd -T
sudo ss -lntp
sudo ufw status verbose
```

由管理员确认实际端口后才设置变量并添加规则：

```bash
BLOG_SSH_PORT='填写实际SSH端口'
sudo ufw allow "$BLOG_SSH_PORT/tcp"
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw default deny incoming
sudo ufw default allow outgoing
sudo ufw status numbered
```

只有确认第二条 SSH 会话仍能连接、必要端口已允许、云防火墙一致后，才人工执行 `sudo ufw enable`。对已有规则先评估其他用户/服务，不擅自删除。此任务不改变 SSH 认证、root 登录、IP 白名单，不安装 Fail2ban。[Ubuntu 防火墙说明](https://ubuntu.com/server/docs/how-to/security/firewalls/)。

## 人工发布与失败处理

在真实配置、HTTPS 和本地就绪检查完成后，管理员通过 SSH 登录，用现有普通用户主动执行：

```bash
/opt/blog/scripts/deploy.sh
```

脚本锁定 `/opt/blog/logs/deployment.lock`，deploy 和 rollback 共享锁，防止并发。检查 source 位置、main 分支、干净工作树和真实 origin，再 fetch/fast-forward main；不会强制 reset。检查固定 Hugo、Go 最低版本、模块完整性、内容规范和配置就绪。构建到新 release（UTC 时间 + Git 短提交 + 随机串），检查产物与站内资源后标记 ready，并用同目录临时符号链接加 os.replace 原子切换 current。新构建失败不触碰当前站点，保留失败目录及日志供排查。

激活后 curl 使用 `--resolve domain:443:127.0.0.1` 直查本机 Nginx，保留正常证书校验；比对 release-id.txt 并检查首页、搜索、RSS、Sitemap、Logo/头像/Favicon，避免代理缓存让错误版本看似通过。公网 DNS 和端到端访问仍需人工另查。

任何关键失败都非零退出；切换前保存 current 和 previous，失败时先恢复 current，再恢复原来的 previous 并检查旧版本，保证默认回滚目标不丢失；首次发布无旧版本则移除本次 current 链接，明确失败，不伪称回滚到不存在的网站。进程被 SIGINT/SIGTERM 中断也触发恢复；SIGKILL、机器断电无法运行 trap，应人工检查 current、previous 和日志。

只有线上检查成功后才清理：最多保留 current + previous + 最近其他版本，总计五个。清理严格校验 release ID、标记、路径、所有权与无符号链接；绝不删除 current/previous，不删除未知目录。发现异常则警告停止清理，此时可能暂时多于五个，宁可保留也不冒险删文件。清理失败不撤销已成功网站。

## 手动回滚

```bash
/opt/blog/scripts/rollback.sh
/opt/blog/scripts/rollback.sh 20261023T120000Z-abcdef012345-12345678
```

第二条只是 ID 格式示例，必须换成实际已有 ready release。默认回到 previous。回滚也持锁、原子切换、检查 HTTPS；失败恢复回滚前版本，不清理历史。回滚只切换静态文件，不强行回退源码工作树；再次发布前先在 Git 上明确选择修复策略并同步 main。

## 日志、手动维护与恢复

部署/回滚终端实时输出并保存到 `/opt/blog/logs/deploy-*.log`、`rollback-*.log`，包含时间、release、步骤和结果，不开启 set -x，不输出私钥或 token。把 logrotate.conf 的 DEPLOY_USER 替换为真实用户后由管理员安装到 `/etc/logrotate.d/blog`，运行 `sudo logrotate --debug /etc/logrotate.d/blog` 检查。每周轮转、最多 12 份、10MB 阈值、压缩；轮转依赖系统实际调度，不是脚本自身定时任务。

Nginx 访问/错误日志分别在 `/var/log/nginx/blog.access.log` 和 blog.error.log，使用发行版 nginx 日志轮转配置；先确认 `/etc/logrotate.d/nginx` 覆盖这些路径，避免重复配置。检查：`sudo nginx -t`、`journalctl -u nginx`、`curl -I https://真实域名/`。

系统与软件更新由用户手动管理。先查看更新、阅读版本兼容性，在本地测试 Hugo/PaperMod 升级，保留回退工具后再维护 VPS。不启用 unattended-upgrades、不启用自动重启、不关闭已有用户更新机制、不在 deploy.sh 整体升级系统。无需持续监控、自动通知、Webhook、Actions 或定时发布。

备份以 GitHub 已提交源码为主。**未提交草稿不受 GitHub 保护**；SSH/TLS 私钥和部分 VPS 私有配置也不在公开仓库，需要用户自行安全保管，恢复时可能重新生成密钥和申请证书。本项目不增加全盘快照、对象存储、数据库或异地备份服务。

从全新 VPS 恢复：核对用户/SSH/架构 → 安装系统依赖及固定 Go → 建立目录权限 → 新建/配置只读 Deploy Key → 完整 clone 源码 → 安装 Python/Hugo/锁定模块 → 恢复真实 deploy.env 与审阅脚本 → 核对 DNS → HTTP Webroot → 签发 HTTPS → HTTPS Nginx → 续期和 UFW → 执行首次部署 → 公网验证并回滚演练。源代码可重建全部静态网站，无数据库迁移；缺失密钥和私有配置必须人工重新配置。

Nginx 路径行为以 [官方 try_files 文档](https://nginx.org/en/docs/http/ngx_http_core_module.html#try_files) 为参考，最终必须在实际机器运行 nginx -t。

## Cloudflare Web Analytics

在 Cloudflare dashboard 的 Web Analytics 添加真实 hostname，在 Manage site 取得 beacon 代码中的 token，填写 hugo.yaml 的 `params.cloudflareAnalyticsToken`。这是 VPS 的普通网页脚本集成，不依赖 Cloudflare Pages 或改变托管平台。只填公开 beacon 标识，不填账户 API Token。生产构建后检查脚本与后台数据；开发预览不会加载。[官方非代理站点步骤](https://developers.cloudflare.com/web-analytics/get-started/)。当前配置为空，尚未启用。
