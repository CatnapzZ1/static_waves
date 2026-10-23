#!/usr/bin/env python3
import importlib.util,json,pathlib,tempfile,unittest
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
        name=self.make(1);self.m.activate(name);self.m.link('');self.assertFalse((self.base/'current').is_symlink())
        (self.base/'current').symlink_to('/tmp')
        with self.assertRaises(ValueError):self.m.current()
    def test_cleanup_refuses_nested_symlink(self):
        names=[self.make(i) for i in range(7)];self.m.activate(names[-1])
        (self.base/'releases'/names[0]/'outside').symlink_to('/tmp')
        with self.assertRaises(ValueError):self.m.cleanup()
        self.assertTrue((self.base/'releases'/names[0]).exists())
if __name__=='__main__':unittest.main()
