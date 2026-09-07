export interface Project {
  id: string
  name: string
  description: string
  status: 'active' | 'archived'
  due_date: string | null
  created_at: string
  updated_at: string
}

export interface ProjectMemberOut {
  id: string
  display_name: string
  email: string
}

export interface ProjectMemberOut {
  id: string
  display_name: string
  email: string
}

export type TaskStatus = 'open' | 'in_progress' | 'done'
export type TaskPriority = 'low' | 'medium' | 'high'

export interface Task {
  id: string
  project_id: string
  title: string
  description: string
  status: TaskStatus
  priority: TaskPriority
  due_date: string | null
  assignee_id: string | null
  assignee_name: string | null
  created_at: string
  updated_at: string
}

export interface Comment {
  id: string
  task_id: string
  author_id: string | null
  author_name: string | null
  body: string
  created_at: string
  updated_at: string
}

export interface TaskAttachmentOut {
  id: string
  file_id: string
  filename: string
  mime_type: string
  size_bytes: number
  created_at: string
  created_by_name: string | null
}

export interface TaskDetail extends Task {
  comments: Comment[]
  attachments: TaskAttachmentOut[]
}

export interface MemberOut {
  id: string
  display_name: string
}

export interface DocumentRef {
  id: string
  project_id: string | null
  title: string
  category: string
  relative_path: string | null
  folder_id: string | null
  file_id: string | null
  created_at: string
  updated_at: string
}

export interface FolderOut {
  id: string
  name: string
  parent_id: string | null
  created_at: string
  updated_at: string
}

export interface CatalogEntry {
  relative_path: string
  name: string
  root_name: string
  size_bytes: number
}

export interface DocumentContent {
  document: DocumentRef
  content: string | null
  missing: boolean
  is_binary: boolean
  download_url: string | null
}

export type AIActionType = 'analyze' | 'plan' | 'execute' | 'summarize'
export type AIActionStatus = 'pending' | 'completed' | 'failed'

export interface AIResult {
  id: string
  action_id: string
  content: string
  summary: string
  created_at: string
}

export interface AIAction {
  id: string
  project_id: string | null
  task_id: string | null
  action_type: AIActionType
  input_text: string
  context_summary: string
  status: AIActionStatus
  provider: string
  error: string
  created_at: string
  completed_at: string | null
}

export interface AIActionDetail extends AIAction {
  result: AIResult | null
}

export interface DashboardStats {
  projects: number
  tasks: number
  documents: number
  ai_actions: number
}

export interface Dashboard {
  stats: DashboardStats
  recent_projects: Project[]
  recent_ai_actions: AIActionDetail[]
}

export interface PaginationMeta {
  page: number
  pageSize: number
  totalItems: number
  totalPages: number
  hasNext: boolean
  hasPrevious: boolean
}

export interface EnvelopeMeta {
  pagination?: PaginationMeta
}

export interface EnvelopeLinks {
  [key: string]: unknown
}

export interface Envelope<T> {
  data: T
  meta: EnvelopeMeta
  links: EnvelopeLinks
}

export interface AuthTokens {
  access_token: string
  refresh_token: string
  token_type: string
}

export interface AuthUser {
  id: string
  email: string
  display_name: string
  status: 'active' | 'blocked'
  organization_id: string | null
  version: number
  created_at: string
}

export interface MeOut extends AuthUser {
  organization: { id: string; name: string } | null
  roles: string[]
}

export interface OrganizationOut {
  id: string
  name: string
  description: string | null
  status: string
  created_by: string | null
  version: number
  created_at: string
  updated_at: string
}

export interface NotificationOut {
  id: string
  title: string
  body: string
  entity_type: string
  entity_id: string | null
  read_at: string | null
  created_at: string
}

export interface ProjectSearchItem {
  id: string
  name: string
  status: string
}

export interface TaskSearchItem {
  id: string
  title: string
  status: string
  project_id: string
}

export interface DocumentSearchItem {
  id: string
  title: string
  project_id: string | null
  folder_id: string | null
}

export interface FileSearchItem {
  id: string
  filename: string
  mime_type: string
}

export interface CustomerSearchItem {
  id: string
  name: string
  status: string
}

export interface SearchResults {
  projects: ProjectSearchItem[]
  tasks: TaskSearchItem[]
  documents: DocumentSearchItem[]
  files: FileSearchItem[]
  customers: CustomerSearchItem[]
}

export type CustomerStatus = 'lead' | 'active' | 'archived'

export interface TagOut {
  id: string
  name: string
}

export interface CompanyOut {
  id: string
  name: string
  created_at: string
  updated_at: string
}

export interface CustomerOut {
  id: string
  name: string
  status: CustomerStatus
  description: string
  company_id: string | null
  company: CompanyOut | null
  company_name: string | null
  tags: TagOut[]
  created_at: string
  updated_at: string
}

export interface ContactOut {
  id: string
  customer_id: string
  name: string
  email: string | null
  phone: string | null
  created_at: string
  updated_at: string
}

export interface CustomerNoteOut {
  id: string
  customer_id: string
  author_id: string | null
  author_name: string | null
  body: string
  created_at: string
  updated_at: string
}

export interface SettingOut {
  key: string
  value: string
}

export interface AuditRecordOut {
  id: string
  action_type: string
  entity_type: string
  entity_id: string | null
  user_id: string | null
  organization_id: string | null
  detail: Record<string, unknown>
  created_at: string
}

export interface UserRow {
  id: string
  email: string
  display_name: string
  status: string
  organization_id: string | null
  version: number
  created_at: string
  roles: string[]
}

export interface InvitedUser {
  id: string
  email: string
  display_name: string
  organization_id: string
  generated_password: string | null
}
