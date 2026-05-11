from app.core.config import Settings
from app.models import (
    Resume,
    ResumeSection,
    StudentBasicInfo,
    StudentCompetition,
    StudentEducation,
    StudentInternship,
    StudentPaper,
    StudentPatent,
    StudentPortrait,
    StudentProject,
)
from app.services.embedding_provider import HuggingFaceLocalEmbeddingsProvider
from app.services.keyword_retriever import tokenize_for_bm25
from app.services.normalizer import Normalizer
from app.services.portrait import AcademicPortraitEngine, PortraitEngine
from app.services.rerank_provider import Qwen3LocalReranker, Qwen3RerankCompressor
from app.services.rule_extractor import RuleExtractor
from app.services.semantic_chunking import ChunkBuilder
from app.services.segmenter import SectionSegmenter
from app.services.student_identity import StudentIdentityService
from app.services.student_retriever import StudentRetrieverService
from app.services.vectorize import Vectorizer

from langchain_core.documents import Document


def test_segmenter_splits_common_sections():
    raw_text = """
张三
13800138000
教育经历
2022.09-2026.06 XX大学 计算机科学与技术 本科 GPA 3.8/4.0
项目经历
校园二手交易平台
负责需求调研与原型设计，推动上线。
技能证书
Python SQL Excel
"""
    sections = SectionSegmenter().segment(raw_text)
    assert sections["education"]
    assert sections["project"]
    assert sections["skills"]
    assert "award" in sections
    assert "paper" in sections


def test_segmenter_splits_academic_outputs_without_mixing_awards():
    raw_text = """
张三
论文成果
基于推荐系统的用户行为分析论文
EI会议录用 2025.06
竞赛经历
数学建模竞赛省二等奖
专利成果
一种教育数据分析方法 发明专利
获奖经历
校一等奖学金
"""
    sections = SectionSegmenter().segment(raw_text)
    assert sections["paper"]
    assert sections["competition"]
    assert sections["patent"]
    assert sections["award"]
    assert not any("论文" in item for item in sections["award"])


def test_rule_extractor_returns_basic_and_skill_fields():
    sections = {
        "basic_info": ["张三\n13800138000\nzhangsan@example.com"],
        "education": ["2022.09-2026.06 XX大学 计算机科学与技术 本科 GPA 3.8/4.0"],
        "internship": [],
        "project": ["校园二手交易平台\n负责需求调研、原型设计、推动上线"],
        "paper": ["基于推荐系统的用户行为分析论文\nEI会议录用 2025.06"],
        "patent": [],
        "competition": [],
        "award": [],
        "certificate": [],
        "skills": ["Python SQL Excel"],
        "self_eval": [],
    }
    payload = RuleExtractor().extract(sections)
    assert payload["basic_info"]["phone"] == "13800138000"
    assert payload["basic_info"]["email"] == "zhangsan@example.com"
    assert payload["educations"][0]["degree"] == "本科"
    assert {item["skill_name"] for item in payload["skills"]} >= {"Python", "SQL", "Excel"}
    assert payload["papers"][0]["publication_type"] in {"EI", "会议", "论文"}
    assert payload["awards"] == []


def test_rule_extractor_prefers_full_major_names():
    sections = {
        "basic_info": [],
        "education": [
            "2022.09-2026.06 湖北经济学院 电子商务 本科",
            "2022.09-2026.06 南京邮电大学 计算机科学与技术 本科",
        ],
        "internship": [],
        "project": [],
        "paper": [],
        "patent": [],
        "competition": [],
        "award": [],
        "certificate": [],
        "skills": [],
        "self_eval": [],
    }
    payload = RuleExtractor().extract(sections)
    majors = [item["major"] for item in payload["educations"]]
    assert majors == ["电子商务", "计算机科学与技术"]


def test_normalizer_converts_gpa_and_filters_tags():
    payload = {
        "basic_info": {"highest_degree": "大学本科"},
        "educations": [{"gpa_raw": "GPA 3.8/4.0", "degree": "本科生"}],
        "portrait": {
            "capability_tags": ["数据分析", "未知标签"],
            "behavior_tags": ["结果导向"],
            "job_direction_tags": ["数据分析", "未知方向"],
        },
    }
    normalized = Normalizer().normalize(payload)
    assert normalized["basic_info"]["highest_degree"] == "本科"
    assert normalized["educations"][0]["gpa_normalized"] == 3.8
    assert normalized["portrait"]["capability_tags"] == ["数据分析"]


def test_normalizer_infers_school_level_from_school_name():
    payload = {
        "basic_info": {},
        "educations": [
            {"school_name": "复旦大学", "degree": "本科"},
            {"school_name": "南京邮电大学", "degree": "本科"},
            {"school_name": "湖北经济学院", "degree": "本科"},
        ],
        "portrait": {},
    }
    normalized = Normalizer().normalize(payload)
    assert [item["school_level"] for item in normalized["educations"]] == ["985", "双一流", "普通本科"]


def test_portrait_engine_builds_summary():
    payload = {
        "educations": [{"gpa_normalized": 3.7}],
        "internships": [{"description_raw": "负责活动运营并提升转化率12%", "metrics": ["提升12%"]}],
        "projects": [{"background": "负责用户调研与原型设计", "metrics": []}],
        "skills": [{"skill_name": "Python"}, {"skill_name": "SQL"}, {"skill_name": "Axure"}],
        "portrait": {},
    }
    portrait = PortraitEngine().build(payload)
    assert portrait["student_type"] in {"学术型", "实践型", "复合型", "探索型"}
    assert portrait["portrait_summary"]
    assert portrait["job_direction_tags"]


def test_student_portrait_engine_builds_academic_tags():
    payload = {
        "basic_info": {"research_interest": "关注自然语言处理与教育技术交叉方向"},
        "educations": [{"gpa_normalized": 3.8}],
        "projects": [{"background": "基于Python完成文本分析与问卷研究"}],
        "papers": [{"description": "论文围绕NLP方法进行学习行为分析"}],
        "patents": [],
        "competitions": [{"description": "数学建模竞赛省级二等奖"}],
        "skills": [{"skill_name": "Python"}, {"skill_name": "SQL"}],
        "portrait": {},
    }
    portrait = AcademicPortraitEngine().build(payload)
    assert portrait["portrait_mode"] == "student"
    assert portrait["research_direction_tags"]
    assert portrait["method_tags"]
    assert portrait["academic_potential_tags"]


def test_vectorizer_returns_stable_dimension():
    vectorizer = Vectorizer()
    vector = vectorizer.embed("sample resume text")
    assert len(vector) == 8
    assert all(0 <= item <= 1 for item in vector)


def test_chunk_builder_generates_academic_chunks():
    resume = Resume(id=1, analysis_mode="student", source_file_name="a.pdf", source_file_path="/tmp/a.pdf", file_type="pdf")
    resume.basic_info = StudentBasicInfo(resume_id=1, name="张三", highest_degree="本科")
    resume.educations = [
        StudentEducation(
            id=11,
            resume_id=1,
            school_name="华东师范大学",
            degree="本科",
            major="教育技术学",
            gpa_raw="3.8/4.0",
            core_courses=["机器学习", "数据挖掘"],
        )
    ]
    resume.projects = [
        StudentProject(
            id=21,
            resume_id=1,
            project_name="学习分析平台",
            role_name="负责人",
            background="完成学习行为分析与可视化",
            methods_or_tech=["Python", "文本分析"],
        )
    ]
    resume.papers = [
        StudentPaper(id=31, resume_id=1, title="教育数据挖掘论文", publication_type="EI", description="围绕学习分析展开")
    ]
    resume.patents = [StudentPatent(id=41, resume_id=1, patent_name="学习分析系统", patent_type="发明专利")]
    resume.competitions = [StudentCompetition(id=51, resume_id=1, competition_name="数学建模竞赛", award_level="省二等奖")]
    resume.sections = [ResumeSection(id=61, resume_id=1, section_type="certificate", order_no=1, raw_content="CET-6 560")]
    resume.portrait = StudentPortrait(
        resume_id=1,
        portrait_mode="student",
        student_type="学术型",
        research_direction_tags=["教育数据挖掘"],
        method_tags=["Python建模"],
        academic_potential_tags=["科研参与度高"],
    )
    chunks = ChunkBuilder().build(resume)
    assert {chunk.chunk_type for chunk in chunks} >= {"education", "project", "paper", "patent", "competition", "certificate"}
    assert all(chunk.chunk_type != "skills" for chunk in chunks)


def test_chunk_builder_generates_career_chunks():
    resume = Resume(id=2, analysis_mode="student", source_file_name="b.pdf", source_file_path="/tmp/b.pdf", file_type="pdf")
    resume.basic_info = StudentBasicInfo(resume_id=2, name="李四", highest_degree="本科")
    resume.educations = [StudentEducation(id=12, resume_id=2, school_name="上海大学", degree="本科", major="统计学")]
    resume.projects = [StudentProject(id=22, resume_id=2, project_name="用户分层分析项目", background="完成用户画像分析")]
    resume.internships = [
        StudentInternship(id=32, resume_id=2, company_name="某互联网公司", job_title="数据分析实习生", description_raw="负责用户分析")
    ]
    resume.sections = [ResumeSection(id=62, resume_id=2, section_type="certificate", order_no=1, raw_content="计算机二级")]
    resume.portrait = StudentPortrait(
        resume_id=2,
        portrait_mode="student",
        student_type="实践型",
        job_direction_tags=["数据分析"],
        capability_tags=["数据分析"],
        behavior_tags=["结果导向"],
    )
    chunks = ChunkBuilder().build(resume)
    assert {chunk.chunk_type for chunk in chunks} >= {"education", "project", "internship", "certificate"}
    assert all(chunk.chunk_type != "paper" for chunk in chunks)


def test_huggingface_embeddings_provider_loads_real_model():
    provider = HuggingFaceLocalEmbeddingsProvider(
        Settings(
            embedding_provider="huggingface",
            embedding_model_path="/Users/zgsq/models/Qwen3-Embedding-0.6B",
            embedding_device="cpu",
            embedding_normalize=True,
        )
    )
    query_vector = provider.embed_query("找做过教育数据挖掘项目的学生")
    document_vectors = provider.embed_documents(["学习分析平台项目，负责教育数据清洗和建模。"])
    assert query_vector
    assert document_vectors
    assert len(query_vector) == len(document_vectors[0])
    assert all(isinstance(item, float) for item in query_vector[:10])


def test_student_retriever_groups_hits_by_resume():
    row_map = {
        101: type(
            "ChunkRow",
            (),
            {
                "id": 101,
                "resume_id": 1,
                "chunk_type": "paper",
                "content_text": "教育数据挖掘论文",
                "metadata_json": {
                    "student_id": 10,
                    "student_name": "张三",
                    "school_name": "华东师范大学",
                    "major": "教育技术学",
                    "analysis_mode": "student",
                    "student_type": "学术型",
                },
            },
        )(),
        102: type(
            "ChunkRow",
            (),
            {
                "id": 102,
                "resume_id": 1,
                "chunk_type": "project",
                "content_text": "学习分析平台项目",
                "metadata_json": {
                    "student_id": 10,
                    "student_name": "张三",
                    "school_name": "华东师范大学",
                    "major": "教育技术学",
                    "analysis_mode": "student",
                    "student_type": "学术型",
                },
            },
        )(),
    }
    hits = [
        {
            "chunk_id": 101,
            "score": 0.91,
            "distance": 0.1,
            "rerank_score": 0.91,
            "cosine_score": 0.7,
            "cosine_distance": 0.3,
            "keyword_score": 1.0,
            "rrf_score": 0.03,
            "dense_rank": 2,
            "keyword_rank": 1,
            "retrieval_sources": ["dense", "keyword"],
            "score_source": "rerank",
            "content_text": "教育数据挖掘论文",
            "chunk_type": "paper",
        },
        {
            "chunk_id": 102,
            "score": 0.88,
            "distance": 0.2,
            "rerank_score": 0.88,
            "cosine_score": 0.8,
            "cosine_distance": 0.2,
            "keyword_score": None,
            "rrf_score": 0.01,
            "dense_rank": 1,
            "keyword_rank": None,
            "retrieval_sources": ["dense"],
            "score_source": "rerank",
            "content_text": "学习分析平台项目",
            "chunk_type": "project",
        },
    ]
    grouped = StudentRetrieverService._group_chunk_hits(hits, row_map, "student", 3)
    assert grouped[0]["student_id"] == 10
    assert grouped[0]["resume_id"] == 1
    assert grouped[0]["best_score"] == 0.91
    assert grouped[0]["hits"][0]["chunk_type"] == "paper"
    assert grouped[0]["hits"][0]["distance"] == 0.1
    assert grouped[0]["hits"][0]["rerank_score"] == 0.91
    assert grouped[0]["hits"][0]["cosine_score"] == 0.7
    assert grouped[0]["hits"][0]["keyword_rank"] == 1
    assert grouped[0]["hits"][0]["retrieval_sources"] == ["dense", "keyword"]
    assert grouped[0]["hits"][0]["score_source"] == "rerank"


def test_student_identity_service_builds_deterministic_fingerprint():
    service = StudentIdentityService.__new__(StudentIdentityService)
    resume = Resume(id=9, analysis_mode="student", source_file_name="a.pdf", source_file_path="/tmp/a.pdf", file_type="pdf")
    resume.basic_info = StudentBasicInfo(resume_id=9, name="张 三", graduation_date="2026.06")
    resume.educations = [StudentEducation(resume_id=9, school_name="华东师范大学", major="计算机科学与技术")]
    fingerprint, status, _ = service._build_fingerprint(resume)
    assert status == "resolved"
    assert " " not in fingerprint
    assert "华东师范大学".lower() in fingerprint


def test_qwen3_reranker_formats_instruction():
    reranker = Qwen3LocalReranker.__new__(Qwen3LocalReranker)
    reranker.instruction = "Judge student resume relevance"
    formatted = reranker._format_instruction("找NLP项目", "NLP课程项目")
    assert "<Instruct>: Judge student resume relevance" in formatted
    assert "<Query>: 找NLP项目" in formatted
    assert "<Document>: NLP课程项目" in formatted


def test_qwen3_rerank_compressor_sorts_documents():
    class FakeReranker:
        def score_documents(self, query, documents):
            return [0.2, 0.9]

    compressor = Qwen3RerankCompressor(reranker=FakeReranker())
    documents = [
        Document(page_content="弱相关", metadata={"chunk_id": 1, "cosine_score": 0.8, "cosine_distance": 0.2}),
        Document(page_content="强相关", metadata={"chunk_id": 2, "cosine_score": 0.5, "cosine_distance": 0.5}),
    ]
    compressed = compressor.compress_documents(documents, "query")
    assert compressed[0].metadata["chunk_id"] == 2
    assert compressed[0].metadata["rerank_score"] == 0.9
    assert compressed[0].metadata["score_source"] == "rerank"


def test_bm25_tokenizer_keeps_chinese_and_hard_keywords():
    tokens = tokenize_for_bm25("Java 后端 Spring Boot Redis 数学建模")
    assert "java" in tokens
    assert "redis" in tokens
    assert "数学" in tokens or "数学建模" in tokens


def test_student_retriever_rrf_fuses_and_deduplicates_hits():
    class HybridSettings:
        rrf_k = 60
        rrf_dense_weight = 1.0
        rrf_keyword_weight = 1.0

    service = StudentRetrieverService.__new__(StudentRetrieverService)
    service.settings = HybridSettings()
    dense_hits = [
        {"chunk_id": 1, "distance": 0.2},
        {"chunk_id": 2, "distance": 0.5},
    ]
    keyword_hits = [
        {"chunk_id": 2, "keyword_rank": 1},
        {"chunk_id": 3, "keyword_rank": 2},
    ]
    fused = service._rrf_fuse(dense_hits, keyword_hits)
    by_id = {item["chunk_id"]: item for item in fused}
    assert len(by_id) == 3
    assert by_id[2]["retrieval_sources"] == ["dense", "keyword"]
    assert by_id[2]["dense_rank"] == 2
    assert by_id[2]["keyword_rank"] == 1
    assert by_id[2]["rrf_score"] > by_id[1]["rrf_score"]


def test_student_retriever_falls_back_to_rrf_when_rerank_fails():
    class BrokenSettings:
        rerank_enabled = True
        rerank_provider = "unsupported"

    service = StudentRetrieverService.__new__(StudentRetrieverService)
    service.settings = BrokenSettings()
    row_map = {
        1: type(
            "ChunkRow",
            (),
            {"id": 1, "resume_id": 1, "chunk_type": "project", "content_text": "项目", "metadata_json": {}},
        )()
    }
    hits = [
        {
            "chunk_id": 1,
            "score": 0.6,
            "distance": 0.4,
            "rerank_score": None,
            "cosine_score": 0.6,
            "cosine_distance": 0.4,
            "keyword_score": 1.0,
            "rrf_score": 0.05,
            "dense_rank": 1,
            "keyword_rank": 1,
            "retrieval_sources": ["dense", "keyword"],
            "score_source": "rrf",
            "content_text": "项目",
            "chunk_type": "project",
        }
    ]
    result = service._rerank_or_fallback("query", hits, row_map, 3)
    assert result[0]["score"] == 0.05
    assert result[0]["rerank_score"] is None
    assert result[0]["score_source"] == "rrf_fallback"
