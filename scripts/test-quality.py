#!/usr/bin/env python3
import importlib.util, pathlib, subprocess, tempfile, unittest
import yaml
spec = importlib.util.spec_from_file_location('validate', pathlib.Path(__file__).with_name('validate.py'))
v = importlib.util.module_from_spec(spec); spec.loader.exec_module(v)
ROOT = pathlib.Path(__file__).resolve().parent.parent
BASE = dict(title='测试', slug='test-post', date='2024-01-01', description='摘要', categories=['技术研究'], tags=[], draft=False)
def article(**changes):
    return '---\n'+yaml.safe_dump(BASE|changes, allow_unicode=True)+'---\n正文\n'
class ContentTests(unittest.TestCase):
    def test_valid(self):
        self.assertEqual(v.article_errors('content/posts/test/index.md',article())[0], [])
    def test_bad_fields(self):
        cases = [dict(title=''), dict(description=''), dict(slug='中文'), dict(date='2024-02-30'), dict(categories='技术研究'), dict(categories=[]), dict(categories=['技术研究','随笔']), dict(categories=['新分类']), dict(tags='tag'), dict(draft='true'), dict(aliases=['https://bad.test/']), dict(aliases=['/../about/']), dict(math='yes'), dict(url='/override/')]
        for change in cases:
            with self.subTest(change=change):
                self.assertTrue(v.article_errors('content/posts/test/index.md',article(**change))[0])
    def test_duplicates_and_yaml(self):
        self.assertTrue(v.content_errors({'content/posts/a/index.md': article().encode(), 'content/posts/b/index.md': article().encode()}))
        self.assertTrue(v.article_errors('content/posts/x.md',article())[0])
        self.assertTrue(v.article_errors('content/posts/x/index.md','---\ntitle: [\n---\n')[0])
        self.assertTrue(v.article_errors('content/posts/x/index.md',article().replace('slug: test-post','slug: one\nslug: two'))[0])
        self.assertTrue(v.content_errors({'content/posts/a/index.md': article(aliases=['/about/']).encode()}))
    def test_secrets(self):
        cases = {'.env': b'local', 'public/a.html': b'generated', 'secret.txt': ('-----BEGIN '+'OPENSSH PRIVATE KEY-----').encode(), 'token.txt': ('ghp_'+'x'*36).encode()}
        for name, data in cases.items():
            self.assertTrue(v.secret_errors({name:data}))
    def test_staged_snapshot_not_worktree(self):
        with tempfile.TemporaryDirectory(prefix='blog-index-test-') as temp:
            root=pathlib.Path(temp)
            def git(*args): return subprocess.run(['git',*args],cwd=root,check=True,stdout=subprocess.DEVNULL)
            git('init','-b','main')
            path=root/'content/posts/test/index.md';path.parent.mkdir(parents=True)
            path.write_text(article(draft=True));git('add','content')
            path.write_text(article(draft=False))
            cmd=['python3',str(ROOT/'scripts/validate.py'),'staged']
            bad=subprocess.run(cmd,cwd=root,capture_output=True,text=True)
            self.assertNotEqual(bad.returncode,0);self.assertIn('draft: true',bad.stderr)
            git('add','content');path.write_text(article(draft=True))
            good=subprocess.run(cmd,cwd=root,capture_output=True,text=True)
            self.assertEqual(good.returncode,0,good.stderr)
            git('config','core.hooksPath',str(ROOT/'.githooks'))
            # The real hook delegates relative to repository root: test a self-contained copy.
            import shutil
            shutil.copytree(ROOT/'scripts',root/'scripts',ignore=shutil.ignore_patterns('__pycache__'))
            hook=subprocess.run([str(ROOT/'.githooks/pre-commit')],cwd=root,capture_output=True,text=True)
            self.assertEqual(hook.returncode,0,hook.stderr)
    def test_broken_resource(self):
        with tempfile.TemporaryDirectory(prefix='blog-link-test-') as temp:
            path=pathlib.Path(temp)/'index.html';path.write_text('<img src="/missing.png">')
            self.assertTrue(any('missing.png' in x for x in v.output_errors(temp,'https://test.invalid/')))
if __name__=='__main__':unittest.main()
