/**
 * Forum service — real backend implementation.
 *
 * INTEGRATION NOTE: exported names and signatures are unchanged from the
 * mock version (`getQuestions`, `getQuestionById`, `getAnswersByQuestionId`,
 * `submitQuestion`, `submitAnswer`, `voteOnTarget`, `getUserVote`,
 * `getQuestions_sync`, `ForumResult<T>`), so Forum.tsx, QuestionThread.tsx
 * and Profile.tsx needed no changes.
 *
 * Two caches back the synchronous functions those pages rely on:
 *   - `questionCache`  for `getQuestions_sync()` (used by Profile.tsx)
 *   - `voteCache`      for `getUserVote()`       (used by QuestionThread.tsx)
 * Both are filled from the server responses, so the values they return are
 * server-computed, never locally guessed. Vote totals in particular always
 * come from the backend's aggregate — this module never increments a counter
 * itself.
 *
 * Author objects arrive embedded in question and answer responses; they are
 * pushed into the auth service's user cache so `getUserById()` keeps working
 * synchronously during render.
 */
import type { Question, Answer } from '../types';
import { api, errorMessage } from './api';
import { cacheUsers } from './auth';

export interface ForumResult<T> {
  success: boolean;
  data?: T;
  error?: string;
}

// The backend returns authors and the caller's own vote alongside each
// record. These extend the frontend's own types rather than altering them.
type QuestionPayload = Question & { author?: any; userVote?: number };
type AnswerPayload = Answer & { author?: any; userVote?: number };

interface PaginatedQuestions {
  items: QuestionPayload[];
  total: number;
  page: number;
  pageSize: number;
}

let questionCache: Question[] = [];
const voteCache = new Map<string, 1 | -1>();

function absorbQuestion(q: QuestionPayload): Question {
  if (q.author) cacheUsers([q.author]);
  if (q.userVote === 1 || q.userVote === -1) voteCache.set(q.id, q.userVote);
  else voteCache.delete(q.id);
  const { author, userVote, ...question } = q;
  return question as Question;
}

function absorbAnswer(a: AnswerPayload): Answer {
  if (a.author) cacheUsers([a.author]);
  if (a.userVote === 1 || a.userVote === -1) voteCache.set(a.id, a.userVote);
  else voteCache.delete(a.id);
  const { author, userVote, ...answer } = a;
  return answer as Answer;
}

export interface QuestionQuery {
  search?: string;
  categoryId?: string | null;
  tags?: string[];
  answered?: 'all' | 'answered' | 'unanswered';
  sortBy?: 'latest' | 'most-upvoted' | 'most-answered';
  page?: number;
  pageSize?: number;
}

/**
 * Loads questions. Called with no arguments by Forum.tsx, which does its own
 * client-side filtering over the full list exactly as before — so its
 * behaviour is unchanged. The optional query lets you push search, filter,
 * sort and pagination down to the server when you want to.
 */
export async function getQuestions(query: QuestionQuery = {}): Promise<ForumResult<Question[]>> {
  try {
    const params = new URLSearchParams();
    if (query.search) params.set('search', query.search);
    if (query.categoryId) params.set('categoryId', query.categoryId);
    if (query.tags?.length) params.set('tags', query.tags.join(','));
    if (query.answered && query.answered !== 'all') params.set('answered', query.answered);
    if (query.sortBy) params.set('sortBy', query.sortBy);
    params.set('page', String(query.page ?? 1));
    params.set('pageSize', String(query.pageSize ?? 100));

    const result = await api.get<PaginatedQuestions>(`/questions?${params.toString()}`);
    const questions = result.items.map(absorbQuestion);
    questionCache = questions;
    return { success: true, data: questions };
  } catch (error) {
    return { success: false, error: errorMessage(error, 'Could not load questions.') };
  }
}

export async function getQuestionsPage(
  query: QuestionQuery = {},
): Promise<ForumResult<PaginatedQuestions>> {
  try {
    const params = new URLSearchParams();
    if (query.search) params.set('search', query.search);
    if (query.categoryId) params.set('categoryId', query.categoryId);
    if (query.tags?.length) params.set('tags', query.tags.join(','));
    if (query.answered && query.answered !== 'all') params.set('answered', query.answered);
    if (query.sortBy) params.set('sortBy', query.sortBy);
    params.set('page', String(query.page ?? 1));
    params.set('pageSize', String(query.pageSize ?? 20));

    const result = await api.get<PaginatedQuestions>(`/questions?${params.toString()}`);
    result.items.forEach(absorbQuestion);
    return { success: true, data: result };
  } catch (error) {
    return { success: false, error: errorMessage(error, 'Could not load questions.') };
  }
}

export async function getQuestionById(id: string): Promise<ForumResult<Question>> {
  try {
    const payload = await api.get<QuestionPayload>(`/questions/${encodeURIComponent(id)}`);
    return { success: true, data: absorbQuestion(payload) };
  } catch (error) {
    return { success: false, error: errorMessage(error, 'Question not found.') };
  }
}

export async function getAnswersByQuestionId(
  questionId: string,
  sort: 'votes' | 'newest' = 'votes',
): Promise<ForumResult<Answer[]>> {
  try {
    const payload = await api.get<AnswerPayload[]>(
      `/questions/${encodeURIComponent(questionId)}/answers?sort=${sort}`,
    );
    return { success: true, data: payload.map(absorbAnswer) };
  } catch (error) {
    return { success: false, error: errorMessage(error, 'Could not load answers.') };
  }
}

export async function submitQuestion(
  question: Omit<
    Question,
    'id' | 'createdAt' | 'updatedAt' | 'answerCount' | 'upvotes' | 'downvotes' | 'isAnswered' | 'views'
  >,
): Promise<ForumResult<Question>> {
  try {
    // authorId is deliberately not sent: the backend takes the author from
    // the auth cookie, so a client cannot post as someone else.
    const payload = await api.post<QuestionPayload>('/questions', {
      title: question.title,
      body: question.body,
      categoryId: question.categoryId,
      tags: question.tags,
    });
    const created = absorbQuestion(payload);
    questionCache = [created, ...questionCache];
    return { success: true, data: created };
  } catch (error) {
    return { success: false, error: errorMessage(error, 'Could not post your question.') };
  }
}

export async function submitAnswer(
  answer: Omit<Answer, 'id' | 'createdAt' | 'updatedAt' | 'upvotes' | 'downvotes' | 'isAccepted'>,
): Promise<ForumResult<Answer>> {
  try {
    const payload = await api.post<AnswerPayload>(
      `/questions/${encodeURIComponent(answer.questionId)}/answers`,
      { body: answer.body },
    );
    return { success: true, data: absorbAnswer(payload) };
  } catch (error) {
    return { success: false, error: errorMessage(error, 'Could not post your answer.') };
  }
}

export async function editQuestion(
  id: string,
  updates: { title?: string; body?: string; categoryId?: string; tags?: string[]; status?: string },
): Promise<ForumResult<Question>> {
  try {
    const payload = await api.patch<QuestionPayload>(`/questions/${encodeURIComponent(id)}`, updates);
    return { success: true, data: absorbQuestion(payload) };
  } catch (error) {
    return { success: false, error: errorMessage(error, 'Could not update the question.') };
  }
}

export async function deleteQuestion(id: string): Promise<ForumResult<null>> {
  try {
    await api.delete(`/questions/${encodeURIComponent(id)}`);
    questionCache = questionCache.filter(q => q.id !== id);
    return { success: true, data: null };
  } catch (error) {
    return { success: false, error: errorMessage(error, 'Could not delete the question.') };
  }
}

export async function editAnswer(id: string, body: string): Promise<ForumResult<Answer>> {
  try {
    const payload = await api.patch<AnswerPayload>(`/answers/${encodeURIComponent(id)}`, { body });
    return { success: true, data: absorbAnswer(payload) };
  } catch (error) {
    return { success: false, error: errorMessage(error, 'Could not update the answer.') };
  }
}

export async function deleteAnswer(id: string): Promise<ForumResult<null>> {
  try {
    await api.delete(`/answers/${encodeURIComponent(id)}`);
    return { success: true, data: null };
  } catch (error) {
    return { success: false, error: errorMessage(error, 'Could not delete the answer.') };
  }
}

/**
 * Casts a vote. The `userId` parameter is kept so QuestionThread.tsx needs no
 * edit, but it is not what identifies the voter — the backend uses the auth
 * cookie. Sending the same value twice removes the vote; sending the
 * opposite value switches it. Both totals come back server-computed.
 */
export async function voteOnTarget(
  userId: string,
  targetId: string,
  targetType: 'question' | 'answer',
  value: 1 | -1,
): Promise<ForumResult<{ upvotes: number; downvotes: number }>> {
  void userId;
  try {
    const result = await api.post<{ upvotes: number; downvotes: number; userVote: number }>(
      '/votes',
      { targetType, targetId, value },
    );
    if (result.userVote === 1 || result.userVote === -1) voteCache.set(targetId, result.userVote);
    else voteCache.delete(targetId);

    questionCache = questionCache.map(q =>
      q.id === targetId ? { ...q, upvotes: result.upvotes, downvotes: result.downvotes } : q,
    );
    return { success: true, data: { upvotes: result.upvotes, downvotes: result.downvotes } };
  } catch (error) {
    return { success: false, error: errorMessage(error, 'Could not record your vote.') };
  }
}

/** Synchronous, as before — reads the cache filled by the calls above. */
export function getUserVote(userId: string, targetId: string): 1 | -1 | 0 {
  void userId;
  return voteCache.get(targetId) ?? 0;
}

/** Synchronous, as before — used by Profile.tsx. */
export function getQuestions_sync(): Question[] {
  return [...questionCache];
}

/** Loads a user's own questions, for the profile page. */
export async function getQuestionsByAuthor(authorId: string): Promise<ForumResult<Question[]>> {
  const result = await getQuestions({ pageSize: 100 });
  if (!result.success || !result.data) return result;
  return { success: true, data: result.data.filter(q => q.authorId === authorId) };
}
