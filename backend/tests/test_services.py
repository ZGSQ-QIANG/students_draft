from app.services.normalizer import Normalizer
from app.services.portrait import PortraitEngine
from app.services.rule_extractor import RuleExtractor
from app.services.segmenter import SectionSegmenter
from app.services.vectorize import Vectorizer


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


def test_rule_extractor_returns_basic_and_skill_fields():
    sections = {
        "basic_info": ["张三\n13800138000\nzhangsan@example.com"],
        "education": ["2022.09-2026.06 XX大学 计算机科学与技术 本科 GPA 3.8/4.0"],
        "internship": [],
        "project": ["校园二手交易平台\n负责需求调研、原型设计、推动上线"],
        "awards": [],
        "skills": ["Python SQL Excel"],
        "self_eval": [],
    }
    payload = RuleExtractor().extract(sections)
    assert payload["basic_info"]["phone"] == "13800138000"
    assert payload["basic_info"]["email"] == "zhangsan@example.com"
    assert payload["educations"][0]["degree"] == "本科"
    assert {item["skill_name"] for item in payload["skills"]} >= {"Python", "SQL", "Excel"}


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


def test_vectorizer_returns_stable_dimension():
    vectorizer = Vectorizer()
    vector = vectorizer.embed("sample resume text")
    assert len(vector) == 8
    assert all(0 <= item <= 1 for item in vector)

