import { apiRequest } from './client';
import type { ExtractLog, ResumeDetail, ResumeListItem } from '../types';

export async function fetchResumes() {
  return apiRequest<ResumeListItem[]>('/resumes');
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
  return apiRequest<{ batch_id: string; items: Array<{ resume_id: number; file_name: string; status: string }> }>('/resumes/upload', {
    method: 'POST',
    body: formData
  });
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

