import { apiRequest } from './client';
import type { ExtractLog, GroupReport, ResumeDetail, ResumeListItem, SemanticSearchResult } from '../types';

export interface ResumeSearchParams {
  name?: string;
  school_name?: string;
  major?: string;
  student_type?: string;
  keyword?: string;
}

export interface ResumeSemanticSearchParams {
  query: string;
  top_k?: number;
  chunk_types?: string[];
}

export async function fetchResumes(params: ResumeSearchParams = {}) {
  const query = new URLSearchParams();
  Object.entries(params).forEach(([key, value]) => {
    if (value) {
      query.set(key, value);
    }
  });
  const suffix = query.toString() ? `?${query.toString()}` : '';
  return apiRequest<ResumeListItem[]>(`/resumes${suffix}`);
}

export async function semanticSearchResumes(payload: ResumeSemanticSearchParams) {
  return apiRequest<SemanticSearchResult[]>('/resumes/semantic-search', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json'
    },
    body: JSON.stringify(payload)
  });
}

export async function fetchResumeDetail(id: number) {
  return apiRequest<ResumeDetail>(`/resumes/${id}`);
}

export async function fetchResumeLogs(id: number) {
  return apiRequest<ExtractLog[]>(`/resumes/${id}/logs`);
}

export async function reprocessResume(id: number) {
  return apiRequest<{ message: string; resume_id: number }>(`/resumes/${id}/reprocess`, {
    method: 'POST'
  });
}

export async function uploadResumes(files: File[]) {
  const formData = new FormData();
  files.forEach((file) => formData.append('files', file));
  return apiRequest<{ batch_id: string; items: Array<{ resume_id: number; file_name: string; status: string; analysis_mode: string }> }>(
    '/resumes/upload',
    {
      method: 'POST',
      body: formData
    }
  );
}

export async function saveReview(id: number, payload: unknown) {
  return apiRequest<ResumeDetail>(`/resumes/${id}/review`, {
    method: 'PUT',
    headers: {
      'Content-Type': 'application/json'
    },
    body: JSON.stringify(payload)
  });
}

export async function fetchGroupReport() {
  return apiRequest<GroupReport>('/reports/group');
}
