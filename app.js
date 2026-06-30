// AuraMeet Client Application Logic

document.addEventListener('DOMContentLoaded', () => {
    // Application State
    let state = {
        config: null,
        team: [],
        currentResults: {
            meeting_title: 'Weekly Sync Meeting',
            summary: '',
            action_items: []
        }
    };

    // DOM Elements
    const navTabs = document.querySelectorAll('.nav-tab');
    const tabPanes = document.querySelectorAll('.tab-pane');
    
    // Toast elements
    const toast = document.getElementById('toast');
    const toastIcon = document.getElementById('toast-icon');
    const toastMessage = document.getElementById('toast-message');

    // Load initial data
    loadConfig();
    loadTeam();

    // ==========================================
    // 1. NAVIGATION & TAB SWITCHING
    // ==========================================
    navTabs.forEach(tab => {
        tab.addEventListener('click', () => {
            const targetTab = tab.getAttribute('data-tab');
            
            // Update active tab button
            navTabs.forEach(t => t.classList.remove('active'));
            tab.classList.add('active');
            
            // Show active pane
            tabPanes.forEach(pane => {
                if (pane.id === targetTab) {
                    pane.classList.add('active');
                } else {
                    pane.classList.remove('active');
                }
            });

            // Trigger specific tab focus events if needed
            if (targetTab === 'tab-team') {
                renderTeamTable();
            }
        });
    });

    // ==========================================
    // 2. SMTP SETTINGS MODULE
    // ==========================================
    const smtpForm = document.getElementById('smtp-form');
    const testSmtpBtn = document.getElementById('btn-test-smtp');
    const whisperModelSelect = document.getElementById('whisper-model-select');

    function loadConfig() {
        fetch('/api/config')
            .then(res => res.json())
            .then(data => {
                state.config = data;
                
                // Populating form inputs
                document.getElementById('smtp-host').value = data.smtp.host || '';
                document.getElementById('smtp-port').value = data.smtp.port || 587;
                document.getElementById('smtp-username').value = data.smtp.username || '';
                document.getElementById('smtp-password').value = data.smtp.password || '';
                document.getElementById('smtp-sender-email').value = data.smtp.sender_email || '';
                document.getElementById('smtp-use-ssl').checked = data.smtp.use_ssl || false;
                document.getElementById('smtp-use-tls').checked = data.smtp.use_tls !== false;
                
                if (data.whisper_model) {
                    whisperModelSelect.value = data.whisper_model;
                }

                updateSmtpStatusIndicator(data.smtp);
            })
            .catch(err => {
                showToast('Failed to load settings from server', 'error');
                console.error(err);
            });
    }

    function updateSmtpStatusIndicator(smtp) {
        const smtpBadge = document.getElementById('smtp-status');
        if (smtp.host && smtp.username && smtp.password) {
            smtpBadge.className = 'status-value badge badge-green';
            smtpBadge.innerHTML = '<i class="fa-solid fa-check-circle"></i> Configured';
        } else {
            smtpBadge.className = 'status-value badge badge-orange';
            smtpBadge.innerHTML = '<i class="fa-solid fa-triangle-exclamation"></i> Not Configured';
        }
    }

    // Save Settings Handler
    smtpForm.addEventListener('submit', (e) => {
        e.preventDefault();
        
        const updatedConfig = {
            smtp: {
                host: document.getElementById('smtp-host').value,
                port: parseInt(document.getElementById('smtp-port').value),
                username: document.getElementById('smtp-username').value,
                password: document.getElementById('smtp-password').value,
                sender_email: document.getElementById('smtp-sender-email').value,
                use_ssl: document.getElementById('smtp-use-ssl').checked,
                use_tls: document.getElementById('smtp-use-tls').checked
            },
            whisper_model: whisperModelSelect.value
        };

        fetch('/api/config', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(updatedConfig)
        })
        .then(res => res.json())
        .then(data => {
            showToast('Settings saved successfully!', 'success');
            state.config = updatedConfig;
            updateSmtpStatusIndicator(updatedConfig.smtp);
        })
        .catch(err => {
            showToast('Failed to save settings', 'error');
            console.error(err);
        });
    });

    // Test SMTP Connection Handler
    testSmtpBtn.addEventListener('click', () => {
        const testConfig = {
            smtp: {
                host: document.getElementById('smtp-host').value,
                port: parseInt(document.getElementById('smtp-port').value),
                username: document.getElementById('smtp-username').value,
                password: document.getElementById('smtp-password').value,
                sender_email: document.getElementById('smtp-sender-email').value,
                use_ssl: document.getElementById('smtp-use-ssl').checked,
                use_tls: document.getElementById('smtp-use-tls').checked
            }
        };

        testSmtpBtn.disabled = true;
        testSmtpBtn.innerHTML = '<i class="fa-solid fa-circle-notch fa-spin"></i> Testing...';
        showToast('Testing mail server connection...', 'info');

        fetch('/api/smtp/test', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(testConfig)
        })
        .then(res => {
            if (!res.ok) {
                return res.json().then(errData => { throw new Error(errData.message); });
            }
            return res.json();
        })
        .then(data => {
            showToast('SMTP Connection Successful!', 'success');
        })
        .catch(err => {
            showToast(`Connection failed: ${err.message}`, 'error');
        })
        .finally(() => {
            testSmtpBtn.disabled = false;
            testSmtpBtn.innerHTML = '<i class="fa-solid fa-vial"></i> Test Connection';
        });
    });

    // ==========================================
    // 3. TEAM DIRECTORY MODULE
    // ==========================================
    const teamTbody = document.getElementById('team-tbody');
    const addTeamMemberBtn = document.getElementById('btn-add-team-member');
    const saveTeamBtn = document.getElementById('btn-save-team');
    const statsTeamCount = document.getElementById('stats-team-count');

    function loadTeam() {
        fetch('/api/team')
            .then(res => res.json())
            .then(data => {
                state.team = data;
                renderTeamTable();
                statsTeamCount.textContent = `${data.length} Members`;
            })
            .catch(err => {
                showToast('Failed to load team list', 'error');
                console.error(err);
            });
    }

    function renderTeamTable() {
        teamTbody.innerHTML = '';
        state.team.forEach((member, index) => {
            const tr = document.createElement('tr');
            tr.innerHTML = `
                <td>
                    <input type="text" class="td-input name-input" value="${member.name}" placeholder="Name">
                </td>
                <td>
                    <input type="email" class="td-input email-input" value="${member.email}" placeholder="email@example.com">
                </td>
                <td>
                    <input type="text" class="td-input role-input" value="${member.role || ''}" placeholder="Role (e.g. Designer)">
                </td>
                <td class="text-center">
                    <button class="icon-btn icon-btn-danger btn-delete-member" data-index="${index}">
                        <i class="fa-solid fa-trash-can"></i>
                    </button>
                </td>
            `;
            teamTbody.appendChild(tr);
        });

        // Add event listeners to delete buttons
        document.querySelectorAll('.btn-delete-member').forEach(btn => {
            btn.addEventListener('click', (e) => {
                const idx = parseInt(btn.getAttribute('data-index'));
                state.team.splice(idx, 1);
                renderTeamTable();
            });
        });
    }

    // Add New Member Row Handler
    addTeamMemberBtn.addEventListener('click', () => {
        // Collect currently typed data first to preserve changes before re-rendering
        collectTeamFormData();
        
        state.team.push({ name: '', email: '', role: '' });
        renderTeamTable();
        
        // Scroll to the bottom of the table
        const tableContainer = teamTbody.parentElement.parentElement;
        tableContainer.scrollTop = tableContainer.scrollHeight;
    });

    function collectTeamFormData() {
        const rows = teamTbody.querySelectorAll('tr');
        const updatedTeam = [];
        
        rows.forEach(row => {
            const name = row.querySelector('.name-input').value.stripOrTrim();
            const email = row.querySelector('.email-input').value.stripOrTrim();
            const role = row.querySelector('.role-input').value.stripOrTrim();
            
            if (name || email) {
                updatedTeam.push({ name, email, role });
            }
        });
        
        state.team = updatedTeam;
    }

    // Save Team Handler
    saveTeamBtn.addEventListener('click', () => {
        collectTeamFormData();
        
        // Validation check
        const invalid = state.team.some(m => !m.name || !m.email);
        if (invalid) {
            showToast('All team members must have a Name and Email!', 'error');
            return;
        }

        fetch('/api/team', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(state.team)
        })
        .then(res => res.json())
        .then(data => {
            showToast('Team directory saved!', 'success');
            statsTeamCount.textContent = `${state.team.length} Members`;
            renderTeamTable();
        })
        .catch(err => {
            showToast('Failed to save team directory', 'error');
            console.error(err);
        });
    });

    // Helper to strip whitespaces
    String.prototype.stripOrTrim = function() {
        return this.trim();
    };

    // ==========================================
    // 4. TRANSCRIPT ANALYZER MODULE (TEXT)
    // ==========================================
    const pastedTranscript = document.getElementById('pasted-transcript');
    const summarySentencesInput = document.getElementById('summary-sentences');
    const analyzeTextBtn = document.getElementById('btn-analyze-text');
    const resultsSection = document.getElementById('analysis-results-section');
    const meetingTitleInput = document.getElementById('meeting-title');
    const summaryTextArea = document.getElementById('meeting-summary-text');
    const tasksTbody = document.getElementById('tasks-tbody');
    const addTaskBtn = document.getElementById('btn-add-task');
    const emailAllBtn = document.getElementById('btn-email-all');

    analyzeTextBtn.addEventListener('click', () => {
        const text = pastedTranscript.value.trim();
        if (!text) {
            showToast('Please type or paste a meeting transcript first!', 'error');
            return;
        }

        analyzeTextBtn.disabled = true;
        analyzeTextBtn.innerHTML = '<i class="fa-solid fa-circle-notch fa-spin"></i> Processing...';
        showToast('Running local NLP models...', 'info');

        fetch('/api/analyze-text', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                text: text,
                summary_sentences: summarySentencesInput.value
            })
        })
        .then(res => res.json())
        .then(data => {
            showToast('Meeting analyzed successfully!', 'success');
            
            state.currentResults.summary = data.summary;
            state.currentResults.action_items = data.action_items;
            
            renderAnalysisResults();
        })
        .catch(err => {
            showToast('Failed to analyze transcript', 'error');
            console.error(err);
        })
        .finally(() => {
            analyzeTextBtn.disabled = false;
            analyzeTextBtn.innerHTML = '<i class="fa-solid fa-wand-magic-sparkles"></i> Run Analysis';
        });
    });

    function renderAnalysisResults() {
        resultsSection.classList.remove('hidden');
        summaryTextArea.value = state.currentResults.summary;
        meetingTitleInput.value = state.currentResults.meeting_title;
        
        renderTasksTable();
        
        // Scroll results into view
        resultsSection.scrollIntoView({ behavior: 'smooth', block: 'start' });
    }

    function renderTasksTable() {
        tasksTbody.innerHTML = '';
        
        if (state.currentResults.action_items.length === 0) {
            tasksTbody.innerHTML = `
                <tr id="no-tasks-row">
                    <td colspan="4" class="text-center" style="color: var(--text-muted); padding: 20px;">
                        No action items detected. Click "Add Item" to add one manually.
                    </td>
                </tr>
            `;
            return;
        }

        state.currentResults.action_items.forEach((item, index) => {
            const tr = document.createElement('tr');
            
            // Build assignee dropdown mapping existing team
            let optionsHtml = `<option value="Unassigned" ${item.assignee === 'Unassigned' ? 'selected' : ''}>Unassigned</option>`;
            state.team.forEach(member => {
                const isSelected = item.assignee.toLowerCase() === member.name.toLowerCase();
                optionsHtml += `<option value="${member.name}" ${isSelected ? 'selected' : ''}>${member.name}</option>`;
            });

            tr.innerHTML = `
                <td>
                    <input type="text" class="td-input task-desc-input" value="${item.task}" placeholder="Action Item description">
                </td>
                <td>
                    <select class="td-select task-assignee-select">
                        ${optionsHtml}
                    </select>
                </td>
                <td>
                    <input type="text" class="td-input task-due-input" value="${item.due_date}" placeholder="e.g. Friday, Tomorrow">
                </td>
                <td class="action-btn-cell">
                    <button class="icon-btn icon-btn-success btn-email-single" data-index="${index}" title="Send email to assignee">
                        <i class="fa-solid fa-envelope"></i>
                    </button>
                    <button class="icon-btn icon-btn-danger btn-delete-task" data-index="${index}" title="Delete task">
                        <i class="fa-solid fa-trash-can"></i>
                    </button>
                </td>
            `;
            tasksTbody.appendChild(tr);
        });

        // Event listener: Delete Task
        document.querySelectorAll('.btn-delete-task').forEach(btn => {
            btn.addEventListener('click', () => {
                const idx = parseInt(btn.getAttribute('data-index'));
                collectTasksFormData();
                state.currentResults.action_items.splice(idx, 1);
                renderTasksTable();
            });
        });

        // Event listener: Email Single Task
        document.querySelectorAll('.btn-email-single').forEach(btn => {
            btn.addEventListener('click', () => {
                const idx = parseInt(btn.getAttribute('data-index'));
                collectTasksFormData();
                const taskItem = state.currentResults.action_items[idx];
                
                if (taskItem.assignee === 'Unassigned') {
                    showToast('Cannot send task email: Assignee is Unassigned!', 'error');
                    return;
                }

                btn.disabled = true;
                btn.innerHTML = '<i class="fa-solid fa-circle-notch fa-spin"></i>';
                showToast(`Sending email to ${taskItem.assignee}...`, 'info');

                fetch('/api/send-emails', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        meeting_title: meetingTitleInput.value,
                        meeting_summary: summaryTextArea.value,
                        tasks: [taskItem]
                    })
                })
                .then(res => res.json())
                .then(data => {
                    const resDetails = data.results[0];
                    if (resDetails.status === 'success') {
                        showToast(`Email sent to ${taskItem.assignee} successfully!`, 'success');
                    } else {
                        showToast(`Failed to email ${taskItem.assignee}: ${resDetails.message}`, 'error');
                    }
                })
                .catch(err => {
                    showToast('SMTP Server Error. Check SMTP configuration tab.', 'error');
                    console.error(err);
                })
                .finally(() => {
                    btn.disabled = false;
                    btn.innerHTML = '<i class="fa-solid fa-envelope"></i>';
                });
            });
        });
    }

    function collectTasksFormData() {
        const rows = tasksTbody.querySelectorAll('tr');
        if (rows.length === 1 && rows[0].id === 'no-tasks-row') {
            state.currentResults.action_items = [];
            return;
        }

        const updatedTasks = [];
        rows.forEach(row => {
            const task = row.querySelector('.task-desc-input').value.trim();
            const assignee = row.querySelector('.task-assignee-select').value;
            const due_date = row.querySelector('.task-due-input').value.trim();
            
            if (task) {
                updatedTasks.push({ task, assignee, due_date });
            }
        });
        state.currentResults.action_items = updatedTasks;
    }

    // Add Task Handler
    addTaskBtn.addEventListener('click', () => {
        collectTasksFormData();
        state.currentResults.action_items.push({
            task: '',
            assignee: 'Unassigned',
            due_date: 'Today'
        });
        renderTasksTable();
    });

    // Email All / Dispatch Tasks Handler
    emailAllBtn.addEventListener('click', () => {
        collectTasksFormData();
        
        if (state.currentResults.action_items.length === 0) {
            showToast('No action items to email!', 'error');
            return;
        }

        const activeTasks = state.currentResults.action_items.filter(t => t.assignee !== 'Unassigned');
        if (activeTasks.length === 0) {
            showToast('No tasks have been assigned. Assign team members first!', 'error');
            return;
        }

        emailAllBtn.disabled = true;
        emailAllBtn.innerHTML = '<i class="fa-solid fa-circle-notch fa-spin"></i> Dispatching Emails...';
        showToast('Sending personalized emails to team members...', 'info');

        fetch('/api/send-emails', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                meeting_title: meetingTitleInput.value,
                meeting_summary: summaryTextArea.value,
                tasks: state.currentResults.action_items
            })
        })
        .then(res => {
            if (!res.ok) {
                return res.json().then(errData => { throw new Error(errData.message); });
            }
            return res.json();
        })
        .then(data => {
            let successCount = 0;
            let failList = [];
            
            data.results.forEach(res => {
                if (res.status === 'success') successCount++;
                else failList.push(`${res.assignee} (${res.message || 'error'})`);
            });

            if (successCount > 0 && failList.length === 0) {
                showToast(`Successfully emailed all ${successCount} assignees!`, 'success');
            } else if (successCount > 0 && failList.length > 0) {
                showToast(`Emailed ${successCount} assignees. Failed: ${failList.join(', ')}`, 'orange');
            } else {
                showToast(`All emails failed to dispatch. Check SMTP tab.`, 'error');
            }
        })
        .catch(err => {
            showToast(`Error dispatching emails: ${err.message}`, 'error');
            console.error(err);
        })
        .finally(() => {
            emailAllBtn.disabled = false;
            emailAllBtn.innerHTML = '<i class="fa-solid fa-paper-plane"></i> Dispatch Email Notifications';
        });
    });


    // ==========================================
    // 5. AUDIO TRANSCRIPTION MODULE (WHISPER)
    // ==========================================
    const dropZone = document.getElementById('audio-drop-zone');
    const fileInput = document.getElementById('audio-file-input');
    const progressContainer = document.getElementById('upload-progress-container');
    const progressFilename = document.getElementById('progress-filename');
    const progressPercentage = document.getElementById('progress-percentage');
    const progressBarFill = document.getElementById('progress-bar-fill');

    // Drag-over styling hooks
    ['dragenter', 'dragover'].forEach(eventName => {
        dropZone.addEventListener(eventName, (e) => {
            e.preventDefault();
            dropZone.classList.add('dragover');
        }, false);
    });

    ['dragleave', 'drop'].forEach(eventName => {
        dropZone.addEventListener(eventName, (e) => {
            e.preventDefault();
            dropZone.classList.remove('dragover');
        }, false);
    });

    // Handle dropped files
    dropZone.addEventListener('drop', (e) => {
        const dt = e.dataTransfer;
        const files = dt.files;
        if (files.length > 0) {
            handleAudioUpload(files[0]);
        }
    });

    // Handle browsed file selection
    fileInput.addEventListener('change', () => {
        if (fileInput.files.length > 0) {
            handleAudioUpload(fileInput.files[0]);
        }
    });

    function handleAudioUpload(file) {
        // Validate it is audio file
        if (!file.type.startsWith('audio/') && !file.name.endsWith('.mp3') && !file.name.endsWith('.wav') && !file.name.endsWith('.m4a')) {
            showToast('Invalid file format. Please upload MP3, WAV or M4A audio!', 'error');
            return;
        }

        // Show Progress Container
        progressContainer.classList.remove('hidden');
        progressFilename.textContent = file.name;
        progressBarFill.style.width = '0%';
        progressPercentage.textContent = 'Uploading...';
        
        const formData = new FormData();
        formData.append('file', file);

        // Simulated progress bar animation (since Whisper CPU execution runs entirely server-side in a single block)
        let simulatedProgress = 0;
        const progressInterval = setInterval(() => {
            if (simulatedProgress < 90) {
                simulatedProgress += Math.random() * 5 + 1;
                if (simulatedProgress > 90) simulatedProgress = 90;
                
                progressBarFill.style.width = `${Math.floor(simulatedProgress)}%`;
                progressPercentage.textContent = `${Math.floor(simulatedProgress)}% Transcribing...`;
            }
        }, 1500);

        fetch('/api/upload', {
            method: 'POST',
            body: formData
        })
        .then(res => {
            clearInterval(progressInterval);
            if (!res.ok) {
                return res.json().then(errData => { throw new Error(errData.message); });
            }
            return res.json();
        })
        .then(data => {
            progressBarFill.style.width = '100%';
            progressPercentage.textContent = '100% Complete!';
            showToast('Audio transcription and analysis completed!', 'success');
            
            // Set results
            pastedTranscript.value = data.transcript;
            state.currentResults.summary = data.summary;
            state.currentResults.action_items = data.action_items;
            
            // Wait 1 second so user sees 100% complete, then switch tab & render results
            setTimeout(() => {
                progressContainer.classList.add('hidden');
                document.getElementById('btn-tab-dashboard').click();
                renderAnalysisResults();
            }, 1000);
        })
        .catch(err => {
            clearInterval(progressInterval);
            progressContainer.classList.add('hidden');
            showToast(`Transcription error: ${err.message}`, 'error');
            console.error(err);
        });
    }

    // ==========================================
    // 6. TOAST NOTIFICATIONS UTILITY
    // ==========================================
    let toastTimeout;
    function showToast(message, type = 'info') {
        clearTimeout(toastTimeout);
        
        toastMessage.textContent = message;
        toast.className = 'toast'; // Reset classes
        
        // Apply type classes
        if (type === 'success') {
            toast.classList.add('toast-success');
            toastIcon.className = 'fa-solid fa-circle-check';
        } else if (type === 'error') {
            toast.classList.add('toast-error');
            toastIcon.className = 'fa-solid fa-circle-xmark';
        } else if (type === 'orange') {
            toast.classList.add('toast-orange');
            toastIcon.className = 'fa-solid fa-triangle-exclamation';
        } else {
            toast.classList.add('toast-info');
            toastIcon.className = 'fa-solid fa-circle-info';
        }
        
        toast.classList.remove('hidden');

        // Auto hide after 5 seconds
        toastTimeout = setTimeout(() => {
            toast.classList.add('hidden');
        }, 5000);
    }
});
