# ESXi LLM 推理学习环境 - 操作手册

## 环境概览

```
ESXi Host (192.168.2.14)
├── VM1: llm-inference (192.168.2.15) - Ollama 推理服务
│   ├── 16 vCPU / 64GB RAM / 100GB disk
│   ├── Ollama v0.32.14 (snap)
│   └── Models: qwen2.5:1.5b, qwen2.5:7b
│
└── VM2: llm-dev (192.168.2.16) - Python 开发环境
    ├── 8 vCPU / 32GB RAM / 80GB disk
    ├── JupyterLab, LangChain, Gradio, Streamlit
    └── 通过 API 连接 VM1 的 Ollama
```

## 连接信息

| 主机 | IP | 用户 | 密码 |
|------|-----|------|------|
| ESXi | 192.168.2.14 | root | Admin123@pl |
| llm-inference | 192.168.2.15 | llm1 | Admin123@pl |
| llm-dev | 192.168.2.16 | llm2 | Admin123@pl |

---

## 一、ESXi 主机操作

### 1.1 SSH 连接 ESXi

```bash
ssh root@192.168.2.14
# 密码提示格式: (root@192.168.2.14) Password:
# ESXi 使用 BusyBox shell，没有 bash
# 提示符格式: [root@bogon:~]
```

### 1.2 查看已注册的 VM

```bash
vim-cmd vmsvc/getallvms
```

### 1.3 VM 电源管理

```bash
# 查看电源状态
vim-cmd vmsvc/power.getstate <vmid>

# 开机
vim-cmd vmsvc/power.on <vmid>

# 关机
vim-cmd vmsvc/power.off <vmid>

# 强制关闭（VM 无响应时）
esxcli vm process list                                    # 查找 World ID
esxcli vm process kill --type=force --world-id=<id>       # 强制终止
```

### 1.4 Datastore 管理

```bash
# 查看 datastore 空间
esxcli storage filesystem list

# 当前布局:
# data-ssd:  ~886GB total, ~118GB free  (其他业务 VM)
# data_sata: ~36TB total, ~21.7TB free  (LLM VM 在此)
```

### 1.5 注册/注销 VM

```bash
# 注销（从清单移除，不删文件）
vim-cmd vmsvc/unregister <vmid>

# 注册（从 VMX 文件添加到清单）
vim-cmd solo/registervm /vmfs/volumes/data_sata/llm-inference/llm-inference.vmx
vim-cmd solo/registervm /vmfs/volumes/data_sata/llm-dev/llm-dev.vmx
```

### 1.6 VMDK 磁盘克隆（跨 datastore 迁移）

```bash
# 创建目标目录
mkdir -p /vmfs/volumes/data_sata/llm-inference

# 克隆磁盘（thin provisioned）
vmkfstools -i /vmfs/volumes/data-ssd/llm-inference/llm-inference.vmdk \
           /vmfs/volumes/data_sata/llm-inference/llm-inference.vmdk -d thin

# 复制配置文件
cp /vmfs/volumes/data-ssd/llm-inference/*.vmx   /vmfs/volumes/data_sata/llm-inference/
cp /vmfs/volumes/data-ssd/llm-inference/*.nvram /vmfs/volumes/data_sata/llm-inference/
cp /vmfs/volumes/data-ssd/llm-inference/*.vmsd  /vmfs/volumes/data_sata/llm-inference/
```

**注意：** 不要用 `cp` 复制 VMDK 文件，必须用 `vmkfstools -i`。ESXi 的 SSH 会话断开后后台进程会被杀死，长时间克隆需在前台运行。

### 1.7 修改 VMX 文件

```bash
# 断开 CDROM（避免引用旧 datastore 上的 ISO）
sed -i 's|ide1:0.startConnected = "TRUE"|ide1:0.startConnected = "FALSE"|' <vmx文件>
sed -i 's|ide1:0.deviceType = "cdrom-image"|ide1:0.deviceType = "cdrom-raw"|' <vmx文件>

# 删除旧的 swap 和迁移日志路径
sed -i '/sched.swap.derivedName/d' <vmx文件>
sed -i '/migrate.hostlog/d' <vmx文件>
```

### 1.8 上传 ISO 到 ESXi（从本机）

```bash
# 使用 scp 上传 ISO
scp /tmp/esxi_iso/ubuntu-22.04.5-live-server-amd64.iso root@192.168.2.14:/vmfs/volumes/data-ssd/iso/
```

---

## 二、VM1 - llm-inference (Ollama 推理服务)

### 2.1 SSH 连接

```bash
ssh llm1@192.168.2.15
# 密码: Admin123@pl
```

### 2.2 Ollama 服务管理（snap 安装）

```bash
# 查看状态
sudo systemctl status snap.ollama.ollama

# 重启服务
sudo snap restart ollama

# 查看配置
sudo snap get ollama

# 设置 API 监听地址（允许外部访问）
sudo snap set ollama host=0.0.0.0

# 其他配置项
sudo snap set ollama num-parallel=2        # 并行请求数
sudo snap set ollama keep-alive=10m        # 模型保持加载时间
sudo snap set ollama max-loaded-models=2   # 最大同时加载模型数
```

### 2.3 模型管理

```bash
# 拉取模型
ollama pull qwen2.5:1.5b      # 1.5B 参数, ~986MB
ollama pull qwen2.5:7b         # 7.6B 参数, ~4.7GB

# 列出已安装模型
ollama list

# 删除模型
ollama rm <model-name>

# 模型存储路径（snap 版本）
ls /var/snap/ollama/common/models/
```

### 2.4 API 使用

```bash
# 查看已安装模型
curl -s http://localhost:11434/api/tags | python3 -m json.tool

# 文本生成（非流式）
curl -s http://localhost:11434/api/generate \
  -d '{"model":"qwen2.5:1.5b","prompt":"你好","stream":false}'

# 从外部访问（VM2 或其他机器）
curl -s http://192.168.2.15:11434/api/tags
```

### 2.5 交互式对话

```bash
ollama run qwen2.5:1.5b
>>> 你好
>>> 什么是机器学习？
>>> /bye
```

---

## 三、VM2 - llm-dev (Python 开发环境)

### 3.1 SSH 连接

```bash
ssh llm2@192.168.2.16
# 密码: Admin123@pl
```

### 3.2 环境变量

```bash
# 已在 ~/.bashrc 中配置:
export PATH="$HOME/.local/bin:$PATH"
export OLLAMA_HOST="http://192.168.2.15:11434"
```

### 3.3 已安装的 Python 包

```bash
pip3 list | grep -iE 'langchain|jupyter|gradio|streamlit|chromadb|faiss|openai'
```

| 包 | 版本 | 用途 |
|----|------|------|
| jupyterlab | 4.6.3 | 交互式开发环境 |
| langchain | 1.3.18 | LLM 应用框架 |
| langchain-openai | 1.6.0 | OpenAI 兼容接口 |
| langchain-community | 0.4.2 | 社区集成 |
| gradio | 6.26.0 | Web UI 快速搭建 |
| streamlit | 1.63.0 | 数据应用框架 |
| chromadb | 1.5.9 | 向量数据库 |
| faiss-cpu | 1.15.0 | 向量检索 |
| openai | 3.7.0 | OpenAI SDK |

### 3.4 启动 JupyterLab

```bash
jupyter lab --ip=0.0.0.0 --port=8888 --no-browser
# 浏览器访问: http://192.168.2.16:8888
```

### 3.5 Python 调用 Ollama（LangChain）

```python
from langchain_openai import ChatOpenAI

llm = ChatOpenAI(
    base_url="http://192.168.2.15:11434/v1",
    api_key="ollama",
    model="qwen2.5:1.5b"   # 或 "qwen2.5:7b"
)

response = llm.invoke("什么是机器学习？")
print(response.content)
```

### 3.6 Python 调用 Ollama（OpenAI SDK）

```python
from openai import OpenAI

client = OpenAI(
    base_url="http://192.168.2.15:11434/v1",
    api_key="ollama"
)

response = client.chat.completions.create(
    model="qwen2.5:7b",
    messages=[{"role": "user", "content": "你好"}]
)
print(response.choices[0].message.content)
```

### 3.7 LangChain + ChromaDB 向量检索示例

```python
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_community.vectorstores import Chroma
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.chains import RetrievalQA
from langchain_community.document_loaders import TextLoader

# 初始化 LLM 和 Embeddings（用 Ollama）
llm = ChatOpenAI(base_url="http://192.168.2.15:11434/v1", api_key="ollama", model="qwen2.5:7b")
embeddings = OpenAIEmbeddings(base_url="http://192.168.2.15:11434/v1", api_key="ollama")

# 加载文档并分割
loader = TextLoader("your_document.txt")
docs = loader.load()
splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
chunks = splitter.split_documents(docs)

# 存入向量数据库
vectorstore = Chroma.from_documents(chunks, embeddings)

# 创建检索链
qa = RetrievalQA.from_chain_type(llm=llm, retriever=vectorstore.as_retriever())
result = qa.invoke("文档的主要内容是什么？")
print(result)
```

### 3.8 Gradio 快速搭建 Chat UI

```python
import gradio as gr
from langchain_openai import ChatOpenAI

llm = ChatOpenAI(base_url="http://192.168.2.15:11434/v1", api_key="ollama", model="qwen2.5:7b")

def chat(message, history):
    response = llm.invoke(message)
    return response.content

demo = gr.ChatInterface(fn=chat, title="LLM Chat")
demo.launch(server_name="0.0.0.0", server_port=7860)
```

---

## 四、VM 迁移流程（data-ssd -> data_sata）

本次因 data-ssd 磁盘 100% 满，将两个 VM 迁移到 data_sata。

### 完整步骤

```bash
# 1. SSH 到 ESXi
ssh root@192.168.2.14

# 2. 关闭 VM
vim-cmd vmsvc/power.off 53    # llm-inference（如无响应需强制关闭）
vim-cmd vmsvc/power.off 54    # llm-dev

# 强制关闭（备选）
esxcli vm process list
esxcli vm process kill --type=force --world-id=<id>

# 3. 在 data_sata 创建目录
mkdir -p /vmfs/volumes/data_sata/llm-inference
mkdir -p /vmfs/volumes/data_sata/llm-dev

# 4. 克隆磁盘（耗时较长，需前台运行）
vmkfstools -i /vmfs/volumes/data-ssd/llm-inference/llm-inference.vmdk \
           /vmfs/volumes/data_sata/llm-inference/llm-inference.vmdk -d thin

vmkfstools -i /vmfs/volumes/data-ssd/llm-dev/llm-dev.vmdk \
           /vmfs/volumes/data_sata/llm-dev/llm-dev.vmdk -d thin

# 5. 复制配置文件
cp /vmfs/volumes/data-ssd/llm-inference/*.vmx   /vmfs/volumes/data_sata/llm-inference/
cp /vmfs/volumes/data-ssd/llm-inference/*.nvram /vmfs/volumes/data_sata/llm-inference/
cp /vmfs/volumes/data-ssd/llm-inference/*.vmsd  /vmfs/volumes/data_sata/llm-inference/

cp /vmfs/volumes/data-ssd/llm-dev/*.vmx   /vmfs/volumes/data_sata/llm-dev/
cp /vmfs/volumes/data-ssd/llm-dev/*.nvram /vmfs/volumes/data_sata/llm-dev/
cp /vmfs/volumes/data-ssd/llm-dev/*.vmsd  /vmfs/volumes/data_sata/llm-dev/

# 6. 修改 VMX 中的路径引用
sed -i 's|ide1:0.startConnected = "TRUE"|ide1:0.startConnected = "FALSE"|' /vmfs/volumes/data_sata/llm-inference/llm-inference.vmx
sed -i 's|ide1:0.deviceType = "cdrom-image"|ide1:0.deviceType = "cdrom-raw"|' /vmfs/volumes/data_sata/llm-inference/llm-inference.vmx
sed -i '/sched.swap.derivedName/d' /vmfs/volumes/data_sata/llm-inference/llm-inference.vmx
sed -i '/migrate.hostlog/d' /vmfs/volumes/data_sata/llm-inference/llm-inference.vmx
# VM2 同理

# 7. 注销旧 VM
vim-cmd vmsvc/unregister 53
vim-cmd vmsvc/unregister 54

# 8. 注册新 VM
vim-cmd solo/registervm /vmfs/volumes/data_sata/llm-inference/llm-inference.vmx
vim-cmd solo/registervm /vmfs/volumes/data_sata/llm-dev/llm-dev.vmx

# 9. 开机
vim-cmd vmsvc/power.on <new-vmid-1>
vim-cmd vmsvc/power.on <new-vmid-2>

# 10. 清理旧文件（释放 data-ssd 空间）
rm -rf /vmfs/volumes/data-ssd/llm-inference/
rm -rf /vmfs/volumes/data-ssd/llm-dev/
```

---

## 五、Expect 自动化模板

ESXi 和 VM 的 SSH 不支持密钥免密（初始配置），自动化操作需要 expect 脚本。

### 5.1 ESXi 操作模板

```tcl
#!/usr/bin/expect -f
set timeout 60
spawn ssh -o StrictHostKeyChecking=no root@192.168.2.14
expect "Password:"
send "Admin123@pl\r"
expect -re {\[root@.*\] }

# 在此添加 ESXi 命令
send "vim-cmd vmsvc/getallvms 2>&1\r"
expect -re {\[root@.*\] }

send "exit\r"
expect eof
```

### 5.2 VM 操作模板

```tcl
#!/usr/bin/expect -f
set timeout 30
spawn ssh -o StrictHostKeyChecking=no llm1@192.168.2.15
expect "password:"
send "Admin123@pl\r"
expect -re {llm1@server1.*\$ }

# 在此添加命令
send "ollama list\r"
expect -re {llm1@server1.*\$ }

send "exit\r"
expect eof
```

**注意：** Tcl 中 `$HOME`、`$PATH` 等变量会被 expect 解释，需用花括号包裹：
```tcl
send {export PATH="$HOME/.local/bin:$PATH"}
```

---

## 六、常见问题

### ESXi 相关

| 问题 | 解决方案 |
|------|----------|
| VM 无法关机（有 pending question） | `esxcli vm process kill --type=force --world-id=<id>` |
| data-ssd 100% 满 | 迁移 VM 到 data_sata，或清理不用的 VM |
| `cp` 复制 VMDK 失败/卡住 | 必须用 `vmkfstools -i` 克隆 |
| 后台进程断开 SSH 后被杀 | 在前台 expect 会话中运行长时间命令 |
| ESXi 没有 bash | 用 `sh` 代替，BusyBox 命令有限 |

### Ollama 相关

| 问题 | 解决方案 |
|------|----------|
| API 外部无法访问 | `sudo snap set ollama host=0.0.0.0` 然后 `sudo snap restart ollama` |
| 模型丢失（切换安装方式后） | snap 模型路径: `/var/snap/ollama/common/models/`，需重新 pull |
| CPU 推理慢 | 优先使用 1.5b 小模型测试，7b 用于正式任务 |
| install.sh 下载慢 | 用 snap 安装: `sudo snap install ollama` |

### VM 间通信

| 问题 | 解决方案 |
|------|----------|
| VM2 无法连接 VM1 Ollama | 检查 VM1 的 `snap get ollama host` 是否为 `0.0.0.0` |
| LangChain 连接超时 | 确认 VM1 防火墙未阻止 11434 端口 |
