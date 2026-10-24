#!/usr/bin/env python3
import importlib.util,json,os,pathlib,subprocess,tempfile,unittest
spec=importlib.util.spec_from_file_location('releases',pathlib.Path(__file__).resolve().parent.parent/'deploy/releases.py')
r=importlib.util.module_from_spec(spec);spec.loader.exec_module(r)
class ReleaseTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory(prefix='blog-release-test-')
        self.base=pathlib.Path(self.tmp.name);(self.base/'releases').mkdir();self.m=r.Releases(self.base)
    def tearDown(self): self.tmp.cleanup()
    def make(self,i):
        name=f'20240101T0000{i:02d}Z-abcdef012345-12345678'
        p=self.m.create(name)
        for file in ('index.html','index.json','index.xml','sitemap.xml','favicon.ico'): (p/file).write_text('fixture')
        self.m.ready(name);return name
    def test_activate_rollback_retention(self):
        names=[self.make(i) for i in range(8)]
        self.m.activate(names[0]);self.m.activate(names[7]);self.m.cleanup()
        self.assertEqual(self.m.current(),names[7]);self.assertEqual(self.m.current('previous'),names[0])
        self.assertEqual(len(list((self.base/'releases').iterdir())),5)
        self.m.activate(names[0]);self.assertEqual(self.m.current(),names[0])
        self.m.link(names[7]);self.assertEqual(self.m.current(),names[7])
    def test_reject_escape_and_incomplete(self):
        with self.assertRaises(ValueError): self.m.activate('../outside')
        name='20240101T000000Z-abcdef0-12345678';self.m.create(name)
        with self.assertRaises(ValueError): self.m.activate(name)
        self.assertFalse((self.base/'current').exists())
    def test_symlink_and_first_deployment_restore(self):
        name=self.make(1);self.m.activate(name);self.m.restore('','');self.assertFalse((self.base/'current').is_symlink())
        self.assertFalse((self.base/'previous').is_symlink())
        (self.base/'current').symlink_to('/tmp')
        with self.assertRaises(ValueError):self.m.current()
    def test_failed_deploy_preserves_default_rollback(self):
        a,b,c=[self.make(i) for i in range(3)]
        self.m.activate(a);self.m.activate(b)
        old,previous=self.m.current(),self.m.current('previous')
        self.m.activate(c);self.m.restore(old,previous)
        self.assertEqual((self.m.current(),self.m.current('previous')),(b,a))
        self.m.activate(self.m.current('previous'))
        self.assertEqual(self.m.current(),a)
    def test_failed_rollback_restores_history(self):
        a,b=[self.make(i) for i in range(2)]
        self.m.activate(a);self.m.activate(b)
        old,previous=self.m.current(),self.m.current('previous')
        self.m.activate(a);self.m.restore(old,previous)
        self.assertEqual((self.m.current(),self.m.current('previous')),(b,a))
    def test_failed_second_deploy_removes_new_previous(self):
        a,b=[self.make(i) for i in range(2)]
        self.m.activate(a);self.m.activate(b);self.m.restore(a,'')
        self.assertEqual(self.m.current(),a)
        self.assertFalse((self.base/'previous').is_symlink())
    def test_shell_failure_trap_restores_both_links(self):
        a,b,c=[self.make(i) for i in range(3)]
        deploy=pathlib.Path(__file__).resolve().parent.parent/'deploy'
        # Exercise the real shell functions/traps and Python CLI. Only replace
        # machine-specific startup and the fixed CLI base with temporary paths.
        runtime=(deploy/'common.sh').read_text().split('step() {',1)[1]
        helper=self.base/'helper.py'
        helper.write_text('import os,sys\n'
                          f'sys.path.insert(0,{str(deploy)!r})\n'
                          'import releases\n'
                          'manager=releases.Releases(os.environ["RELEASE_TEST_BASE"])\n'
                          'releases.Releases=lambda base: manager\n'
                          'releases.main()\n')
        script='set -Eeuo pipefail\nstep() {'+runtime+'\nhealth() { return 0; }\nactivate_release "$1"\n'
        env=os.environ|{'BLOG_HELPER':str(helper),'RELEASE_TEST_BASE':str(self.base),'log':str(self.base/'test.log')}
        for current,previous,target,failure in [('', '', a, 'false'), (a, '', b, 'false'),
                                               (b, a, c, 'false'), (b, a, a, 'false'),
                                               (b, a, c, 'kill -TERM $$')]:
            with self.subTest(current=current,previous=previous,target=target,failure=failure):
                self.m.restore(current,previous)
                result=subprocess.run(['bash','-c',script+failure,'test',target],env=env,capture_output=True,text=True)
                self.assertNotEqual(result.returncode,0)
                self.assertIn('Failure; restoring previous release',result.stdout)
                self.assertNotIn('CRITICAL',result.stdout)
                self.assertEqual((self.m.current(),self.m.current('previous')),(current,previous))
    def test_cleanup_refuses_nested_symlink(self):
        names=[self.make(i) for i in range(7)];self.m.activate(names[-1])
        (self.base/'releases'/names[0]/'outside').symlink_to('/tmp')
        with self.assertRaises(ValueError):self.m.cleanup()
        self.assertTrue((self.base/'releases'/names[0]).exists())
if __name__=='__main__':unittest.main()
