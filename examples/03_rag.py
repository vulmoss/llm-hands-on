"""第三个练习：先构建索引，再单独观察检索和回答。"""

from llm_lab.client import OllamaClient
from llm_lab.config import Settings
from llm_lab.rag import VectorIndex, answer_question, format_hits


def main():
    settings = Settings.from_env()
    client = OllamaClient(settings)
    index = VectorIndex.load(settings.index_path)
    question = "学习实验室的推理服务和应用分别负责什么？"
    print(format_hits(index.search(client, question)))
    print(answer_question(client, index, question)["answer"])


if __name__ == "__main__":
    main()
