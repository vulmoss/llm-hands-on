# Web × AI 安全实验课：测试环境部署与 Agent 交接手册

文档日期：2026-09-23。文档检查：20 段 Bash / 6 段 Python 语法通过；版本切换、重复执行、服务文件冲突保护和回滚已在临时目录验证；在线验收脚本已对两个本地实验进程验证。Linux 用户级 systemd、SSH 持久化与 .16 实际部署仍由接手 agent 执行验收。

用途：将本文件交给另一个 agent，由其在你的测试环境部署、验证并交接。**本文件是待执行操作手册，不是已完成部署的证明。**

## 0. 给接手 Agent 的任务

> 请按本文件在 192.168.2.16 上部署 Web × AI 教学模块。先核对登录身份与环境，再按阶段执行；每阶段记录命令退出状态和证据。采用文中固定代码版本，不把 main 的后续变更自动带入。部署后运行 12 组对照、两个服务的在线验收和一次 Ollama 调用，最后填交接表。已有修改和共享服务应保留；遇到认证、端口归属或环境不符时明确报告阻塞位置。文中的预期结果不等于实测结果。未执行的浏览器、模型或重启检查必须标为未验证。

### 完成定义

- `.16` 上部署固定版本源码，记录完整提交号和部署路径。
- 12 组自动对照全部通过，保存 JSON 原始证据。
- 漏洞版 `127.0.0.1:8787` 与修复版 `127.0.0.1:8788` 均可用；完成健康、匿名访问和所有权对照。
- 从 Mac 通过 SSH 隧道可打开页面；有浏览器能力时完成点击验收。
- `.16` 能调用 `.15:11434` 的 `qwen2.5:1.5b`，保存一次 AI 草稿并人工指出其是否误判。
- 明确服务在退出 SSH、重新登录、重启后的持久化状态；没有验证重启就不能写“重启验证通过”。
- 写出交接报告和回滚信息。若 Ollama 不通，可以先交接“Web 模块通过、AI 阶段阻塞”，不能写整体全部完成。

### 范围

本次部署的是学习模块，不是完整自动化漏洞扫描平台。不会因此启动 Vulfocus 靶场、扫描真实资产、改 TiDB、安装 DeepAudit 或部署完整 IdP/S3。新服务只监听回环地址，使用合成会话与数据，**不可作为生产服务或直接暴露到局域网/公网**。

## 1. 已知环境与待核实项

| 节点 | 已知角色 | 本次操作 |
|---|---|---|
| Mac / 控制端 | 编辑、Git、浏览器、Burp | SSH、隧道、浏览器验收；可准备离线包 |
| 192.168.2.15 | Ollama、TiDB SQL、PD/TiKV、Vulfocus、监控 | 仅调用现有 Ollama 11434，默认 1.5B、并发 1 |
| 192.168.2.16 | Ubuntu 22.04、Python 3.10、开发环境、PD/TiKV | 首选部署节点，登录用户 `llm2` |
| 192.168.2.17 | TiUP 控制、PD/TiKV | 本次不操作 |

2026-09-23 已验证：代码的 Python 3.10 / 3.12 GitHub CI 通过，Mac 上 106 项 pytest 与 9 项提示词库测试通过，Ollama 1.5B 可调用。**未在 .16 实际部署**：当时非交互 SSH 返回 `Permission denied (publickey,password)`。这些是历史记录，部署时仍要核对。

文档不含 SSH 密码、GitHub Token 或数据库密码。用已有 SSH agent / 正常密码登录；需要用户提供认证时只请求登录条件，不要求用户把密码写入此文件、命令行或 GitHub。不要从旧 Git remote 中提取嵌入凭据。公网仓库拉取不需要 Token。

## 2. 固定参数与目录

| 参数 | 固定值 / 默认值 |
|---|---|
| 源仓库 | `https://github.com/vulmoss/llm-hands-on.git` |
| 已测代码提交 | `7a4680768418f4491d7c2fa629f2011c38715c08` |
| 部署基目录 | `/home/llm2/labs/web-ai-course` |
| 版本目录 | `releases/7a4680768418` |
| 当前版本入口 | `current` 符号链接 |
| 证据 | `evidence/<UTC部署时间>/` |
| 用户级服务 | `web-ai-vulnerable.service`、`web-ai-fixed.service` |
| Ollama | `http://192.168.2.15:11434`，`qwen2.5:1.5b` |

固定 SHA 对应课程代码；本操作文档可以来自后续文档提交，不要求二者 SHA 相同。若换代码版本，先重新验证再修改参数与交接报告。

以下 Linux 命令使用 **Bash**。除特别标为 Mac 外，都在 `.16` 的 `llm2` 会话执行；不要把 Linux 命令直接粘贴进 Mac 终端。后续各块使用本节变量，断开后按下文“恢复会话”重新导入。

## 3. 登录与初始化（Mac → .16）

在 Mac 执行：

```bash
ssh -o ConnectTimeout=5 llm2@192.168.2.16
```

首次出现主机密钥提示时，使用已知资产记录核对指纹；不要用 `StrictHostKeyChecking=no`。登录失败就记录此阶段阻塞，不要修改 sshd 或批量尝试密码。

登录后进入 Bash 并初始化：

```bash
bash
set -Eeuo pipefail
umask 077
export LAB_BASE=/home/llm2/labs/web-ai-course
export LAB_PIN=7a4680768418f4491d7c2fa629f2011c38715c08
export LAB_RELEASE="$LAB_BASE/releases/${LAB_PIN:0:12}"
export LAB_RUN="$(date -u +%Y%m%dT%H%M%SZ)"
export LAB_EVIDENCE="$LAB_BASE/evidence/$LAB_RUN"
export LAB_PYTHON="$(command -v python3)"
export OLLAMA_BASE_URL=http://192.168.2.15:11434
export OLLAMA_MODEL=qwen2.5:1.5b
export OLLAMA_TIMEOUT=180
export LLM_MAX_TOKENS=768
[ "$(id -un)" = llm2 ] || { echo 'STOP: 需要 llm2 用户'; exit 1; }
ip -4 -o addr show | python3 -c 'import sys; assert "192.168.2.16/" in sys.stdin.read(), "STOP: 非预期部署节点"'
mkdir -p "$LAB_BASE/releases" "$LAB_EVIDENCE"
# 仅保存本文件定义的非敏感变量；不导出整个 shell 环境。
{
  for key in LAB_BASE LAB_PIN LAB_RELEASE LAB_RUN LAB_EVIDENCE LAB_PYTHON OLLAMA_BASE_URL OLLAMA_MODEL OLLAMA_TIMEOUT LLM_MAX_TOKENS; do
    printf 'export %s=%q\n' "$key" "${!key}"
  done
} > "$LAB_EVIDENCE/session.env"
printf '本次证据目录：%s\n' "$LAB_EVIDENCE"
```

记录打印出来的路径。恢复会话时，进入 `.16` 后执行 `bash`、`set -Eeuo pipefail`，再 `source /home/llm2/labs/web-ai-course/evidence/实际时间/session.env`。不要重新生成另一个时间戳后误把两次结果混合。

## 4. 预检查与资源基线

```bash
{
  date -u
  hostname
  id
  "$LAB_PYTHON" --version
  "$LAB_PYTHON" -c 'import sys,sqlite3; assert sys.version_info >= (3,10); print("sqlite",sqlite3.sqlite_version)'
  command -v git curl ss systemctl loginctl
  df -h "$LAB_BASE"
  free -h
  ss -ltn
} | tee "$LAB_EVIDENCE/preflight.txt"
{
  for unit in pd-2379.service tikv-20160.service node_exporter-9100.service blackbox_exporter-9115.service; do
    printf '%s ' "$unit"
    systemctl is-active "$unit" || true
  done
} > "$LAB_EVIDENCE/shared-services-before.txt"
```

建议基目录所在文件系统至少 1 GB 可用、内存至少 512 MB available；这是部署余量，不是性能保证。只读记录共享服务状态，不能为通过本课而重启数据库或推理服务。

首次部署检查端口；如果是更新已有本课服务，先完成第 12 节的“更新前处理”，再进行此检查：

```bash
"$LAB_PYTHON" - <<'PY'
import socket
for port in (8787, 8788):
    with socket.socket() as sock:
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        try:
            sock.bind(('127.0.0.1', port))
        except OSError as exc:
            raise SystemExit(f'STOP: {port} 已占用，先确认归属，不要 kill 未知进程：{exc}')
print('两个教学端口可用')
PY
```

如果被其他服务占用，停止在此，记录占用情况。可以另行选择两个端口，但必须同时修改服务、验收命令、隧道和文档；浏览器扩展默认限定 8787。

## 5. 获取固定版本（在线默认；离线替代见第 13 节）

本目录与用户原有 checkout 分离。不要覆盖 `/home/llm2` 下已有学习工程，也不要对其执行强制重置。

```bash
if [ ! -e "$LAB_RELEASE" ]; then
  git init "$LAB_RELEASE"
  git -C "$LAB_RELEASE" remote add origin https://github.com/vulmoss/llm-hands-on.git
fi
[ -d "$LAB_RELEASE/.git" ] || { echo 'STOP: 版本目录不是独立 Git 仓库'; exit 1; }
[ "$(git -C "$LAB_RELEASE" remote get-url origin)" = https://github.com/vulmoss/llm-hands-on.git ] || { echo 'STOP: remote 与预期不同'; exit 1; }
[ -z "$(git -C "$LAB_RELEASE" status --porcelain)" ] || { echo 'STOP: 版本目录有未提交文件'; exit 1; }
git -C "$LAB_RELEASE" fetch --depth=1 origin "$LAB_PIN"
git -C "$LAB_RELEASE" checkout --detach "$LAB_PIN"
[ "$(git -C "$LAB_RELEASE" rev-parse HEAD)" = "$LAB_PIN" ]
git -C "$LAB_RELEASE" rev-parse HEAD | tee "$LAB_EVIDENCE/code-sha.txt"
cd "$LAB_RELEASE"
export PYTHONPATH="$LAB_RELEASE/src"
```

验收：完整 SHA 与 LAB_PIN 一致。这里不需要 pip、npm、Docker、数据库账号或云模型 API Key。

## 6. 部署前离线验收

```bash
cd "$LAB_RELEASE"
export PYTHONPATH="$LAB_RELEASE/src"
"$LAB_PYTHON" -m llm_lab.web_security list | tee "$LAB_EVIDENCE/lab-list.txt"
"$LAB_PYTHON" -m llm_lab.web_security run --all --output "$LAB_EVIDENCE/http-controls.json" | tee "$LAB_EVIDENCE/http-controls.log"
"$LAB_PYTHON" -m llm_lab.web_security frontend > "$LAB_EVIDENCE/frontend-fixtures.json"
"$LAB_PYTHON" scripts/gen_security_catalog.py --check | tee "$LAB_EVIDENCE/catalog-check.txt"
"$LAB_PYTHON" - <<'PY'
import json, os
from pathlib import Path
p = Path(os.environ['LAB_EVIDENCE']) / 'http-controls.json'
d = json.loads(p.read_text())
assert d['kind'] == 'local-http-controls'
assert len(d['cases']) == 12 and d['passed'] is True
assert all(m['passed'] is True for c in d['cases'] for m in c['modes'].values())
print('PASS: 12 组 × 漏洞版/修复版，含正常请求对照')
PY
```

每组 `vulnerable=True` 和 `fixed=True` 表示两种模式都符合各自预期，不是两者都安全。程序退出 1 为对照失败，退出 2 为输入/连接等错误；不能只看最后一行日志。`set -o pipefail` 保证 tee 不掩盖失败。

可选的开发回归（有包源网络时，在隔离 venv 中执行）：

```bash
"$LAB_PYTHON" -m venv "$LAB_BASE/test-venv"
"$LAB_BASE/test-venv/bin/python" -m pip install pytest==8.4.2
PYTHONPATH="$LAB_RELEASE/src" "$LAB_BASE/test-venv/bin/python" -m pytest -q "$LAB_RELEASE/tests/security/test_web_course.py" | tee "$LAB_EVIDENCE/pytest-web-course.txt"
```

固定代码预期为 33 项。若系统没有 venv 或包源不可用，记录“可选 pytest 未执行”，不要升级全局 Python；第 6 节标准库 HTTP 对照仍是必做项。

## 7. 原子切换 current 与创建用户级服务

### 7.1 先核对用户服务管理器

```bash
systemctl --user show-environment > /dev/null
loginctl show-user llm2 -p Linger | tee "$LAB_EVIDENCE/linger-before.txt"
```

若用户服务管理器不可用，改用第 11 节前台方式，不要伪造为后台部署成功。若需退出 SSH 后长期运行或开机无人登录也启动，需要 `Linger=yes`。如果已有 sudo 权限且本次交接要求无人值守，可仅启用此用户：`sudo loginctl enable-linger llm2`，记录这项变更。没有该权限时保留前台方案或报告管理员操作项，不修改 sudoers。

**本次不重启共享 VM 验证开机启动。** 可以验收 enable 状态与重连，但开机实际验证另行安排。

### 7.2 记录旧版本并切换

```bash
"$LAB_PYTHON" - <<'PY'
import os
from pathlib import Path
base = Path(os.environ['LAB_BASE'])
release = Path(os.environ['LAB_RELEASE']).resolve()
current = base / 'current'
if current.exists() and not current.is_symlink():
    raise SystemExit('STOP: current 是实体目录，不覆盖')
previous = str(current.resolve(strict=True)) if current.is_symlink() else ''
evidence = Path(os.environ['LAB_EVIDENCE'])
record = evidence / 'previous-release.txt'
if not record.exists():
    record.write_text(previous + '\n')
next_link = base / ('current-next-' + os.environ['LAB_RUN'])
if next_link.exists() or next_link.is_symlink():
    raise SystemExit('STOP: 待切换链接已存在，先核对上次操作状态')
next_link.symlink_to(release, target_is_directory=True)
os.replace(next_link, current)
print('current ->', release)
PY
```

重新执行切换不会覆盖本次原始回滚记录。如果 current 是断链，先排查旧版本缺失，不继续切换。

### 7.3 生成服务定义（只写两个本课单位）

```bash
"$LAB_PYTHON" - <<'PY'
import os, shutil
from pathlib import Path
base = Path(os.environ['LAB_BASE'])
python = Path(os.environ['LAB_PYTHON'])
if any(ch in str(base) + str(python) for ch in ' \n\t"%'):
    raise SystemExit('STOP: 本手册服务路径要求不含空格、换行、引号或百分号')
units = Path.home() / '.config/systemd/user'
units.mkdir(parents=True, exist_ok=True)
backup = Path(os.environ['LAB_EVIDENCE']) / 'units-before'
backup.mkdir(exist_ok=True)
marker = '# Managed by llm-hands-on web-ai-course deployment\n'
# 先检查两个文件归属，再写入，避免只更新了一半才发现冲突。
for mode in ('vulnerable','fixed'):
    path = units / f'web-ai-{mode}.service'
    if path.is_symlink():
        raise SystemExit(f'STOP: 服务定义是符号链接：{path}')
    if path.exists() and not path.read_text().startswith(marker):
        raise SystemExit(f'STOP: 同名服务不属于本手册：{path}')
for mode, port in [('vulnerable',8787),('fixed',8788)]:
    path = units / f'web-ai-{mode}.service'
    if path.exists() and not (backup/path.name).exists():
        shutil.copy2(path, backup/path.name)
    path.write_text(marker + f'''[Unit]
Description=Web AI teaching lab ({mode})
After=network.target

[Service]
Type=simple
WorkingDirectory={base}/current
Environment=PYTHONPATH={base}/current/src
Environment=PYTHONUNBUFFERED=1
ExecStart={python} -m llm_lab.web_security serve --mode {mode} --port {port}
Restart=on-failure
RestartSec=3
KillSignal=SIGINT
TimeoutStopSec=10
NoNewPrivileges=true
UMask=0077
MemoryMax=512M
TasksMax=128
CPUQuota=100%

[Install]
WantedBy=default.target
''')
print('两个用户级服务定义已生成')
PY
systemctl --user daemon-reload
systemctl --user enable web-ai-vulnerable.service web-ai-fixed.service
systemctl --user restart web-ai-vulnerable.service web-ai-fixed.service
systemctl --user --no-pager status web-ai-vulnerable.service web-ai-fixed.service | tee "$LAB_EVIDENCE/service-status.txt"
```

这些上限只约束 `.16` 的教学服务，不约束 `.15` 的 Ollama。两个服务各有一个仅回环监听的临时内部回调端口，属 SSRF 教学实现；不要把它们误判为额外对外开放服务。会话、上传和数据库数据都在内存中，重启服务会重置。

## 8. 在线验收与模型连通

### 8.1 健康与权限矩阵（.16）

```bash
cd "$LAB_BASE/current"
export PYTHONPATH="$LAB_BASE/current/src"
"$LAB_PYTHON" - <<'PY' | tee "$LAB_EVIDENCE/live-services.json"
import json, time
from llm_lab.web_security.runner import request
results = []
for mode, port in [('vulnerable',8787),('fixed',8788)]:
    base = f'http://127.0.0.1:{port}'
    for attempt in range(10):
        try:
            health = request(base,'GET','/health')
            break
        except OSError:
            if attempt == 9:
                raise
            time.sleep(1)
    assert health['status'] == 200
    assert json.loads(health['body'])['mode'] == mode
    anonymous = request(base,'GET','/orders?id=1')
    own = request(base,'GET','/orders?id=1',{'Cookie':'sid=alice-lab'})
    other = request(base,'GET','/orders?id=2',{'Cookie':'sid=alice-lab'})
    bob = request(base,'GET','/orders?id=2',{'Cookie':'sid=bob-lab'})
    assert anonymous['status'] == 401
    assert own['status'] == bob['status'] == 200
    assert 'A-book' in own['body'] and 'B-book' in bob['body']
    assert other['status'] == (200 if mode == 'vulnerable' else 403)
    if mode == 'vulnerable':
        assert 'B-book' in other['body']
    assert request(base,'GET','/frontend/index.html')['status'] == 200
    results.append({'mode':mode,'health':health,'anonymous':anonymous,'own':own,'other':other,'bob':bob})
print(json.dumps({'passed':True,'services':results},ensure_ascii=False,indent=2))
PY
ss -ltnp | tee "$LAB_EVIDENCE/listeners-after.txt"
```

验收：8787/8788 的监听地址必须是 `127.0.0.1`，不能是 `0.0.0.0` 或 `::`。不要仅凭 systemctl 显示 active 判定服务可用。

### 8.2 Ollama（.16 发起）

```bash
"$LAB_PYTHON" -m llm_lab.web_security doctor | tee "$LAB_EVIDENCE/ollama-doctor.json"
"$LAB_PYTHON" -m llm_lab.web_security run --lab idor --output "$LAB_EVIDENCE/idor.json"
"$LAB_PYTHON" -m llm_lab.web_security review --evidence "$LAB_EVIDENCE/idor.json" > "$LAB_EVIDENCE/model-input.json"
"$LAB_PYTHON" -m llm_lab.web_security review --evidence "$LAB_EVIDENCE/idor.json" --live --output "$LAB_EVIDENCE/model-review.md"
test -s "$LAB_EVIDENCE/model-review.md"
```

doctor 应显示目标模型 `installed=true`；生成文件不等于答案正确。人工核对草稿是否区分 Alice / Bob、200 / 403 和对象所有权。此前 1.5B 模型曾把跨用户访问误写为正常回归，必须在报告中纠正。`done_reason=length` 表示截断，不能交接为完整草稿。

不通时核对当前终端环境变量、`.16→.15:11434` 路由及现有服务状态；不要顺手更改防火墙或重启共享 Ollama。记录“Web 验收通过 / AI 阶段失败”，保留证据。

## 9. SSH 隧道与浏览器验收（Mac）

在 **Mac 的另一个终端** 执行，保持前台：

```bash
ssh -N -o ExitOnForwardFailure=yes -o ServerAliveInterval=30 -o ServerAliveCountMax=3 \
  -L 127.0.0.1:8787:127.0.0.1:8787 \
  -L 127.0.0.1:8788:127.0.0.1:8788 \
  llm2@192.168.2.16
```

若本地端口占用，先确认是否是自己上次的隧道；不要杀其他服务。`ExitOnForwardFailure` 用于避免隧道未建成却继续验收。

| 浏览器操作 | 漏洞版 `http://127.0.0.1:8787/frontend/index.html` | 修复版 `http://127.0.0.1:8788/frontend/index.html` |
|---|---|---|
| 教学登录 Alice | 200 | 200 |
| 点击订单 1 | 200，A-book | 200，A-book |
| 点击订单 2 | 200，B-book | 403，owner mismatch |
| 动态加载模块 | 出现教学 chunk 文本 | 同左 |

每个页面先点击登录。Cookie 按主机而非端口隔离，这两个地址可能共享合成 Cookie；本课演示不是两个独立安全域。记录截图或浏览器可见结果；没有浏览器工具就写“HTTP 通过、浏览器点击未验证”。

DOM 选做：页面地址后加 `?mode=vulnerable#%3Cb%3ELAB%3C%2Fb%3E` 出现粗体，再改 `mode=fixed` 显示文本。DOM 查询开关与服务端漏洞/修复开关相互独立。CSRF/CORS、插件和真实反射 XSS 的浏览器验收不属于上述四项自动推论。

## 10. 共享服务复查、持久化与交接

在 `.16`：

```bash
{
  for unit in pd-2379.service tikv-20160.service node_exporter-9100.service blackbox_exporter-9115.service; do
    printf '%s ' "$unit"
    systemctl is-active "$unit" || true
  done
} > "$LAB_EVIDENCE/shared-services-after.txt"
diff -u "$LAB_EVIDENCE/shared-services-before.txt" "$LAB_EVIDENCE/shared-services-after.txt" || true
systemctl --user is-enabled web-ai-vulnerable.service web-ai-fixed.service | tee "$LAB_EVIDENCE/service-enabled.txt"
loginctl show-user llm2 -p Linger | tee "$LAB_EVIDENCE/linger-after.txt"
journalctl --user -u web-ai-vulnerable.service -u web-ai-fixed.service --since '30 minutes ago' --no-pager > "$LAB_EVIDENCE/service-journal.txt"
```

对比不一致时记录并调查，不自动“修复”共享服务。journal 只用于调试本课进程，证据不提交到公共仓库。

验证退出 SSH 后的运行：先结束 Mac 隧道，再关闭部署 SSH；重新登录 `.16`，恢复 session.env，重复第 8.1 节。记录结果。保留旧会话或隧道时，不能证明“最后一个登录会话退出后仍运行”。开机 enable + Linger=yes 只是启动配置，不代表实际重启测试通过。

在 `$LAB_EVIDENCE/HANDOFF.md` 填下面的表，不能把预期直接复制到“实际”栏：

| 项目 | 实际结果 / 证据 |
|---|---|
| 操作时间、执行 agent | |
| 节点 IP、hostname、用户、Python | |
| 固定提交 SHA、release/current 路径 | |
| 原 current 目标、是否首次部署 | |
| 12 组对照、可选 33 项测试 | |
| 双服务健康、匿名/所有权矩阵 | |
| 8787/8788 实际监听地址 | |
| Ollama 模型、返回状态、草稿及人工纠正 | |
| Mac 隧道与浏览器点击 | |
| user systemd / 前台模式 | |
| Linger 原值/现值，是否由本次变更 | |
| 退出 SSH 后验证；重启验证是否未做 | |
| 共享服务前后差异 | |
| 阻塞项、未验证项、下一步 | |
| 回滚目标与服务备份目录 | |

完成后将 HANDOFF.md 和最小必要证据交给用户；不要擅自上传节点日志、凭据或原始业务数据。

## 11. 无用户级 systemd 时的前台方案

分别保持 `.16` 的两个 SSH 终端，在每个终端恢复第 3 节的 session.env，再执行对应一条：

```bash
cd "$LAB_RELEASE"
export PYTHONPATH="$LAB_RELEASE/src"
"$LAB_PYTHON" -m llm_lab.web_security serve --mode vulnerable --port 8787
```

```bash
cd "$LAB_RELEASE"
export PYTHONPATH="$LAB_RELEASE/src"
"$LAB_PYTHON" -m llm_lab.web_security serve --mode fixed --port 8788
```

另开第三个会话完成第 8 节（将工作路径/PYTHONPATH 指向 LAB_RELEASE），Mac 建隧道后完成第 9 节。此方案退出会话/按 Ctrl-C 后服务停止；明确交接为“前台临时部署”，不能承诺持久化。不使用裸 `nohup` 代替可靠服务管理。

## 12. 更新、回滚与停止

### 更新前处理

只更新本手册管理的两个单位，先检查 `systemctl --user cat web-ai-vulnerable.service web-ai-fixed.service`，确认包含本手册的 Managed 标记与正确路径。记录状态、原 current 和单位内容。先在新 release 完成第 6 节；维护窗口切换时停止自己的两个单位，执行第 7 节，再跑第 8 节。新代码版本必须另建 release，不能在运行中的目录 git pull。

### 当前版本验收失败：恢复旧 release

先确认 `$LAB_EVIDENCE/previous-release.txt` 属于本次部署且指向有效的历史版本。本节只适用于已有旧版本；首次部署没有回滚目标，执行后面的停止步骤即可。

```bash
"$LAB_PYTHON" - <<'PY'
import os
from pathlib import Path
base = Path(os.environ['LAB_BASE'])
record = Path(os.environ['LAB_EVIDENCE']) / 'previous-release.txt'
text = record.read_text().strip()
if not text:
    raise SystemExit('STOP: 首次部署无旧版本，使用停止步骤')
previous = Path(text).resolve(strict=True)
if not previous.is_relative_to((base/'releases').resolve()) or not (previous/'src/llm_lab/web_security').is_dir():
    raise SystemExit('STOP: 回滚目录不合法')
next_link = base / ('rollback-next-' + os.environ['LAB_RUN'])
if next_link.exists() or next_link.is_symlink():
    raise SystemExit('STOP: 回滚临时链接已存在，先核对状态')
next_link.symlink_to(previous, target_is_directory=True)
os.replace(next_link, base/'current')
print('已恢复 current ->', previous)
PY
# 如果本次修改过服务定义，恢复备份；无备份则保持本手册定义。
for unit in web-ai-vulnerable.service web-ai-fixed.service; do
  if [ -f "$LAB_EVIDENCE/units-before/$unit" ]; then
    cp "$LAB_EVIDENCE/units-before/$unit" "$HOME/.config/systemd/user/$unit"
  fi
done
systemctl --user daemon-reload
systemctl --user restart web-ai-vulnerable.service web-ai-fixed.service
```

重新完成第 8.1 节并记录回滚后的 SHA。内存实验数据不会恢复，服务重启后回到合成初始状态；原始证据保留。

### 首次失败或结束实验：停止

```bash
systemctl --user disable --now web-ai-vulnerable.service web-ai-fixed.service
systemctl --user is-active web-ai-vulnerable.service web-ai-fixed.service || true
ss -ltnp
```

确认教学端口不再由本课监听，Mac 隧道按 Ctrl-C 结束。保留源码、服务定义与 evidence 方便复盘，不执行递归删除。只有本次确实把 Linger 从 no 改成 yes，且确认 llm2 没有其他依赖 lingering 的用户服务时，才考虑 `sudo loginctl disable-linger llm2`；否则保留并在交接中说明。

## 13. 测试节点不能访问 GitHub：离线源码替代

在有网络的 Mac、**独立临时 checkout** 中拉取仓库并确保具有目标提交，用完整 Git archive（不是仅增量文件的旧交付 ZIP）：

```bash
git clone https://github.com/vulmoss/llm-hands-on.git llm-hands-on-deploy-source
cd llm-hands-on-deploy-source
git cat-file -e 7a4680768418f4491d7c2fa629f2011c38715c08^{commit}
git archive --format=tar.gz --output=../web-ai-course-7a4680768418.tar.gz 7a4680768418f4491d7c2fa629f2011c38715c08
cd ..
shasum -a 256 web-ai-course-7a4680768418.tar.gz
scp web-ai-course-7a4680768418.tar.gz llm2@192.168.2.16:/home/llm2/labs/web-ai-course/
```

记录 Mac 打印的 SHA256，通过交接记录传给部署 agent。在 `.16` 恢复 session.env 后执行 `sha256sum "$LAB_BASE/web-ai-course-7a4680768418.tar.gz"`，与 Mac 记录逐字符核对。**未经校验不解包**。

解包前确认 LAB_RELEASE 不存在；在线方案若留下半成品，保留原目录并选择一个明确记录的新目录，不直接覆盖。核对完成后执行：

```bash
[ ! -e "$LAB_RELEASE" ] || { echo 'STOP: release 已存在，不覆盖'; exit 1; }
mkdir -p "$LAB_RELEASE"
tar -xzf "$LAB_BASE/web-ai-course-7a4680768418.tar.gz" -C "$LAB_RELEASE"
printf '%s\n' "$LAB_PIN" > "$LAB_EVIDENCE/code-sha.txt"
printf '%s\n' '来源为受控 Mac 的 git archive；目标无 .git，SHA 与包校验记录一起留存' > "$LAB_EVIDENCE/source-method.txt"
cd "$LAB_RELEASE"
export PYTHONPATH="$LAB_RELEASE/src"
```

跳过第 5 节 Git 检查，继续第 6 节。记录“源码包传输及 SHA256 核对”，不能声称目标节点执行过 git rev-parse。标准库实验无需离线 wheels；可选 pytest 没有包源就标为未执行。

## 14. 故障定位表

| 故障 | 下一步 |
|---|---|
| SSH Permission denied | 处理正常登录条件；不试探旧配置中的秘密，不改 sshd |
| Python < 3.10 / 无 sqlite3 | 报告基础环境不符；别替换系统 Python |
| GitHub DNS/TLS/网络失败 | 修复合法网络/证书链，或第 13 节离线包；不关闭 TLS 验证 |
| 8787/8788 占用 | 核对归属，只停止本次管理的服务；其他进程不动 |
| systemctl --user 无 bus | 当前登录方式不支持用户服务；用前台方案或交管理员处理 |
| 服务 active 但页面失败 | 看本课 journal，核对 WorkingDirectory、PYTHONPATH、固定版本和端口 |
| memory/cgroup 限制启动失败 | 记录日志和主机能力；不要用 sudo 运行整套漏洞服务规避 |
| 离线对照失败 | 停止发布阶段，保存失败 JSON，按 case 定位，不能忽略失败 |
| 模型不存在 / timeout | 保留 Web 部署，标记 AI 阶段阻塞；不自动拉大模型或重启共享服务 |
| AI 结论错误 | 记录人工纠正；这是模型质量问题，不等于 HTTP 实验失败 |
| 浏览器请求结果与 CLI 不同 | 核对端口/模式、Cookie、代理/隧道和是否重启；不要只重复截图 |

课程入口：[GitHub README](https://github.com/vulmoss/llm-hands-on/blob/main/05-security/web-ai-course/README.md)。固定代码提交：[7a46807](https://github.com/vulmoss/llm-hands-on/commit/7a4680768418f4491d7c2fa629f2011c38715c08)。历史 CI：[Python 3.10/3.12 检查](https://github.com/vulmoss/llm-hands-on/actions/runs/35805709716)。
