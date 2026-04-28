(function () {
    const revealNodes = document.querySelectorAll('[data-animate]');
    revealNodes.forEach((node) => node.classList.add('is-visible'));

    const bootstrapNode = document.getElementById('story-editor-data');
    if (!bootstrapNode) {
        return;
    }
    const bootstrapData = JSON.parse(bootstrapNode.textContent || '{}');
    const storyId = bootstrapData.story_id;
    const token = localStorage.getItem('auth_token');
    if (!token || !storyId) {
        window.location.replace(`/login/?next=/story/${storyId || ''}/scenes/`);
        return;
    }
    const titleEl = document.getElementById('scene-editor-story-title');
    const backLink = document.getElementById('scene-editor-back-link');
    const openStoryBtn = document.getElementById('scene-editor-open-story-btn');
    const errorBox = document.getElementById('scene-editor-error');
    const successBox = document.getElementById('scene-editor-success');
    const form = document.getElementById('scene-create-form');
    const sceneList = document.getElementById('scene-list');
    const choiceRows = document.getElementById('choice-rows');
    const addChoiceBtn = document.getElementById('choice-add-btn');
    const loadingText = document.getElementById('scene-editor-loading');
    const submitBtn = document.getElementById('scene-create-submit');
    const titleInput = document.getElementById('scene-title');
    const contentInput = document.getElementById('scene-content');
    const backgroundUrlInput = document.getElementById('scene-background-url');
    const isStartingInput = document.getElementById('scene-is-starting');
    const isEndingInput = document.getElementById('scene-is-ending');
    if (!titleEl || !backLink || !errorBox || !successBox || !form || !sceneList || !choiceRows || !addChoiceBtn || !loadingText || !submitBtn || !titleInput || !contentInput || !backgroundUrlInput || !isStartingInput || !isEndingInput) {
        return;
    }
    let attributes = [];
    let scenes = [];
    let editingSceneId = null;
    const setLoading = (isLoading) => {
        submitBtn.disabled = isLoading;
        loadingText.classList.toggle('d-none', !isLoading);
    };
    const showError = (message) => {
        errorBox.textContent = message;
        errorBox.classList.remove('d-none');
        successBox.classList.add('d-none');
        successBox.textContent = '';
    };
    const showSuccess = (message) => {
        successBox.textContent = message;
        successBox.classList.remove('d-none');
        errorBox.classList.add('d-none');
        errorBox.textContent = '';
    };
    const authHeaders = () => ({
        Authorization: `Token ${token}`,
        'Content-Type': 'application/json',
    });
    const optionsForAttributes = () => {
        const opts = ['<option value="">None</option>'];
        attributes.forEach((attribute) => {
            opts.push(`<option value="${attribute.key}">${attribute.label}</option>`);
        });
        return opts.join('');
    };
    const optionsForScenes = () => {
        const opts = ['<option value="">Select next scene</option>'];
        scenes.forEach((scene) => {
            opts.push(`<option value="${scene.id}">${scene.title || `Scene ${scene.id}`}</option>`);
        });
        return opts.join('');
    };

    const createConditionRow = (key = '', val = '') => {
        const row = document.createElement('div');
        row.className = 'condition-row';
        row.dataset.conditionRow = 'true';
        row.innerHTML = `
            <select data-require-key class="choice-select">${optionsForAttributes()}</select>
            <span class="condition-op">≥</span>
            <input data-require-value class="choice-input-num" type="number" step="1" placeholder="0" value="${val}">
            <button type="button" class="btn-icon-sm" data-remove-row title="Remove condition">×</button>
        `;
        if (key) row.querySelector('[data-require-key]').value = key;
        row.querySelector('[data-remove-row]').addEventListener('click', () => row.remove());
        return row;
    };

    const createEffectRow = (key = '', val = '') => {
        const row = document.createElement('div');
        row.className = 'effect-row';
        row.dataset.effectRow = 'true';
        row.innerHTML = `
            <select data-effect-key class="choice-select">${optionsForAttributes()}</select>
            <span class="effect-op">Δ</span>
            <input data-effect-delta class="choice-input-num" type="number" step="1" placeholder="0" value="${val}">
            <button type="button" class="btn-icon-sm" data-remove-row title="Remove effect">×</button>
        `;
        if (key) row.querySelector('[data-effect-key]').value = key;
        row.querySelector('[data-remove-row]').addEventListener('click', () => row.remove());
        return row;
    };

    const createChoiceRow = (choiceData = null) => {
        const row = document.createElement('div');
        row.className = 'choice-row';
        row.dataset.choiceRow = 'true';
        let textVal = '';
        let targetVal = '';
        if (choiceData) {
            textVal = choiceData.text || '';
            targetVal = choiceData.target_scene_id || '';
        }
        row.innerHTML = `
            <div class="choice-grid">
                <input data-choice-text class="choice-select" type="text" maxlength="200" placeholder="Choice text" value="${textVal}">
                <select data-choice-target class="choice-select">${optionsForScenes()}</select>
            </div>
            <div class="choice-details-grid">
                <div class="choice-conditions-container">
                    <div class="choice-conditions-header">
                        <span class="text-sm font-semibold">Required attributes</span>
                        <button type="button" class="btn btn-sm btn-outline-primary" data-add-condition>+ Condition</button>
                    </div>
                    <div class="conditions-list"></div>
                </div>
                <div class="choice-effects-container">
                    <div class="choice-effects-header">
                        <span class="text-sm font-semibold">Effects on attributes</span>
                        <button type="button" class="btn btn-sm btn-outline-primary" data-add-effect>+ Effect</button>
                    </div>
                    <div class="effects-list"></div>
                </div>
            </div>
            <button type="button" class="btn btn-outline-danger px-3 py-2 text-sm choice-delete" style="margin-top: 12px; width: 100%;" data-choice-delete>Delete choice</button>
        `;

        const targetSelect = row.querySelector('[data-choice-target]');
        if (targetVal) targetSelect.value = targetVal;

        const conditionsList = row.querySelector('.conditions-list');
        const effectsList = row.querySelector('.effects-list');

        if (choiceData && choiceData.conditions && typeof choiceData.conditions === 'object') {
            for (const [k, v] of Object.entries(choiceData.conditions)) {
                conditionsList.appendChild(createConditionRow(k, v));
            }
        } else if (choiceData && choiceData.requirement && choiceData.requirement.key) {
            conditionsList.appendChild(createConditionRow(choiceData.requirement.key, choiceData.requirement.value));
        } else {
            conditionsList.appendChild(createConditionRow());
        }

        if (choiceData && choiceData.effects && typeof choiceData.effects === 'object') {
            for (const [k, v] of Object.entries(choiceData.effects)) {
                effectsList.appendChild(createEffectRow(k, v));
            }
        } else if (choiceData && choiceData.effect && choiceData.effect.key) {
            effectsList.appendChild(createEffectRow(choiceData.effect.key, choiceData.effect.delta));
        } else {
            effectsList.appendChild(createEffectRow());
        }

        row.querySelector('[data-add-condition]').addEventListener('click', () => {
            conditionsList.appendChild(createConditionRow());
        });
        row.querySelector('[data-add-effect]').addEventListener('click', () => {
            effectsList.appendChild(createEffectRow());
        });
        row.querySelector('[data-choice-delete]').addEventListener('click', () => {
            row.remove();
        });
        return row;
    };    const refreshChoiceSelects = () => {
        choiceRows.querySelectorAll('[data-choice-target]').forEach((select) => {
            const current = select.value;
            select.innerHTML = optionsForScenes();
            if (current) {
                select.value = current;
            }
        });
        choiceRows.querySelectorAll('[data-require-key], [data-effect-key]').forEach((select) => {
            const current = select.value;
            select.innerHTML = optionsForAttributes();
            if (current) {
                select.value = current;
            }
        });
    };
    const renderSceneList = () => {
        if (!scenes.length) {
            sceneList.innerHTML = '<p class="section-hint">No scenes yet. Create first scene.</p>';
            return;
        }
        sceneList.innerHTML = scenes.map((scene) => {
            const flags = [scene.is_starting ? 'Start' : '', scene.is_ending ? 'End' : ''].filter(Boolean).join(', ');
            return `
                <div class="scene-item">
                    <h3>${scene.title || 'Untitled scene'}</h3>
                    <p>${scene.content || 'No content yet.'}</p>
                    <p>Choices: ${scene.choices.length}${flags ? ` | ${flags}` : ''}</p>
                    <div class="scene-actions">
                        <button class="btn btn-outline-primary btn-sm edit-scene" data-scene-id="${scene.id}">Edit</button>
                        <button class="btn btn-outline-danger btn-sm delete-scene" data-scene-id="${scene.id}">Delete</button>
                    </div>
                </div>
            `;
        }).join('');
        // attach event listeners
        sceneList.querySelectorAll('.edit-scene').forEach(btn => {
            btn.addEventListener('click', () => {
                const sceneId = Number.parseInt(btn.dataset.sceneId, 10);
                const scene = scenes.find(s => s.id === sceneId);
                if (scene) enterEditMode(scene);
            });
        });
        sceneList.querySelectorAll('.delete-scene').forEach(btn => {
            btn.addEventListener('click', async () => {
                const sceneId = Number.parseInt(btn.dataset.sceneId, 10);
                if (!confirm('Delete this scene? This cannot be undone.')) return;
                try {
                    const response = await fetch(`/story/api/${storyId}/scenes/${sceneId}/delete/`, {
                        method: 'POST',
                        headers: authHeaders(),
                    });
                    const data = await response.json();
                    if (!response.ok) {
                        showError(data?.error || 'Delete failed.');
                        return;
                    }
                    showSuccess('Scene deleted.');
                    await loadSceneData();
                } catch (error) {
                    showError(error.message || 'Request failed.');
                }
            });
        });
    };
    const enterEditMode = (scene) => {
        editingSceneId = scene.id;
        submitBtn.textContent = 'Update scene';
        // populate form
        titleInput.value = scene.title || '';
        contentInput.value = scene.content || '';
        backgroundUrlInput.value = scene.background_image_url || '';
        isEndingInput.checked = scene.is_ending || false;
        isStartingInput.checked = scene.is_starting || false;
        // populate choices
        choiceRows.innerHTML = '';
        if (scene.choices && scene.choices.length) {
            scene.choices.forEach(choice => {
                const row = createChoiceRow({
                    text: choice.text,
                    target_scene_id: choice.target_scene_id,
                    conditions: choice.conditions,
                    requirement: choice.requirement,
                    effects: choice.effects,
                });
                choiceRows.appendChild(row);
            });
        } else {
            choiceRows.appendChild(createChoiceRow());
        }
        refreshChoiceSelects();
        // scroll to form
        form.scrollIntoView({ behavior: 'smooth' });
    };
    const exitEditMode = () => {
        editingSceneId = null;
        form.reset();
        submitBtn.textContent = 'Create scene';
        submitBtn.disabled = false;
        choiceRows.innerHTML = '';
        choiceRows.appendChild(createChoiceRow());
    };
    // expose for cancel button (if we add one)
    window.cancelSceneEdit = exitEditMode;
    const loadSceneData = async () => {
        const response = await fetch(`/story/api/${storyId}/scenes/`, {
            headers: { Authorization: `Token ${token}` },
        });
        const data = await response.json();
        if (!response.ok) {
            throw new Error(data?.error || 'Failed to load scene editor data.');
        }
        titleEl.textContent = data.story.title;
        backLink.href = `/story/${storyId}/edit/`;
        attributes = data.attributes || [];
        scenes = data.scenes || [];
        renderSceneList();
        refreshChoiceSelects();
    };
    const collectChoices = () => {
        const parsed = [];
        choiceRows.querySelectorAll('[data-choice-row]').forEach((row, index) => {
            const text = row.querySelector('[data-choice-text]').value.trim();
            const targetSceneId = row.querySelector('[data-choice-target]').value;

            const conditions = {};
            row.querySelectorAll('[data-condition-row]').forEach(condRow => {
                const key = condRow.querySelector('[data-require-key]').value;
                const val = condRow.querySelector('[data-require-value]').value;
                if (key && val !== '') {
                    conditions[key] = Number(val);
                }
            });

            const effects = {};
            row.querySelectorAll('[data-effect-row]').forEach(effRow => {
                const key = effRow.querySelector('[data-effect-key]').value;
                const val = effRow.querySelector('[data-effect-delta]').value;
                if (key && val !== '') {
                    effects[key] = Number(val);
                }
            });

            if (!text && !targetSceneId && Object.keys(conditions).length === 0 && Object.keys(effects).length === 0) {
                return;
            }
            if (!text) {
                throw new Error(`Choice #${index + 1}: text required.`);
            }

            const choice = {
                text,
                target_scene_id: targetSceneId ? Number.parseInt(targetSceneId, 10) : null,
                conditions,
                effects,
            };
            parsed.push(choice);
        });
        return parsed;
    };
    openStoryBtn.addEventListener('click', () => {
        window.open(`/story/${storyId}`, '_blank');
    });
    addChoiceBtn.addEventListener('click', () => {
        choiceRows.appendChild(createChoiceRow());
    });
    form.addEventListener('submit', async (event) => {
        event.preventDefault();
        setLoading(true);
        errorBox.classList.add('d-none');
        successBox.classList.add('d-none');
        try {
            const choices = collectChoices();
            const payload = {
                title: titleInput.value.trim(),
                content: contentInput.value.trim(),
                background_image_url: backgroundUrlInput.value.trim(),
                is_ending: isEndingInput.checked,
                is_starting: isStartingInput.checked,
                choices,
            };
            let response;
            if (editingSceneId) {
                response = await fetch(`/story/api/${storyId}/scenes/${editingSceneId}/update/`, {
                    method: 'POST',
                    headers: authHeaders(),
                    body: JSON.stringify(payload),
                });
            } else {
                response = await fetch(`/story/api/${storyId}/scenes/create/`, {
                    method: 'POST',
                    headers: authHeaders(),
                    body: JSON.stringify(payload),
                });
            }
            const data = await response.json();
            if (!response.ok) {
                showError(data?.error || (editingSceneId ? 'Scene update failed.' : 'Scene create failed.'));
                return;
            }
            showSuccess(editingSceneId ? 'Scene updated.' : 'Scene created.');
            exitEditMode();
            await loadSceneData();
        } catch (error) {
            showError(error.message || 'Request failed.');
        } finally {
            setLoading(false);
        }
    });
    loadSceneData().catch((error) => {
        showError(error.message || 'Failed to initialize scene editor.');
    });
})();
