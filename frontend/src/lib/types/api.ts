/**
 * Shared API types between frontend and backend.
 *
 * These types match the Pydantic schemas defined in the backend.
 * Keep in sync with backend/src/api/schemas.py
 */

// ===== Enums =====

export enum TaskStatus {
  TODO = "TODO",
  IN_PROGRESS = "IN_PROGRESS",
  DONE = "DONE",
  BLOCKED = "BLOCKED",
}

export enum TaskPriority {
  LOW = "LOW",
  MEDIUM = "MEDIUM",
  HIGH = "HIGH",
  CRITICAL = "CRITICAL",
}

export enum EventType {
  TASK_CREATED = "TASK_CREATED",
  TASK_UPDATED = "TASK_UPDATED",
  TASK_DELETED = "TASK_DELETED",
  ATTACHMENT_ADDED = "ATTACHMENT_ADDED",
  ATTACHMENT_REMOVED = "ATTACHMENT_REMOVED",
  REMINDER_SENT = "REMINDER_SENT",
  LOGIN = "LOGIN",
  PASSWORD_CHANGED = "PASSWORD_CHANGED",
}

// ===== Common =====

export interface ErrorDetail {
  code: string;
  message: string;
  details: Record<string, unknown>;
  correlation_id?: string;
}

export interface ErrorResponse {
  error: ErrorDetail;
}

export interface HealthResponse {
  status: string;
}

export interface ReadinessResponse {
  status: string;
  components: Record<string, string>;
}

// ===== Authentication =====

export interface RegisterRequest {
  email: string;
  password: string;
  full_name?: string;
}

export interface LoginRequest {
  email: string;
  password: string;
}

export interface TokenResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;
  expires_in: number;
}

export interface RefreshTokenRequest {
  refresh_token: string;
}

export interface ChangePasswordRequest {
  current_password: string;
  new_password: string;
}

export interface UpdateProfileRequest {
  full_name: string;
}

export interface UserResponse {
  id: string;
  email: string;
  full_name?: string;
  created_at: string;
}

// ===== Tasks =====

export interface TaskCreate {
  title: string;
  description?: string;
  status?: TaskStatus;
  priority?: TaskPriority;
  due_date?: string; // ISO datetime
  tags?: string[];
}

export interface TaskUpdate {
  title?: string;
  description?: string;
  status?: TaskStatus;
  priority?: TaskPriority;
  due_date?: string; // ISO datetime
  tags?: string[];
}

export interface TaskResponse {
  id: string;
  owner_id: string;
  title: string;
  description?: string;
  status: TaskStatus;
  priority: TaskPriority;
  due_date?: string; // ISO datetime
  tags: string[];
  created_at: string;
  updated_at: string;
}

export interface TaskListResponse {
  items: TaskResponse[];
  page: number;
  page_size: number;
  total: number;
}

// ===== Chat =====

export interface ChatMessageRequest {
  message: string;
}

export interface ChatMessageResponse {
  reply: string;
  created_task?: TaskResponse;
}

export interface AttachmentSummary {
  id: string;
  filename: string;
  size_bytes: number;
  content_type: string;
  created_at: string;
}

export interface TaskDetailResponse {
  task: TaskResponse;
  attachments: AttachmentSummary[];
}

// ===== Attachments =====

export interface AttachmentResponse {
  id: string;
  filename: string;
  content_type: string;
  size_bytes: number;
  created_at: string;
}

export interface AttachmentListResponse {
  items: AttachmentResponse[];
}

// ===== Audit =====

export interface AuditEventResponse {
  id: string;
  user_id?: string;
  event_type: EventType;
  task_id?: string;
  attachment_id?: string;
  details: Record<string, unknown>;
  created_at: string;
}

export interface AuditEventListResponse {
  items: AuditEventResponse[];
  page: number;
  page_size: number;
  total: number;
}

// ===== Type Guards =====

export function isErrorResponse(data: unknown): data is ErrorResponse {
  return (
    typeof data === "object" &&
    data !== null &&
    "error" in data &&
    typeof (data as ErrorResponse).error === "object"
  );
}
