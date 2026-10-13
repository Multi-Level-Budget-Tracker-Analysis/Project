// ==============================================================================
// MULTI-LEVEL BUDGET TRACKER ANALYTICS — API CLIENT LAYER
// ==============================================================================

const API_BASE = "";

const api = {
  // 0. Authentication
  async login(username, password) {
    const res = await fetch(`${API_BASE}/api/auth/login`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ username, password })
    });
    const result = await res.json();
    if (!res.ok) throw new Error(result.error || "Authentication failed.");
    return result;
  },

  async register(username, password, fullName, role) {
    const res = await fetch(`${API_BASE}/api/auth/register`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ username, password, full_name: fullName, role })
    });
    const result = await res.json();
    if (!res.ok) throw new Error(result.error || "Registration failed.");
    return result;
  },

  async demoLogin(role) {
    const res = await fetch(`${API_BASE}/api/auth/demo`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ role })
    });
    const result = await res.json();
    if (!res.ok) throw new Error(result.error || "Demo login failed.");
    return result;
  },

  async getAuthProfiles() {
    const res = await fetch(`${API_BASE}/api/auth/me`);
    if (!res.ok) throw new Error("Failed to load demo profiles.");
    return await res.json();
  },

  // 1. Executive Overview
  async getOverview(year = "All", level = "All") {
    const res = await fetch(`${API_BASE}/api/overview?year=${encodeURIComponent(year)}&level=${encodeURIComponent(level)}`);
    if (!res.ok) throw new Error("Failed to load overview data.");
    return await res.json();
  },

  // 2. Individual Level
  async getIndividual(category = "All", year = "All") {
    const res = await fetch(`${API_BASE}/api/individual?category=${encodeURIComponent(category)}&year=${encodeURIComponent(year)}`);
    if (!res.ok) throw new Error("Failed to load individual analytics.");
    return await res.json();
  },

  async calculateIndividual(inputData) {
    const res = await fetch(`${API_BASE}/api/individual/calculate`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(inputData)
    });
    const result = await res.json();
    if (!res.ok) throw new Error(result.error || "Failed to calculate individual analytics.");
    return result.data;
  },

  async addTransaction(txData) {
    const res = await fetch(`${API_BASE}/api/individual/transaction`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(txData)
    });
    const result = await res.json();
    if (!res.ok) throw new Error(result.error || "Failed to record transaction.");
    return result;
  },

  async deleteTransaction(txId) {
    const res = await fetch(`${API_BASE}/api/individual/transaction/${txId}`, {
      method: "DELETE"
    });
    const result = await res.json();
    if (!res.ok) throw new Error(result.error || "Failed to delete transaction.");
    return result;
  },

  async updateBudget(category, monthlyBudget) {
    const res = await fetch(`${API_BASE}/api/individual/budget`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ category, monthly_budget: monthlyBudget })
    });
    const result = await res.json();
    if (!res.ok) throw new Error(result.error || "Failed to update category budget.");
    return result;
  },

  // 3. Organization Level
  async getOrganization(department = "All", year = "All") {
    const res = await fetch(`${API_BASE}/api/organization?department=${encodeURIComponent(department)}&year=${encodeURIComponent(year)}`);
    if (!res.ok) throw new Error("Failed to load organization analytics.");
    return await res.json();
  },

  async calculateOrganization(inputData) {
    const res = await fetch(`${API_BASE}/api/organization/calculate`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(inputData)
    });
    const result = await res.json();
    if (!res.ok) throw new Error(result.error || "Failed to calculate organization analytics.");
    return result.data;
  },

  async addOrder(orderData) {
    const res = await fetch(`${API_BASE}/api/organization/order`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(orderData)
    });
    const result = await res.json();
    if (!res.ok) throw new Error(result.error || "Failed to save order/cost item.");
    return result;
  },

  async deleteOrder(orderId) {
    const res = await fetch(`${API_BASE}/api/organization/order/${orderId}`, {
      method: "DELETE"
    });
    const result = await res.json();
    if (!res.ok) throw new Error(result.error || "Failed to delete order.");
    return result;
  },

  // 4. State & Nation Level
  async getStateNation(year = "All") {
    const res = await fetch(`${API_BASE}/api/state-nation?year=${encodeURIComponent(year)}`);
    if (!res.ok) throw new Error("Failed to load state & national analytics.");
    return await res.json();
  },

  // 5. Predictive Analytics & What-If
  async getPredictive() {
    const res = await fetch(`${API_BASE}/api/predictive`);
    if (!res.ok) throw new Error("Failed to load predictive analytics.");
    return await res.json();
  },

  async simulatePredictive(params) {
    const res = await fetch(`${API_BASE}/api/predictive/simulate`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(params)
    });
    const result = await res.json();
    if (!res.ok) throw new Error(result.error || "Simulation failed.");
    return result;
  },

  // 6. Power BI Sync & Assets
  async exportAllPowerBICSVs() {
    const res = await fetch(`${API_BASE}/api/powerbi/export-all`, {
      method: "POST"
    });
    const result = await res.json();
    if (!res.ok) throw new Error(result.error || "Failed to sync Power BI CSVs.");
    return result;
  },

  async getPbiDax() {
    const res = await fetch(`${API_BASE}/api/powerbi/dax`);
    return await res.text();
  },

  async getPbiPq() {
    const res = await fetch(`${API_BASE}/api/powerbi/powerquery`);
    return await res.text();
  }
};
