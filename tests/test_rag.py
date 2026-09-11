import json

import pytest

from llm_lab.rag import Chunk, VectorIndex, answer_question, load_chunks, normalize


def test_chunk_offsets_overlap_and_no_tail_duplicates(tmp_path):
    (tmp_path / "note.md").write_text("abcdefghij", encoding="utf-8")
    chunks = load_chunks(tmp_path, chunk_size=6, overlap=2)
    assert [(c.start, c.end, c.text) for c in chunks] == [(0, 6, "abcdef"), (4, 10, "efghij")]
    assert all(c.source == "note.md" for c in chunks)
    with pytest.raises(ValueError):
        load_chunks(tmp_path, 5, 5)


def test_external_symlink_is_rejected(tmp_path):
    directory = tmp_path / "notes"
    directory.mkdir()
    outside = tmp_path / "outside.md"
    outside.write_text("outside", encoding="utf-8")
    (directory / "link.md").symlink_to(outside)
    with pytest.raises(ValueError, match="目录外"):
        load_chunks(directory)


def test_build_persist_rank_and_rebuild(client, tmp_path):
    chunks = [Chunk("python.md", 0, 6, "Python"), Chunk("other.md", 0, 5, "other")]
    index = VectorIndex.build(client, chunks)
    path = tmp_path / "index.json"
    index.save(path)
    loaded = VectorIndex.load(path)
    hits = loaded.search(client, "Python 是什么", k=1)
    assert hits[0].chunk.source == "python.md"
    assert hits[0].score == pytest.approx(1)
    VectorIndex.build(client, chunks).save(path)
    assert len(VectorIndex.load(path).chunks) == 2


def test_rag_passes_sources_to_prompt(client):
    index = VectorIndex.build(client, [Chunk("python.md", 0, 6, "Python")])
    answer = answer_question(client, index, "Python 是什么")
    assert answer["sources"][0]["chunk"]["source"] == "python.md"
    assert "[1] python.md" in client.requests[0]["messages"][-1]["content"]


def test_threshold_can_skip_generation(client):
    index = VectorIndex.build(client, [Chunk("python.md", 0, 6, "Python")])
    result = answer_question(client, index, "天气", min_score=0.9)
    assert result["sources"] == []
    assert "无法回答" in result["answer"]
    assert not client.requests


def test_incompatible_model_and_dimensions(client):
    index = VectorIndex("different-model", [Chunk("x", 0, 1, "x")], [[1, 0]])
    with pytest.raises(ValueError, match="模型"):
        index.search(client, "question")
    index.model = client.settings.embedding_model
    index.vectors = [[1, 0, 0]]
    with pytest.raises(ValueError, match="维度"):
        index.search(client, "question")


@pytest.mark.parametrize("vector", [[], [0, 0], [float("nan"), 1], [True], ["1"], [10**1000]])
def test_invalid_vectors(vector):
    with pytest.raises(ValueError):
        normalize(vector)


def test_invalid_index(client, tmp_path):
    path = tmp_path / "index.json"
    with pytest.raises(ValueError, match="先运行"):
        VectorIndex.load(path)
    path.write_text(json.dumps({"version": 55}), encoding="utf-8")
    with pytest.raises(ValueError, match="版本"):
        VectorIndex.load(path)
