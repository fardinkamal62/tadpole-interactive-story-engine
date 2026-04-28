const storyStage = document.getElementById("story-stage");
const storyTitle = document.getElementById("story-title");
const storyContent = document.getElementById("story-content");
const storyChoices = document.getElementById("story-choices");
const storyAttributes = document.getElementById("story-attributes");
const storyError = document.getElementById("story-error");
const storyEnding = document.getElementById("story-ending");
const storyEndingText = document.getElementById("story-ending-text");
const storyRestart = document.getElementById("story-restart");
const storyIdLabel = document.getElementById("story-id");
const sceneIdLabel = document.getElementById("scene-id");
const storyName = document.getElementById("story-name");
const storyDescription = document.getElementById("story-description");
const storyLoader = document.getElementById("story-loader");
const storyAudio = document.getElementById("story-audio");
const storyAudioControl = document.getElementById("story-audio-control");
const storyAudioControls = document.getElementById("story-audio-controls");
const storyAudioEmpty = document.getElementById("story-audio-empty");
const storyAudioToggle = document.getElementById("story-audio-toggle");
const storyAudioVolume = document.getElementById("story-audio-volume");
const storyAudioStatus = document.getElementById("story-audio-status");
const storyFullscreenToggle = document.getElementById("story-fullscreen-toggle");
const storyInfoControl = document.getElementById("story-info-control");
const storyInfoToggle = document.getElementById("story-info-toggle");

let csrfToken = "";
let activeStoryId = null;
let activeStoryMeta = null;
let audioReady = false;

const isFullscreenSupported = !!(document.fullscreenEnabled && storyStage?.requestFullscreen);

const isStageFullscreen = () => document.fullscreenElement === storyStage;

const syncFullscreenButton = () => {
    if (!storyFullscreenToggle) {
        return;
    }

    const active = isStageFullscreen();
    storyFullscreenToggle.classList.toggle("is-fullscreen", active);
    storyFullscreenToggle.setAttribute("aria-label", active ? "Exit fullscreen" : "Enter fullscreen");
    storyFullscreenToggle.setAttribute("aria-pressed", active ? "true" : "false");
};

const toggleFullscreen = async () => {
    if (!isFullscreenSupported || !storyStage) {
        return;
    }

    try {
        if (isStageFullscreen()) {
            await document.exitFullscreen();
            return;
        }
        await storyStage.requestFullscreen();
    } catch (error) {
        // Ignore permission/user gesture errors and keep current mode.
    }
};

const animateInView = () => {
    const animatedNodes = document.querySelectorAll("[data-animate]");
    if (!animatedNodes.length) {
        return;
    }

    if (window.matchMedia("(prefers-reduced-motion: reduce)").matches || !("IntersectionObserver" in window)) {
        animatedNodes.forEach((node) => node.classList.add("is-visible"));
        return;
    }

    const observer = new IntersectionObserver((entries) => {
        entries.forEach((entry) => {
            if (entry.isIntersecting) {
                entry.target.classList.add("is-visible");
                observer.unobserve(entry.target);
            }
        });
    }, { threshold: 0.12 });

    animatedNodes.forEach((node) => observer.observe(node));
};

const getStoryIdFromQuery = () => {
    const pathMatch = window.location.pathname.match(/\/story\/(\d+)\/?/);
    if (pathMatch) {
        return pathMatch[1];
    }
    const params = new URLSearchParams(window.location.search);
    const storyId = params.get("story_id");
    return storyId || "1";
};

const setStageBackground = (imageUrl) => {
    if (imageUrl) {
        storyStage.style.backgroundImage = `url("${imageUrl}")`;
        return;
    }
    storyStage.style.backgroundImage = "none";
};

const setStoryMeta = (story) => {
    if (!story) {
        return;
    }
    activeStoryMeta = story;
    storyName.textContent = story.title || "Story";
    document.title = `${story.title || "Story"} | Tadpole`;
    window.title = document.title;
    if (story.description) {
        storyDescription.textContent = story.description;
        storyDescription.hidden = false;
    } else {
        storyDescription.textContent = "";
        storyDescription.hidden = true;
    }
};

const setLoading = (isLoading) => {
    storyLoader.hidden = !isLoading;
    storyStage.classList.toggle("is-loading", isLoading);
    storyChoices.querySelectorAll("button").forEach((button) => {
        const isAvailable = button.dataset.available === "1";
        button.disabled = isLoading || !isAvailable;
    });
};

const updateAudioStatus = () => {
    if (!storyAudioStatus || !storyAudioToggle) {
        return;
    }

    storyAudioToggle.classList.toggle("is-muted", storyAudio.muted || storyAudio.volume === 0);
    storyAudioToggle.setAttribute("aria-label", storyAudio.muted || storyAudio.volume === 0 ? "Unmute" : "Mute");

    if (storyAudio.muted || storyAudio.volume === 0) {
        storyAudioStatus.textContent = "Muted";
        return;
    }
    storyAudioStatus.textContent = `Volume ${Math.round(storyAudio.volume * 100)}%`;
};

const applyVolume = () => {
    if (!storyAudioVolume || !storyAudioToggle) {
        return;
    }

    const volumeValue = Number(storyAudioVolume.value) / 100;
    storyAudio.volume = volumeValue;
    if (volumeValue > 0 && storyAudio.muted) {
        storyAudio.muted = false;
    }
    updateAudioStatus();
};

const setAudioControlsVisible = (visible) => {
    if (storyAudioControls) {
        storyAudioControls.hidden = !visible;
    }
    if (storyAudioEmpty) {
        storyAudioEmpty.hidden = visible;
    }
    if (storyAudioControl) {
        storyAudioControl.classList.toggle("is-disabled", !visible);
        if (!visible) {
            storyAudioControl.classList.remove("is-open");
        }
    }
    if (storyAudioToggle) {
        storyAudioToggle.disabled = !visible;
    }
};

const attemptPlayAudio = () => {
    if (!storyAudio.src) {
        return;
    }
    storyAudio.play().catch(() => {
        // Autoplay might be blocked until user interacts.
    });
};

const setStoryAudio = (story) => {
    if (!story || !story.background_music_url) {
        storyAudio.pause();
        storyAudio.removeAttribute("src");
        storyAudio.load();
        setAudioControlsVisible(false);
        audioReady = false;
        return;
    }

    if (storyAudio.src !== story.background_music_url) {
        storyAudio.src = story.background_music_url;
        storyAudio.loop = true;
        audioReady = true;
    }
    setAudioControlsVisible(true);
    applyVolume();
    attemptPlayAudio();
};

const setError = (message) => {
    if (!message) {
        storyError.hidden = true;
        storyError.textContent = "";
        return;
    }
    storyError.hidden = false;
    storyError.textContent = message;
};

const renderAttributes = (attributes) => {
    storyAttributes.innerHTML = "";
    if (!attributes.length) {
        const row = document.createElement("div");
        row.className = "attribute-row";
        row.innerHTML = "<span>No tracked attributes</span><strong>-</strong>";
        storyAttributes.appendChild(row);
        return;
    }

    attributes.forEach((attribute) => {
        const row = document.createElement("div");
        row.className = "attribute-row";
        row.innerHTML = `<span>${attribute.label}</span><strong>${attribute.value}</strong>`;
        storyAttributes.appendChild(row);
    });
};

const renderChoices = (choices) => {
    storyChoices.innerHTML = "";
    choices.forEach((choice) => {
        const button = document.createElement("button");
        button.type = "button";
        button.className = "story-choice";
        button.textContent = choice.text;
        button.dataset.available = choice.available ? "1" : "0";
        button.disabled = !choice.available;
        button.style.animationDelay = `${Math.min(storyChoices.children.length * 60, 220)}ms`;
        button.addEventListener("click", () => handleChoice(choice.id));
        storyChoices.appendChild(button);
    });
};

const renderScene = (payload) => {
    const scene = payload.scene;
    storyStage.classList.remove("scene-swap");
    void storyStage.offsetWidth;
    storyStage.classList.add("scene-swap");
    setStoryMeta(payload.story || activeStoryMeta);
    setStoryAudio(payload.story || activeStoryMeta);
    storyTitle.textContent = scene.title || "Scene";
    storyContent.textContent = scene.content || "";
    storyEnding.hidden = true;
    renderChoices(scene.choices || []);
    renderAttributes(payload.attributes || []);
    setStageBackground(scene.background_image_url);
    storyIdLabel.textContent = activeStoryId || "-";
    sceneIdLabel.textContent = scene.id || "-";
};

const renderEnding = (payload) => {
    storyStage.classList.remove("scene-swap");
    void storyStage.offsetWidth;
    storyStage.classList.add("scene-swap");
    setStoryMeta(payload.story || activeStoryMeta);
    setStoryAudio(payload.story || activeStoryMeta);

    const scene = payload.scene || {};
    if (scene.title) storyTitle.textContent = scene.title;
    if (scene.content) storyContent.textContent = scene.content;
    setStageBackground(scene.background_image_url);
    if (scene.id) sceneIdLabel.textContent = scene.id;

    storyEnding.hidden = false;
    storyChoices.innerHTML = "";
    storyEndingText.textContent = payload.message || "The story concludes here.";
    renderAttributes(payload.final_attributes || []);
};

const startStory = async () => {
    setError("");
    activeStoryId = getStoryIdFromQuery();
    try {
        const response = await fetch(`/story/api/start/?story_id=${activeStoryId}`, {
            credentials: "same-origin",
        });
        const payload = await response.json();
        if (!response.ok) {
            setError(payload.error || "Failed to start the story.");
            return;
        }
        csrfToken = payload.csrf_token || "";
        renderScene(payload);
    } catch (error) {
        setError("Network error while starting the story.");
    }
};

const handleChoice = async (choiceId) => {
    setError("");
    setLoading(true);
    if (audioReady) {
        attemptPlayAudio();
    }
    try {
        const response = await fetch("/story/api/choice/", {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
                "X-CSRFToken": csrfToken,
            },
            credentials: "same-origin",
            body: JSON.stringify({
                choice_id: choiceId,
                story_id: activeStoryId,
            }),
        });
        const payload = await response.json();
        if (!response.ok) {
            setError(payload.error || "Failed to apply choice.");
            return;
        }
        if (payload.ending) {
            renderEnding(payload);
            return;
        }
        csrfToken = payload.csrf_token || csrfToken;
        renderScene(payload);
    } catch (error) {
        setError("Network error while applying choice.");
    } finally {
        setLoading(false);
    }
};

if (storyRestart) {
    storyRestart.addEventListener("click", () => startStory());
}

if (storyAudioToggle) {
    storyAudioToggle.addEventListener("click", () => {
        if (!audioReady) {
            return;
        }
        storyAudio.muted = !storyAudio.muted;
        updateAudioStatus();
        if (!storyAudio.muted) {
            attemptPlayAudio();
        }
    });
}

if (storyAudioVolume) {
    storyAudioVolume.addEventListener("input", applyVolume);
}

if (storyFullscreenToggle) {
    if (!isFullscreenSupported) {
        storyFullscreenToggle.classList.add("is-hidden");
    } else {
        syncFullscreenButton();
        storyFullscreenToggle.addEventListener("click", toggleFullscreen);
        document.addEventListener("fullscreenchange", syncFullscreenButton);
    }
}

if (storyInfoControl && storyInfoToggle) {
    storyInfoToggle.addEventListener("click", () => {
        const isOpen = storyInfoControl.classList.toggle("is-open");
        storyInfoToggle.setAttribute("aria-expanded", isOpen ? "true" : "false");
    });

    document.addEventListener("click", (event) => {
        if (!storyInfoControl.contains(event.target)) {
            storyInfoControl.classList.remove("is-open");
            storyInfoToggle.setAttribute("aria-expanded", "false");
        }
    });

    document.addEventListener("keydown", (event) => {
        if (event.key === "Escape") {
            storyInfoControl.classList.remove("is-open");
            storyInfoToggle.setAttribute("aria-expanded", "false");
        }
    });
}

animateInView();
startStory();
