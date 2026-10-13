// ==============================================================================
// MULTI-LEVEL BUDGET TRACKER ANALYTICS — AUTHENTICATION & SESSION MANAGER
// ==============================================================================

const Auth = {
  STORAGE_KEY: "budget_tracker_user",

  getUser() {
    try {
      const data = localStorage.getItem(this.STORAGE_KEY);
      return data ? JSON.parse(data) : null;
    } catch (e) {
      return null;
    }
  },

  setUser(user) {
    localStorage.setItem(this.STORAGE_KEY, JSON.stringify(user));
  },

  logout() {
    localStorage.removeItem(this.STORAGE_KEY);
    window.location.href = "/login";
  },

  isAuthenticated() {
    return !!this.getUser();
  },

  requireAuth() {
    const user = this.getUser();
    const currentPath = window.location.pathname;
    const isAuthPage = currentPath === "/" || currentPath === "/login";

    if (!user && !isAuthPage) {
      window.location.href = "/login";
      return false;
    }
    return true;
  },

  renderUserBadge() {
    const container = document.getElementById("header-user-container");
    if (!container) return;

    const user = this.getUser();
    if (!user) {
      container.innerHTML = `
        <a href="/login" class="btn btn-outline btn-sm" style="color: #FFFFFF; border-color: rgba(255,255,255,0.4);">
          🔑 Sign In
        </a>
      `;
      return;
    }

    const initials = user.full_name
      ? user.full_name.split(" ").map(w => w[0]).slice(0, 2).join("").toUpperCase()
      : user.username.slice(0, 2).toUpperCase();

    container.innerHTML = `
      <div class="user-profile-badge">
        <div class="user-avatar-circle">${initials}</div>
        <div class="user-meta">
          <div class="user-name">${this.escapeHtml(user.full_name || user.username)}</div>
          <div class="user-role-pill">${this.escapeHtml(user.role || 'Analyst')}</div>
        </div>
        <button type="button" class="btn-logout" title="Sign out" onclick="Auth.logout()">
          Sign Out
        </button>
      </div>
    `;
  },

  escapeHtml(str) {
    if (!str) return "";
    return String(str)
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;")
      .replace(/'/g, "&#039;");
  }
};

// Global sync button listener
document.addEventListener("DOMContentLoaded", () => {
  const syncBtn = document.getElementById("btn-global-export-pbi");
  if (syncBtn) {
    syncBtn.addEventListener("click", async () => {
      try {
        syncBtn.disabled = true;
        syncBtn.innerText = "⏳ Syncing...";
        const res = await api.exportAllPowerBICSVs();
        if (typeof App !== "undefined" && App.showToast) {
          App.showToast(res.message || "Power BI datasets synchronized successfully!", "success");
        } else {
          alert(res.message || "Power BI datasets synchronized successfully!");
        }
      } catch (err) {
        alert("Error syncing CSVs: " + err.message);
      } finally {
        syncBtn.disabled = false;
        syncBtn.innerText = "⚡ Sync Power BI CSVs";
      }
    });
  }

  // Render header badge if element exists
  Auth.renderUserBadge();
});
