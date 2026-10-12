import React, { useEffect, useRef, useState } from 'react';
import {
  Sparkles, ShieldCheck, SendHorizontal, RotateCcw, BookOpen, UsersRound,
  GraduationCap, TrendingUp, ChevronRight, LockKeyhole, Server, CircleHelp,
  CheckCircle2, AlertCircle, LoaderCircle, Database, MessageCircle, Zap,
} from 'lucide-react';
import { api } from './api';

const FALLBACK_PROMPTS = [
  'How many students are enrolled?',
  'What is the overall average score?',
  'What is the attendance rate?',
  'Which subject has the highest average marks?',
  'Compare performance by program',
  'Show Semester 4 performance',
];

const SELECTED_ICONS = [UsersRound, TrendingUp, CheckCircle2, BookOpen, GraduationCap, Database, GraduationCap, CheckCircle2];

export default function AssistantPage({ user }) {
  const [capabilities, setCapabilities] = useState(null);
  const [messages, setMessages] = useState([]);
  const [question, setQuestion] = useState('');
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState('');
  const endRef = useRef(null);
  const inputRef = useRef(null);
  const pending = useRef(false);

  useEffect(() => {
    let active = true;
    api.assistantCapabilities()
      .then(data => { if (active) setCapabilities(data); })
      .catch(err => { if (active) setError(err.message || 'Could not load assistant'); });
    return () => { active = false; };
  }, []);

  useEffect(() => { endRef.current?.scrollIntoView({ behavior: 'smooth', block: 'end' }); }, [messages, busy]);

  async function ask(nextQuestion) {
    const q = nextQuestion.trim();
    if (q.length < 3 || q.length > 500 || pending.current) return;
    pending.current = true;
    setBusy(true);
    setError('');
    setQuestion('');
    setMessages(old => [...old, { id: `${Date.now()}-q`, from: 'user', text: q }]);
    try {
      const answer = await api.askAssistant(q);
      setMessages(old => [...old, { id: `${Date.now()}-a`, from: 'assistant', ...answer }]);
    } catch (err) {
      setError(err.message || 'Unable to answer. Please try again.');
    } finally {
      pending.current = false;
      setBusy(false);
      inputRef.current?.focus();
    }
  }

  const prompts = capabilities?.prompts || FALLBACK_PROMPTS;
  const enabledLLM = capabilities?.mode === 'llm_available';
  const canAsk = !busy && question.trim().length >= 3 && question.length <= 500;

  return <div className="p10-page">
    <header className="p10-heading">
      <div>
        <div className="eyebrow"><span className="eyebrow-dot"/> PHASE 10 / ACADEMIC ASSISTANT</div>
        <h1>Ask CampusFlow <span className="p10-title-star"><Sparkles size={25}/></span></h1>
        <p>Ask questions about student records and get answers from your academic data.</p>
      </div>
      <span className="p10-connection"><span className="p10-connection-dot"/> Connected to SQLite</span>
    </header>

    <div className="p10-layout">
      <aside className="p10-side">
        <section className="p10-side-block">
          <div className="p10-side-title"><Zap size={17}/> TRY A QUESTION</div>
          <div className="p10-prompts">
            {prompts.map((prompt, index) => {
              const Icon = SELECTED_ICONS[index % SELECTED_ICONS.length];
              return <button key={prompt} type="button" onClick={() => ask(prompt)} disabled={busy} className="p10-prompt">
                <Icon size={18}/><span>{prompt}</span><ChevronRight size={15} className="p10-chevron"/>
              </button>;
            })}
          </div>
        </section>
        <section className="p10-side-block p10-privacy">
          <div className="p10-side-title"><ShieldCheck size={17}/> YOUR DATA STAYS PROTECTED</div>
          <p>The assistant can only read approved academic summaries. It cannot edit records or run SQL entered in chat.</p>
          <div className="p10-privacy-line"><LockKeyhole size={15}/><span>Signed in as <b>{user.role === 'admin' ? 'Administrator' : 'Teacher'}</b></span></div>
          <div className="p10-privacy-line"><Server size={15}/><span>{enabledLLM ? 'Optional AI wording for aggregate facts' : 'Local questions, no API key required'}</span></div>
        </section>
      </aside>

      <section className="p10-chat" aria-label="Academic assistant conversation">
        <div className="p10-chat-topbar">
          <div className="p10-bot-avatar"><Sparkles size={21}/></div>
          <div className="p10-bot-identity"><strong>CampusFlow Assistant</strong><span><span className="p10-status-dot"/> {enabledLLM ? 'Local answers + optional AI wording' : 'Verified local academic answers'}</span></div>
          <button className="p10-clear" type="button" onClick={() => { setMessages([]); setError(''); }} disabled={!messages.length || busy} title="Clear conversation"><RotateCcw size={16}/> <span>New chat</span></button>
        </div>
        <div className="p10-chat-scroll" aria-live="polite" aria-relevant="additions">
          {messages.length === 0 && <div className="p10-welcome">
            <div className="p10-welcome-orb"><Sparkles size={32}/></div>
            <div className="p10-overline">YOUR ACADEMIC COPILOT</div>
            <h2>What would you like to know?</h2>
            <p>Explore student counts, attendance trends, marks, subjects, and semester performance. Every answer is based on your saved CampusFlow records.</p>
            <div className="p10-welcome-tiles">
              <button type="button" disabled={busy} onClick={() => ask('How many students are enrolled?')}><span><UsersRound size={18}/></span><b>Student overview</b><small>Enrollment at a glance</small></button>
              <button type="button" disabled={busy} onClick={() => ask('What is the overall average score?')}><span><TrendingUp size={18}/></span><b>Academic insights</b><small>Marks and performance</small></button>
            </div>
          </div>}
          {messages.map(message => <div key={message.id} className={`p10-message p10-message-${message.from}`}>
            {message.from === 'assistant' && <span className="p10-message-icon"><Sparkles size={17}/></span>}
            <div className="p10-message-inner">
              {message.from === 'assistant' && <div className="p10-message-name">CampusFlow Assistant <span>{message.mode === 'llm' ? 'AI enhanced' : 'Verified data'}</span></div>}
              <div className="p10-message-bubble">{message.from === 'user' ? message.text : message.answer}</div>
              {message.metrics?.length > 0 && <div className="p10-metrics">{message.metrics.map((metric, i) => <div className="p10-metric" key={i}><small>{metric.label}</small><strong>{metric.value}</strong></div>)}</div>}
              {message.rows?.length > 0 && <div className="p10-records">{message.rows.map((row, i) => <div className="p10-record" key={i}><span className="p10-record-num">{String(i+1).padStart(2,'0')}</span><span className="p10-record-name"><b>{row.label}</b><small>{row.detail}</small></span><strong>{row.value}</strong></div>)}</div>}
              {message.note && <div className="p10-answer-note"><CircleHelp size={14}/>{message.note}</div>}
            </div>
          </div>)}
          {busy && <div className="p10-message p10-message-assistant"><span className="p10-message-icon"><Sparkles size={17}/></span><div className="p10-typing"><i/><i/><i/><span>Checking academic records...</span></div></div>}
          {error && <div className="p10-error" role="alert"><AlertCircle size={18}/>{error}</div>}
          <div ref={endRef}/>
        </div>
        <form className="p10-compose" onSubmit={event => {event.preventDefault(); if(canAsk) ask(question);}}>
          <div className="p10-compose-control">
            <MessageCircle size={20} className="p10-compose-icon"/>
            <input ref={inputRef} aria-label="Ask an academic question" type="text" value={question} maxLength={500} onChange={event => setQuestion(event.target.value)} placeholder="Ask about marks, attendance, or semester performance..." disabled={busy}/>
            <button type="submit" disabled={!canAsk} aria-label="Send question"><SendHorizontal size={20}/></button>
          </div>
          <div className="p10-compose-foot"><span><ShieldCheck size={14}/> Read-only · Authenticated · Database-backed</span><span>{question.length}/500</span></div>
        </form>
      </section>
    </div>
  </div>;
}
