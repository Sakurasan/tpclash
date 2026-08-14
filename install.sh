#!/usr/bin/env bash
#
# TPClash 一键安装脚本
#
# 作用: 自动检测系统架构, 从 GitHub Releases 下载对应平台的 TPClash(mihomo) 二进制
#       并安装为 systemd 服务(若系统支持), 同时可自动启动服务.
#
# 用法:
#   bash install.sh                       # 安装最新版, 使用 /etc/clash.yaml 配置
#   bash install.sh --config <url|path>   # 指定 clash 配置(本地路径或远程 URL)
#   bash install.sh --version <tag>       # 指定版本 tag(默认 latest)
#   bash install.sh --with-ghproxy        # 通过 mirror.ghproxy.com 镜像下载
#   bash install.sh --start               # 安装完成后立即启动服务
#   bash install.sh --help                # 查看帮助
#
# 环境变量:
#   TPCLASH_ARCH     手动指定架构(如 amd64-v3/arm64/386), 默认自动检测
#   GITHUB_TOKEN     设置后可用于提升 GitHub API 限速
#
set -euo pipefail

# --------------------------------------------------------------------------
# 默认配置
# --------------------------------------------------------------------------
REPO_OWNER="TPClash"
REPO_NAME="tpclash"
GH_API="https://api.github.com/repos/${REPO_OWNER}/${REPO_NAME}/releases/latest"
GH_RELEASE="https://github.com/${REPO_OWNER}/${REPO_NAME}/releases/download"
GH_PROXY="https://mirror.ghproxy.com/"
VERSION="latest"
CONFIG_PATH="/etc/clash.yaml"
WITH_GHPROXY=0
START_SERVICE=0

usage() {
    sed -n '2,12p' "$0"
    exit 0
}

# --------------------------------------------------------------------------
# 辅助函数
# --------------------------------------------------------------------------
log()  { printf '\033[1;32m[install]\033[0m %s\n' "$*"; }
warn() { printf '\033[1;33m[install]\033[0m %s\n' "$*"; }
die()  { printf '\033[1;31m[install]\033[0m %s\n' "$*" >&2; exit 1; }

# 自动检测架构 -> TPClash 构建产物中的架构标识
detect_arch() {
    if [ -n "${TPCLASH_ARCH:-}" ]; then
        echo "$TPCLASH_ARCH"
        return
    fi

    local mach
    mach="$(uname -m)"
    case "$mach" in
        x86_64|amd64)
            # 大部分云厂商 CPU 均支持 amd64-v3, 可自行通过 TPCLASH_ARCH=amd64 强制兼容版
            echo "amd64-v3"
            ;;
        aarch64|arm64)        echo "arm64"  ;;
        armv7l|armhf)         echo "armv7"  ;;
        armv6l)               echo "armv6"  ;;
        armv5te|arm)          echo "armv5"  ;;
        i386|i486|i586|i686)  echo "386"    ;;
        mips64le)             echo "mips64le" ;;
        mips64)               echo "mips64" ;;
        mipsel)               echo "mipsle" ;;
        mips)                 echo "mips"   ;;
        *) die "不支持的架构: $mach, 请通过 TPCLASH_ARCH 手动指定" ;;
    esac
}

# 解析命令行参数
parse_args() {
    while [ $# -gt 0 ]; do
        case "$1" in
            --config)    shift; CONFIG_PATH="${1:-}"; [ -n "$CONFIG_PATH" ] || die "--config 需要参数" ;;
            --version)   shift; VERSION="${1:-}";      [ -n "$VERSION" ]  || die "--version 需要参数" ;;
            --with-ghproxy) WITH_GHPROXY=1 ;;
            --start)     START_SERVICE=1 ;;
            --help|-h)   usage ;;
            *) die "未知参数: $1 (使用 --help 查看帮助)" ;;
        esac
        shift
    done
}

# 获取最新 release 版本号
get_latest_version() {
    local ver
    if ! ver="$(curl -sSL ${GITHUB_TOKEN:+-H "Authorization: Bearer ${GITHUB_TOKEN}"} "$GH_API")"; then
        die "查询最新版本失败: $ver"
    fi
    # 提取 tag_name, 去掉开头的 v
    ver="$(printf '%s' "$ver" | sed -n 's/.*"tag_name":"\(v\?[^"]*\)".*/\1/p')"
    [ -n "$ver" ] || die "无法解析最新版本: $GH_API"
    echo "$ver"
}

# --------------------------------------------------------------------------
# 主流程
# --------------------------------------------------------------------------
main() {
    parse_args "$@"

    command -v curl >/dev/null 2>&1 || die "缺少 curl 命令, 请先安装"
    command -v uname >/dev/null 2>&1 || die "缺少 uname 命令"

    if [ "$(id -u)" != "0" ]; then
        warn "建议以 root 运行: sudo bash $0 --config $CONFIG_PATH"
    fi

    local arch bin_name down_url target
    arch="$(detect_arch)"
    log "检测到架构: $arch"

    if [ "$VERSION" = "latest" ]; then
        VERSION="$(get_latest_version)"
    fi
    log "目标版本: v${VERSION#v}"

    bin_name="tpclash-mihomo-linux-${arch}"
    down_url="${GH_RELEASE}/v${VERSION#v}/${bin_name}"
    if [ "$WITH_GHPROXY" = "1" ]; then
        down_url="${GH_PROXY}${down_url}"
    fi

    target="/usr/local/bin/tpclash"
    log "下载 $bin_name -> $target"
    if ! curl -fSL --progress-bar "$down_url" -o "$target"; then
        # 部分架构(如 amd64)可能只有兼容版产物, 尝试回退
        if [ "$arch" = "amd64-v3" ]; then
            warn "未找到 amd64-v3 产物, 回退到 amd64 兼容版..."
            down_url="${GH_RELEASE}/v${VERSION#v}/tpclash-mihomo-linux-amd64"
            [ "$WITH_GHPROXY" = "1" ] && down_url="${GH_PROXY}${down_url}"
            curl -fSL --progress-bar "$down_url" -o "$target" || die "下载失败: $down_url"
            warn "已回退安装兼容版(amd64), 可通过 TPCLASH_ARCH=amd64-v3 强制使用 v3 版"
        else
            die "下载失败: $down_url"
        fi
    fi
    chmod +x "$target"
    log "二进制安装完成: $target"

    # 尝试通过内置 install 命令安装为 systemd 服务
    if command -v systemctl >/dev/null 2>&1; then
        log "检测到 systemd, 安装为系统服务..."
        "$target" install --config "$CONFIG_PATH"
        systemctl daemon-reload >/dev/null 2>&1 || warn "daemon-reload 失败"
        if [ "$START_SERVICE" = "1" ]; then
            log "启动并开启自启..."
            systemctl enable --now tpclash >/dev/null 2>&1 || systemctl start tpclash
            systemctl status tpclash --no-pager || true
        else
            warn "如需启动服务请执行: systemctl start tpclash"
        fi
    else
        warn "当前系统不支持 systemd, 请直接运行: $target -c $CONFIG_PATH"
    fi

    log "TPClash(v${VERSION#v}) 安装完成!"
}

main "$@"