export type AnalysisMode = 'student';

export interface ResumeListItem {
  id: number;
  student_id?: number | null;
  batch_id?: string | null;
  source_file_name: string;
  file_type: string;
  student_name?: string | null;
  school_name?: string | null;
  major?: string | null;
  student_type?: string | null;
  analysis_mode: AnalysisMode;
  analysis_status: string;
  parse_status: string;
  extract_status: string;
  current_version: number;
  last_error_stage?: string | null;
  last_error_message?: string | null;
}

export interface ResumeSection {
  id: number;
  section_type: string;
  page_no?: number | null;
  order_no: number;
  raw_content: string;
  normalized_content?: string | null;
}

export interface BasicInfo {
  name?: string | null;
  gender?: string | null;
  phone?: string | null;
  email?: string | null;
  city?: string | null;
  highest_degree?: string | null;
  graduation_date?: string | null;
  political_status?: string | null;
  research_interest?: string | null;
  target_research_direction?: string | null;
}

export interface Education {
  school_name?: string | null;
  school_level?: string | null;
  degree?: string | null;
  major?: string | null;
  start_date?: string | null;
  end_date?: string | null;
  gpa_raw?: string | null;
  gpa_normalized?: number | null;
}

export interface Experience {
  company_name?: string | null;
  project_name?: string | null;
  job_title?: string | null;
  role_name?: string | null;
  start_date?: string | null;
  end_date?: string | null;
  description_raw?: string | null;
  responsibilities?: string[];
  actions?: string[];
  results?: string[];
  metrics?: string[];
  tools_used?: string[];
  skills_inferred?: string[];
  methods_or_tech?: string[];
  deliverables?: string[];
}

export interface Award {
  award_name?: string | null;
  award_type?: string | null;
  award_level?: string | null;
  award_date?: string | null;
  description?: string | null;
}

export interface Skill {
  skill_name: string;
  skill_category?: string | null;
  proficiency_level?: string | null;
  source_type?: string | null;
}

export interface Paper {
  title?: string | null;
  role?: string | null;
  publication_type?: string | null;
  status?: string | null;
  publish_date?: string | null;
  description?: string | null;
}

export interface Patent {
  patent_name?: string | null;
  patent_type?: string | null;
  role?: string | null;
  status?: string | null;
  application_date?: string | null;
  description?: string | null;
}

export interface Competition {
  competition_name?: string | null;
  award_level?: string | null;
  role?: string | null;
  competition_date?: string | null;
  description?: string | null;
}

export interface Portrait {
  portrait_mode?: AnalysisMode | null;
  student_type?: string | null;
  capability_tags: string[];
  behavior_tags: string[];
  job_direction_tags: string[];
  research_direction_tags: string[];
  method_tags: string[];
  academic_potential_tags: string[];
  strengths: string[];
  risks_or_gaps: string[];
  portrait_summary?: string | null;
  confidence_score?: number | null;
}

export interface ResumeDetail {
  id: number;
  source_file_name: string;
  analysis_mode: AnalysisMode;
  analysis_status: string;
  parse_status: string;
  extract_status: string;
  current_version: number;
  raw_text?: string | null;
  sections: ResumeSection[];
  basic_info?: BasicInfo | null;
  educations: Education[];
  internships: Experience[];
  projects: Experience[];
  awards: Award[];
  papers: Paper[];
  patents: Patent[];
  competitions: Competition[];
  skills: Skill[];
  portrait?: Portrait | null;
  last_error_stage?: string | null;
  last_error_message?: string | null;
}

export interface ExtractLog {
  id: number;
  stage_name: string;
  model_name?: string | null;
  prompt_version?: string | null;
  input_text?: string | null;
  output_text?: string | null;
  validate_result?: Record<string, unknown> | null;
  status: string;
  error_message?: string | null;
}

export interface SemanticSearchChunkHit {
  chunk_id: number;
  chunk_type: string;
  score: number;
  distance: number;
  rerank_score?: number | null;
  cosine_score: number;
  cosine_distance: number;
  keyword_score?: number | null;
  rrf_score?: number | null;
  dense_rank?: number | null;
  keyword_rank?: number | null;
  retrieval_sources: string[];
  score_source: 'rerank' | 'rrf' | 'rrf_fallback' | 'cosine' | 'cosine_fallback' | string;
  content_text: string;
  metadata?: Record<string, unknown> | null;
}

export interface SemanticSearchResult {
  student_id?: number | null;
  resume_id: number;
  student_name?: string | null;
  school_name?: string | null;
  major?: string | null;
  analysis_mode: AnalysisMode;
  student_type?: string | null;
  best_score: number;
  hits: SemanticSearchChunkHit[];
}

export interface CountItem {
  name: string;
  count: number;
}

export interface CoverageMetric {
  key: string;
  label: string;
  value: number;
}

export interface WordCloudItem {
  name: string;
  value: number;
}

export interface HeatmapCell {
  x: string;
  y: string;
  value: number;
}

export interface HeatmapPayload {
  title: string;
  x_labels: string[];
  y_labels: string[];
  cells: HeatmapCell[];
}

export interface GroupReport {
  meta: {
    analysis_mode: AnalysisMode;
    generated_at: string;
    raw_resume_count: number;
    primary_resume_count: number;
    student_count: number;
  };
  summary: {
    student_count: number;
    raw_resume_count: number;
    primary_resume_count: number;
    school_count: number;
    major_count: number;
    avg_project_count: number;
    avg_internship_count: number;
  };
  basic_distribution: {
    school_levels: CountItem[];
    schools_top: CountItem[];
    majors_top: CountItem[];
    degrees: CountItem[];
  };
  coverage: CoverageMetric[];
  tag_distribution: {
    student_types: CountItem[];
    research_direction_tags: CountItem[];
    method_tags: CountItem[];
    academic_potential_tags: CountItem[];
    job_direction_tags: CountItem[];
    capability_tags: CountItem[];
    behavior_tags: CountItem[];
  };
  wordcloud: {
    research_direction: WordCloudItem[];
    job_direction: WordCloudItem[];
  };
  heatmaps: HeatmapPayload[];
}
