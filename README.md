<div align="center">
<img src="docs/Logo.png" width=200px>

<h1>TPClash</h1>

TPClash(Transparent proxy tool for Clash)，是一个用于 Clash 的透明代理辅助工具, 由于众所周知的原因~~手笨~~而创建的.

</div>

## 一、TPClash 是什么

TPClash 可以自动安装 ~~Clash Premium~~（已停更）/ Mihomo, 并自动配置基于 Tun 的透明代理.

**TPClash 的透明代理规则、日志配置、Dashboard(UI) 配置等全部从标准的 Clash 配置文件内读取, 并完成自适应; TPClash 暂时不会创建自己的自定义
配置文件(减轻使用负担).**

## 二、一键安装

支持 systemd 的 Linux 系统可通过脚本一键下载并安装最新版 TPClash(mihomo):

```sh
# 安装最新版(默认读取 /etc/clash.yaml 配置)
bash <(curl -fsSL https://raw.githubusercontent.com/Sakurasan/tpclash/master/install.sh)

# 指定远程/本地配置文件, 并安装后立即启动
bash <(curl -fsSL https://raw.githubusercontent.com/Sakurasan/tpclash/master/install.sh) \
  --config https://example.com/clash.yaml --start

# 国内网络可搭配 ghproxy 镜像加速下载
bash <(curl -fsSL https://raw.githubusercontent.com/Sakurasan/tpclash/master/install.sh) --with-ghproxy
```

脚本会自动检测架构并下载对应平台的 `tpclash-mihomo` 二进制, 安装到 `/usr/local/bin/tpclash`, 若系统支持则注册为 systemd 服务。
更多参数请执行 `bash install.sh --help` 查看。

## 三、使用教程

为了使README更加整洁干练，以突出重要内容，分成了两部分。

若您需要使用教程，请[点击这里](GUIDE.md)跳转到使用教程

（不使用GitHub Wiki的原因是因为不方便备份）

## 四、TPClash 做了什么

**TPClash 在启动后会进行如下动作:**

- 1、创建 `/data/clash` 目录(可自行指定成其他目录), 并将其作为 Clash 的 `Home Dir`
- 2、将 Clash 二进制文件、Dashboard(官方+yacd)、必要的 ruleset、Country.mmdb 释放到 `/data/clash` 目录
- 3、从本地或远程读取配置, 进行模版解析后复制到 `/data/clash/xclash.yaml`
- 4、启动官方的 Clash, 并设置必要参数, 比如 `-ext-ui`、`-d` 等
- 5、选择性进行网络配置, 例如为 Docker 用户自动设置 nftables
- 6、在后台持续监视本地或远程配置文件变动, 然后自动重载

## 五、如何编译 TPClash

由于 TPClash 是一个集成工具, 所以在编译前请安装好以下工具链:

- git
- curl
- jq
- tar
- gzip
- nodejs(用于编译 Dashboard)
- pnpm(Dashboard 编译所需依赖工具, 可通过 `npm i -g xxx` 安装)
- golang 1.21+
- [mise](https://mise.jdx.dev/)(集成了 go-task 类似的任务运行器与工具链管理)

项目内的 `mise.toml` 已写好工具链声明与自动编译任务, 只需执行:

```sh
git clone https://github.com/Sakurasan/tpclash.git
cd tpclash
mise install    # 安装 node/golang 等工具链
mise run        # 构建全部平台并打包到 build/dist/
```

**其他高级编译(例如单独编译特定平台)请执行 `mise tasks` 查看.**

常用构建任务:

| 命令 | 说明 |
| --- | --- |
| `mise run default` | 构建全部支持平台并打包 |
| `mise run build-all` | 构建全部支持平台(latest mihomo) |
| `mise run package` | 将已构建产物打包到 build/dist/ |
| `mise run linux-arm64-mihomo` | 仅构建 linux/arm64 |
| `mise run linux-amd64-mihomo` | 仅构建 linux/amd64 |
| `mise run linux-amd64-v3-mihomo` | 仅构建 linux/amd64-v3 |
| `mise run clean` | 清理构建缓存 |

支持的全部平台: `386`, `amd64`, `amd64-v3`, `arm64`, `arm32`, `riscv64`。

## 六、其他说明

TPClash 默认释放的文件包含了 [Loyalsoldier/clash-rules](https://github.com/Loyalsoldier/clash-rules) 相关文件, 可在规则中直接使用;

**TPClash 同时也释放了 [Hackl0us/GeoIP2-CN](https://github.com/Hackl0us/GeoIP2-CN) 项目的 Country.mmdb 文件, 该 GeoIP 数据库
仅包含中国大陆地区 IP, 所以如果使用 `GEOIP,US,PROXY` 等其他国家规则会失败.**

## 七、复活版TPClash频道&讨论群

Telegram 频道: [https://t.me/tpclash](https://t.me/tpclash)

Telegram 交流群：[https://t.me/+98SPc9rmV8w3Mzll](https://t.me/+98SPc9rmV8w3Mzll)

## Stargazers over time
[![Stargazers over time](https://starchart.cc/Sakurasan/tpclash.svg?variant=adaptive)](https://starchart.cc/Sakurasan/tpclash)
