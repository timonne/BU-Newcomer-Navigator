import { useState, useEffect } from 'react';
import { useNavigate, useSearchParams, Link } from 'react-router';
import { useAuth } from '../context/AuthContext';
import { signIn, register, sendVerificationCode, verifyCode } from '../services/auth';
import { generateUsername } from '../data/users';
import { MOCK_USERS } from '../data/users';
import type { AccountType } from '../types';
import LoadingSpinner from '../components/common/LoadingSpinner';

type Mode = 'signin' | 'signup';
type SignupStep = 'details' | 'verify';

const ACCOUNT_TYPE_LABELS: Record<AccountType, string> = {
  student: 'Student',
  staff: 'Staff',
  other: 'Other',
};

export default function Home() {
  const [searchParams] = useSearchParams();
  const [mode, setMode] = useState<Mode>((searchParams.get('mode') as Mode) || 'signin');
  const { isAuthenticated, signIn: ctxSignIn, signInAsDemo } = useAuth();
  const navigate = useNavigate();

  useEffect(() => {
    if (isAuthenticated) navigate('/forum');
  }, [isAuthenticated, navigate]);

  return (
    <main className="min-h-[calc(100vh-3.75rem)] flex flex-col">
      {/* Hero split layout */}
      <div className="flex-1 grid grid-cols-1 lg:grid-cols-2">
        {/* Left — Brand */}
        <div className="hidden lg:flex flex-col justify-between p-12 xl:p-16" style={{ backgroundColor: '#1E3A8A' }}>
          <div>
            <div className="flex items-center gap-3 mb-12">
              <div className="w-10 h-10 rounded-lg bg-white/10 flex items-center justify-center text-white font-bold text-lg">NN</div>
              <span className="text-white font-semibold text-lg" style={{ fontFamily: 'var(--font-display)' }}>Newcomer Navigation</span>
            </div>
            <h1 className="text-5xl xl:text-6xl text-white mb-6 leading-tight" style={{ fontFamily: 'var(--font-display)' }}>
              Find your footing at Bennett.
            </h1>
            <p className="text-blue-200 text-lg leading-relaxed max-w-md">
              Your guided companion for navigating university life — answers from seniors, staff, and an AI assistant built for newcomers.
            </p>
          </div>

          {/* Feature highlights */}
          <div className="grid grid-cols-1 gap-4 mt-12">
            {[
              { icon: '💬', title: 'Community Forum', desc: 'Ask questions, share knowledge, and connect with peers' },
              { icon: '🤖', title: 'Navi — AI Assistant', desc: 'Instant answers about hostel, courses, campus, and more' },
              { icon: '🎓', title: 'Verified Answers', desc: 'Trusted responses from staff and verified seniors' },
            ].map(f => (
              <div key={f.title} className="flex items-start gap-3 p-4 rounded-xl bg-white/5 border border-white/10">
                <span className="text-2xl">{f.icon}</span>
                <div>
                  <p className="text-white font-semibold text-sm">{f.title}</p>
                  <p className="text-blue-200 text-xs mt-0.5">{f.desc}</p>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Right — Auth form */}
        <div className="flex items-center justify-center p-6 sm:p-10 bg-slate-50">
          <div className="w-full max-w-md">
            {/* Mobile logo */}
            <div className="lg:hidden text-center mb-8">
              <div className="inline-flex items-center gap-2">
                <div className="w-9 h-9 rounded-md flex items-center justify-center text-white font-bold text-sm" style={{ backgroundColor: '#1E3A8A' }}>NN</div>
                <span className="font-semibold text-slate-800 text-lg" style={{ fontFamily: 'var(--font-display)' }}>Newcomer Navigation</span>
              </div>
              <p className="text-slate-500 text-sm mt-2">Bennett University, Greater Noida</p>
            </div>

            {/* Tab switcher */}
            <div className="flex bg-white rounded-xl border border-slate-200 p-1 mb-8">
              {(['signin', 'signup'] as Mode[]).map(m => (
                <button
                  key={m}
                  onClick={() => setMode(m)}
                  className={`flex-1 py-2.5 text-sm font-medium rounded-lg transition-all ${
                    mode === m ? 'bg-blue-800 text-white shadow-sm' : 'text-slate-500 hover:text-slate-700'
                  }`}
                  style={mode === m ? { backgroundColor: '#1E3A8A' } : {}}
                >
                  {m === 'signin' ? 'Sign in' : 'Sign up'}
                </button>
              ))}
            </div>

            {mode === 'signin'
              ? <SignInForm onSuccess={user => { ctxSignIn(user); navigate('/forum'); }} onSwitchMode={() => setMode('signup')} />
              : <SignUpForm onSuccess={user => { ctxSignIn(user); navigate('/forum'); }} onSwitchMode={() => setMode('signin')} />
            }

            <div className="mt-4 text-center">
              <button
                onClick={() => { signInAsDemo(); navigate('/forum'); }}
                className="text-xs text-slate-400 hover:text-slate-600 underline transition-colors"
              >
                Explore as demo user (no sign-in required)
              </button>
            </div>
          </div>
        </div>
      </div>
    </main>
  );
}

/* ---- Sign In Form ---- */
function SignInForm({ onSuccess, onSwitchMode }: { onSuccess: (u: any) => void; onSwitchMode: () => void }) {
  const [identifier, setIdentifier] = useState('');
  const [password, setPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!identifier.trim()) return setError('Please enter your email or username.');
    if (!password) return setError('Please enter your password.');
    setError('');
    setLoading(true);
    const result = await signIn(identifier, password);
    setLoading(false);
    if (result.success && result.user) onSuccess(result.user);
    else setError(result.error || 'Sign-in failed.');
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      <div>
        <label className="block text-sm font-medium text-slate-700 mb-1.5">Email or username</label>
        <input
          type="text"
          value={identifier}
          onChange={e => { setIdentifier(e.target.value); setError(''); }}
          placeholder="sneha.gupta or sneha@bennett.edu.in"
          className="w-full px-4 py-2.5 rounded-lg border border-slate-300 text-sm focus:outline-none focus:ring-2 focus:ring-blue-300 transition-colors bg-white"
          autoFocus
        />
      </div>

      <div>
        <label className="block text-sm font-medium text-slate-700 mb-1.5">Password</label>
        <div className="relative">
          <input
            type={showPassword ? 'text' : 'password'}
            value={password}
            onChange={e => { setPassword(e.target.value); setError(''); }}
            placeholder="Enter your password"
            className="w-full px-4 py-2.5 pr-11 rounded-lg border border-slate-300 text-sm focus:outline-none focus:ring-2 focus:ring-blue-300 transition-colors bg-white"
          />
          <button type="button" onClick={() => setShowPassword(v => !v)} className="absolute right-3 top-1/2 -translate-y-1/2 text-slate-400 hover:text-slate-600">
            {showPassword ? <EyeOffIcon /> : <EyeIcon />}
          </button>
        </div>
      </div>

      {error && <p className="text-sm text-red-600 bg-red-50 rounded-lg px-3 py-2">{error}</p>}

      <button
        type="submit"
        disabled={loading}
        className="w-full py-2.5 text-sm font-semibold text-white rounded-lg transition-colors disabled:opacity-60 flex items-center justify-center gap-2"
        style={{ backgroundColor: '#1E3A8A' }}
      >
        {loading && <LoadingSpinner size={15} />}
        Sign in
      </button>

      <div className="bg-slate-50 border border-slate-200 rounded-lg p-3">
        <p className="text-xs text-slate-500 font-medium mb-1.5">Demo accounts</p>
        <div className="space-y-1">
          {[
            { label: 'Student (Aryan)', value: 'aryan.sharma' },
            { label: 'Staff (Dr. Suresh)', value: 'dr.suresh.kumar' },
          ].map(a => (
            <button
              key={a.value}
              type="button"
              onClick={() => setIdentifier(a.value)}
              className="text-xs text-blue-700 hover:underline block"
            >
              {a.label} → {a.value}
            </button>
          ))}
        </div>
      </div>

      <p className="text-center text-sm text-slate-500">
        Don't have an account?{' '}
        <button type="button" onClick={onSwitchMode} className="text-blue-700 font-medium hover:underline">Sign up</button>
      </p>
    </form>
  );
}

/* ---- Sign Up Form ---- */
function SignUpForm({ onSuccess, onSwitchMode }: { onSuccess: (u: any) => void; onSwitchMode: () => void }) {
  const [step, setStep] = useState<SignupStep>('details');
  const [accountType, setAccountType] = useState<AccountType>('student');
  const [fullName, setFullName] = useState('');
  const [generatedUsername, setGeneratedUsername] = useState('');
  const [phone, setPhone] = useState('');
  const [email, setEmail] = useState('');
  const [course, setCourse] = useState('');
  const [password, setPassword] = useState('');
  const [confirm, setConfirm] = useState('');
  const [showPass, setShowPass] = useState(false);
  const [loading, setLoading] = useState(false);
  const [errors, setErrors] = useState<Record<string, string>>({});
  const [registeredUser, setRegisteredUser] = useState<any>(null);
  const [verifyCode_state, setVerifyCode_state] = useState('');
  const [verifyMsg, setVerifyMsg] = useState('');
  const [verifySent, setVerifySent] = useState(false);

  useEffect(() => {
    if (fullName.trim()) {
      const existing = MOCK_USERS.map(u => u.username);
      setGeneratedUsername(generateUsername(fullName, existing));
    } else {
      setGeneratedUsername('');
    }
  }, [fullName]);

  function passwordStrength(p: string): { label: string; color: string; width: string } {
    if (!p) return { label: '', color: 'bg-slate-200', width: 'w-0' };
    if (p.length < 6) return { label: 'Too short', color: 'bg-red-400', width: 'w-1/4' };
    if (p.length < 8) return { label: 'Weak', color: 'bg-orange-400', width: 'w-2/4' };
    if (/[A-Z]/.test(p) && /[0-9]/.test(p)) return { label: 'Strong', color: 'bg-green-500', width: 'w-full' };
    return { label: 'Fair', color: 'bg-yellow-400', width: 'w-3/4' };
  }

  const strength = passwordStrength(password);

  function validate() {
    const e: Record<string, string> = {};
    if (!fullName.trim()) e.fullName = 'Full name is required.';
    if (!phone.trim() || !/^[+\d\s\-()]{7,15}$/.test(phone)) e.phone = 'Enter a valid phone number.';
    if (!email.trim() || !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)) e.email = 'Enter a valid email address.';
    if (accountType === 'student' && !email.endsWith('@bennett.edu.in')) {
      // Note: warn but don't block
    }
    if (!password || password.length < 6) e.password = 'Password must be at least 6 characters.';
    if (password !== confirm) e.confirm = 'Passwords do not match.';
    return e;
  }

  async function handleRegister(e: React.FormEvent) {
    e.preventDefault();
    const errs = validate();
    if (Object.keys(errs).length > 0) return setErrors(errs);
    setErrors({});
    setLoading(true);
    const result = await register({ fullName, phone, email, accountType, password, confirmPassword: confirm, course });
    setLoading(false);
    if (result.success && result.user) {
      setRegisteredUser(result.user);
      if (accountType !== 'other') {
        setStep('verify');
        handleSendCode(result.user);
      } else {
        onSuccess(result.user);
      }
    } else {
      setErrors({ submit: result.error || 'Registration failed.' });
    }
  }

  async function handleSendCode(user?: any) {
    const u = user || registeredUser;
    setLoading(true);
    const result = await sendVerificationCode(u.email);
    setLoading(false);
    setVerifyMsg(result.message);
    setVerifySent(result.success);
  }

  async function handleVerify(e: React.FormEvent) {
    e.preventDefault();
    setLoading(true);
    const result = await verifyCode(registeredUser.id, verifyCode_state);
    setLoading(false);
    setVerifyMsg(result.message);
    if (result.success) {
      setTimeout(() => onSuccess({ ...registeredUser, verificationStatus: 'verified' }), 800);
    }
  }

  if (step === 'verify') {
    return (
      <div className="space-y-4">
        <div className="text-center mb-6">
          <div className="w-14 h-14 rounded-full bg-blue-50 flex items-center justify-center mx-auto mb-3">
            <svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="#1E3A8A" strokeWidth="1.5" strokeLinecap="round"><path d="M3 8l7.89 5.26a2 2 0 0 0 2.22 0L21 8M5 19h14a2 2 0 0 0 2-2V7a2 2 0 0 0-2-2H5a2 2 0 0 0-2 2v10a2 2 0 0 0 2 2z"/></svg>
          </div>
          <h3 className="font-semibold text-slate-800" style={{ fontFamily: 'var(--font-display)' }}>Verify your email</h3>
          <p className="text-sm text-slate-500 mt-1">
            {accountType === 'student' ? 'Student' : 'Staff'} accounts require email verification.
          </p>
        </div>
        {verifyMsg && (
          <div className={`text-xs rounded-lg px-3 py-2 ${verifySent ? 'bg-blue-50 text-blue-700 border border-blue-200' : 'bg-red-50 text-red-700'}`}>
            {verifyMsg}
          </div>
        )}
        <form onSubmit={handleVerify} className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-slate-700 mb-1.5">Verification code</label>
            <input
              value={verifyCode_state}
              onChange={e => setVerifyCode_state(e.target.value)}
              placeholder="Enter 6-digit code (DEMO: 123456)"
              className="w-full px-4 py-2.5 rounded-lg border border-slate-300 text-sm focus:outline-none focus:ring-2 focus:ring-blue-300 bg-white font-mono tracking-widest"
              maxLength={6}
            />
          </div>
          <button
            type="submit"
            disabled={loading || verifyCode_state.length < 4}
            className="w-full py-2.5 text-sm font-semibold text-white rounded-lg flex items-center justify-center gap-2 disabled:opacity-60"
            style={{ backgroundColor: '#1E3A8A' }}
          >
            {loading && <LoadingSpinner size={14} />}
            Verify & Continue
          </button>
          <button
            type="button"
            onClick={() => onSuccess(registeredUser)}
            className="w-full text-xs text-slate-400 hover:text-slate-600 underline"
          >
            Skip for now (demo — continue without verification)
          </button>
        </form>
      </div>
    );
  }

  return (
    <form onSubmit={handleRegister} className="space-y-4">
      {/* Account type */}
      <div>
        <label className="block text-sm font-medium text-slate-700 mb-2">I am a</label>
        <div className="grid grid-cols-3 gap-2">
          {(['student', 'staff', 'other'] as AccountType[]).map(t => (
            <button
              key={t}
              type="button"
              onClick={() => setAccountType(t)}
              className={`py-2 text-sm font-medium rounded-lg border transition-all ${
                accountType === t
                  ? 'border-blue-700 text-blue-800 bg-blue-50'
                  : 'border-slate-300 text-slate-600 hover:border-slate-400 bg-white'
              }`}
            >
              {ACCOUNT_TYPE_LABELS[t]}
            </button>
          ))}
        </div>
        {(accountType === 'student' || accountType === 'staff') && (
          <p className="text-xs text-amber-700 bg-amber-50 rounded px-2 py-1 mt-2 border border-amber-200">
            {accountType === 'student' ? 'Student' : 'Staff'} accounts require a <strong>@bennett.edu.in</strong> email for verification.
          </p>
        )}
      </div>

      {/* Full name */}
      <div>
        <label className="block text-sm font-medium text-slate-700 mb-1.5">Full name <span className="text-red-500">*</span></label>
        <input
          value={fullName}
          onChange={e => { setFullName(e.target.value); setErrors(p => ({ ...p, fullName: '' })); }}
          placeholder="e.g. Sneha Gupta"
          className={`w-full px-4 py-2.5 rounded-lg border text-sm focus:outline-none focus:ring-2 focus:ring-blue-300 bg-white ${errors.fullName ? 'border-red-400' : 'border-slate-300'}`}
        />
        {generatedUsername && (
          <p className="text-xs text-slate-500 mt-1">
            Your username will be: <span className="font-mono font-medium text-blue-700">@{generatedUsername}</span>
          </p>
        )}
        {errors.fullName && <p className="text-xs text-red-600 mt-1">{errors.fullName}</p>}
      </div>

      {/* Phone */}
      <div>
        <label className="block text-sm font-medium text-slate-700 mb-1.5">Phone number <span className="text-red-500">*</span></label>
        <input
          type="tel"
          value={phone}
          onChange={e => { setPhone(e.target.value); setErrors(p => ({ ...p, phone: '' })); }}
          placeholder="+91 98765 43210"
          className={`w-full px-4 py-2.5 rounded-lg border text-sm focus:outline-none focus:ring-2 focus:ring-blue-300 bg-white ${errors.phone ? 'border-red-400' : 'border-slate-300'}`}
        />
        {errors.phone && <p className="text-xs text-red-600 mt-1">{errors.phone}</p>}
      </div>

      {/* Email */}
      <div>
        <label className="block text-sm font-medium text-slate-700 mb-1.5">Email <span className="text-red-500">*</span></label>
        <input
          type="email"
          value={email}
          onChange={e => { setEmail(e.target.value); setErrors(p => ({ ...p, email: '' })); }}
          placeholder={accountType !== 'other' ? 'yourname@bennett.edu.in' : 'your@email.com'}
          className={`w-full px-4 py-2.5 rounded-lg border text-sm focus:outline-none focus:ring-2 focus:ring-blue-300 bg-white ${errors.email ? 'border-red-400' : 'border-slate-300'}`}
        />
        {errors.email && <p className="text-xs text-red-600 mt-1">{errors.email}</p>}
      </div>

      {/* Course (student/staff only) */}
      {accountType !== 'other' && (
        <div>
          <label className="block text-sm font-medium text-slate-700 mb-1.5">
            {accountType === 'student' ? 'Course / Programme' : 'Department'}
          </label>
          <input
            value={course}
            onChange={e => setCourse(e.target.value)}
            placeholder={accountType === 'student' ? 'e.g. B.Tech CSE' : 'e.g. Computer Science'}
            className="w-full px-4 py-2.5 rounded-lg border border-slate-300 text-sm focus:outline-none focus:ring-2 focus:ring-blue-300 bg-white"
          />
        </div>
      )}

      {/* Password */}
      <div>
        <label className="block text-sm font-medium text-slate-700 mb-1.5">Password <span className="text-red-500">*</span></label>
        <div className="relative">
          <input
            type={showPass ? 'text' : 'password'}
            value={password}
            onChange={e => { setPassword(e.target.value); setErrors(p => ({ ...p, password: '' })); }}
            placeholder="At least 6 characters"
            className={`w-full px-4 py-2.5 pr-11 rounded-lg border text-sm focus:outline-none focus:ring-2 focus:ring-blue-300 bg-white ${errors.password ? 'border-red-400' : 'border-slate-300'}`}
          />
          <button type="button" onClick={() => setShowPass(v => !v)} className="absolute right-3 top-1/2 -translate-y-1/2 text-slate-400 hover:text-slate-600">
            {showPass ? <EyeOffIcon /> : <EyeIcon />}
          </button>
        </div>
        {password && (
          <div className="mt-2">
            <div className="h-1 bg-slate-200 rounded-full overflow-hidden">
              <div className={`h-full rounded-full transition-all ${strength.color} ${strength.width}`} />
            </div>
            <p className="text-xs text-slate-500 mt-1">{strength.label}</p>
          </div>
        )}
        {errors.password && <p className="text-xs text-red-600 mt-1">{errors.password}</p>}
      </div>

      {/* Confirm password */}
      <div>
        <label className="block text-sm font-medium text-slate-700 mb-1.5">Re-enter password <span className="text-red-500">*</span></label>
        <input
          type="password"
          value={confirm}
          onChange={e => { setConfirm(e.target.value); setErrors(p => ({ ...p, confirm: '' })); }}
          placeholder="Repeat your password"
          className={`w-full px-4 py-2.5 rounded-lg border text-sm focus:outline-none focus:ring-2 focus:ring-blue-300 bg-white ${errors.confirm ? 'border-red-400' : 'border-slate-300'}`}
        />
        {errors.confirm && <p className="text-xs text-red-600 mt-1">{errors.confirm}</p>}
      </div>

      {errors.submit && <p className="text-sm text-red-600 bg-red-50 rounded-lg px-3 py-2">{errors.submit}</p>}

      <p className="text-xs text-slate-400 leading-relaxed">
        By signing up, you agree to the Newcomer Navigation community guidelines and terms of use.
      </p>

      <button
        type="submit"
        disabled={loading}
        className="w-full py-2.5 text-sm font-semibold text-white rounded-lg flex items-center justify-center gap-2 disabled:opacity-60"
        style={{ backgroundColor: '#1E3A8A' }}
      >
        {loading && <LoadingSpinner size={14} />}
        Create Account
      </button>

      <p className="text-center text-sm text-slate-500">
        Already have an account?{' '}
        <button type="button" onClick={onSwitchMode} className="text-blue-700 font-medium hover:underline">Sign in</button>
      </p>
    </form>
  );
}

function EyeIcon() {
  return (
    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"/><circle cx="12" cy="12" r="3"/>
    </svg>
  );
}
function EyeOffIcon() {
  return (
    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <path d="M17.94 17.94A10.07 10.07 0 0 1 12 20c-7 0-11-8-11-8a18.45 18.45 0 0 1 5.06-5.94M9.9 4.24A9.12 9.12 0 0 1 12 4c7 0 11 8 11 8a18.5 18.5 0 0 1-2.16 3.19m-6.72-1.07a3 3 0 1 1-4.24-4.24M1 1l22 22"/>
    </svg>
  );
}
