from app.models.resume import Resume, ResumeSection
from app.models.student import (
    EmbeddingIndex,
    ExtractLog,
    ResumeReviewVersion,
    StudentAward,
    StudentBasicInfo,
    StudentEducation,
    StudentInternship,
    StudentPortrait,
    StudentProject,
    StudentSkill,
)

all_models = [
    Resume,
    ResumeSection,
    StudentBasicInfo,
    StudentEducation,
    StudentInternship,
    StudentProject,
    StudentAward,
    StudentSkill,
    StudentPortrait,
    ResumeReviewVersion,
    ExtractLog,
    EmbeddingIndex,
]
