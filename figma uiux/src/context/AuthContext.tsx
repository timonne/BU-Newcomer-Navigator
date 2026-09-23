import React, { createContext, useContext, useState, useCallback, useEffect } from 'react';
import type { User } from '../types';
import { getCurrentUser, signOut as apiSignOut, signIn as apiSignIn } from '../services/auth';

/**
 * INTEGRATION NOTE: the context value keeps every member it had before
 * (`currentUser`, `isAuthenticated`, `signIn`, `signOut`,
 * `updateCurrentUser`, `signInAsDemo`) with the same signatures, so Navbar,
 * Home, Profile, Forum, QuestionThread, Chatbot and AskQuestionModal all work
 * unchanged. `isRestoring` is added for anyone who wants it; nothing is
 * required to use it.
 *
 * Two real changes behind the same interface:
 *   - the session is restored from the backend's httpOnly cookie on mount,
 *     so a page refresh no longer signs you out
 *   - the hardcoded DEMO_USER object is gone; `signInAsDemo()` now signs in
 *     to the seeded demo account against the real backend
 */

interface AuthContextValue {
  currentUser: User | null;
  isAuthenticated: boolean;
  signIn: (user: User) => void;
  signOut: () => void;
  updateCurrentUser: (updates: Partial<User>) => void;
  // DEMO: signs in as the seeded demo student for quick exploration.
  signInAsDemo: () => void;
  // True until the initial session check finishes.
  isRestoring: boolean;
}

const AuthContext = createContext<AuthContextValue | null>(null);

// Credentials of the seeded demo account (backend/seed.py). Not a secret —
// a well-known local development login that only exists after seeding.
const DEMO_IDENTIFIER = 'sneha.demo@example.com';
const DEMO_PASSWORD = 'DemoPassword123';

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [currentUser, setCurrentUser] = useState<User | null>(null);
  const [isRestoring, setIsRestoring] = useState(true);

  // Restore the session from the auth cookie on first mount.
  useEffect(() => {
    let cancelled = false;
    getCurrentUser()
      .then(user => {
        if (!cancelled) setCurrentUser(user);
      })
      .finally(() => {
        if (!cancelled) setIsRestoring(false);
      });
    return () => {
      cancelled = true;
    };
  }, []);

  const signIn = useCallback((user: User) => {
    setCurrentUser(user);
  }, []);

  const signOut = useCallback(() => {
    // Clear locally straight away so the UI responds immediately, then tell
    // the backend to drop the cookie.
    setCurrentUser(null);
    void apiSignOut();
  }, []);

  const updateCurrentUser = useCallback((updates: Partial<User>) => {
    setCurrentUser(prev => (prev ? { ...prev, ...updates } : prev));
  }, []);

  const signInAsDemo = useCallback(() => {
    void apiSignIn(DEMO_IDENTIFIER, DEMO_PASSWORD).then(result => {
      if (result.success && result.user) setCurrentUser(result.user);
      else
        console.warn(
          'Demo sign-in failed. Has the backend been started and seeded? ' +
            'Run `python seed.py` in the backend folder.',
        );
    });
  }, []);

  return (
    <AuthContext.Provider
      value={{
        currentUser,
        isAuthenticated: !!currentUser,
        signIn,
        signOut,
        updateCurrentUser,
        signInAsDemo,
        isRestoring,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error('useAuth must be used inside AuthProvider');
  return ctx;
}
