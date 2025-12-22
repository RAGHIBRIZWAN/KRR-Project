import React from 'react';
import ReactDOM from 'react-dom/client';
import Landing from './Landing';
import AssessmentLogin from './AssessmentLogin';
import Assessment from './Assessment';
import Results from './Results';
import './styles.css';

const path = window.location.pathname.toLowerCase();
const isAssessmentLogin = path === '/assessment' || path === '/assessment/';
const isAssessmentQuestions = path.startsWith('/assessment/questions');
const isResults = path.includes('/results');

ReactDOM.createRoot(document.getElementById('root')).render(
  <React.StrictMode>
    {isAssessmentLogin ? <AssessmentLogin /> : isAssessmentQuestions ? <Assessment /> : isResults ? <Results /> : <Landing />}
  </React.StrictMode>
);
