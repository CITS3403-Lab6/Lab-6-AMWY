function getCsrfToken() {
    const tokenMeta = document.querySelector('meta[name="csrf-token"]');
    if (tokenMeta) {
        return tokenMeta.getAttribute("content");
    }

    const tokenInput = document.querySelector('input[name="csrf_token"]');
    if (tokenInput) {
        return tokenInput.value;
    }

    return "";
}

window.getCsrfToken = getCsrfToken;

const originalFetch = window.fetch;
window.fetch = function(resource, options = {}) {
    const method = (options.method || "GET").toUpperCase();

    if (!["GET", "HEAD", "OPTIONS", "TRACE"].includes(method)) {
        const headers = new Headers(options.headers || {});
        const token = getCsrfToken();

        if (token && !headers.has("X-CSRFToken")) {
            headers.set("X-CSRFToken", token);
        }

        options.headers = headers;
    }

    return originalFetch(resource, options);
};

if (window.jQuery) {
    window.jQuery.ajaxSetup({
        beforeSend: function(xhr, settings) {
            const method = (settings.type || "GET").toUpperCase();

            if (!["GET", "HEAD", "OPTIONS", "TRACE"].includes(method)) {
                const token = getCsrfToken();

                if (token) {
                    xhr.setRequestHeader("X-CSRFToken", token);
                }
            }
        }
    });
}
