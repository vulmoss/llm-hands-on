# 交给 Agent 的部署手册：DVWA + Juice Shop + Ollama

## 0. 执行任务与边界

请在测试节点部署本模块，记录代码提交、镜像摘要和每条验收结果。默认登录 `llm2@192.168.2.16`，仅调用 `.15` 的 Ollama。容器不是 VM 级安全隔离；`.16` 仍有 PD/TiKV，若做容器逃逸、任意执行器研究或资源压力实验，应改用独立新 VM，本课程脚本不覆盖这些实验。

优先配置：Ubuntu 22.04/24.04 x86_64、Python 3.10+、Docker Engine 28+、Compose 2.24+，至少 4 GB available RAM 和 10 GB 磁盘余量。容器限额约 2.25 GiB RAM、2.5 CPU，总资源只是初始预算；与已有服务并存时每次只启用一个靶场。若新建专用 VM，建议 4 vCPU / 8 GB RAM / 40 GB 磁盘，IP 由现有网络规划分配，不能猜一个未占用地址。

环境历史资料：`.15` 有 Docker 与 Vulfocus，但不把本课程直接塞到 `.15`；`.16` 是否有 Docker、可否正常 SSH 未在本次证实。不要重启 TiDB、修改 ESXi、批量拉取 Vulfocus 镜像或更改已有 Docker daemon 配置。

完成标准：固定源码 + 三个镜像摘要 → Compose 校验 → DVWA 初始化/登录 → SQLi 最小对照 → Juice Shop 首页/限定挑战 → Agent 离线与真实模型实验 → HANDOFF.md。环境启动、应用登录、挑战完成是三个不同验收层。

## 1. 登录、目录与基线

在 Mac：

```bash
ssh -o ConnectTimeout=5 llm2@192.168.2.16
```

使用已有认证方式；主机指纹按资产记录核对，不关闭校验，不把密码写到仓库。认证失败时交接具体错误和阶段，不试探其他账号。

在 `.16` 的 Bash：

```bash
set -Eeuo pipefail
umask 077
mkdir -p "$HOME/labs"
cd "$HOME/labs"
git clone https://github.com/vulmoss/llm-hands-on.git llm-immersion-source
cd llm-immersion-source
export COURSE="$PWD/05-security/immersive-12-stage"
export LAB_STATE="$HOME/labs/immersion-state"
export PYTHONPATH="$PWD/src"
mkdir -p "$LAB_STATE/evidence"
git rev-parse HEAD | tee "$LAB_STATE/evidence/code-commit.txt"
python3 --version
hostname
id
free -h
df -h .
systemctl is-active pd-2379.service tikv-20160.service || true
ss -ltn
```

交付归档包含固定版本的代码；在线克隆时以交付说明指定的提交为准，在 clone 后执行 `git checkout --detach 指定的完整SHA` 再保存 code-commit。不要在已有目录反复 clone 或强制覆盖修改。第二次执行时进入原目录，读取已记录的提交与镜像锁；不要自动 pull main。

记录节点资源与共享服务前置状态到 `$LAB_STATE/evidence/preflight.txt`。若有代理，记录是否影响 registry 和 Ollama，但不要保存带认证信息的代理 URL。

## 2. Docker 前置条件

```bash
python3 "$COURSE/scripts/labctl.py" plan --state "$LAB_STATE"
python3 "$COURSE/scripts/labctl.py" preflight --state "$LAB_STATE"
```

preflight 只检查 Docker/Compose、当地 Unix socket 和同名项目归属。内存、磁盘、节点身份及共享服务仍需第 1 节人工核对。`plan` 完全离线，不会连接 Docker。

Docker 不存在时，由有管理员权限的操作者按以下官方 apt 方式安装；已有 Docker 满足版本则跳过。先检查 docker.io / containerd / runc / podman-docker 等是否已有业务依赖，发现冲突就停，不按通用教程自动卸载。

```bash
# 仅适用于确认可安装 Docker 的 Ubuntu 测试节点；已有运行时不要盲目执行。
sudo apt-get update
sudo apt-get install -y ca-certificates curl
sudo install -m 0755 -d /etc/apt/keyrings
sudo curl -fsSL https://download.docker.com/linux/ubuntu/gpg -o /etc/apt/keyrings/docker.asc
sudo chmod a+r /etc/apt/keyrings/docker.asc
. /etc/os-release
printf 'Types: deb\nURIs: https://download.docker.com/linux/ubuntu\nSuites: %s\nComponents: stable\nArchitectures: %s\nSigned-By: /etc/apt/keyrings/docker.asc\n' \
  "$VERSION_CODENAME" "$(dpkg --print-architecture)" | sudo tee /etc/apt/sources.list.d/docker.sources > /dev/null
sudo apt-get update
sudo apt-get install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
```

脚本以当前用户调用 docker，需已有访问 Docker socket 的权限。新增 docker 组成员相当于扩展主机控制权限，不能在教学脚本中静默修改；让管理员按测试节点账户策略配置后重新登录。脚本不支持远程 Docker context，以免在错误主机创建靶场。

## 3. 首次锁定镜像，再按摘要复现

```bash
python3 "$COURSE/scripts/labctl.py" lock --state "$LAB_STATE"
python3 "$COURSE/scripts/labctl.py" config --target both --state "$LAB_STATE"
```

bootstrap 来源是官方 `ghcr.io/digininja/dvwa:latest`、`mariadb:10.11`、`bkimminich/juice-shop:v20.2.0`。**这些标签不是最终可重复版本**。lock 拉取 `linux/amd64` 后从实际 Docker inspect 记录 RepoDigest、Image ID、平台与时间，生成 `$LAB_STATE/images.lock.json`；随后启动只用 `repo@sha256:...` 且禁止隐式拉取。

保存锁文件及源码提交才能重现同一组环境。第一次锁定的 DVWA 随 bootstrap 标签变化，部署 agent 必须完成后续初始化和 SQLi 验收；本文未捏造一个未经拉取确认的 digest。锁已存在则脚本拒绝重写。升级先停止旧项目、保留锁和数据，在新状态目录锁定并重新验收；同名运行项目的 state 不符会被拒绝。

Compose 数据库密码是明确标记的合成实验值，不是你的现有数据库密码。MariaDB 没有发布宿主端口；DVWA 的 DB_SERVER 固定为 Compose 内的 db，不连接 TiDB。

## 4. 启动 DVWA

```bash
python3 "$COURSE/scripts/labctl.py" up --target dvwa --state "$LAB_STATE"
python3 "$COURSE/scripts/labctl.py" status --target dvwa --state "$LAB_STATE"
curl --noproxy '*' --fail --silent --show-error http://127.0.0.1:4280/login.php -o "$LAB_STATE/evidence/dvwa-login.html"
```

Compose 等待数据库和应用健康，最长 180 秒；若启动失败，先运行本节 labctl status 保存状态，并用 `docker ps -a --filter label=com.docker.compose.project=llm-immersion` 定位本课容器后保存其 `docker logs 容器ID`，不重复 up 直到弄清原因。CLI 上 up 发现已监听端口会停止而不是杀进程；要重启自己的项目，先用 stop，再 up。

两个网络均为 internal，减少靶场向外部网络发起请求；只支持本地挑战。不要把这个配置当成容器到宿主完全不可达的安全保证。不给容器 docker.sock、host network、privileged 或宿主业务目录。

## 5. 隧道、DVWA 初始化与 SQLi 对照

Mac 新终端：

```bash
ssh -N -o ExitOnForwardFailure=yes -o ServerAliveInterval=30 \
  -L 127.0.0.1:4280:127.0.0.1:4280 \
  -L 127.0.0.1:4300:127.0.0.1:4300 \
  llm2@192.168.2.16
```

1. 浏览器访问 `http://127.0.0.1:4280/setup.php`，在该教学实例点击 Create / Reset Database。此动作重置的是独立 DVWA 数据库；不是现有 TiDB。
2. 打开 `/login.php`，教学默认用户 `admin` / `password`，保存登录页与登录后截图。初始化失败时检查专用 db 日志，不修改 `.15`。
3. 在 DVWA Security 确认 Low。本 Compose 指定默认 Low，但已有会话的设置仍可能不同。
4. 在 SQL Injection 模块先提交 ID `1`，再提交 `1' OR '1'='1`。只观察教学姓名行数，不导出表或密码。
5. 可在 `.16` 或经过隧道的 Mac 执行以下脚本，记录正常/异常两次请求的行数和响应摘要，不保存 Cookie/CSRF token。

```bash
python3 "$COURSE/scripts/dvwa_sqli.py" --output "$LAB_STATE/evidence/dvwa-sqli.json"
```

预期正常 1 行，异常多于 1 行；退出 0 表示观察到该 Low 教学模式，1 表示没有观察到，2 表示初始化/登录/连接/解析错误。脚本只允许固定回环 4280，不接受任意目标 URL，不自动初始化数据库。HTTP 成功不等于发现所有 SQLi 类型。

修复原理与自动正反对照继续用上一模块的 SQLite 参数化实验；DVWA 的不同 security level 不直接等同于你完成了生产修复。手工切换 Impossible 后再测时，需要保持相同已登录会话；当前脚本新登录默认 Low，不能拿它冒充 Impossible 测试。

## 6. 切换 Juice Shop

```bash
python3 "$COURSE/scripts/labctl.py" stop --target dvwa --state "$LAB_STATE"
python3 "$COURSE/scripts/labctl.py" up --target juice --state "$LAB_STATE"
python3 "$COURSE/scripts/labctl.py" status --target juice --state "$LAB_STATE"
curl --noproxy '*' --fail --silent --show-error http://127.0.0.1:4300/ -o "$LAB_STATE/evidence/juice-home.html"
```

浏览器打开 `http://127.0.0.1:4300`，确认应用标题与页面；在自己这个实例的教程/Score Board 中选一项基础 Web 挑战。项目版本会影响挑战内容和 UI，按镜像锁中的版本记录实际名称，不强行套用旧截图。

本次不接 Juice Shop 内置聊天机器人、云服务或区块链挑战。当前上游的某些挑战依赖外部 AI/服务；内部网络配置下可能不可用，不算整个靶场失败。课程的 Ollama 由宿主 Python 调用，与 Juice Shop 内置机器人分开。

容器 stop/start 保留容器层，down/up 会重建 Juice Shop；浏览器本地存储也可能保存进度。重开挑战前先导出学习记录、使用新浏览器配置，并说明状态是否清空，不能把前一次完成标记当新一轮成绩。

## 7. Ollama 与 Agent 练习

在源码根目录的 `.16`：

```bash
export PYTHONPATH="$PWD/src"
export OLLAMA_BASE_URL=http://192.168.2.15:11434
export OLLAMA_MODEL=qwen2.5:1.5b
export OLLAMA_TIMEOUT=180
export LLM_MAX_TOKENS=768
export LLM_TEMPERATURE=0
python3 -m llm_lab.web_security doctor
python3 "$COURSE/scripts/practice.py" loop --mode normal --output "$LAB_STATE/evidence/agent-fixture.json"
python3 "$COURSE/scripts/practice.py" loop --live --output "$LAB_STATE/evidence/agent-live.json"
```

默认脚本替身的成功不证明真实模型支持工具调用。真实 1.5B 若不调用工具、产生未知参数、提前回答或耗尽预算，都应记录；先看 trace，按需要再小规模对比已有 7B，不能自动拉取新大模型或并发调用。

完整 A/B、回归、SKILL 与 PoC 门禁流程见 STAGES.md。所有原始模型输出保存在本地证据目录，不自动执行其中内容。

## 8. 离线镜像搬运

在可访问官方 registry 的 Linux amd64 Docker 主机运行同一份 labctl.py lock，保存锁文件。将镜像导出为一个包：

```bash
python3 - "$LAB_STATE" <<'PY'
import json, pathlib, subprocess, sys
state = pathlib.Path(sys.argv[1])
images = json.loads((state/'images.lock.json').read_text())['images']
# 保存 bootstrap tag；同时保留原始 digest 与 Image ID 供目标核对。
subprocess.run(['docker','save','-o',str(state/'images.tar'),*[x['seed'] for x in images.values()]],check=True)
PY
sha256sum "$LAB_STATE/images.tar" "$LAB_STATE/images.lock.json"
```

把包、锁、源码归档和 SHA256 记录一起传到目标，逐项校验后 `docker load -i images.tar`。**docker save/load 可能不保留 RepoDigests**：导入后检查锁内 `repo@sha256` 是否能被 `docker image inspect` 解析；不行就不能直接用当前摘要启动脚本。可在目标恢复 registry 访问后按 digest pull，或由管理员搭建经过校验的内部 registry。不要为了离线启动把摘要替换回 latest 后仍宣称同一版本。

因此在线首次锁定是默认可执行路径；“完全断网且无内部 registry”的额外镜像分发需单独验收。这条限制必须带进交接报告，不能靠替换随机第三方镜像解决。

## 9. 停止、日志与交接

```bash
python3 "$COURSE/scripts/labctl.py" stop --target both --state "$LAB_STATE"
python3 "$COURSE/scripts/labctl.py" down --state "$LAB_STATE"
```

down 移除本课容器和网络，但不接受 `-v`，保留 DVWA 数据卷。不要执行 docker system prune、删除所有卷或修改其他项目。要重置练习数据，用该实例 DVWA setup 页面；确认会清除的仅为合成数据。

交接报告放 `$LAB_STATE/HANDOFF.md`，至少填写：节点/用户/版本、源码 SHA、三个镜像摘要、state 路径、Docker 与 Compose 版本、共享服务前后状态、实际端口绑定、DVWA 初始化/登录/SQLi 结果、Juice 首页与挑战实际名称、脚本替身结果、真实模型结果、人工误判修正、未验证项、停止/重启方法。登录账号不等于系统管理账号，不混用真实凭据。

启动成功后仍要回看 `docker ps` / inspect 的 HostIp：发布端口只能是 127.0.0.1。如果主机已有服务性能明显下降，先停止本课容器并记录，不修改共享服务资源配置。
