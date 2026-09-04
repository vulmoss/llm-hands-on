# 01 - 基础设施层

> 搭建 LLM 运行环境：ESXi 虚拟化、VM 部署、Ollama 安装配置。

## 内容

| 文件 | 说明 |
|------|------|
| `esxi-lab-guide.md` | ESXi 环境完整操作手册（主机管理、VM 操作、迁移、排错） |
| `llm-inference.vmx` | VM1 配置文件（16vCPU / 64GB RAM / Ollama 推理） |
| `llm-dev.vmx` | VM2 配置文件（8vCPU / 32GB RAM / Python 开发） |

## 学完这层你应该会

- SSH 到 ESXi 主机，用 `vim-cmd` / `esxcli` 管理 VM
- 理解 VM 的资源分配（vCPU、RAM、磁盘、网络）
- 安装和配置 Ollama（snap 方式）
- 用 `ollama pull` / `ollama list` / `ollama ps` 管理模型
- 配置 Ollama 监听 0.0.0.0 允许远程访问

## 环境概览

```
ESXi 6.7.0 (192.168.2.14)
├── VM1 llm-inference (192.168.2.15)
│   └── Ollama v0.32.14 → qwen2.5:1.5b + qwen2.5:7b
└── VM2 llm-dev (192.168.2.16)
    └── Python 3.10 + LangChain + Gradio + ChromaDB
```
