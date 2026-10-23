#!/usr/bin/env python3
"""Shared YAML, staged-snapshot and built-site validators (stdlib + PyYAML)."""
import datetime as dt
import json
import pathlib
import re
import subprocess
import sys
import urllib.parse as url
import xml.etree.ElementTree as ET
from html.parser import HTMLParser
import yaml

CATEGORIES = {'技术研究', '工程实践', '学习笔记', '项目复盘', '随笔'}
RESERVED = {'/', '/posts/', '/tags/', '/categories/', '/archives/', '/search/', '/about/', '/index.json/', '/index.xml/', '/sitemap.xml/', '/robots.txt/', '/404.html/'}
MISSING_BRANDING = {'/favicon.ico', '/favicon-16x16.png', '/favicon-32x32.png', '/apple-touch-icon.png', '/safari-pinned-tab.svg'}

class StrictLoader(yaml.SafeLoader):
    pass

def mapping(loader, node, deep=False):
    result = {}
    for k, v in node.value:
        key = loader.construct_object(k, deep=deep)
        if key in result:
            raise ValueError(f'YAML 重复字段: {key}')
        result[key] = loader.construct_object(v, deep=deep)
    return result
StrictLoader.add_constructor(yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG, mapping)

def frontmatter(text):
    if not text.startswith('---\n'):
        raise ValueError('必须以 YAML Front Matter 开始')
    parts = re.split(r'^---\s*$', text, maxsplit=2, flags=re.M)
    if len(parts) != 3:
        raise ValueError('Front Matter 缺少结束分隔线')
    data = yaml.load(parts[1], Loader=StrictLoader)
    if not isinstance(data, dict):
        raise ValueError('Front Matter 必须是对象')
    return data

def valid_date(value):
    if isinstance(value, (dt.date, dt.datetime)):
        return True
    if not isinstance(value, str):
        return False
    try:
        dt.datetime.fromisoformat(value.replace('Z', '+00:00'))
        return True
    except ValueError:
        return False

def article_errors(path, text, forbid_draft=False):
    errors = []
    if not re.fullmatch(r'content/posts/[^/]+/index\.md', path):
        errors.append('正式文章必须使用 content/posts/<bundle>/index.md')
    try:
        fm = frontmatter(text)
    except (yaml.YAMLError, ValueError, TypeError) as e:
        return [str(e)], None
    for key in ('title', 'description', 'slug'):
        if not isinstance(fm.get(key), str) or not fm[key].strip():
            errors.append(f'{key} 必须为非空字符串')
    if not re.fullmatch(r'[a-z0-9]+(?:-[a-z0-9]+)*', str(fm.get('slug', ''))):
        errors.append('slug 必须为小写英文/数字/连字符')
    if not valid_date(fm.get('date')):
        errors.append('date 无效')
    if 'lastmod' in fm and not valid_date(fm['lastmod']):
        errors.append('lastmod 无效')
    cats = fm.get('categories')
    if not isinstance(cats, list) or len(cats) != 1 or not isinstance(cats[0], str) or cats[0] not in CATEGORIES:
        errors.append('categories 必须恰好包含一个允许的分类')
    tags = fm.get('tags')
    if not isinstance(tags, list) or any(not isinstance(t, str) or not t.strip() for t in tags):
        errors.append('tags 必须为字符串数组（允许空数组）')
    if type(fm.get('draft')) is not bool:
        errors.append('draft 必须是布尔值')
    elif forbid_draft and fm['draft']:
        errors.append('draft: true 不得提交到公开仓库')
    aliases = fm.get('aliases', [])
    if not isinstance(aliases, list):
        errors.append('aliases 必须为数组')
    else:
        for alias in aliases:
            if (not isinstance(alias, str) or not alias.startswith('/') or alias.startswith('//')
                or any(x in alias for x in ('?', '#', '..', '\\', '%')) or re.search(r'\s', alias)):
                errors.append(f'aliases 无效: {alias!r}；必须为站内绝对路径')
    if 'math' in fm and type(fm['math']) is not bool:
        errors.append('math 必须是布尔值')
    if 'cover' in fm:
        cover = fm['cover']
        if not isinstance(cover, dict) or not isinstance(cover.get('image'), str) or not cover.get('alt'):
            errors.append('cover 必须有 image 和 alt')
        elif not url.urlparse(cover['image']).scheme and not cover['image'].startswith('/') and cover.get('relative') is not True:
            errors.append('Bundle 相对封面必须设置 relative: true')
    # These Hugo controls can bypass the public URL/draft model.
    for key in ('url', 'type', 'layout', 'outputs', 'build', '_build', 'headless', 'publishDate', 'publishdate', 'expiryDate', 'expirydate'):
        if key in fm:
            errors.append(f'正式文章不允许覆盖 {key}；使用 slug、aliases、date 和 draft 管理发布')
    return errors, fm

def content_errors(files, forbid_draft=False):
    errors, urls = [], {}
    for path, data in sorted(files.items()):
        if not path.startswith('content/posts/') or not path.lower().endswith(('.md', '.markdown')) or path == 'content/posts/_index.md':
            continue
        issues, fm = article_errors(path, data.decode('utf-8', errors='replace'), forbid_draft)
        errors.extend(f'{path}: {issue}' for issue in issues)
        if not fm:
            continue
        aliases = fm.get('aliases', [])
        routes = [f'/posts/{fm.get("slug", "")}/'] + (aliases if isinstance(aliases, list) else [])
        for route in routes:
            if not isinstance(route, str):
                continue
            if route.endswith('/index.html'):
                route = route[:-10]
            route = route.rstrip('/') + '/'
            if route in RESERVED or route in urls:
                errors.append(f'{path}: slug/alias 路径冲突 {route} ({urls.get(route, "系统页面")})')
            urls[route] = path
    return errors

def git_files():
    raw = subprocess.check_output(['git', 'ls-files', '--stage', '-z'])
    result, modes = {}, {}
    for entry in raw.split(b'\0'):
        if not entry:
            continue
        meta, rawpath = entry.split(b'\t', 1)
        mode, oid, stage = meta.split()
        path = rawpath.decode('utf-8')
        if stage != b'0':
            raise ValueError(f'{path}: 暂存区存在未解决冲突')
        result[path] = subprocess.check_output(['git', 'cat-file', 'blob', oid.decode()])
        modes[path] = mode.decode()
    return result, modes

def secret_errors(files, modes=None):
    errors = []
    patterns = [
        (rb'-----BEGIN (?:OPENSSH |RSA |EC |DSA |ENCRYPTED )?PRIVATE KEY-----', '私钥'),
        (rb'\b(?:gh[pousr]_[A-Za-z0-9]{30,}|github_pat_[A-Za-z0-9_]{40,}|AKIA[A-Z0-9]{16}|sk-[A-Za-z0-9_-]{32,})\b', '疑似 API Token'),
        (rb'(?im)^\s*(?:api[_-]?key|api[_-]?token|password|client_secret|secret_access_key)\s*[:=]\s*["\']?[^\s"\']{12,}', '疑似硬编码凭据'),
    ]
    forbidden_dirs = {'public', 'resources', '.cache', '.tools', '.venv', '.test-output', 'local-drafts', 'node_modules'}
    for path, data in files.items():
        parts = pathlib.PurePosixPath(path).parts
        name = parts[-1]
        if forbidden_dirs.intersection(parts) or name == '.env' or name.startswith('.env.') or name.endswith(('.pem', '.key', '.p12', '.pfx', '.env')) or name in {'id_rsa', 'id_ed25519', '.hugo_build.lock'}:
            errors.append(f'{path}: 禁止提交的本地/生成/敏感文件')
        if modes and modes.get(path) == '120000':
            errors.append(f'{path}: 不允许提交符号链接（防止指向工作区外秘密）')
        for pattern, reason in patterns:
            if re.search(pattern, data):
                errors.append(f'{path}: {reason}；未输出敏感值')
    # Draft protection also applies to locally created pages outside posts.
    for path, data in files.items():
        if path.startswith('content/') and not path.startswith('content/posts/') and path.lower().endswith(('.md', '.markdown')):
            try:
                fm = frontmatter(data.decode('utf-8'))
                if fm.get('draft') is True:
                    errors.append(f'{path}: draft: true 页面不得提交')
            except (yaml.YAMLError, ValueError, TypeError) as e:
                errors.append(f'{path}: {e}')
    return errors

class Page(HTMLParser):
    def __init__(self):
        super().__init__()
        self.refs, self.ids, self.meta = [], set(), {}
    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if 'id' in a:
            self.ids.add(a['id'])
        if tag == 'meta':
            self.meta[a.get('name', a.get('property', ''))] = a.get('content', '')
            if a.get('name', a.get('property', '')) in ('og:image', 'twitter:image') and a.get('content'):
                self.refs.append(a['content'])
        for key in ('href', 'src', 'poster'):
            if a.get(key):
                self.refs.append(a[key])
        if a.get('srcset'):
            self.refs.extend(part.strip().split()[0] for part in a['srcset'].split(',') if part.strip())

def output_errors(root, base_url, allow_branding_missing=True, examples=False):
    root = pathlib.Path(root).resolve()
    errors, warnings = [], set()
    required = ['index.html', 'posts/index.html', 'categories/index.html', 'tags/index.html', 'archives/index.html', 'search/index.html', 'about/index.html', 'index.json', 'index.xml', 'sitemap.xml', 'robots.txt', '404.html']
    for name in required:
        if not (root/name).is_file():
            errors.append(f'{name}: 核心产物缺失')
    try:
        index = json.loads((root/'index.json').read_text())
        if not isinstance(index, list):
            errors.append('index.json 必须为数组（空站点也应为 []）')
        else:
            for item in index:
                if not all(k in item for k in ('title', 'summary', 'content', 'permalink')) or '/posts/' not in item.get('permalink', ''):
                    errors.append('搜索索引字段不正确或混入非文章')
        ET.parse(root/'index.xml')
        ET.parse(root/'sitemap.xml')
    except (OSError, ValueError, ET.ParseError) as e:
        errors.append(f'JSON/XML 格式错误: {e}')
    host = url.urlparse(base_url).netloc
    pages = {}
    for path in root.rglob('*.html'):
        data = path.read_text()
        parser = Page(); parser.feed(data); pages[path] = parser
        if not examples and ('example-basic-post' in data or 'example-technical-post' in data or 'DRAFT_SENTINEL' in data):
            errors.append(f'{path.relative_to(root)}: 示例或草稿泄露')
    for path, parser in pages.items():
        relative = '/' + path.relative_to(root).as_posix()
        if relative.endswith('/index.html'):
            relative = relative[:-10]
        for ref in parser.refs:
            parsed = url.urlparse(url.urljoin(base_url.rstrip('/') + relative, ref))
            if parsed.scheme not in ('http', 'https') or parsed.netloc != host:
                continue
            route = url.unquote(parsed.path)
            target = (root/route.lstrip('/')).resolve()
            if not target.is_relative_to(root):
                errors.append(f'{path.name}: 越界链接 {ref}'); continue
            if target.is_dir() or route.endswith('/'):
                target = target/'index.html'
            if not target.is_file():
                if allow_branding_missing and route in MISSING_BRANDING:
                    warnings.add(f'MANUAL 缺少用户派生素材: {route}')
                else:
                    errors.append(f'{path.relative_to(root)}: 站内链接/资源不存在 {ref}')
            elif parsed.fragment and target in pages and url.unquote(parsed.fragment) not in pages[target].ids:
                errors.append(f'{path.relative_to(root)}: 锚点不存在 {ref}')
    # Check CSS local resources too (fonts, background images).
    for path in root.rglob('*.css'):
        for ref in re.findall(r'url\(["\']?([^\)"\']+)', path.read_text()):
            if ref.startswith(('data:', 'https:', 'http:', '#')):
                continue
            target = (root/ref.lstrip('/')) if ref.startswith('/') else path.parent/ref
            if not target.resolve().is_file():
                errors.append(f'{path.relative_to(root)}: CSS 资源不存在 {ref}')
    for name in ('index.json', 'index.xml', 'sitemap.xml'):
        if (root/name).exists() and not examples and any(x in (root/name).read_text() for x in ('example-basic-post', 'example-technical-post', 'DRAFT_SENTINEL')):
            errors.append(f'{name}: 示例/草稿泄露')
    for warning in sorted(warnings):
        print(warning)
    return errors

def report(errors, label):
    for e in errors:
        print('FAIL', e, file=sys.stderr)
    print(('FAIL ' if errors else 'PASS ') + label)
    return bool(errors)

def main():
    command = sys.argv[1]
    if command == 'content':
        root = pathlib.Path(sys.argv[2] if len(sys.argv) > 2 else '.')
        files = {str(f.relative_to(root)): f.read_bytes() for f in (root/'content').rglob('*') if f.is_file()}
        return report(content_errors(files), 'Front Matter 与 URL 检查')
    if command == 'staged':
        files, modes = git_files()
        return report(secret_errors(files, modes) + content_errors(files, True), 'Git 暂存快照检查')
    if command == 'output':
        return report(output_errors(sys.argv[2], sys.argv[3], '--strict-branding' not in sys.argv), '构建产物与站内链接检查')
    raise SystemExit('Unknown command')
if __name__ == '__main__':
    try:
        sys.exit(main())
    except (OSError, ValueError, subprocess.CalledProcessError) as e:
        print('FAIL', e, file=sys.stderr); sys.exit(1)
