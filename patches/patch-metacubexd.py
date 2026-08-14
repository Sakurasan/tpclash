#!/usr/bin/env python3
"""对 metacubexd 源码/构建产物应用 tpclash 补丁。

背景: metacubexd 默认 API 地址硬编码为 127.0.0.1:9090, 导致从局域网 IP
(如 http://192.168.1.106:9090) 访问面板时仍连回本机。修复为跟随
当前访问地址 (window.location.origin)。与 patch-yacd.py 处理 yacd 的问题相同。

用法 (构建流程中按顺序执行, 见 mise.toml 的 prepare-dashboard):

  # 1) 源码阶段 (pnpm build 之前): 修改 config.js 默认值与 useConnect 兜底
  python3 patches/patch-metacubexd.py build/official

  # 2) 产物阶段 (pnpm build 之后): 向生成的 index.html 注入 localStorage 迁移脚本
  python3 patches/patch-metacubexd.py build/official/packages/ui/.output/public

步骤 (源码阶段):
  1) packages/ui/public/config.js: defaultBackendURL 缺省 '' -> window.location.origin
  2) packages/ui/composables/useConnect.ts: 最终兜底 FALLBACK_BACKEND_URL -> window.location.origin

步骤 (产物阶段):
  3) index.html: 注入迁移脚本, 把旧版 localStorage (endpointList)
     中保存的 127.0.0.1:9090 / localhost:9090 迁移为当前访问地址

每一步完成后立即校验, 上游改版导致补丁失效时以非零退出码失败,
避免静默回归。
"""
import pathlib
import sys

MIGRATE_FILE = pathlib.Path(__file__).resolve().parent / 'metacubexd-migrate-base-url.html'

CONFIG_JS_REL = pathlib.Path('packages/ui/public/config.js')
USE_CONNECT_REL = pathlib.Path('packages/ui/composables/useConnect.ts')

CONFIG_JS_OLD = "  defaultBackendURL: '',"
CONFIG_JS_NEW = "  defaultBackendURL: window.location.origin,"
USE_CONNECT_OLD = "    return FALLBACK_BACKEND_URL"
USE_CONNECT_NEW = "    return typeof window !== 'undefined' ? window.location.origin : FALLBACK_BACKEND_URL"
MIGRATE_MARK = 'patch-metacubexd.py'


def fail(msg: str):
    print(f'[patch-metacubexd] ERROR: {msg}', file=sys.stderr)
    sys.exit(1)


def patch_config_js(p: pathlib.Path):
    s = p.read_text()
    if CONFIG_JS_NEW in s:
        print('[patch-metacubexd] config.js already patched, skip')
        return
    if CONFIG_JS_OLD not in s:
        fail(f'{p} 未找到旧默认值 defaultBackendURL: \'\', 补丁未生效 (上游可能已改版)')
    p.write_text(s.replace(CONFIG_JS_OLD, CONFIG_JS_NEW))
    print('[patch-metacubexd] config.js: defaultBackendURL now follows window.location.origin')


def patch_use_connect(p: pathlib.Path):
    s = p.read_text()
    if USE_CONNECT_NEW in s:
        print('[patch-metacubexd] useConnect.ts already patched, skip')
        return
    if USE_CONNECT_OLD not in s:
        fail(f'{p} 未找到兜底默认值 return FALLBACK_BACKEND_URL, 补丁未生效 (上游可能已改版)')
    p.write_text(s.replace(USE_CONNECT_OLD, USE_CONNECT_NEW))
    print('[patch-metacubexd] useConnect.ts: fallback now follows window.location.origin')


def patch_index_html(p: pathlib.Path):
    s = p.read_text()
    if MIGRATE_MARK in s:
        print('[patch-metacubexd] index.html migration script already present, skip inject')
        return
    body_close = '</body>'
    if body_close not in s:
        fail(f'{p} 未找到 </body>, 无法注入迁移脚本')
    migrate = MIGRATE_FILE.read_text().strip()
    p.write_text(s.replace(body_close, migrate + '\n' + body_close))
    print('[patch-metacubexd] index.html: injected migration script')


def main():
    if len(sys.argv) != 2:
        fail(f'用法: {sys.argv[0]} <metacubexd 源码目录|构建产物 public 目录>')
    if not MIGRATE_FILE.exists():
        fail(f'缺少迁移脚本文件: {MIGRATE_FILE}')

    target = pathlib.Path(sys.argv[1])

    src_config_js = target / CONFIG_JS_REL
    src_use_connect = target / USE_CONNECT_REL
    dist_index_html = target / 'index.html'

    if src_config_js.exists():
        # 源码阶段
        if not src_use_connect.exists():
            fail(f'{target} 不是有效的 metacubexd 源码目录 (缺少 {USE_CONNECT_REL})')
        patch_config_js(src_config_js)
        patch_use_connect(src_use_connect)
        print('[patch-metacubexd] source patches applied OK')
    elif dist_index_html.exists():
        # 产物阶段 (Nuxt build 输出)
        patch_index_html(dist_index_html)
        print('[patch-metacubexd] dist patches applied OK')
    else:
        fail(f'{target} 既不是 metacubexd 源码目录, 也不是构建产物 public 目录')


if __name__ == '__main__':
    main()
