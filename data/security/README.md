# 固定安全样例

`benign.jsonl` 和 `rag-injection.jsonl` 各 10 行，用 `pair_id` 对应。
每行必须且只能包含下列字段，由 `llm_lab.security_eval.validate_cases` 实际校验：

| 字段 | 含义 |
|---|---|
| id | 全局唯一、非空的样例标识 |
| pair_id | 正常/注入样例的配对标识 |
| category | benign 或 injection |
| question | 非空问题 |
| documents | 1–20 个 source/text 对象，source 在同一例中唯一，text 最多 20000 字符 |
| expected_any | 非空参考子串列表，命中任一项即可 |
| forbidden | 非空标记列表，命中任一项判为失败 |

这是教学开发集，不是独立基准。每个片段是虚构资料，source 只是显示标签，不用于读取磁盘。
新增样例时同时补正常对照；配对一致性由 `tests/security/test_security_eval.py` 检查。
运行步骤和判分局限见 [RAG 实验](../../05-security/rag-injection/README.md)。
