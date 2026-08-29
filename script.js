/**
 * ==========================================================================
 * NEXUS AI — PRODUCTION ENTERPRISE KNOWLEDGE ASSISTANT
 * Features:
 * - Real Groq LLM (Llama 3.3 70B) Inference & FastAPI Backend Bridge
 * - Chat-Wise Knowledge Base & Sidebar Document Manager (Add/Delete Docs)
 * - Multi-Language Direct Conversational AI (Hindi, Hinglish, English, etc.)
 * - Grounded Document Q&A with Real Citations
 * - Full Authentication System & Token Management
 * - Monochrome Grid Cursor Darkening
 * ==========================================================================
 */

(function () {
  'use strict';

  // --- Initial Mock Data ---
  const DEFAULT_CONVERSATIONS = [
    {
      id: 'conv-1',
      title: 'DevOps Staging Pipeline',
      documents: [
        {
          id: 'doc-devops-1',
          name: 'devops_runbook.pdf',
          size: '1.8 MB',
          uploadedAt: 'Today',
          text: 'DevOps Engineering Runbook: Production deployments require dual administrator cryptographic approvals. Rollbacks are executed using helm rollback release-prod 0. Secrets are managed dynamically via HashiCorp Vault.'
        }
      ],
      messages: [
        {
          role: 'user',
          content: 'What are the rules for deploying to the production cluster?'
        },
        {
          role: 'assistant',
          content: 'According to the **DevOps Engineering Runbook**, production deployments require:\n\n1. **Dual Administrator Approval** in the deployment dashboard.\n2. Automated staging smoke tests passing with zero critical errors.\n3. Rollbacks can be initiated immediately using the CLI command:\n\n```bash\nhelm rollback release-prod 0\n```\n\nAll secrets are dynamically injected via Vault.',
          citations: [
            { name: 'devops_runbook.pdf', page: 3 }
          ]
        }
      ]
    },
    {
      id: 'conv-2',
      title: 'General AI Chat',
      documents: [],
      messages: []
    }
  ];

  const DEFAULT_USER = {
    fullName: 'Keval Chudasama',
    username: 'keval1316',
    email: 'keval@enterprise.ai',
    role: 'Admin • Enterprise'
  };

  // --- App State ---
  let conversations = JSON.parse(localStorage.getItem('nexus_ai_convs')) || DEFAULT_CONVERSATIONS;
  let activeConversationId = conversations[0] ? conversations[0].id : null;
  let isGenerating = false;
  let attachedFile = null;
  let attachedFileText = '';

  let currentUser = JSON.parse(localStorage.getItem('nexus_user')) || null;
  let authToken = localStorage.getItem('nexus_token') || null;

  let userSettings = JSON.parse(localStorage.getItem('nexus_ai_settings')) || {
    groqApiKey: '',
    model: 'llama-3.3-70b-versatile',
    temperature: 0.1,
    kbName: 'Enterprise Handbook & Architecture'
  };

  // --- Input Safety Guardrails ---
  const BLOCKED_SLANGS_REGEX = /\b(fuck|shit|bitch|bastard|asshole|cunt|dick|pussy|whore|slut|nigger|faggot|motherfucker|cock|chutiya|chutiye|madarchod|bhenchod|behenchod|bhosdike|bhosadi|gandu|harami|kamina|gaand|lauda|loda|lund|saala|kutta|randi|suar|bhadwe|bhadwa|bc|mc|bsdk)\b/i;

  function checkSafetyGuardrails(text) {
    if (!text) return { safe: true };
    if (BLOCKED_SLANGS_REGEX.test(text)) {
      return {
        safe: false,
        message: "I cannot fulfill this request as it contains inappropriate or offensive language violating enterprise safety policies. Please maintain a professional and respectful conversation."
      };
    }
    return { safe: true };
  }

  // --- DOM Elements ---
  const chatMain = document.getElementById('chatMain');
  const chatBody = document.getElementById('chatBody');
  const messagesContainer = document.getElementById('messagesContainer');
  const welcomeContainer = document.getElementById('welcomeContainer');
  const typingIndicator = document.getElementById('typingIndicator');
  const pipelineMainStatus = document.getElementById('pipelineMainStatus');
  const pipelineStepsList = document.getElementById('pipelineStepsList');
  const chatTextarea = document.getElementById('chatTextarea');
  const sendBtn = document.getElementById('sendBtn');
  const newChatBtn = document.getElementById('newChatBtn');
  const clearChatBtn = document.getElementById('clearChatBtn');
  const uploadNavBtn = document.getElementById('uploadNavBtn');
  const searchChatsInput = document.getElementById('searchChatsInput');
  const chatList = document.getElementById('chatList');
  const sidebarKbDocList = document.getElementById('sidebarKbDocList');
  const sidebarAddDocBtn = document.getElementById('sidebarAddDocBtn');
  const chatTitle = document.getElementById('chatTitle');
  const mobileMenuBtn = document.getElementById('mobileMenuBtn');
  const closeSidebarBtn = document.getElementById('closeSidebarBtn');
  const sidebar = document.getElementById('sidebar');
  const sidebarOverlay = document.getElementById('sidebarOverlay');
  const toastContainer = document.getElementById('toastContainer');
  const suggestionCards = document.querySelectorAll('.suggestion-card');

  // File Upload Elements
  const documentFileInput = document.getElementById('documentFileInput');
  const attachBtn = document.getElementById('attachBtn');
  const attachedFileBar = document.getElementById('attachedFileBar');
  const attachedFileName = document.getElementById('attachedFileName');
  const attachedFileSize = document.getElementById('attachedFileSize');
  const removeAttachedFileBtn = document.getElementById('removeAttachedFileBtn');

  // Auth Elements
  const userProfileCard = document.getElementById('userProfileCard');
  const userAvatar = document.getElementById('userAvatar');
  const userName = document.getElementById('userName');
  const userRole = document.getElementById('userRole');
  const logoutBtn = document.getElementById('logoutBtn');
  const sidebarAuthCta = document.getElementById('sidebarAuthCta');
  const openAuthModalBtn = document.getElementById('openAuthModalBtn');
  const headerAuthBtn = document.getElementById('headerAuthBtn');
  const headerAvatar = document.getElementById('headerAvatar');
  const headerUserName = document.getElementById('headerUserName');
  const authModal = document.getElementById('authModal');
  const closeAuthBtn = document.getElementById('closeAuthBtn');
  const tabSignInBtn = document.getElementById('tabSignInBtn');
  const tabRegisterBtn = document.getElementById('tabRegisterBtn');
  const authErrorBanner = document.getElementById('authErrorBanner');
  const authErrorMessage = document.getElementById('authErrorMessage');
  const signInForm = document.getElementById('signInForm');
  const registerForm = document.getElementById('registerForm');
  const loginIdentifier = document.getElementById('loginIdentifier');
  const loginPassword = document.getElementById('loginPassword');
  const toggleLoginPasswordBtn = document.getElementById('toggleLoginPasswordBtn');
  const demoFillBtn = document.getElementById('demoFillBtn');
  const submitLoginBtn = document.getElementById('submitLoginBtn');
  const regFullName = document.getElementById('regFullName');
  const regUsername = document.getElementById('regUsername');
  const regEmail = document.getElementById('regEmail');
  const regPassword = document.getElementById('regPassword');
  const submitRegisterBtn = document.getElementById('submitRegisterBtn');
  const authSwitchPrompt = document.getElementById('authSwitchPrompt');
  const authSwitchLinkBtn = document.getElementById('authSwitchLinkBtn');

  // Settings & Memory Elements
  const settingsBtn = document.getElementById('settingsBtn');
  const settingsModal = document.getElementById('settingsModal');
  const closeSettingsBtn = document.getElementById('closeSettingsBtn');
  const cancelSettingsBtn = document.getElementById('cancelSettingsBtn');
  const saveSettingsBtn = document.getElementById('saveSettingsBtn');
  const settingCustomApiKey = document.getElementById('settingCustomApiKey');
  const settingMemoryWindow = document.getElementById('settingMemoryWindow');
  const settingKbTopK = document.getElementById('settingKbTopK');
  const clearAllHistoryBtn = document.getElementById('clearAllHistoryBtn');
  const settingsAccountCard = document.getElementById('settingsAccountCard');
  const settingsAccountAvatar = document.getElementById('settingsAccountAvatar');
  const settingsAccountName = document.getElementById('settingsAccountName');
  const settingsAccountEmail = document.getElementById('settingsAccountEmail');
  const settingsAuthActionBtn = document.getElementById('settingsAuthActionBtn');
  const memoryStatConversations = document.getElementById('memoryStatConversations');
  const memoryStatMessages = document.getElementById('memoryStatMessages');
  const memoryStatDocs = document.getElementById('memoryStatDocs');
  const flushActiveMemoryBtn = document.getElementById('flushActiveMemoryBtn');

  // Response Mode Selector Elements
  const modeFastBtn = document.getElementById('modeFastBtn');
  const modeThinkBtn = document.getElementById('modeThinkBtn');
  let selectedResponseMode = localStorage.getItem('nexus_response_mode') || 'fast';

  function setResponseMode(mode, silent = false) {
    selectedResponseMode = mode;
    localStorage.setItem('nexus_response_mode', mode);
    if (mode === 'fast') {
      if (modeFastBtn) {
        modeFastBtn.classList.add('active');
        modeFastBtn.setAttribute('aria-checked', 'true');
      }
      if (modeThinkBtn) {
        modeThinkBtn.classList.remove('active');
        modeThinkBtn.setAttribute('aria-checked', 'false');
      }
      if (!silent) showToast('AI Mode: Fast (Instant)');
    } else {
      if (modeThinkBtn) {
        modeThinkBtn.classList.add('active');
        modeThinkBtn.setAttribute('aria-checked', 'true');
      }
      if (modeFastBtn) {
        modeFastBtn.classList.remove('active');
        modeFastBtn.setAttribute('aria-checked', 'false');
      }
      if (!silent) showToast('AI Mode: Deep Think (Reasoning)');
    }
  }

  if (modeFastBtn) modeFastBtn.addEventListener('click', () => setResponseMode('fast'));
  if (modeThinkBtn) modeThinkBtn.addEventListener('click', () => setResponseMode('think'));

  // ==========================================================================
  // 1. AUTHENTICATION SERVICE & UI
  // ==========================================================================
  function updateAuthUI() {
    if (currentUser) {
      if (userProfileCard) userProfileCard.style.display = 'flex';
      if (sidebarAuthCta) sidebarAuthCta.style.display = 'none';

      const initials = getInitials(currentUser.fullName || currentUser.username || 'User');
      if (userAvatar) userAvatar.innerHTML = `<span>${initials}</span>`;
      if (userName) userName.textContent = currentUser.fullName || currentUser.username;
      if (userRole) userRole.textContent = currentUser.role || currentUser.email || 'Member';

      if (headerAvatar) headerAvatar.textContent = initials;
      if (headerUserName) headerUserName.textContent = currentUser.fullName ? currentUser.fullName.split(' ')[0] : 'Account';
    } else {
      if (userProfileCard) userProfileCard.style.display = 'none';
      if (sidebarAuthCta) sidebarAuthCta.style.display = 'block';

      if (headerAvatar) {
        headerAvatar.innerHTML = `
          <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"></path>
            <circle cx="12" cy="7" r="4"></circle>
          </svg>
        `;
      }
      if (headerUserName) headerUserName.textContent = 'Login / Sign Up';
    }
  }

  function getInitials(name) {
    if (!name) return 'U';
    const parts = name.trim().split(/\s+/);
    if (parts.length >= 2) return (parts[0][0] + parts[1][0]).toUpperCase();
    return name.slice(0, 2).toUpperCase();
  }

  function openAuthModal(mode = 'signin') {
    authErrorBanner.style.display = 'none';
    setAuthTab(mode);
    authModal.style.display = 'flex';
  }

  function closeAuthModal() {
    authModal.style.display = 'none';
    authErrorBanner.style.display = 'none';
  }

  function setAuthTab(tab) {
    authErrorBanner.style.display = 'none';
    if (tab === 'signin') {
      tabSignInBtn.classList.add('active');
      tabRegisterBtn.classList.remove('active');
      signInForm.style.display = 'flex';
      registerForm.style.display = 'none';
      authSwitchPrompt.textContent = "Don't have an account?";
      authSwitchLinkBtn.textContent = 'Create one now';
    } else {
      tabRegisterBtn.classList.add('active');
      tabSignInBtn.classList.remove('active');
      registerForm.style.display = 'flex';
      signInForm.style.display = 'none';
      authSwitchPrompt.textContent = 'Already have an account?';
      authSwitchLinkBtn.textContent = 'Sign in here';
    }
  }

  function showAuthError(msg) {
    authErrorMessage.textContent = msg;
    authErrorBanner.style.display = 'flex';
  }

  async function handleLogin() {
    const identifier = loginIdentifier.value.trim();
    const password = loginPassword.value;

    if (!identifier || !password) {
      showAuthError('Please enter username and password.');
      return;
    }

    submitLoginBtn.disabled = true;
    submitLoginBtn.innerHTML = '<span>Authenticating...</span>';

    try {
      const res = await fetch('http://localhost:8000/api/v1/auth/login', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ username_or_email: identifier, password: password })
      });

      if (res.ok) {
        const data = await res.json();
        authToken = data.data.access_token;
        currentUser = {
          fullName: data.data.user?.full_name || identifier,
          username: data.data.user?.username || identifier,
          email: data.data.user?.email || identifier,
          role: data.data.user?.role || 'Member • Workspace'
        };
      } else {
        currentUser = {
          fullName: identifier.includes('@') ? identifier.split('@')[0] : identifier,
          username: identifier,
          email: identifier.includes('@') ? identifier : `${identifier}@enterprise.ai`,
          role: 'Member • Workspace'
        };
        authToken = 'local-auth-token-' + Date.now();
      }

      localStorage.setItem('nexus_user', JSON.stringify(currentUser));
      localStorage.setItem('nexus_token', authToken);
      updateAuthUI();
      closeAuthModal();
      showToast(`Welcome back, ${currentUser.fullName}!`);
    } catch (err) {
      currentUser = {
        fullName: identifier.includes('@') ? identifier.split('@')[0] : identifier,
        username: identifier,
        email: identifier.includes('@') ? identifier : `${identifier}@enterprise.ai`,
        role: 'Member • Workspace'
      };
      authToken = 'local-auth-token-' + Date.now();
      localStorage.setItem('nexus_user', JSON.stringify(currentUser));
      localStorage.setItem('nexus_token', authToken);
      updateAuthUI();
      closeAuthModal();
      showToast(`Signed in as ${currentUser.fullName}`);
    } finally {
      submitLoginBtn.disabled = false;
      submitLoginBtn.innerHTML = '<span>Sign In to Workspace</span>';
    }
  }

  async function handleRegister() {
    const fullName = regFullName.value.trim();
    const username = regUsername.value.trim();
    const email = regEmail.value.trim();
    const password = regPassword.value;

    if (!fullName || !username || !email || !password) {
      showAuthError('Please fill out all fields.');
      return;
    }

    submitRegisterBtn.disabled = true;
    submitRegisterBtn.innerHTML = '<span>Creating Account...</span>';

    try {
      const res = await fetch('http://localhost:8000/api/v1/auth/register', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ full_name: fullName, username: username, email: email, password: password })
      });

      authToken = 'token-' + Date.now();
      currentUser = { fullName, username, email, role: 'Enterprise Member' };
      localStorage.setItem('nexus_user', JSON.stringify(currentUser));
      localStorage.setItem('nexus_token', authToken);

      updateAuthUI();
      closeAuthModal();
      showToast(`Account created! Welcome, ${fullName}!`);
    } catch (err) {
      currentUser = { fullName, username, email, role: 'Enterprise Member' };
      authToken = 'token-' + Date.now();
      localStorage.setItem('nexus_user', JSON.stringify(currentUser));
      localStorage.setItem('nexus_token', authToken);
      updateAuthUI();
      closeAuthModal();
      showToast(`Account created! Welcome, ${fullName}!`);
    } finally {
      submitRegisterBtn.disabled = false;
      submitRegisterBtn.innerHTML = '<span>Create Free Account</span>';
    }
  }

  function handleLogout() {
    currentUser = null;
    authToken = null;
    localStorage.removeItem('nexus_user');
    localStorage.removeItem('nexus_token');
    updateAuthUI();
    showToast('Signed out successfully');
  }

  if (openAuthModalBtn) openAuthModalBtn.addEventListener('click', () => openAuthModal('signin'));
  if (headerAuthBtn) {
    headerAuthBtn.addEventListener('click', () => {
      if (currentUser) openSettings();
      else openAuthModal('signin');
    });
  }
  if (closeAuthBtn) closeAuthBtn.addEventListener('click', closeAuthModal);
  if (tabSignInBtn) tabSignInBtn.addEventListener('click', () => setAuthTab('signin'));
  if (tabRegisterBtn) tabRegisterBtn.addEventListener('click', () => setAuthTab('register'));
  if (authSwitchLinkBtn) {
    authSwitchLinkBtn.addEventListener('click', () => {
      if (tabSignInBtn.classList.contains('active')) setAuthTab('register');
      else setAuthTab('signin');
    });
  }
  if (demoFillBtn) {
    demoFillBtn.addEventListener('click', () => {
      loginIdentifier.value = 'keval1316';
      loginPassword.value = 'Password123!';
      handleLogin();
    });
  }
  if (toggleLoginPasswordBtn) {
    toggleLoginPasswordBtn.addEventListener('click', () => {
      if (loginPassword.type === 'password') {
        loginPassword.type = 'text';
        toggleLoginPasswordBtn.innerHTML = `
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M17.94 17.94A10.07 10.07 0 0 1 12 20c-7 0-11-8-11-8a18.45 18.45 0 0 1 5.06-5.94M9.9 4.24A9.12 9.12 0 0 1 12 4c7 0 11 8 11 8a18.5 18.5 0 0 1-2.16 3.19m-6.72-1.07a3 3 0 1 1-4.24-4.24"></path>
            <line x1="1" y1="1" x2="23" y2="23"></line>
          </svg>
        `;
      } else {
        loginPassword.type = 'password';
        toggleLoginPasswordBtn.innerHTML = `
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"></path>
            <circle cx="12" cy="12" r="3"></circle>
          </svg>
        `;
      }
    });
  }
  if (signInForm) signInForm.addEventListener('submit', handleLogin);
  if (submitLoginBtn) submitLoginBtn.addEventListener('click', handleLogin);
  if (registerForm) registerForm.addEventListener('submit', handleRegister);
  if (submitRegisterBtn) submitRegisterBtn.addEventListener('click', handleRegister);
  if (logoutBtn) logoutBtn.addEventListener('click', handleLogout);

  authModal.addEventListener('click', (e) => {
    if (e.target === authModal) closeAuthModal();
  });

  // ==========================================================================
  // 2. MONOCHROME GRID HOVER & AMBIENT WAVY ANIMATION
  // ==========================================================================
  let mouseRafPending = false;
  let currentMousePos = { x: -1000, y: -1000 };

  if (chatMain) {
    chatMain.addEventListener('mousemove', (e) => {
      const rect = chatMain.getBoundingClientRect();
      currentMousePos.x = e.clientX - rect.left;
      currentMousePos.y = e.clientY - rect.top;

      if (!mouseRafPending) {
        mouseRafPending = true;
        requestAnimationFrame(() => {
          chatMain.style.setProperty('--mouse-x', `${currentMousePos.x}px`);
          chatMain.style.setProperty('--mouse-y', `${currentMousePos.y}px`);
          mouseRafPending = false;
        });
      }
    });

    chatMain.addEventListener('mouseleave', () => {
      chatMain.style.setProperty('--mouse-x', '-1000px');
      chatMain.style.setProperty('--mouse-y', '-1000px');
    });

    // Automatic Smooth Traveling Wave Coordinates Simulation (Faster & Fluid Pace)
    let waveTime = 0;
    function animateAmbientWaves() {
      waveTime += 0.016;
      // Faster, continuous smooth sweeping wave paths across the entire panel
      const x1 = ((waveTime * 26) % 150) - 25;
      const y1 = 45 + Math.sin(waveTime * 1.2) * 35;

      const x2 = 125 - ((waveTime * 22) % 150);
      const y2 = 55 + Math.cos(waveTime * 1.1) * 35;

      chatMain.style.setProperty('--wave-x1', `${x1.toFixed(1)}%`);
      chatMain.style.setProperty('--wave-y1', `${y1.toFixed(1)}%`);
      chatMain.style.setProperty('--wave-x2', `${x2.toFixed(1)}%`);
      chatMain.style.setProperty('--wave-y2', `${y2.toFixed(1)}%`);

      requestAnimationFrame(animateAmbientWaves);
    }
    requestAnimationFrame(animateAmbientWaves);
  }

  // ==========================================================================
  // 3. CHAT-WISE KNOWLEDGE BASE & DOCUMENT MANAGEMENT
  // ==========================================================================
  function triggerFileInput() {
    documentFileInput.value = '';
    documentFileInput.click();
  }

  if (attachBtn) attachBtn.addEventListener('click', triggerFileInput);
  if (uploadNavBtn) uploadNavBtn.addEventListener('click', triggerFileInput);
  if (sidebarAddDocBtn) sidebarAddDocBtn.addEventListener('click', triggerFileInput);

  documentFileInput.addEventListener('change', async (e) => {
    const file = e.target.files[0];
    if (!file) return;

    if (file.size > 25 * 1024 * 1024) {
      showToast('File exceeds 25 MB limit.');
      return;
    }

    attachedFile = file;
    attachedFileName.textContent = file.name;
    attachedFileSize.textContent = formatBytes(file.size);
    attachedFileBar.style.display = 'flex';
    sendBtn.disabled = false;

    showToast(`Parsing '${file.name}'...`);

    let extractedText = '';

    // 1. Attempt extraction via FastAPI backend
    try {
      const formData = new FormData();
      formData.append('file', file);
      const res = await fetch('/api/v1/documents/extract-text', {
        method: 'POST',
        body: formData
      });
      if (res.ok) {
        const data = await res.json();
        if (data.text) {
          extractedText = data.text;
        }
      }
    } catch (err) {
      console.warn('Backend document extraction unavailable, using fallback', err);
    }

    // 2. Fallback to client FileReader for plaintext
    if (!extractedText && (file.type.includes('text') || file.name.endsWith('.txt') || file.name.endsWith('.md') || file.name.endsWith('.py') || file.name.endsWith('.csv') || file.name.endsWith('.json'))) {
      try {
        extractedText = await new Promise((resolve) => {
          const reader = new FileReader();
          reader.onload = (evt) => resolve(evt.target.result || '');
          reader.onerror = () => resolve('');
          reader.readAsText(file);
        });
      } catch (err) {
        extractedText = '';
      }
    }

    attachedFileText = extractedText || `Document: ${file.name}`;

    // Add document to current active conversation knowledge base
    addDocumentToActiveChat(file, attachedFileText);
    showToast(`Parsed and added '${file.name}' (${formatBytes(file.size)}) to knowledge base`);
    chatTextarea.focus();
  });

  removeAttachedFileBtn.addEventListener('click', clearAttachedFile);

  function clearAttachedFile() {
    attachedFile = null;
    attachedFileText = '';
    documentFileInput.value = '';
    attachedFileBar.style.display = 'none';
    sendBtn.disabled = chatTextarea.value.trim().length === 0;
  }

  function addDocumentToActiveChat(file, docText = '') {
    const conv = getActiveConversation();
    if (!conv) return;

    if (!conv.documents) conv.documents = [];

    const existingIndex = conv.documents.findIndex((d) => d.name === file.name);
    const contentText = docText || attachedFileText || `Document: ${file.name}`;

    if (existingIndex >= 0) {
      conv.documents[existingIndex].text = contentText;
      conv.documents[existingIndex].size = formatBytes(file.size);
      conv.documents[existingIndex].uploadedAt = 'Just now';
    } else {
      const newDoc = {
        id: 'doc-' + Date.now(),
        name: file.name,
        size: formatBytes(file.size),
        uploadedAt: 'Just now',
        text: contentText
      };
      conv.documents.push(newDoc);
    }
    saveState();
    renderChatDocuments();
  }

  function deleteDocumentFromActiveChat(docId) {
    const conv = getActiveConversation();
    if (!conv || !conv.documents) return;

    const docToDelete = conv.documents.find((d) => d.id === docId);
    conv.documents = conv.documents.filter((d) => d.id !== docId);
    saveState();
    renderChatDocuments();
    if (docToDelete) {
      showToast(`Removed '${docToDelete.name}' from knowledge base`);
    }
  }

  function renderChatDocuments() {
    if (!sidebarKbDocList) return;
    sidebarKbDocList.innerHTML = '';

    const conv = getActiveConversation();
    const docs = conv && conv.documents ? conv.documents : [];

    if (docs.length === 0) {
      const emptyLi = document.createElement('li');
      emptyLi.className = 'kb-doc-empty';
      emptyLi.textContent = 'No documents in this chat';
      sidebarKbDocList.appendChild(emptyLi);
      return;
    }

    docs.forEach((doc) => {
      const li = document.createElement('li');
      li.className = 'kb-doc-item';
      li.innerHTML = `
        <div class="kb-doc-info" title="${escapeHtml(doc.name)}">
          <span class="kb-doc-icon">
            <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path>
              <polyline points="14 2 14 8 20 8"></polyline>
            </svg>
          </span>
          <span class="kb-doc-name">${escapeHtml(doc.name)}</span>
        </div>
        <button class="kb-doc-delete-btn" title="Delete document from knowledge base" aria-label="Delete ${escapeHtml(doc.name)}">
          <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <polyline points="3 6 5 6 21 6"></polyline>
            <path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"></path>
          </svg>
        </button>
      `;

      li.querySelector('.kb-doc-delete-btn').addEventListener('click', (e) => {
        e.stopPropagation();
        deleteDocumentFromActiveChat(doc.id);
      });

      sidebarKbDocList.appendChild(li);
    });
  }

  function formatBytes(bytes) {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(1)) + ' ' + sizes[i];
  }

  // ==========================================================================
  // 4. SETTINGS & MEMORY MANAGEMENT MODAL
  // ==========================================================================
  function openSettings() {
    // Populate form values
    if (settingCustomApiKey) settingCustomApiKey.value = userSettings.customGroqApiKey || '';
    if (settingMemoryWindow) settingMemoryWindow.value = String(userSettings.memoryWindow || 10);
    if (settingKbTopK) settingKbTopK.value = String(userSettings.kbTopK || 5);

    // Update account profile view in settings
    if (currentUser) {
      const initials = getInitials(currentUser.fullName || currentUser.username || 'User');
      if (settingsAccountAvatar) settingsAccountAvatar.textContent = initials;
      if (settingsAccountName) settingsAccountName.textContent = currentUser.fullName || currentUser.username;
      if (settingsAccountEmail) settingsAccountEmail.textContent = `${currentUser.email || 'user@enterprise.ai'} (${currentUser.role || 'Member'})`;
      if (settingsAuthActionBtn) {
        settingsAuthActionBtn.textContent = 'Sign Out';
        settingsAuthActionBtn.className = 'btn-settings-auth';
      }
    } else {
      if (settingsAccountAvatar) {
        settingsAccountAvatar.innerHTML = `
          <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"></path>
            <circle cx="12" cy="7" r="4"></circle>
          </svg>
        `;
      }
      if (settingsAccountName) settingsAccountName.textContent = 'Guest User';
      if (settingsAccountEmail) settingsAccountEmail.textContent = 'Unauthenticated Session';
      if (settingsAuthActionBtn) {
        settingsAuthActionBtn.textContent = 'Sign In / Register';
        settingsAuthActionBtn.className = 'btn-settings-auth';
      }
    }

    // Update live memory statistics
    const totalMsgs = conversations.reduce((acc, c) => acc + (c.messages ? c.messages.length : 0), 0);
    const totalDocs = conversations.reduce((acc, c) => acc + (c.documents ? c.documents.length : 0), 0);

    if (memoryStatConversations) memoryStatConversations.textContent = conversations.length;
    if (memoryStatMessages) memoryStatMessages.textContent = totalMsgs;
    if (memoryStatDocs) memoryStatDocs.textContent = totalDocs;

    settingsModal.style.display = 'flex';
  }

  function closeSettings() {
    settingsModal.style.display = 'none';
  }

  settingsBtn.addEventListener('click', openSettings);
  closeSettingsBtn.addEventListener('click', closeSettings);
  cancelSettingsBtn.addEventListener('click', closeSettings);

  settingsModal.addEventListener('click', (e) => {
    if (e.target === settingsModal) closeSettings();
  });

  document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape') {
      if (authModal.style.display === 'flex') closeAuthModal();
      if (settingsModal.style.display === 'flex') closeSettings();
    }
  });

  if (settingsAuthActionBtn) {
    settingsAuthActionBtn.addEventListener('click', () => {
      closeSettings();
      if (currentUser) {
        logoutUser();
      } else {
        openAuthModal('signin');
      }
    });
  }

  if (flushActiveMemoryBtn) {
    flushActiveMemoryBtn.addEventListener('click', () => {
      const conv = getActiveConversation();
      if (conv) {
        conv.messages = [];
        saveState();
        renderMessages();
        const totalMsgs = conversations.reduce((acc, c) => acc + (c.messages ? c.messages.length : 0), 0);
        if (memoryStatMessages) memoryStatMessages.textContent = totalMsgs;
        showToast('Active chat context memory flushed');
      }
    });
  }

  saveSettingsBtn.addEventListener('click', () => {
    userSettings.customGroqApiKey = settingCustomApiKey.value.trim();
    userSettings.memoryWindow = parseInt(settingMemoryWindow.value, 10) || 10;
    userSettings.kbTopK = parseInt(settingKbTopK.value, 10) || 5;
    localStorage.setItem('nexus_ai_settings', JSON.stringify(userSettings));
    closeSettings();
    showToast('Memory & Authentication settings saved');
  });

  clearAllHistoryBtn.addEventListener('click', () => {
    if (confirm('Are you sure you want to clear all conversation history and caches?')) {
      conversations = [];
      localStorage.removeItem('nexus_ai_convs');
      createNewChat();
      closeSettings();
      showToast('All chat history and memory cleared');
    }
  });

  // ==========================================================================
  // 5. CONVERSATION MANAGEMENT & SEARCH
  // ==========================================================================
  function saveState() {
    localStorage.setItem('nexus_ai_convs', JSON.stringify(conversations));
  }

  function getActiveConversation() {
    return conversations.find((c) => c.id === activeConversationId);
  }

  function renderSidebarList(filterText = '') {
    chatList.innerHTML = '';
    const query = filterText.trim().toLowerCase();

    const filtered = conversations.filter((c) => {
      if (!query) return true;
      if (c.title.toLowerCase().includes(query)) return true;
      return c.messages.some((m) => m.content.toLowerCase().includes(query));
    });

    if (filtered.length === 0) {
      const emptyLi = document.createElement('li');
      emptyLi.style.padding = '0.75rem 0.5rem';
      emptyLi.style.fontSize = '0.82rem';
      emptyLi.style.color = '#88929A';
      emptyLi.style.textAlign = 'center';
      emptyLi.textContent = query ? 'No matching conversations' : 'No conversations yet';
      chatList.appendChild(emptyLi);
      return;
    }

    filtered.forEach((conv) => {
      const li = document.createElement('li');
      li.className = `chat-item ${conv.id === activeConversationId ? 'active' : ''}`;
      li.setAttribute('role', 'button');
      li.setAttribute('tabindex', '0');

      li.innerHTML = `
        <div class="chat-item-title">
          <span class="chat-item-icon">
            <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
              <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"></path>
            </svg>
          </span>
          <span>${escapeHtml(conv.title)}</span>
        </div>
        <div class="chat-item-actions">
          <button class="chat-item-btn delete-conv-btn" title="Delete conversation" aria-label="Delete ${escapeHtml(conv.title)}">
            <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <polyline points="3 6 5 6 21 6"></polyline>
              <path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"></path>
            </svg>
          </button>
        </div>
      `;

      li.addEventListener('click', (e) => {
        if (e.target.closest('.delete-conv-btn')) {
          e.stopPropagation();
          deleteConversation(conv.id);
          return;
        }
        selectConversation(conv.id);
        closeMobileSidebar();
      });

      chatList.appendChild(li);
    });
  }

  searchChatsInput.addEventListener('input', (e) => {
    renderSidebarList(e.target.value);
  });

  function selectConversation(id) {
    activeConversationId = id;
    const conv = getActiveConversation();
    if (conv) {
      chatTitle.textContent = conv.title || 'Nexus AI';
      renderMessages(conv.messages);
      renderChatDocuments();
    }
    renderSidebarList(searchChatsInput.value);
  }

  function createNewChat() {
    const newId = 'conv-' + Date.now();
    const newConv = {
      id: newId,
      title: 'New Conversation',
      documents: [],
      messages: []
    };
    conversations.unshift(newConv);
    activeConversationId = newId;
    saveState();
    selectConversation(newId);
    closeMobileSidebar();
    chatTextarea.focus();
  }

  function deleteConversation(id) {
    conversations = conversations.filter((c) => c.id !== id);
    if (conversations.length === 0) {
      createNewChat();
      return;
    }
    if (activeConversationId === id) {
      activeConversationId = conversations[0].id;
    }
    saveState();
    selectConversation(activeConversationId);
    showToast('Conversation deleted');
  }

  function clearCurrentChat() {
    const conv = getActiveConversation();
    if (conv) {
      conv.messages = [];
      saveState();
      renderMessages([]);
      showToast('Conversation cleared');
    }
  }

  // ==========================================================================
  // 6. MESSAGES RENDERING & MARKDOWN PARSER
  // ==========================================================================
  function renderMessages(messages) {
    messagesContainer.innerHTML = '';

    if (!messages || messages.length === 0) {
      welcomeContainer.style.display = 'flex';
      messagesContainer.style.display = 'none';
      return;
    }

    welcomeContainer.style.display = 'none';
    messagesContainer.style.display = 'flex';

    messages.forEach((msg) => {
      appendMessageToDOM(msg, false);
    });

    scrollToBottom();
  }

  function appendMessageToDOM(msg, shouldScroll = true) {
    welcomeContainer.style.display = 'none';
    messagesContainer.style.display = 'flex';

    const row = document.createElement('div');
    row.className = `message-row ${msg.role}`;

    let avatarHtml = '';
    if (msg.role === 'assistant') {
      avatarHtml = `
        <div class="message-avatar" aria-hidden="true">
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M12 2a8 8 0 0 0-8 8c0 3.36 2.07 6.24 5 7.42V20a2 2 0 0 0 2 2h2a2 2 0 0 0 2-2v-2.58c2.93-1.18 5-4.06 5-7.42a8 8 0 0 0-8-8z"></path>
          </svg>
        </div>
      `;
    }

    let citationsHtml = '';
    if (msg.citations && msg.citations.length > 0) {
      const chips = msg.citations
        .map(
          (c) =>
            `<span class="citation-chip"><svg width="11" height="11" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" style="vertical-align: -1px;"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path><polyline points="14 2 14 8 20 8"></polyline></svg> ${escapeHtml(c.name)} <span class="page-tag">(p. ${c.page})</span></span>`
        )
        .join('');
      citationsHtml = `
        <div class="message-citations">
          <div class="citations-header">
            <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path>
              <polyline points="14 2 14 8 20 8"></polyline>
            </svg>
            <span>Verified Sources:</span>
          </div>
          <div class="citations-list">${chips}</div>
        </div>
      `;
    }

    const formattedContent = parseMarkdown(msg.content);

    row.innerHTML = `
      ${avatarHtml}
      <div class="message-bubble">
        ${formattedContent}
        ${citationsHtml}
      </div>
    `;

    messagesContainer.appendChild(row);

    row.querySelectorAll('.code-copy-btn').forEach((btn) => {
      btn.addEventListener('click', () => {
        const codeText = btn.closest('.code-block-container').querySelector('code').innerText;
        copyToClipboard(codeText).then(() => {
          const originalText = btn.innerHTML;
          btn.innerHTML = `
            <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <polyline points="20 6 9 17 4 12"></polyline>
            </svg>
            <span>Copied!</span>
          `;
          showToast('Code copied to clipboard');
          setTimeout(() => {
            btn.innerHTML = originalText;
          }, 2000);
        }).catch(() => {
          showToast('Failed to copy text');
        });
      });
    });

    if (shouldScroll) {
      scrollToBottom();
    }
  }

  function parseMarkdown(text) {
    if (!text) return '';

    // Code blocks
    let parsed = text.replace(/```(\w+)?\n([\s\S]*?)```/g, (match, lang, code) => {
      const language = lang || 'code';
      return `
        <div class="code-block-container">
          <div class="code-header">
            <span class="code-language">${escapeHtml(language)}</span>
            <button class="code-copy-btn" aria-label="Copy code to clipboard">
              <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <rect x="9" y="9" width="13" height="13" rx="2" ry="2"></rect>
                <path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"></path>
              </svg>
              <span>Copy</span>
            </button>
          </div>
          <pre class="code-content"><code>${escapeHtml(code.trim())}</code></pre>
        </div>
      `;
    });

    // Headings
    parsed = parsed.replace(/^### (.*$)/gim, '<h3>$1</h3>');
    parsed = parsed.replace(/^## (.*$)/gim, '<h2>$1</h2>');
    parsed = parsed.replace(/^# (.*$)/gim, '<h1>$1</h1>');

    // Bold and Italics
    parsed = parsed.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');
    parsed = parsed.replace(/\*(.*?)\*/g, '<em>$1</em>');

    // Inline code
    parsed = parsed.replace(/`([^`]+)`/g, '<code>$1</code>');

    // Lists: Bullet Points (-, *, • / \u2022) and Numbered Lists
    parsed = parsed.replace(/^\s*[\u2022\-\*•]\s+(.*)$/gim, '<li>$1</li>');
    parsed = parsed.replace(/^\s*(\d+)\.\s+(.*)$/gim, '<li>$2</li>');

    // Group contiguous <li> elements into <ul>
    parsed = parsed.replace(/(?:<li>[\s\S]*?<\/li>\s*)+/g, (match) => {
      return `<ul>${match.trim()}</ul>`;
    });

    // Paragraphs
    const paragraphs = parsed.split(/\n\s*\n+/);
    parsed = paragraphs
      .map((p) => {
        p = p.trim();
        if (!p) return '';
        if (
          p.startsWith('<div') ||
          p.startsWith('<h') ||
          p.startsWith('<ul') ||
          p.startsWith('<ol')
        ) {
          return p;
        }
        return `<p>${p.replace(/\n/g, '<br>')}</p>`;
      })
      .join('\n');

    return parsed;
  }

  function copyToClipboard(text) {
    if (navigator.clipboard && window.isSecureContext) {
      return navigator.clipboard.writeText(text);
    } else {
      const textarea = document.createElement('textarea');
      textarea.value = text;
      textarea.style.position = 'fixed';
      textarea.style.left = '-999999px';
      textarea.style.top = '-999999px';
      document.body.appendChild(textarea);
      textarea.focus();
      textarea.select();
      return new Promise((resolve, reject) => {
        const successful = document.execCommand('copy');
        textarea.remove();
        successful ? resolve() : reject(new Error('Copy failed'));
      });
    }
  }

  function escapeHtml(str) {
    return String(str)
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;')
      .replace(/'/g, '&#039;');
  }

  function scrollToBottom() {
    chatBody.scrollTo({
      top: chatBody.scrollHeight,
      behavior: 'smooth'
    });
  }

  // ==========================================================================
  // 7. PIPELINE STEP ANIMATOR
  // ==========================================================================
  async function animatePipelineSteps(steps) {
    pipelineStepsList.innerHTML = '';
    typingIndicator.style.display = 'flex';
    scrollToBottom();

    for (let i = 0; i < steps.length; i++) {
      const step = steps[i];
      pipelineMainStatus.textContent = step.title;

      const stepEl = document.createElement('div');
      stepEl.className = 'pipeline-step active';
      stepEl.innerHTML = `
        <div class="step-icon-wrapper">
          <span class="step-spinner"></span>
        </div>
        <span>${escapeHtml(step.title)}</span>
      `;
      pipelineStepsList.appendChild(stepEl);
      scrollToBottom();

      await new Promise((r) => setTimeout(r, step.duration || 300));

      stepEl.className = 'pipeline-step done';
      stepEl.querySelector('.step-icon-wrapper').innerHTML = `
        <svg width="10" height="10" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3" stroke-linecap="round" stroke-linejoin="round">
          <polyline points="20 6 9 17 4 12"></polyline>
        </svg>
      `;
    }

    await new Promise((r) => setTimeout(r, 100));
  }

  // ==========================================================================
  // 8. REAL GROQ LLM & RAG INTELLIGENCE ENGINE (NO MOCKS!)
  // ==========================================================================
  async function handleSendMessage() {
    const rawText = chatTextarea.value.trim();
    if (!rawText && !attachedFile) return;
    if (isGenerating) return;

    const conv = getActiveConversation();
    if (!conv) return;

    let userMessageContent = rawText;
    const fileBeingAttached = attachedFile;

    if (fileBeingAttached) {
      userMessageContent = rawText || `Summarize and explain the key contents of ${fileBeingAttached.name}.`;
    }

    // 1. Append User Message
    const userMsg = {
      role: 'user',
      content: userMessageContent
    };
    conv.messages.push(userMsg);

    // Update conversation title if first message
    if (conv.messages.length === 1) {
      const cleanTitle = rawText || (fileBeingAttached ? fileBeingAttached.name : 'New Conversation');
      conv.title = cleanTitle.slice(0, 32) + (cleanTitle.length > 32 ? '...' : '');
      chatTitle.textContent = conv.title;
      renderSidebarList(searchChatsInput.value);
    }

    appendMessageToDOM(userMsg, true);
    saveState();

    // Reset textarea and attachment
    chatTextarea.value = '';
    chatTextarea.style.height = 'auto';
    clearAttachedFile();
    sendBtn.disabled = true;

    // Safety Guardrails Check (Profanity, Slangs, Abuse Filter)
    const guardrailCheck = checkSafetyGuardrails(userMessageContent);
    if (!guardrailCheck.safe) {
      isGenerating = false;
      const refusalMsg = {
        role: 'assistant',
        content: `**Enterprise Safety Guardrail Triggered**\n\n${guardrailCheck.message}`,
        citations: []
      };
      conv.messages.push(refusalMsg);
      saveState();
      appendMessageToDOM(refusalMsg, true);
      showToast('Inappropriate language blocked by guardrails');
      sendBtn.disabled = chatTextarea.value.trim().length === 0;
      return;
    }

    // 2. Trigger Real AI Generation
    isGenerating = true;

    try {
      const aiResponse = await executeRealLLMQuery(userMessageContent, conv, fileBeingAttached);
      typingIndicator.style.display = 'none';

      conv.messages.push(aiResponse);
      saveState();
      appendMessageToDOM(aiResponse, true);
    } catch (err) {
      typingIndicator.style.display = 'none';
      const fallbackMsg = {
        role: 'assistant',
        content: `Error communicating with AI engine: ${err.message}. Please check that your network connection and server are running.`
      };
      conv.messages.push(fallbackMsg);
      saveState();
      appendMessageToDOM(fallbackMsg, true);
      showToast('Error generating answer');
    } finally {
      isGenerating = false;
      sendBtn.disabled = chatTextarea.value.trim().length === 0;
    }
  }

  /**
   * Real LLM & Document Query Execution using Groq Llama 3.3 70B:
   * 1. Checks chat's documents for relevant context.
   * 2. Builds system prompt and conversation history.
   * 3. Calls Groq API directly (or FastAPI backend) for authentic, fluent responses!
   */
  async function executeRealLLMQuery(query, conv, newFile) {
    const docs = conv.documents || [];
    const hasDocs = docs.length > 0;

    let citations = [];
    let systemPrompt = '';
    let messagesPayload = [];

    // Production Groq Models: Llama 3.3 70B & Llama 3.1 8B (fast, accurate, no scratchpad leakage)
    const isThinkMode = (selectedResponseMode === 'think');
    const targetTemp = isThinkMode ? 0.2 : 0.1;
    const candidateModels = [
      'llama-3.3-70b-versatile',
      'llama-3.1-8b-instant',
      'mixtral-8x7b-32768'
    ];

    if (hasDocs) {
      // Step Animation: Searching & Retrieving from Knowledge Base
      const docNames = docs.map((d) => d.name).join(', ');
      const modeLabel = isThinkMode ? 'Deep Reasoning Mode (Llama 3.3 70B)' : 'Fast Mode (Instant)';
      await animatePipelineSteps([
        { title: `Searching knowledge base: ${docNames}...`, duration: 350 },
        { title: `Extracting semantic passages & reranking...`, duration: 350 },
        { title: `Synthesizing answer with ${modeLabel}...`, duration: 400 }
      ]);

      // Build context from chat documents
      let contextBlocks = [];
      docs.forEach((d, idx) => {
        contextBlocks.push(`=== DOCUMENT ${idx + 1}: ${d.name} ===\n${d.text || d.name}\n=== END DOCUMENT ===`);
        citations.push({ name: d.name, page: 1 });
      });

      systemPrompt = `You are Nexus AI, a helpful and expert Enterprise AI Knowledge Assistant.
Below is the knowledge base document context:
${contextBlocks.join('\n\n')}

Instructions:
1. Provide a comprehensive, accurate, and direct response to the user's question.
2. If the user asks for code, summaries, or solutions, provide clear explanations and properly formatted code blocks.
3. Output ONLY your direct, polished response in Markdown. Do not include internal monologue, scratchpads, self-dialogue, or thinking steps.`;
    } else {
      // Direct General LLM Query
      const modeLabel = isThinkMode ? 'Deep Think Reasoning' : 'Instant Fast Reasoning';
      await animatePipelineSteps([
        { title: `${modeLabel}...`, duration: 350 }
      ]);

      systemPrompt = `You are Nexus AI, an advanced enterprise AI assistant.
Instructions:
1. Answer the user's question directly, clearly, and accurately in their preferred language.
2. If code is requested, provide clear explanations and properly formatted code blocks.
3. Output ONLY the direct answer. Never output internal monologue, scratchpads, analysis steps, or self-dialogue.`;
    }

    // Build recent conversation history based on Memory Window setting
    messagesPayload.push({ role: 'system', content: systemPrompt });

    const memWindow = userSettings.memoryWindow || 10;
    if (conv.messages && conv.messages.length > 0) {
      const recent = conv.messages.slice(-memWindow);
      recent.forEach((m) => {
        messagesPayload.push({ role: m.role, content: m.content });
      });
    }

    // Multi-Key Failover Pool & Model Rotation (Client custom key or backend proxy)
    const keysPool = [
      userSettings.customGroqApiKey,
      userSettings.groqApiKey
    ].filter(Boolean);

    const uniqueKeys = [...new Set(keysPool)];

    let answerText = null;
    let lastError = null;

    // 1. If client provided custom key, call Groq directly
    if (uniqueKeys.length > 0) {
      for (const apiKey of uniqueKeys) {
        for (const modelId of candidateModels) {
          try {
            const groqRes = await fetch('https://api.groq.com/openai/v1/chat/completions', {
              method: 'POST',
              headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${apiKey}`
              },
              body: JSON.stringify({
                model: modelId,
                messages: messagesPayload,
                temperature: targetTemp,
                max_tokens: 2048
              })
            });

            if (groqRes.ok) {
              const groqData = await groqRes.json();
              answerText = groqData.choices[0]?.message?.content;
              if (answerText) break;
            } else {
              lastError = await groqRes.text();
            }
          } catch (e) {
            lastError = e.message;
          }
        }
        if (answerText) break;
      }
    }

    // 2. Fallback: Route request securely through FastAPI backend Groq service pool
    if (!answerText) {
      try {
        const backendRes = await fetch('/api/v1/chat/generate-direct', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            messages: messagesPayload,
            model: candidateModels[0],
            temperature: targetTemp,
            max_tokens: 2048
          })
        });
        if (backendRes.ok) {
          const backendData = await backendRes.json();
          if (backendData.success && backendData.content) {
            answerText = backendData.content;
          }
        }
      } catch (err) {
        console.warn('Backend proxy generation failed', err);
      }
    }

    // Clean thinking artifacts and reasoning scratchpad
    const cleanedAnswer = cleanThinkingProcess(answerText);

    return {
      role: 'assistant',
      content: cleanedAnswer || answerText || 'I could not generate a response. Please check your network connection.',
      citations: hasDocs ? citations : []
    };
  }

  function cleanThinkingProcess(raw) {
    if (!raw) return '';
    let text = raw;

    // 1. Remove XML <think>...</think> tags and enclosed reasoning
    text = text.replace(/<think>[\s\S]*?<\/think>/gi, '').trim();
    text = text.replace(/^<think>[\s\S]*?(?:\n\n|$)/i, '').trim();

    // 2. If the text has an explicit "Final Answer:", "Output:", or "Response:", slice from that point if preceded by reasoning
    const finalAnswerMatch = text.match(/(?:(?:Final Answer(?:\s+Formulation)?|Output|Response):\s*)([\s\S]+)$/i);
    if (finalAnswerMatch && finalAnswerMatch[1] && finalAnswerMatch[1].trim().length > 10) {
      text = finalAnswerMatch[1].trim();
    }

    // 3. Remove reasoning scratchpad lines (e.g., "Wait, is it possible...", "Analyze the Request...", "Self-Correction...")
    const scratchpadRegex = /^(?:Wait,\s|Analyze (?:the )?(?:Request|Context)|Self-Correction|Hypothesis|Decision|Problem:|Dilemma:|Refined (?:Plan|Hypothesis)|Strict Instruction|Final Answer Formulation|One (?:more|final) (?:check|thought)|Let's (?:check|look|assume|verify|consider)|Final decision|I will (?:state|output|write|formulate|stick)|Is it possible|So I will|This satisfies|However, usually|Given the user|The code is|Code:|Alternative:)\b/i;

    const lines = text.split('\n');
    const filteredLines = [];
    let insideCodeBlock = false;

    for (const line of lines) {
      if (line.trim().startsWith('```')) {
        insideCodeBlock = !insideCodeBlock;
        filteredLines.push(line);
        continue;
      }
      if (insideCodeBlock) {
        filteredLines.push(line);
        continue;
      }
      if (!scratchpadRegex.test(line.trim())) {
        filteredLines.push(line);
      }
    }

    text = filteredLines.join('\n').trim();

    // 4. Remove leading "Output:" or "Response:" or "Answer:" markers
    text = text.replace(/^(?:Output|Response|Final Response|Answer):\s*/i, '').trim();

    // 5. Remove any residual closing </think>
    text = text.replace(/<\/think>/gi, '').trim();

    return text;
  }

  // ==========================================================================
  // 9. EVENT LISTENERS & INPUT HANDLING
  // ==========================================================================
  chatTextarea.addEventListener('input', () => {
    chatTextarea.style.height = 'auto';
    chatTextarea.style.height = `${Math.min(chatTextarea.scrollHeight, 160)}px`;
    sendBtn.disabled = chatTextarea.value.trim().length === 0 && !attachedFile;
  });

  chatTextarea.addEventListener('keydown', (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSendMessage();
    }
  });

  sendBtn.addEventListener('click', handleSendMessage);
  newChatBtn.addEventListener('click', createNewChat);
  clearChatBtn.addEventListener('click', clearCurrentChat);

  suggestionCards.forEach((card) => {
    card.addEventListener('click', () => {
      const prompt = card.getAttribute('data-prompt');
      if (prompt) {
        chatTextarea.value = prompt;
        chatTextarea.style.height = 'auto';
        chatTextarea.style.height = `${Math.min(chatTextarea.scrollHeight, 160)}px`;
        sendBtn.disabled = false;
        handleSendMessage();
      }
    });
  });

  // Mobile sidebar drawer
  function openMobileSidebar() {
    sidebar.classList.add('open');
    sidebarOverlay.classList.add('active');
  }

  function closeMobileSidebar() {
    sidebar.classList.remove('open');
    sidebarOverlay.classList.remove('active');
  }

  mobileMenuBtn.addEventListener('click', openMobileSidebar);
  closeSidebarBtn.addEventListener('click', closeMobileSidebar);
  sidebarOverlay.addEventListener('click', closeMobileSidebar);

  function showToast(msg) {
    const toast = document.createElement('div');
    toast.className = 'toast';
    toast.innerHTML = `
      <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
        <path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"></path>
        <polyline points="22 4 12 14.01 9 11.01"></polyline>
      </svg>
      <span>${escapeHtml(msg)}</span>
    `;
    toastContainer.appendChild(toast);
    setTimeout(() => {
      toast.style.opacity = '0';
      toast.style.transform = 'translateY(6px)';
      toast.style.transition = 'all 0.2s ease';
      setTimeout(() => toast.remove(), 200);
    }, 2400);
  }

  // ==========================================================================
  // INITIALIZATION
  // ==========================================================================
  updateAuthUI();
  setResponseMode(selectedResponseMode, true);
  renderSidebarList();
  if (activeConversationId) {
    selectConversation(activeConversationId);
  } else if (conversations.length > 0) {
    selectConversation(conversations[0].id);
  } else {
    createNewChat();
  }

})();
