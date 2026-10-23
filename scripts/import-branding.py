#!/usr/bin/env python3
"""Deterministic resize/crop of supplied assets; no generated replacement art."""
import argparse, hashlib, json, pathlib, shutil
from PIL import Image, ImageOps
import yaml
parser = argparse.ArgumentParser()
parser.add_argument('logo', type=pathlib.Path)
parser.add_argument('avatar', type=pathlib.Path)
parser.add_argument('--favicon-box', default='210,155,1070,950', help='猫咪区域 left,top,right,bottom（源图坐标）')
args = parser.parse_args()
root = pathlib.Path(__file__).resolve().parent.parent
static = root/'static'
site = static/'images/site'
originals = root/'brand-originals'
outputs = [site/'logo.png', site/'avatar.webp', static/'favicon.ico', static/'favicon-16x16.png', static/'favicon-32x32.png', static/'apple-touch-icon.png', static/'safari-pinned-tab.svg']
if any(f.exists() for f in outputs) or originals.exists():
    raise SystemExit('目标已有素材，拒绝覆盖。请先人工审阅并迁移旧副本。')
logo = ImageOps.exif_transpose(Image.open(args.logo)).convert('RGBA')
avatar = ImageOps.exif_transpose(Image.open(args.avatar)).convert('RGB')
box = tuple(map(int, args.favicon_box.split(',')))
if len(box) != 4 or not (0 <= box[0] < box[2] <= logo.width and 0 <= box[1] < box[3] <= logo.height):
    raise SystemExit('favicon-box 超出源图范围')
originals.mkdir(); site.mkdir(parents=True, exist_ok=True)
manifest = {'faviconCrop': box, 'assets': []}
for kind, source in [('logo', args.logo), ('avatar', args.avatar)]:
    dest = originals/(kind + source.suffix.lower())
    shutil.copyfile(source, dest)
    manifest['assets'].append({'original': str(dest.relative_to(root)), 'sha256': hashlib.sha256(source.read_bytes()).hexdigest()})
logo.thumbnail((320, 320), Image.Resampling.LANCZOS)
logo.save(site/'logo.png', optimize=True)
ImageOps.fit(avatar, (320, 320), Image.Resampling.LANCZOS).save(site/'avatar.webp', quality=88)
cat = Image.open(args.logo).convert('RGBA').crop(box)
cat.thumbnail((224, 224), Image.Resampling.LANCZOS)
icon = Image.new('RGBA', (256,256), 'white')
icon.alpha_composite(cat, ((256-cat.width)//2, (256-cat.height)//2))
icon.save(static/'favicon.ico', sizes=[(16,16),(32,32),(48,48)])
for size, name in [(16,'favicon-16x16.png'), (32,'favicon-32x32.png'), (180,'apple-touch-icon.png')]:
    icon.resize((size,size), Image.Resampling.LANCZOS).save(static/name)
# Safari monochrome mask, traced as horizontal runs of dark pixels from the real logo.
mask = icon.convert('L').resize((64,64), Image.Resampling.LANCZOS)
runs = []
for y in range(64):
    x=0
    while x < 64:
        if mask.getpixel((x,y)) >= 128:
            x+=1; continue
        start=x
        while x < 64 and mask.getpixel((x,y)) < 128: x+=1
        runs.append(f'M{start} {y}h{x-start}v1H{start}z')
(static/'safari-pinned-tab.svg').write_text('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64"><path d="'+''.join(runs)+'"/></svg>\n')
manifest['outputs'] = [{'path': str(f.relative_to(root)), 'bytes': f.stat().st_size, 'sha256': hashlib.sha256(f.read_bytes()).hexdigest()} for f in outputs]
(originals/'manifest.json').write_text(json.dumps(manifest, ensure_ascii=False, indent=2)+'\n')
config = root/'hugo.yaml'
c = yaml.safe_load(config.read_text())
c['params']['avatar']='/images/site/avatar.webp'
c['params']['label']['icon']='/images/site/logo.png'
c['params']['assets'].update(favicon='/favicon.ico', favicon16x16='/favicon-16x16.png', favicon32x32='/favicon-32x32.png', apple_touch_icon='/apple-touch-icon.png', safari_pinned_tab='/safari-pinned-tab.svg')
config.write_text(yaml.safe_dump(c, allow_unicode=True, sort_keys=False))
print('PASS 原始素材保留于 brand-originals/；发布副本与 favicon 已生成；hugo.yaml 已更新')
