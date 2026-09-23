# 安全实验目录

由 `data/security/labs.json` 生成。修改清单后运行 `python scripts/gen_security_catalog.py`。

离线测试检查程序行为；真实模型与 Promptfoo CLI 的实测结论见各实验报告。

| 实验 | 真实模型评估 | 报告 |
|---|---|---|
| [RAG 文档注入与正常对照](rag-injection/README.md) | 模型实测状态见报告 | [验证记录](../reports/security/baseline.md) |
| [Agent 工具执行边界](agent-boundaries/README.md) | 无需模型（本地回归） | [验证记录](../reports/security/baseline.md) |
| [Promptfoo 本地 API 接入](integrations/promptfoo/README.md) | 模型实测状态见报告 | [验证记录](../reports/security/baseline.md) |
| [Web 安全 12 组漏洞与修复对照](web-ai-course/README.md) | 无需模型（本地回归） | [验证记录](../reports/security/web-ai-course.md) |
| [Ollama 审阅 Web 实验证据](web-ai-course/units/02-ai-workflow.md) | 模型实测状态见报告 | [验证记录](../reports/security/web-ai-course.md) |
| [12 阶段沉浸式学习与靶场复现](immersive-12-stage/README.md) | 模型实测状态见报告 | [验证记录](immersive-12-stage/VALIDATION.md) |

## 离线验收命令

从仓库根目录执行：

```bash
python -m pytest -q tests/security/test_security_eval.py
python -m pytest -q tests/security/test_agent_boundaries.py
python -m pytest -q tests/security/test_promptfoo_contract.py
python -m pytest -q tests/security/test_web_course.py
python -m llm_lab.web_security run --lab idor --output .data/web-ai-course/idor.json
PYTHONPATH=src python3 -m pytest tests/security/test_immersion_course.py -q
```
