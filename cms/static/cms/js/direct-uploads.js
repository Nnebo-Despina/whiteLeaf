/*
 * Direct-to-Supabase uploads, shared by the /manage/ dashboard and the Django admin (backstage).
 *
 * The browser sends the file straight to Supabase (signed upload URL). Django/Vercel only ever
 * receive the saved object path, so the Vercel 4.5 MB request limit can never be hit.
 *
 * Works through event delegation, so rows added later (e.g. "Add another Room image" in the
 * admin) are handled automatically.
 */
(() => {
    "use strict";

    const SELECTOR = 'input[type="file"][data-upload-target]';

    const IMAGES = { ".jpg": "image/jpeg", ".jpeg": "image/jpeg", ".png": "image/png", ".webp": "image/webp", ".gif": "image/gif" };
    const VIDEOS = { ".mp4": "video/mp4", ".webm": "video/webm" };

    function csrfToken(form) {
        const field = form.querySelector('input[name="csrfmiddlewaretoken"]');
        if (field) return field.value;
        const cookie = document.cookie.split(";").map(v => v.trim()).find(v => v.startsWith("csrftoken="));
        return cookie ? decodeURIComponent(cookie.slice("csrftoken=".length)) : "";
    }

    function extensionOf(name) {
        const dot = name.lastIndexOf(".");
        return dot >= 0 ? name.slice(dot).toLowerCase() : "";
    }

    function statusFor(input) {
        if (!input._uploadStatus) {
            const p = document.createElement("p");
            p.className = "direct-upload-status";
            p.style.cssText = "margin-top:8px;font-size:12px;color:#8a8171";
            p.setAttribute("role", "status");
            input.insertAdjacentElement("afterend", p);
            input._uploadStatus = p;
        }
        return input._uploadStatus;
    }

    function say(input, message, state) {
        const p = statusFor(input);
        p.textContent = message;
        p.style.color = state === "error" ? "#b3261e" : state === "ok" ? "#2e7d32" : "#8a8171";
    }

    function tokenUrlFor(input, form) {
        return input.dataset.uploadTokenUrl || form.dataset.uploadTokenUrl || "";
    }

    async function requestToken(input, form, file, contentType) {
        const endpoint = tokenUrlFor(input, form);
        if (!endpoint) throw new Error("The upload endpoint is missing from this form.");

        const response = await fetch(endpoint, {
            method: "POST",
            credentials: "same-origin",
            headers: { "Content-Type": "application/json", "X-CSRFToken": csrfToken(form) },
            body: JSON.stringify({
                target: input.dataset.uploadTarget,
                filename: file.name,
                size: file.size,
                content_type: contentType,
            }),
        });

        const data = await response.json().catch(() => ({}));
        if (!response.ok || !data.token || !data.upload_endpoint || !data.path) {
            throw new Error(data.error || `Could not start the upload (server returned ${response.status}). Check the Vercel runtime logs for the error.`);
        }
        return data;
    }

    // Same request supabase-js makes for uploadToSignedUrl(): PUT multipart form to the signed URL.
    function signedUpload(file, info, onProgress) {
        return new Promise((resolve, reject) => {
            const body = new FormData();
            body.append("cacheControl", "3600");
            body.append("", file);

            const xhr = new XMLHttpRequest();
            xhr.open("PUT", info.signed_upload_url);
            if (info.api_key) {
                xhr.setRequestHeader("apikey", info.api_key);
                if (info.api_key.split(".").length === 3) xhr.setRequestHeader("Authorization", `Bearer ${info.api_key}`);
            }
            xhr.upload.onprogress = e => {
                if (e.lengthComputable) onProgress(Math.min(100, Math.round((e.loaded / e.total) * 100)));
            };
            xhr.onload = () => {
                if (xhr.status >= 200 && xhr.status < 300) return resolve();
                let detail = (xhr.responseText || "").slice(0, 200);
                if (xhr.status === 413) detail += " The file is bigger than your Supabase upload limit.";
                reject(new Error(`Supabase said ${xhr.status}: ${detail}`));
            };
            xhr.onerror = () => reject(new Error("Network error while sending the file to Supabase. Check your connection and try again."));
            xhr.send(body);
        });
    }

    function describeError(error) {
        let detail = "";
        try {
            const res = error.originalResponse;
            if (res) {
                const code = res.getStatus();
                detail = ` (Supabase said ${code}: ${(res.getBody() || "").slice(0, 160)})`;
                if (code === 413) detail += " The file is bigger than your Supabase upload limit.";
            }
        } catch (e) { /* ignore */ }
        return (error.message || "Upload failed.") + detail;
    }

    async function handleChange(input) {
        const form = input.closest("form");
        const file = input.files && input.files[0];
        if (!form || !file) return;

        // The saved object path lives in a hidden field with the same name minus "_upload".
        const pathField = form.elements.namedItem(input.name.replace(/_upload$/, ""));
        if (!pathField || !("value" in pathField)) {
            say(input, "This upload box is not connected to its path field. Please tell the developer.", "error");
            input.value = "";
            return;
        }

        const kind = input.dataset.mediaKind === "video" ? "video" : "image";
        const contentType = (kind === "video" ? VIDEOS : IMAGES)[extensionOf(file.name)];
        const maxBytes = Number(input.dataset.maxBytes || 0);

        if (!contentType) {
            say(input, kind === "video" ? "Choose an MP4 or WebM video." : "Choose a JPG, PNG, WEBP or GIF image.", "error");
            input.value = "";
            return;
        }
        if (maxBytes && file.size > maxBytes) {
            say(input, `This file is too large. Maximum size: ${Math.round(maxBytes / 1048576)} MB.`, "error");
            input.value = "";
            return;
        }

        input.dataset.uploading = "true";
        input.disabled = true;
        say(input, "Preparing upload...");
        try {
            const info = await requestToken(input, form, file, contentType);
            say(input, "Uploading: 0%");
            await signedUpload(file, info, pct => say(input, `Uploading: ${pct}%`));
            pathField.value = info.path;
            input.value = ""; // the file itself is never posted to Django
            say(input, "Upload complete. Click Save to finish.", "ok");
        } catch (error) {
            console.error("Direct upload failed:", error);
            say(input, describeError(error), "error");
            input.value = "";
        } finally {
            input.dataset.uploading = "false";
            input.disabled = false;
        }
    }

    document.addEventListener("change", event => {
        const input = event.target;
        if (input && input.matches && input.matches(SELECTOR)) handleChange(input);
    });

    // Block saving while an upload is running; never let a raw file ride along with the form.
    document.addEventListener("submit", event => {
        const form = event.target;
        if (!form || !form.querySelectorAll) return;
        const inputs = [...form.querySelectorAll(SELECTOR)];
        if (inputs.some(i => i.dataset.uploading === "true")) {
            event.preventDefault();
            window.alert("Please wait for the upload to finish, then save.");
        }
    }, true);

    // Forms that only contain direct-upload file boxes never need multipart encoding.
    document.addEventListener("DOMContentLoaded", () => {
        document.querySelectorAll("form").forEach(form => {
            const files = [...form.querySelectorAll('input[type="file"]')];
            if (files.length && files.every(f => f.matches(SELECTOR))) {
                form.enctype = "application/x-www-form-urlencoded";
            }
        });
    });
})();