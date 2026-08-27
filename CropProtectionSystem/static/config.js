// ============================================================
// API Configuration
// ============================================================

// Production Render Flask Backend API URL
let API_BASE_URL = "https://crop-protection-system.onrender.com";

// Support dynamic fallback to current origin for local running/testing
if (window.location.hostname === "localhost" || window.location.hostname === "127.0.0.1") {
    if (window.location.port === "5000") {
        API_BASE_URL = window.location.origin;
    } else {
        API_BASE_URL = "http://localhost:5000";
    }
}
