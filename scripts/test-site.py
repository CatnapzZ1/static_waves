#!/usr/bin/env python3
"""Production and isolated fixtures. Never place demonstrations in real content/."""
import datetime, importlib.util, json, os, pathlib, re, shutil, subprocess, tempfile
import xml.etree.ElementTree as ET
import yaml
ROOT=pathlib.Path(__file__).resolve().parent.parent
spec=importlib.util.spec_from_file_location('validate',ROOT/'scripts/validate.py')
v=importlib.util.module_from_spec(spec);spec.loader.exec_module(v)
config=yaml.safe_load((ROOT/'hugo.yaml').read_text())
BASE=config['baseURL']
def run(*args, cwd=ROOT, env=None):
    subprocess.run(args,cwd=cwd,env=env,check=True)
def build(source,dest,environment='production',base=BASE):
    run('hugo','--source',str(source),'--destination',str(dest),'--environment',environment,'--baseURL',base,'--buildDrafts=false','--buildFuture=false','--buildExpired=false')
def check(root,examples=False):
    errors=v.output_errors(root,BASE,examples=examples)
    if errors: raise AssertionError('\n'.join(errors))
with tempfile.TemporaryDirectory(prefix='blog-site-test-') as tmp:
    tmp=pathlib.Path(tmp)
    production=tmp/'production';build(ROOT,production);check(production)
    html=(production/'index.html').read_text()
    assert 'home-info' in html and 'home-avatar' in html and 'theme-toggle' in html
    assert 'prefers-color-scheme' in html and 'pref-theme' in html
    assert 'Powered by' in html and 'PaperMod' in html
    assert 'katex.min' not in html and 'js/mermaid' not in html
    analytics_enabled=bool(config['params'].get('cloudflareAnalyticsToken')) and '.invalid' not in BASE
    assert ('cloudflareinsights' in html)==analytics_enabled
    for marker in ('rel="canonical"','og:title','twitter:card','application/ld+json'):
        assert marker in html, marker
    for raw in re.findall(r'<script type="application/ld\+json">(.*?)</script>',html,re.S):
        json.loads(raw)
    print('PASS 生产站点：核心产物、真实图片引用、原生主题、示例隔离')
    fixture=tmp/'fixture'
    shutil.copytree(ROOT,fixture,ignore=shutil.ignore_patterns('.git','.cache','.tools','.venv','.test-output','public','resources','local-drafts','__pycache__'))
    for name in ('basic-post','technical-post'):
        dest=fixture/'content/posts'/name
        shutil.copytree(ROOT/'examples'/name,dest)
        post=dest/'index.md';post.write_text(post.read_text().replace('draft: true','draft: false'))
    draft=fixture/'content/posts/unpublished';draft.mkdir()
    (draft/'index.md').write_text((ROOT/'examples/basic-post/index.md').read_text().replace('example-basic-post','draft-sentinel').replace('aliases: ["/old-basic-post/"]','').replace('## 文章结构','DRAFT_SENTINEL\n## 文章结构'))
    future=fixture/'content/posts/future';future.mkdir()
    (future/'index.md').write_text((draft/'index.md').read_text().replace('draft: true','draft: false').replace('draft-sentinel','future-sentinel').replace('2024-01-01','2099-01-01'))
    # Real git history for Git lastmod priority and explicit front matter override.
    run('git','init','-b','main',cwd=fixture)
    run('git','config','user.name','Fixture Test',cwd=fixture)
    run('git','config','user.email','fixture@example.invalid',cwd=fixture)
    run('git','add','content',cwd=fixture)
    env=os.environ|{'GIT_AUTHOR_DATE':'2024-02-03T12:00:00+00:00','GIT_COMMITTER_DATE':'2024-02-03T12:00:00+00:00'}
    run('git','-c','core.hooksPath=/dev/null','commit','-m','Fixture history',cwd=fixture,env=env)
    run('hugo','new','content','--source',str(fixture),'--kind','posts','posts/archetype-check/index.md')
    created=v.frontmatter((fixture/'content/posts/archetype-check/index.md').read_text())
    assert created['slug']=='archetype-check', created
    assert created['draft'] is True
    basic=fixture/'content/posts/basic-post/index.md'
    basic.write_text(basic.read_text().replace('draft: false','draft: false\nlastmod: "2024-03-04"'))
    with basic.open('a') as post:
        post.write('''
## RSS URL check

[附件](./diagram.svg?download=1&mode=raw)
[父路径](../example-basic-post/diagram.svg)
[文章锚点](#rss-url-check)
[外部链接](https://external.invalid/file?x=1&y=2)
[协议相对链接](//external.invalid/file)
[邮箱](mailto:fixture@example.invalid)

`<img src="diagram.svg">`
''')
    fallback=fixture/'content/posts/date-fallback';fallback.mkdir()
    (fallback/'index.md').write_text('---\ntitle: Date fallback\nslug: date-fallback\ndate: \"2024-04-05\"\ndescription: Untracked article\ncategories: [随笔]\ntags: []\ndraft: false\n---\nBody\n'.replace('\\"','"'))
    output=tmp/'examples';build(fixture,output);check(output,True)
    technical=(output/'posts/example-technical-post/index.html').read_text()
    basic_html=(output/'posts/example-basic-post/index.html').read_text()
    for marker in ('chroma','language-python','language-go','language-bash','language-json','copy-code','mermaid-diagram','js/mermaid','katex.min.js','\\(E = mc^2\\)','\\sum','class="toc"'):
        assert marker in technical, f'Missing rendering marker: {marker}'
    assert 'language-mermaid' not in technical
    assert 'katex.min.js' not in basic_html and 'js/mermaid' not in basic_html
    for page, expected_date in [(basic_html,'2024-03-04'),(technical,'2024-02-03'),((output/'posts/date-fallback/index.html').read_text(),'2024-04-05')]:
        meta=v.Page();meta.feed(page)
        assert meta.meta['article:modified_time'].startswith(expected_date), meta.meta
    assert 'og:image' in basic_html and '/posts/example-basic-post/diagram.svg' in basic_html
    assert (output/'old-basic-post/index.html').exists()
    assert not (output/'posts/draft-sentinel').exists() and not (output/'posts/future-sentinel').exists()
    entries=json.loads((output/'index.json').read_text())
    expected={'example-basic-post','example-technical-post'}
    fixture_entries=[x for x in entries if any('/posts/'+slug+'/' in x['permalink'] for slug in expected)]
    assert len(fixture_entries)==2
    assert all('draft-sentinel' not in x['permalink'] and 'future-sentinel' not in x['permalink'] for x in entries)
    rss=ET.parse(output/'index.xml')
    full=''.join(e.text or '' for e in rss.findall('.//{http://purl.org/rss/1.0/modules/content/}encoded'))
    assert 'FULL_RSS_SENTINEL' in full
    assert 'DRAFT_SENTINEL' not in (output/'index.xml').read_text()
    # Check every generated feed, including section and taxonomy feeds.
    basic_url=BASE.rstrip('/')+'/posts/example-basic-post/'
    feeds_checked=0
    for feed in output.rglob('index.xml'):
        for item in ET.parse(feed).findall('.//item'):
            if item.findtext('link')!=basic_url:
                continue
            body=item.findtext('{http://purl.org/rss/1.0/modules/content/}encoded')
            parsed=v.Page();parsed.feed(body)
            for ref in (basic_url+'diagram.svg', basic_url+'diagram.svg?download=1&mode=raw',
                        basic_url+'#rss-url-check', BASE.rstrip('/')+'/about/',
                        'https://external.invalid/file?x=1&y=2', 'https://external.invalid/file',
                        'mailto:fixture@example.invalid'):
                assert ref in parsed.refs, (feed,ref,parsed.refs)
            assert '&lt;img src=&quot;diagram.svg&quot;&gt;' in body
            feeds_checked+=1
    assert feeds_checked>=3, feeds_checked
    assert 'src="diagram.svg"' in basic_html, 'RSS URL conversion must not change page HTML'
    theme=next((ROOT/'.cache/go-mod/github.com/adityatelange').glob('hugo-!paper!mod@'+json.loads((ROOT/'toolchain.json').read_text())['papermodVersion']))
    # Execute the actual upstream Fuse implementation against the actual built index.
    js='''const fs=require('fs'),vm=require('vm');const ctx={};vm.createContext(ctx);vm.runInContext(fs.readFileSync(process.argv[1],'utf8'),ctx);const data=JSON.parse(fs.readFileSync(process.argv[2],'utf8'));const opts=JSON.parse(process.argv[3]);const fuse=new ctx.Fuse(data,opts);for(const q of ['中文搜索','transformer']){if(!fuse.search(q).length)throw Error('No result: '+q);}if(new ctx.Fuse([],opts).search('中文').length)throw Error('empty');console.log('PASS 原生 Fuse 中文/英文/空索引');'''
    run('node','-e',js,str(theme/'assets/js/fuse.basic.min.js'),str(output/'index.json'),json.dumps(config['params']['fuseOpts']))
    # Analytics is absent locally, present only with a valid production host and token.
    config_file=fixture/'hugo.yaml';cf=yaml.safe_load(config_file.read_text())
    cf['params']['cloudflareAnalyticsToken']='0'*32
    config_file.write_text(yaml.safe_dump(cf,allow_unicode=True))
    dev=tmp/'dev';build(fixture,dev,'development','http://localhost:1313/')
    dev_html=(dev/'index.html').read_text()
    assert 'cloudflareinsights' not in dev_html and 'noindex, nofollow' in dev_html
    assert 'Disallow: /' in (dev/'robots.txt').read_text()
    prod=tmp/'analytics';build(fixture,prod,base='https://blog-fixture.test/')
    assert 'cloudflareinsights' in (prod/'index.html').read_text()
    placeholder=tmp/'analytics-placeholder';build(fixture,placeholder,base='https://your-domain.invalid/')
    assert 'cloudflareinsights' not in (placeholder/'index.html').read_text()
    cf['params']['cloudflareAnalyticsToken']=''
    config_file.write_text(yaml.safe_dump(cf,allow_unicode=True))
    disabled=tmp/'analytics-disabled';build(fixture,disabled,base='https://blog-fixture.test/')
    assert 'cloudflareinsights' not in (disabled/'index.html').read_text()
    print('PASS 隔离示例：Chroma/KaTeX 标记/Mermaid hook/封面/aliases/Git lastmod/完整 RSS/草稿与未来文章排除/统计环境隔离')
    # Retain only a report, never copy example output to the real public directory.
    report=ROOT/'.test-output';report.mkdir(exist_ok=True)
    (report/'site-result.json').write_text(json.dumps({'status':'PASS','time':datetime.datetime.now(datetime.timezone.utc).isoformat(),'browserRendering':'MANUAL'},indent=2)+'\n')
