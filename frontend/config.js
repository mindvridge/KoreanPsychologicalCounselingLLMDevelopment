/**
 * Configuration for Korean Mental Health Counseling Frontend
 */

const CONFIG = {
    // API Base URL
    API_BASE_URL: window.location.hostname === 'localhost'
        ? 'http://localhost:8000/api/v1'
        : '/api/v1',

    // Voice API Base URL
    VOICE_API_BASE_URL: window.location.hostname === 'localhost'
        ? 'http://localhost:8001/api/v1'
        : '/voice-api/v1',

    // WebSocket URL for Voice
    VOICE_WS_URL: window.location.hostname === 'localhost'
        ? 'ws://localhost:8001'
        : `${window.location.protocol === 'https:' ? 'wss:' : 'ws:'}//${window.location.host}/voice-ws`,

    // API Key (if required - should be configured on backend or use auth)
    API_KEY: null, // Set if backend requires API key

    // Default Settings
    DEFAULT_TOP_K: 3,

    // Voice Settings
    VOICE: {
        SAMPLE_RATE: 16000,
        BUFFER_SIZE: 4096,
        SILENCE_THRESHOLD: 0.01,
        SILENCE_DURATION: 1500, // ms
        VAD_ENABLED: true,
        DEFAULT_VISUALIZER: 'waveform',
        DEFAULT_VOICE_PROFILE: 'calm_counselor'
    },

    // Session Storage Keys
    STORAGE_KEYS: {
        USER_ID: 'maum_user_id',
        CURRENT_SESSION: 'maum_current_session',
        SELECTED_COUNSELOR: 'maum_selected_counselor',
        CHAT_HISTORY: 'maum_chat_history',
        CONSENT_DATA: 'maum_consent_data'
    },

    // Avatar Mapping
    AVATARS: {
        'warm_mother': '👩‍⚕️',
        'clinical_professional': '👨‍⚕️',
        'friendly_peer': '👦',
        'calm_veteran': '👴',
        'energetic_positive': '👧',
        'cbt_specialist': '🧑‍⚕️',
        'teen_specialist': '👩‍🏫',
        'workplace_specialist': '👨‍💼',
        'couple_therapist': '💑',
        'addiction_specialist': '🧑‍⚕️',
        'trauma_specialist': '👨‍⚕️',
        'eating_disorder_specialist': '👩‍⚕️',
        'elderly_counselor': '👵',
        'lgbtq_friendly': '🏳️‍🌈',
        'multicultural_counselor': '🌍',
        'bullying_specialist': '👮',
        'career_coach': '💼',
        'anger_management_specialist': '🧘'
    },

    // Default Avatar
    DEFAULT_AVATAR: '👨‍⚕️',

    // Toast Duration
    TOAST_DURATION: 3000,

    // Chat Settings
    CHAT_AUTO_SCROLL: true,
    CHAT_TYPING_INDICATOR_DELAY: 500
};

// Helper functions
const StorageHelper = {
    get(key) {
        try {
            const value = localStorage.getItem(key);
            return value ? JSON.parse(value) : null;
        } catch (e) {
            console.error('Error reading from localStorage:', e);
            return null;
        }
    },

    set(key, value) {
        try {
            localStorage.setItem(key, JSON.stringify(value));
        } catch (e) {
            console.error('Error writing to localStorage:', e);
        }
    },

    remove(key) {
        try {
            localStorage.removeItem(key);
        } catch (e) {
            console.error('Error removing from localStorage:', e);
        }
    },

    clear() {
        try {
            localStorage.clear();
        } catch (e) {
            console.error('Error clearing localStorage:', e);
        }
    }
};

// Export for use in app.js
window.CONFIG = CONFIG;
window.StorageHelper = StorageHelper;
