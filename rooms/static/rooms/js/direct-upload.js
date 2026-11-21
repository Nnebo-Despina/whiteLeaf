
document.addEventListener("DOMContentLoaded", () => {
    const uploadInputs = document.querySelectorAll(
        ".direct-video-upload"
    );

    uploadInputs.forEach((input) => {
        const formRow = input.closest("tr") ||
            input.closest(".form-row") ||
            input.parentElement.parentElement;

        const hiddenVideo = formRow.querySelector(
            'input[type="hidden"][name$="-video"]'
        );

        if (!hiddenVideo) {
            console.error("Could not locate the video path field.");
            return;
        }

        const status = document.createElement("p");
        status.className = "video-upload-status";
        status.style.marginTop = "8px";

        input.insertAdjacentElement("afterend", status);

        let uploading = false;

        input.addEventListener("change", async () => {
            const file = input.files[0];

            if (!file) return;

            if (!file.name.toLowerCase().endsWith(".mp4")) {
                status.textContent = "Please select an MP4 video.";
                input.value = "";
                return;
            }

            if (file.size > 500 * 1024 * 1024) {
                status.textContent = "Maximum video size is 500 MB.";
                input.value = "";
                return;
            }

            if (file.type && file.type !== "video/mp4") {
                status.textContent = "Invalid video format.";
                input.value = "";
                return;
            }

            uploading = true;
            input.disabled = true;

            status.textContent = "Preparing upload...";

            try {
                // Step 1: Request a temporary signed upload URL.
                const tokenResponse = await fetch(
                    "/accommodations/video-upload-token/",
                    {
                        method: "POST",
                        credentials: "same-origin",
                        headers: {
                            "Content-Type": "application/json",
                            "X-CSRFToken": getCookie("csrftoken"),
                        },
                        body: JSON.stringify({
                            filename: file.name,
                            size: file.size,
                            content_type: file.type || "video/mp4",
                        }),
                    }
                );

                const uploadData = await tokenResponse.json();

                if (!tokenResponse.ok) {
                    throw new Error(
                        uploadData.error || "Could not prepare upload."
                    );
                }

                // Step 2: Upload directly to Supabase.
                status.textContent = "Uploading video: 0%";

                await uploadDirectly(
                    uploadData.upload_url,
                    uploadData.api_key,
                    file,
                    (percentage) => {
                        status.textContent =
                            `Uploading video: ${percentage}%`;
                    }
                );

                // Step 3: Store the returned object path.
                hiddenVideo.value = uploadData.path;

                // Prevent Django from receiving the video file.
                input.value = "";

                status.textContent =
                    "Video uploaded successfully. Save the room to finish.";

                status.style.color = "green";

            } catch (error) {
                console.error("Video upload failed:", error);

                status.textContent =
                    error.message || "Video upload failed.";

                status.style.color = "red";

            } finally {
                uploading = false;
                input.disabled = false;
            }
        });

        // Prevent accidental form submission during an upload.
        const form = input.closest("form");

        if (form) {
            form.addEventListener("submit", (event) => {
                if (uploading) {
                    event.preventDefault();

                    alert(
                        "Please wait until the video upload finishes."
                    );
                }
            });
        }
    });
});


function getCookie(name) {
    const cookies = document.cookie.split(";");

    for (const cookie of cookies) {
        const trimmed = cookie.trim();

        if (trimmed.startsWith(name + "=")) {
            return decodeURIComponent(
                trimmed.substring(name.length + 1)
            );
        }
    }

    return "";
}


// XMLHttpRequest allows us to track upload progress.
function uploadDirectly(url, apiKey, file, onProgress) {
    return new Promise((resolve, reject) => {
        const xhr = new XMLHttpRequest();

        xhr.open("PUT", url, true);

        xhr.setRequestHeader("apikey", apiKey);
        xhr.setRequestHeader("Content-Type", "video/mp4");
        xhr.setRequestHeader("x-upsert", "false");

        xhr.upload.addEventListener("progress", (event) => {
            if (event.lengthComputable) {
                const percentage = Math.round(
                    (event.loaded / event.total) * 100
                );

                onProgress(percentage);
            }
        });

        xhr.onload = () => {
            if (xhr.status >= 200 && xhr.status < 300) {
                resolve();
            } else {
                reject(
                    new Error(
                        "Supabase upload failed: " + xhr.responseText
                    )
                );
            }
        };

        xhr.onerror = () => {
            reject(new Error("Network error during video upload."));
        };

        xhr.onabort = () => {
            reject(new Error("Video upload was cancelled."));
        };

        xhr.send(file);
    });
}
