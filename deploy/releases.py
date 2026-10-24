#!/usr/bin/env python3
"""Release filesystem operations. Production CLI paths are intentionally fixed."""
import json, os, pathlib, re, shutil, sys, uuid
ID = re.compile(r'^\d{8}T\d{6}Z-[a-f0-9]{7,40}-[a-f0-9]{8}$')
class Releases:
    def __init__(self, base):
        self.base=pathlib.Path(base).absolute()
        self.root=self.base/'releases'
        for path in (self.base,self.root):
            if path.is_symlink() or not path.is_dir() or path.resolve()!=path or path.stat().st_uid != os.getuid():
                raise ValueError(f'Unsafe ownership or directory: {path}')
    def release(self, name):
        if not ID.fullmatch(name): raise ValueError('Invalid release ID')
        path=self.root/name
        if path.is_symlink() or not path.is_dir() or path.resolve().parent!=self.root or path.stat().st_uid!=os.getuid():
            raise ValueError('Unsafe release path/owner')
        metadata=path/'.release.json'
        if metadata.is_symlink() or not metadata.is_file() or metadata.stat().st_uid!=os.getuid():
            raise ValueError('Missing or unsafe release marker')
        data=json.loads(metadata.read_text())
        if data.get('id')!=name: raise ValueError('Release marker mismatch')
        return path, data
    def current(self, link='current'):
        path=self.base/link
        if not path.is_symlink():
            if path.exists(): raise ValueError('Expected symlink: '+link)
            return ''
        target=path.resolve()
        if target.parent!=self.root: raise ValueError('Symlink outside releases')
        self.release(target.name)
        return target.name
    def link(self, name, link='current'):
        target=self.base/link
        if target.exists() and not target.is_symlink(): raise ValueError('Refusing to replace real directory')
        if not name:
            if target.is_symlink(): target.unlink()
            return
        path,data=self.release(name)
        if not data.get('ready'): raise ValueError('Release not verified')
        temp=self.base/('.link-'+uuid.uuid4().hex)
        try:
            temp.symlink_to(path, target_is_directory=True)
            os.replace(temp,target)
        finally:
            if temp.is_symlink(): temp.unlink()
    def create(self, name):
        if not ID.fullmatch(name): raise ValueError('Invalid release ID')
        path=self.root/name;path.mkdir(mode=0o755)
        (path/'.release.json').write_text(json.dumps({'id':name,'ready':False})+'\n')
        return path
    def ready(self, name):
        path,data=self.release(name)
        for file in ('index.html','index.json','index.xml','sitemap.xml','favicon.ico'):
            if not (path/file).is_file(): raise ValueError('Incomplete release: '+file)
        data['ready']=True
        (path/'.release.json').write_text(json.dumps(data)+'\n')
        (path/'release-id.txt').write_text(name+'\n')
    def activate(self, name):
        path,data=self.release(name)
        if not data['ready']: raise ValueError('Release not verified')
        old=self.current()
        if old and old!=name: self.link(old,'previous')
        self.link(name)
        return old
    def restore(self, current, previous):
        # Restore the serving release first, then its original rollback target.
        self.link(current)
        self.link(previous, 'previous')
    def cleanup(self):
        protected={self.current(),self.current('previous')}-{''}
        candidates=[]
        for p in self.root.iterdir():
            # Unknown directories are never removed.
            if not ID.fullmatch(p.name): continue
            self.release(p.name)
            candidates.append(p.name)
        keep=protected|set([n for n in sorted(candidates,reverse=True) if n not in protected][:max(0,5-len(protected))])
        for name in sorted(set(candidates)-keep):
            # Re-check live links and every inode immediately before removal.
            if name in {self.current(),self.current('previous')}: continue
            path,_=self.release(name)
            for p in [path,*path.rglob('*')]:
                if p.is_symlink() or p.lstat().st_uid!=os.getuid() or not p.resolve().is_relative_to(self.root):
                    raise ValueError('Refusing cleanup of symlink, foreign-owned or escaped path')
            shutil.rmtree(path)
            print('Removed old release',name)

def main():
    manager=Releases('/var/www/blog')
    action=sys.argv[1]
    if action=='current': print(manager.current())
    elif action=='previous': print(manager.current('previous'))
    elif action=='create': print(manager.create(sys.argv[2]))
    elif action=='ready': manager.ready(sys.argv[2])
    elif action=='activate': manager.activate(sys.argv[2])
    elif action=='restore': manager.restore(sys.argv[2], sys.argv[3])
    elif action=='cleanup': manager.cleanup()
    else: raise ValueError('Unknown operation')
if __name__=='__main__':
    try: main()
    except (OSError,ValueError,KeyError) as e:
        print('FAIL release operation:',e,file=sys.stderr);sys.exit(1)
