#!/usr/bin/env python3
import json, pathlib, re, shutil, subprocess, sys
lock = json.loads(pathlib.Path('toolchain.json').read_text())
errors = []
def run(args):
    return subprocess.check_output(args, text=True, stderr=subprocess.STDOUT).strip()
def version(v):
    return tuple(map(int, v.split('.')))
for name in ('hugo', 'go'):
    if not shutil.which(name):
        errors.append(f'{name}: 未安装，请运行 scripts/bootstrap.sh')
if shutil.which('hugo'):
    out = run(['hugo', 'version'])
    if '+extended' not in out or not re.search(r'v'+re.escape(lock['hugo'])+r'(?:-|\+|\s)', out):
        errors.append(f'Hugo 必须为锁定的 Extended {lock["hugo"]}，实际 {out}')
    else:
        print('PASS', out)
if shutil.which('go'):
    out = run(['go', 'version'])
    m = re.search(r'go(\d+\.\d+(?:\.\d+)?)', out)
    if not m or version(m[1]) < version(lock['goMinimum']):
        errors.append('Go 版本不符合最低要求')
    else:
        print('PASS', out)
expected = lock['papermodVersion']
if not expected:
    errors.append('PaperMod 尚未解析和锁定；运行 bootstrap.sh，不能视为依赖验证完成')
else:
    try:
        mod = json.loads(run(['go','list','-m','-json','github.com/adityatelange/hugo-PaperMod']))
        if mod.get('Replace') or mod['Version'] != expected:
            errors.append('PaperMod 模块与 toolchain.json 锁定值不一致')
        sums = pathlib.Path('go.sum').read_text()
        for suffix in ('', '/go.mod'):
            if f'github.com/adityatelange/hugo-PaperMod {expected}{suffix} h1:' not in sums:
                errors.append('go.sum 缺少 PaperMod 校验值 '+suffix)
    except (subprocess.CalledProcessError, OSError, KeyError) as e:
        errors.append(f'PaperMod 验证失败: {e}')
for e in errors:
    print('FAIL', e, file=sys.stderr)
sys.exit(bool(errors))
