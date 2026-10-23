#!/usr/bin/env python3
"""Launch gates are distinct from local developer tests."""
import importlib.util, pathlib, re, subprocess, sys, tempfile, urllib.parse
import yaml
ROOT=pathlib.Path(__file__).resolve().parent.parent
spec=importlib.util.spec_from_file_location('validate', ROOT/'scripts/validate.py')
v=importlib.util.module_from_spec(spec);spec.loader.exec_module(v)
failures=[]
def result(ok, label):
    print(('PASS ' if ok else 'FAIL ')+label)
    if not ok: failures.append(label)
def filled(value):
    return isinstance(value,str) and bool(value.strip()) and not re.search(r'待填写|CHANGE_ME|your-domain|example\.com|username|TODO',value,re.I)
c=yaml.safe_load((ROOT/'hugo.yaml').read_text());params=c['params'];base=urllib.parse.urlparse(c['baseURL'])
result(base.scheme=='https' and bool(base.hostname) and base.path=='/' and not base.query and not base.fragment and not base.username and not base.port and not re.search(r'localhost|example\.(com|org|net)|\.(invalid|test|local)$',base.hostname or ''), '真实 HTTPS 根域名 baseURL')
for key,value in [('正式博客名称',c.get('title')),('Logo 文字',params.get('label',{}).get('text')),('站点描述',params.get('description')),('首页简介标题',params['homeInfoParams'].get('Title')),('首页简介正文',params['homeInfoParams'].get('Content')),('关于页面',(ROOT/'content/about.md').read_text())]:
    result(filled(value),key)
for key,ref in [('Logo',params['label'].get('icon')),('头像',params.get('avatar')),('Favicon',params['assets'].get('favicon')),('16px icon',params['assets'].get('favicon16x16')),('32px icon',params['assets'].get('favicon32x32')),('Apple icon',params['assets'].get('apple_touch_icon')),('Safari icon',params['assets'].get('safari_pinned_tab'))]:
    result(isinstance(ref,str) and ref.startswith('/') and (ROOT/'static'/ref.lstrip('/')).is_file(),key+' 静态文件')
for icon in params.get('socialIcons',[]):
    ref=icon.get('url','');parsed=urllib.parse.urlparse(ref)
    valid=ref=='/index.xml' or (filled(ref) and (parsed.scheme=='https' and bool(parsed.netloc) or parsed.scheme=='mailto' and bool(re.fullmatch(r'[^@\s]+@[^@\s]+\.[^@\s]+',parsed.path))))
    result(valid, '社交链接配置 '+icon.get('name','unknown'))
    if valid and ref!='/index.xml':print('MANUAL 确认社交链接实际归属且可访问（自动检查仅验证格式）')
result(not any(c.get(k,False) for k in ('buildDrafts','buildFuture','buildExpired')),'正式构建排除草稿/未来/过期文章')
result(c.get('outputs',{}).get('home')==['HTML','RSS','JSON'],'HTML/RSS/JSON 输出配置')
result((ROOT/'LICENSE').is_file() and 'MIT License' in (ROOT/'LICENSE').read_text(),'MIT 源码许可证')
result((ROOT/'LICENSE-CONTENT.md').is_file() and 'CC BY-NC-SA 4.0' in (ROOT/'LICENSE-CONTENT.md').read_text(),'文章许可说明')
files={str(f.relative_to(ROOT)):f.read_bytes() for f in (ROOT/'content').rglob('*') if f.is_file()}
result(not v.report(v.content_errors(files),'内容模型'), '内容规范通过')
try:
    staged,modes=v.git_files()
    result(not v.report(v.secret_errors(staged,modes)+v.content_errors(staged,True),'仓库暂存快照与已跟踪内容'), '无可识别的敏感文件/草稿被纳入版本管理')
except (OSError,ValueError,subprocess.CalledProcessError) as e:result(False,str(e))
token=params.get('cloudflareAnalyticsToken','')
if not token:print('MANUAL Cloudflare Web Analytics 尚未配置、尚未启用')
else:
    result(bool(re.fullmatch(r'[a-fA-F0-9]{32}',token)),'Analytics beacon token 格式')
    print('MANUAL Cloudflare 仪表盘实际收到统计数据')
if '--config-only' not in sys.argv:
    tools=subprocess.run([str(ROOT/'scripts/check-toolchain.sh')],cwd=ROOT)
    result(tools.returncode==0,'固定工具链')
    if tools.returncode==0:
        with tempfile.TemporaryDirectory(prefix='blog-launch-check-') as temp:
            built=subprocess.run(['hugo','--environment','production','--destination',temp,'--buildDrafts=false','--buildFuture=false','--buildExpired=false'],cwd=ROOT)
            result(built.returncode==0,'正式构建')
            if built.returncode==0:result(not v.report(v.output_errors(temp,c['baseURL'],False),'正式产物/素材/链接/隔离'),'构建输出完整')
for item in ['DNS 真实解析','Nginx 安装与 nginx -t','HTTPS 证书及 Certbot 续期演练','实际 SSH 端口、UFW 与云防火墙','GitHub 只读 Deploy Key','VPS 目录权限','正式发布及回滚演练','浏览器深浅色/移动端/公式/图表/代码复制']:
    print('MANUAL '+item)
print('N/A 初始没有正式文章：不是上线阻断条件')
print('FAIL 尚未具备上线条件' if failures else 'PASS 自动上线检查通过；人工项仍需独立签字确认')
sys.exit(bool(failures))
