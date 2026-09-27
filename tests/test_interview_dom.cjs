const fs = require('fs');
const path = require('path');

const htmlPath = path.resolve(__dirname, '../frontend/interview.html');
const jsPath = path.resolve(__dirname, '../frontend/js/interview.js');

const html = fs.readFileSync(htmlPath, 'utf8');
const js = fs.readFileSync(jsPath, 'utf8');

// Parse all elements with id="..." from html
const idMatches = [...html.matchAll(/id=["']([^"']+)["']/g)].map(m => m[1]);
console.log('Found HTML IDs:', idMatches);

// Create Mock DOM
class MockElement {
  constructor(id, tagName = 'div') {
    this.id = id;
    this.tagName = tagName.toUpperCase();
    this.textContent = '';
    this.innerHTML = '';
    this.value = '';
    this.className = '';
    this.style = {};
    this.classList = {
      add: (cls) => { this.className += ' ' + cls; },
      remove: (cls) => { this.className = this.className.replace(cls, '').trim(); }
    };
    this.listeners = {};
    this.disabled = false;
  }
  addEventListener(event, cb) {
    if (!this.listeners[event]) this.listeners[event] = [];
    this.listeners[event].push(cb);
  }
  dispatchEvent(event) {
    const handlers = this.listeners[event.type] || [];
    for (const h of handlers) h(event);
  }
  focus() {}
}

const elements = {};
idMatches.forEach(id => {
  elements[id] = new MockElement(id);
});

// Setup mock window and document
const errors = [];
const logs = [];

global.window = {
  location: {
    search: '?id=d28c8624',
    href: 'http://127.0.0.1:8000/interview.html?id=d28c8624',
    origin: 'http://127.0.0.1:8000'
  }
};

const nativeFetch = global.fetch;
global.fetch = (url, options) => {
  const fullUrl = url.startsWith('/') ? 'http://127.0.0.1:8000' + url : url;
  return nativeFetch(fullUrl, options);
};

global.document = {
  readyState: 'complete',
  getElementById: (id) => elements[id] || null,
  addEventListener: (event, cb) => cb()
};

global.sessionStorage = {
  getItem: (key) => null,
  setItem: (key, val) => {}
};

global.localStorage = {
  getItem: (key) => null,
  setItem: (key, val) => {}
};

global.alert = (msg) => console.log('[MOCK ALERT]', msg);
global.confirm = (msg) => true;

// Intercept console errors
const origError = console.error;
console.error = (...args) => {
  errors.push(args.join(' '));
  origError('[CONSOLE.ERROR]', ...args);
};

async function runTest() {
  console.log('Evaluating interview.js in Mock DOM...');
  eval(js);

  // Wait for initial loadSessionState async fetch to complete
  await new Promise(r => setTimeout(r, 2000));

  console.log('\n--- VERIFYING INITIAL DOM STATE (QUESTION 1) ---');
  console.log('Candidate Info textContent:', elements['sessionCandidateInfo']?.textContent);
  console.log('Session Ref textContent:', elements['sessionShortId']?.textContent);
  console.log('Question Progress textContent:', elements['questionProgressText']?.textContent);
  console.log('Progress Percentage textContent:', elements['progressPercentageText']?.textContent);
  console.log('Question Badge textContent:', elements['questionBadge']?.textContent);
  console.log('Topic Badge textContent:', elements['topicBadge']?.textContent);
  console.log('Question Text textContent:', elements['questionText']?.textContent);

  if (!elements['questionText']?.textContent || elements['questionText'].textContent.includes('Loading assessment question')) {
    throw new Error('Question text is still stuck on loading!');
  }
  if (!elements['sessionCandidateInfo']?.textContent.includes('Jordan Lee')) {
    throw new Error('Candidate info was not rendered properly!');
  }
  if (!elements['questionProgressText']?.textContent.includes('Question 1')) {
    throw new Error('Progress text not updated!');
  }

  console.log('\n--- TESTING ANSWER SUBMISSION ---');
  elements['candidateAnswer'].value = 'Python decorators are functions that take another function as argument and return a wrapper function. Using @functools.wraps preserves function attributes like docstrings and names.';
  
  // Submit the form
  const submitEvent = { type: 'submit', preventDefault: () => {} };
  elements['answerForm'].dispatchEvent(submitEvent);

  // Wait for evaluation and next question
  await new Promise(r => setTimeout(r, 2500));

  console.log('\n--- VERIFYING NEXT QUESTION STATE (QUESTION 2) ---');
  console.log('Question Progress textContent:', elements['questionProgressText']?.textContent);
  console.log('Progress Percentage textContent:', elements['progressPercentageText']?.textContent);
  console.log('Question Badge textContent:', elements['questionBadge']?.textContent);
  console.log('Question Text textContent:', elements['questionText']?.textContent);

  if (!elements['questionProgressText']?.textContent.includes('Question 2')) {
    throw new Error('Did not advance to Question 2!');
  }

  console.log('\nTotal console errors captured:', errors.length);
  if (errors.length > 0) {
    throw new Error('Console errors were logged: ' + JSON.stringify(errors));
  }

  console.log('\nSUCCESS! All checks passed without any errors!');
}

runTest().catch(err => {
  console.error('TEST FAILED:', err);
  process.exit(1);
});
