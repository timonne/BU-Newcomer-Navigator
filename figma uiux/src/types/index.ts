export type AccountType = 'student' | 'staff' | 'other';
export type VerificationStatus = 'unverified' | 'pending' | 'verified';

export interface User {
  id: string;
  fullName: string;
  username: string;
  email: string;
  phone: string;
  accountType: AccountType;
  verificationStatus: VerificationStatus;
  course?: string;
  department?: string;
  bio?: string;
  avatarColor: string;
  joinedAt: string;
  questionsCount: number;
  answersCount: number;
  upvotesReceived: number;
}

export interface Tag {
  id: string;
  name: string;
  color: string;
}

export interface AcademicCategory {
  id: string;
  name: string;
  type: 'academic' | 'non-academic';
  subcategories?: string[];
}

export interface Question {
  id: string;
  title: string;
  body: string;
  authorId: string;
  categoryId: string;
  tags: string[];
  createdAt: string;
  updatedAt: string;
  answerCount: number;
  upvotes: number;
  downvotes: number;
  isAnswered: boolean;
  views: number;
}

export interface Answer {
  id: string;
  questionId: string;
  body: string;
  authorId: string;
  createdAt: string;
  updatedAt: string;
  upvotes: number;
  downvotes: number;
  isAccepted: boolean;
  parentAnswerId?: string;
}

export interface Vote {
  userId: string;
  targetId: string;
  targetType: 'question' | 'answer';
  value: 1 | -1;
}

export interface ChatMessage {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  timestamp: string;
  sourceType?: 'university' | 'community' | 'general';
  sourceRef?: {
    questionId?: string;
    questionTitle?: string;
    answerId?: string;
    authorName?: string;
  };
}

export interface KnowledgeBaseEntry {
  id: string;
  question: string;
  answer: string;
  keywords: string[];
  category: string;
  sourceType: 'university' | 'community' | 'general';
}

export interface AuthState {
  isAuthenticated: boolean;
  currentUser: User | null;
}

export interface ForumFilters {
  search: string;
  categoryId: string | null;
  sortBy: 'latest' | 'most-upvoted' | 'most-answered';
  answered: 'all' | 'answered' | 'unanswered';
}

export interface RegisterFormData {
  fullName: string;
  phone: string;
  email: string;
  accountType: AccountType;
  password: string;
  confirmPassword: string;
  course?: string;
  department?: string;
}
