(() => {
    "use strict";

    function getCsrfToken(form) {
        const tokenInput = form.querySelector('input[name="csrfmiddlewaretoken"]');
        if (tokenInput) return tokenInput.value;

        const cookie = document.cookie.split(";").map(value => value.trim())
            .find(value => value.startsWith("csrftoken="));
        return cookie ? decodeURIComponent(cookie.slice("csrftoken=".length)) : "";
    }

    function extensionOf(filename) {
        const dot = filename.lastIndexOf(".");
        return dot >= 0 ? filename.slice(dot).toLowerCase() : "";
    }

    function expectedMime(kind, extension) {
        const images = {
            ".jpg": "image/jpeg",
            ".jpeg": "image/jpeg",
            ".png": "image/png",
            ".webp": "image/webp",
            ".gif": "image/gif",
        };
        const videos = {
            ".mp4": "video/mp4",
            ".webm": "video/webm",
        };
        return (kind === "video" ? videos : images)[extension] || "";
    }

    function makeStatus(input) {
        const status = document.createElement("p");
        status.className = "direct-upload-status mt-2 text-xs text-[#8a8171]";
        status.setAttribute("role", "status");
        input.insertAdjacentElement("afterend", status);
        return status;
    }

    async function requestUploadToken(form, file, kind, contentType) {
        const endpoint = form.dataset.uploadTokenUrl;
        if (!endpoint) throw new Error("The upload endpoint is missing from this form.");

        const response = await fetch(endpoint, {
            method: "POST",
            credentials: "same-origin",
            headers: {
                "Content-Type": "application/json",
                "X-CSRFToken": getCsrfToken(form),
            },
            body: JSON.stringify({
                filename: file.name,
                size: file.size,
                content_type: contentType,
                kind,
            }),
        });

        const data = await response.json().catch(() => ({}));
        if (!response.ok || !data.token || !data.upload_endpoint || !data.path) {
            throw new Error(data.error || "Your admin session may have expired, or Supabase did not return an upload token. Refresh and try again.");
        }
        return data;
    }

    function uploadWithTus(file, uploadData, contentType, onProgress) {
        if (!window.tus || !window.tus.Upload) {
            return Promise.reject(new Error("The resumable upload library did not load. Refresh and try again."));
        }

        return new Promise((resolve, reject) => {
            const upload = new window.tus.Upload(file, {
                endpoint: uploadData.upload_endpoint,
                headers: {
                    apikey: uploadData.api_key,
                    "x-signature": uploadData.token,
                },
                metadata: {
                    bucketName: uploadData.bucket,
                    objectName: uploadData.path,
                    contentType,
                    cacheControl: "3600",
                },
                chunkSize: 6 * 1024 * 1024,
                uploadDataDuringCreation: true,
                removeFingerprintOnSuccess: true,
                retryDelays: [0, 3000, 5000, 10000, 20000],
                onError(error) {
                    reject(error);
                },
                onProgress(bytesUploaded, bytesTotal) {
                    const percentage = Math.min(100, Math.round((bytesUploaded / bytesTotal) * 100));
                    onProgress(percentage);
                },
                onSuccess() {
                    resolve();
                },
            });

            upload.start();
        });
    }

    function setupUploadInput(input, form) {
        const status = makeStatus(input);
        const hiddenName = input.name.replace(/_upload$/, "");
        const hiddenPath = form.elements.namedItem(hiddenName);

        if (!hiddenPath || !("value" in hiddenPath)) {
            status.textContent = "Upload field is not connected to its saved path. Please contact the site developer.";
            status.classList.add("text-red-700");
            input.disabled = true;
            return;
        }

        input.addEventListener("change", async () => {
            const file = input.files && input.files[0];
            if (!file) return;

            const kind = input.dataset.mediaKind || "image";
            const extension = extensionOf(file.name);
            const contentType = expectedMime(kind, extension);
            const maxBytes = Number(input.dataset.maxBytes || 0);

            if (!contentType) {
                status.textContent = kind === "video"
                    ? "Choose an MP4 or WebM video."
                    : "Choose a JPG, PNG, WEBP or GIF image.";
                status.classList.add("text-red-700");
                input.value = "";
                return;
            }

            if (file.type && file.type !== contentType && file.type !== "application/octet-stream") {
                status.textContent = "The selected file type does not match its extension.";
                status.classList.add("text-red-700");
                input.value = "";
                return;
            }

            if (maxBytes && file.size > maxBytes) {
                status.textContent = `This file is too large. Maximum size: ${Math.round(maxBytes / (1024 * 1024))} MB.`;
                status.classList.add("text-red-700");
                input.value = "";
                return;
            }

            input.dataset.uploading = "true";
            input.disabled = true;
            status.classList.remove("text-red-700", "text-green-700");
            status.textContent = "Preparing secure upload...";

            try {
                const uploadData = await requestUploadToken(form, file, kind, contentType);
                status.textContent = "Uploading: 0%";

                await uploadWithTus(file, uploadData, contentType, percentage => {
                    status.textContent = `Uploading: ${percentage}%`;
                });

                // The hidden model field receives only the Supabase object key.
                hiddenPath.value = uploadData.path;
                input.value = ""; // Never let the original file be posted to Django/Vercel.
                status.textContent = "Upload complete. Save this form to finish.";
                status.classList.add("text-green-700");
            } catch (error) {
                console.error("Supabase direct upload failed:", error);
                status.textContent = error.message || "Upload failed. Please try again.";
                status.classList.add("text-red-700");
                input.value = "";
            } finally {
                input.dataset.uploading = "false";
                input.disabled = false;
            }
        });
    }

    document.addEventListener("DOMContentLoaded", () => {
        document.querySelectorAll("form[data-upload-token-url]").forEach(form => {
            const uploadInputs = [...form.querySelectorAll('input[type="file"][name$="_upload"]')];
            uploadInputs.forEach(input => setupUploadInput(input, form));

            form.addEventListener("submit", event => {
                const unfinished = uploadInputs.some(input =>
                    input.dataset.uploading === "true" || (input.files && input.files.length > 0)
                );
                if (unfinished) {
                    event.preventDefault();
                    window.alert("Please wait for each media upload to finish before saving. If an upload failed, select the file again and retry.");
                }
            });
        });
    });
})();
