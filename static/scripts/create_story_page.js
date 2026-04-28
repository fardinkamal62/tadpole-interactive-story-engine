(function () {
    const revealNodes = document.querySelectorAll('[data-animate]');
    revealNodes.forEach((node) => node.classList.add('is-visible'));

    const token = localStorage.getItem('auth_token');
    if (!token) {
        window.location.replace('/login/?next=/story/create/');
        return;
    }

    const form = document.getElementById('create-story-form');
    const logoutBtn = document.getElementById('creator-logout-btn');
    const titleInput = document.getElementById('story-title');
    const descriptionInput = document.getElementById('story-description');
    const audioInput = document.getElementById('background-audio');
    const sceneEditorLink = document.getElementById('scene-editor-link');
    const rowsContainer = document.getElementById('attribute-rows');
    const addRowBtn = document.getElementById('attribute-add-btn');
    const errorBox = document.getElementById('create-story-error');
    const successBox = document.getElementById('create-story-success');
    const submitBtn = document.getElementById('create-story-submit');
    const loadingText = document.getElementById('create-story-loading');
    const bootstrapNode = document.getElementById('story-form-data');

    if (!form || !titleInput || !descriptionInput || !audioInput || !sceneEditorLink || !rowsContainer || !addRowBtn || !errorBox || !successBox || !submitBtn || !loadingText) {
        return;
    }

    const bootstrapData = bootstrapNode ? JSON.parse(bootstrapNode.textContent) : null;
    const isEditMode = Boolean(bootstrapData?.story_id);
    const submitUrl = isEditMode
        ? `/story/api/${bootstrapData.story_id}/update/`
        : '/story/api/create/';

    if (isEditMode) {
        sceneEditorLink.href = `/story/${bootstrapData.story_id}/scenes/`;
    } else {
        sceneEditorLink.href = '#';
        sceneEditorLink.classList.add('is-disabled');
        sceneEditorLink.textContent = 'Save story first';
        sceneEditorLink.addEventListener('click', (event) => event.preventDefault());
    }

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
        successBox.innerHTML = message;
        successBox.classList.remove('d-none');
        errorBox.classList.add('d-none');
        errorBox.textContent = '';
    };

    const ensureSessionValid = async () => {
        const response = await fetch('/api/auth/profile/', {
            headers: { Authorization: `Token ${token}` },
        });

        if (response.ok) {
            return true;
        }

        localStorage.removeItem('auth_token');
        localStorage.removeItem('auth_user');
        window.location.replace('/login/?next=/story/create/');
        return false;
    };

    const createAttributeRow = (attribute = {}) => {
        const row = document.createElement('div');
        row.className = 'attribute-row';
        row.dataset.attributeRow = 'true';

        row.innerHTML = `
            <input class="attribute-input" data-attribute-key type="text" placeholder="trust" maxlength="50">
            <input class="attribute-input" data-attribute-label type="text" placeholder="Trust" maxlength="100">
            <input class="attribute-input attribute-number" data-attribute-default type="number" step="1" value="0">
            <button class="btn btn-danger attribute-delete-btn p-2" type="button" data-attribute-delete>Delete</button>
        `;

        row.querySelector('[data-attribute-key]').value = attribute.key || '';
        row.querySelector('[data-attribute-label]').value = attribute.label || '';
        row.querySelector('[data-attribute-default]').value = attribute.initial_value ?? attribute.default_value ?? 0;

        row.querySelector('[data-attribute-delete]').addEventListener('click', () => {
            row.remove();
            syncDeleteButtons();
        });

        return row;
    };

    const syncDeleteButtons = () => {
        rowsContainer.querySelectorAll('[data-attribute-row]').forEach((row) => {
            const deleteBtn = row.querySelector('[data-attribute-delete]');
            deleteBtn.disabled = false;
        });
    };

    const addAttributeRow = (attribute = {}) => {
        rowsContainer.appendChild(createAttributeRow(attribute));
        syncDeleteButtons();
    };

    const parseAttributes = () => Array.from(rowsContainer.querySelectorAll('[data-attribute-row]'))
        .map((row) => {
            const key = row.querySelector('[data-attribute-key]').value.trim().toLowerCase().replace(/\s+/g, '_');
            const label = row.querySelector('[data-attribute-label]').value.trim();
            const rawDefault = row.querySelector('[data-attribute-default]').value;
            if (!key && !label && rawDefault === '') {
                return null;
            }

            const parsedDefault = Number.parseInt(rawDefault || '0', 10);
            return {
                key,
                label: label || key.replace(/_/g, ' ').replace(/\b\w/g, (ch) => ch.toUpperCase()),
                initial_value: Number.isNaN(parsedDefault) ? 0 : parsedDefault,
            };
        })
        .filter(Boolean)
        .filter((item) => item.key);

    const hydrateForm = () => {
        if (!bootstrapData) {
            addAttributeRow();
            return;
        }

        titleInput.value = bootstrapData.title || '';
        descriptionInput.value = bootstrapData.description || '';

        const attributes = Array.isArray(bootstrapData.attributes) ? bootstrapData.attributes : [];
        rowsContainer.innerHTML = '';
        if (attributes.length === 0) {
            addAttributeRow();
        } else {
            attributes.forEach((attribute) => addAttributeRow(attribute));
        }
    };

    logoutBtn?.addEventListener('click', async () => {
        try {
            await fetch('/api/auth/logout/', {
                method: 'POST',
                headers: { Authorization: `Token ${token}` },
            });
        } finally {
            localStorage.removeItem('auth_token');
            localStorage.removeItem('auth_user');
            window.location.replace('/login/');
        }
    });

    addRowBtn.addEventListener('click', () => addAttributeRow());

    hydrateForm();

    form.addEventListener('submit', async (event) => {
        event.preventDefault();
        setLoading(true);
        errorBox.classList.add('d-none');
        successBox.classList.add('d-none');

        const validSession = await ensureSessionValid();
        if (!validSession) {
            setLoading(false);
            return;
        }

        try {
            const attributeDefaults = parseAttributes();
            const formData = new FormData();
            formData.append('title', titleInput.value.trim());
            formData.append('description', descriptionInput.value.trim());
            formData.append('attribute_defaults', JSON.stringify(attributeDefaults));

            if (audioInput.files[0]) {
                formData.append('background_audio', audioInput.files[0]);
            }

            const response = await fetch(submitUrl, {
                method: 'POST',
                headers: {
                    Authorization: `Token ${token}`,
                },
                body: formData,
            });

            const data = await response.json();
            if (!response.ok) {
                showError(data?.error || 'Failed to save story.');
                return;
            }

            if (isEditMode) {
                showSuccess('Story updated. Keep editing or return to the list.');
            } else {
                window.location.replace(`/story/${data.id}/scenes/`);
            }
        } catch (error) {
            showError('Request failed. Try again.');
        } finally {
            setLoading(false);
        }
    });
})();
