export interface ResumeListItem {
  id: number;
  batch_id?: string | null;
  source_file_name: string;
  file_type: string;
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

export interface Portrait {
  student_type?: string | null;
  capability_tags: string[];
  behavior_tags: string[];
  job_direction_tags: string[];
  strengths: string[];
  risks_or_gaps: string[];
  portrait_summary?: string | null;
  confidence_score?: number | null;
}

export interface ResumeDetail {
  id: number;
  source_file_name: string;
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

