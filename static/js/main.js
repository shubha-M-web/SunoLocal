/**
 * SunoLocal - Main Application JavaScript
 * Handles Bookmark toggles, dynamic search interactions, and tooltips.
 */

document.addEventListener("DOMContentLoaded", () => {
  // Initialize Bootstrap Tooltips
  const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
  tooltipTriggerList.map(function (tooltipTriggerEl) {
    return new bootstrap.Tooltip(tooltipTriggerEl);
  });

  // Bookmark / Save Button AJAX Handler
  document.querySelectorAll(".btn-bookmark-toggle").forEach(btn => {
    btn.addEventListener("click", async (e) => {
      e.preventDefault();
      const oppId = btn.getAttribute("data-id");
      if (!oppId) return;

      btn.disabled = true;

      try {
        const response = await fetch(`/api/save/${oppId}`, {
          method: "POST",
          headers: {
            "Content-Type": "application/json"
          }
        });
        const data = await response.json();

        if (data.success) {
          if (data.saved) {
            btn.classList.add("saved");
            btn.innerHTML = '<i class="bi bi-bookmark-fill me-1"></i> Saved';
            showToast("Saved to your bookmarks!", "success");
          } else {
            btn.classList.remove("saved");
            btn.innerHTML = '<i class="bi bi-bookmark me-1"></i> Save';
            showToast("Removed from your bookmarks.", "info");
          }

          // Update header saved counter if present
          const navCounter = document.getElementById("nav-saved-count");
          if (navCounter) {
            navCounter.textContent = data.count;
            navCounter.style.display = data.count > 0 ? "inline-block" : "none";
          }
        }
      } catch (err) {
        console.error("Failed to toggle save state:", err);
      } finally {
        btn.disabled = false;
      }
    });
  });
});

// Helper for lightweight toast notification
function showToast(message, type = "success") {
  let toastContainer = document.getElementById("toast-notification-container");
  if (!toastContainer) {
    toastContainer = document.createElement("div");
    toastContainer.id = "toast-notification-container";
    toastContainer.style.position = "fixed";
    toastContainer.style.top = "1.5rem";
    toastContainer.style.right = "1.5rem";
    toastContainer.style.zIndex = "1090";
    document.body.appendChild(toastContainer);
  }

  const toast = document.createElement("div");
  const bgClass = type === "success" ? "bg-success text-white" : "bg-dark text-white";
  toast.className = `toast align-items-center ${bgClass} border-0 show mb-2`;
  toast.setAttribute("role", "alert");
  toast.setAttribute("aria-live", "assertive");
  toast.setAttribute("aria-atomic", "true");
  toast.innerHTML = `
    <div class="d-flex">
      <div class="toast-body d-flex align-items-center gap-2">
        <i class="bi bi-check-circle-fill"></i>
        <span>${message}</span>
      </div>
      <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast" aria-label="Close"></button>
    </div>
  `;

  toastContainer.appendChild(toast);
  setTimeout(() => {
    toast.remove();
  }, 3500);
}
