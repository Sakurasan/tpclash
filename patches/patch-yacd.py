#!/usr/bin/env python3
"""对 Yacd-meta 源码应用 tpclash 补丁。

背景: yacd 默认 API 地址硬编码为 127.0.0.1:9090, 导致从局域网 IP
(如 http://192.168.1.106:9090) 访问面板时仍连回本机。修复为跟随
当前访问地址 (window.location.origin)。

步骤:
  1) src/store/app.ts: data-base-url 缺省时回退到 window.location.origin
  2) index.html: 移除硬编码的 data-base-url 属性 (否则步骤 1 的回退永远不生效)
  3) index.html: 注入迁移脚本, 把旧版 localStorage (yacd.metacubex.one)
     中保存的 127.0.0.1:9090 / localhost:9090 迁移为当前访问地址

每一步完成后立即校验, 上游改版导致补丁失效时以非零退出码失败,
避免静默回归。

用法: python3 patches/patch-yacd.py [yacd 源码目录, 默认 build/yacd]
"""
import pathlib
import re
import sys

YACD_DIR = pathlib.Path(sys.argv[1] if len(sys.argv) > 1 else 'build/yacd')
MIGRATE_FILE = pathlib.Path(__file__).resolve().parent / 'yacd-migrate-base-url.html'

APP_TS_OLD = ".getAttribute('data-base-url') ?? 'http://127.0.0.1:9090'"
APP_TS_NEW = ".getAttribute('data-base-url') ?? window.location.origin"
DATA_BASE_URL_RE = re.compile(r' data-base-url="[^"]*"')


def fail(msg: str):
    print(f'[patch-yacd] ERROR: {msg}', file=sys.stderr)
    sys.exit(1)


def patch_app_ts():
    p = YACD_DIR / 'src/store/app.ts'
    s = p.read_text()
    if APP_TS_NEW in s:
        print('[patch-yacd] app.ts already patched, skip')
        return
    if APP_TS_OLD not in s:
        fail(f'{p} 未找到旧默认值, 补丁未生效 (上游可能已改版)')
    p.write_text(s.replace(APP_TS_OLD, APP_TS_NEW))
    print('[patch-yacd] app.ts: default API address now follows window.location.origin')


def patch_index_html():
    p = YACD_DIR / 'index.html'
    s = p.read_text()

    # 2) 移除硬编码 data-base-url 属性
    s2, n = DATA_BASE_URL_RE.subn('', s)
    if n == 0:
        fail(f'{p} 未找到 data-base-url 属性, 补丁未生效 (上游可能已改版)')
    s = s2

    # 3) 注入迁移脚本 (放到 </body> 前)
    migrate = MIGRATE_FILE.read_text().strip()
    body_close = '</body>'
    if body_close not in s:
        fail(f'{p} 未找到 </body>, 无法注入迁移脚本')
    if 'yacd.metacubex.one' in s:
        print('[patch-yacd] index.html migration script already present, skip inject')
    else:
        s = s.replace(body_close, migrate + '\n' + body_close)

    p.write_text(s)
    print(f'[patch-yacd] index.html: removed data-base-url, injected migration script ({n} attr removed)')


def main():
    if not (YACD_DIR / 'src/store/app.ts').exists():
        fail(f'{YACD_DIR} 不是有效的 Yacd-meta 源码目录')
    if not MIGRATE_FILE.exists():
        fail(f'缺少迁移脚本文件: {MIGRATE_FILE}')
    patch_app_ts()
    patch_index_html()
    print('[patch-yacd] all patches applied OK')


if __name__ == '__main__':
    main()
