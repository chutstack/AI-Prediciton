// API client for AI Prediction Platform
const API_BASE = "";

function getToken() {
  return localStorage.getItem("token");
}

function setToken(token) {
  localStorage.setItem("token", token);
}

function clearToken() {
  localStorage.removeItem("token");
  localStorage.removeItem("user");
}

function setUser(user) {
  localStorage.setItem("user", JSON.stringify(user));
}

function getUser() {
  try {
    return JSON.parse(localStorage.getItem("user") || "null");
  } catch {
    return null;
  }
}

async function apiFetch(path, options = {}) {
  const token = getToken();
  const headers = {
    "Content-Type": "application/json",
    ...(token ? { Authorization: `Bearer ${token}` } : {}),
    ...options.headers,
  };

  const res = await fetch(API_BASE + path, { ...options, headers });
  const data = await res.json();
  if (!res.ok) {
    throw new Error(data.detail || "Request failed");
  }
  return data;
}

async function login(email, password) {
  const form = new URLSearchParams({ username: email, password });
  const res = await fetch("/auth/token", {
    method: "POST",
    headers: { "Content-Type": "application/x-www-form-urlencoded" },
    body: form,
  });
  const data = await res.json();
  if (!res.ok) throw new Error(data.detail || "Login failed");
  setToken(data.access_token);
  setUser(data.user);
  return data;
}

async function register(email, password, fullName) {
  const data = await apiFetch("/auth/register", {
    method: "POST",
    body: JSON.stringify({ email, password, full_name: fullName }),
  });
  setToken(data.access_token);
  setUser(data.user);
  return data;
}

async function getMe() {
  return apiFetch("/auth/me");
}

async function generatePrediction(market, symbol = null) {
  return apiFetch("/predictions/generate", {
    method: "POST",
    body: JSON.stringify({ market, symbol: symbol || undefined }),
  });
}

async function getHistory(limit = 20, market = null) {
  const params = new URLSearchParams({ limit });
  if (market) params.set("market", market);
  return apiFetch(`/predictions/history?${params}`);
}

async function getStats() {
  return apiFetch("/predictions/stats");
}

async function getPublicSignals() {
  return apiFetch("/predictions/public");
}

async function getPlans() {
  return apiFetch("/billing/plans");
}

async function demoActivate(tier = null, creditPackage = null) {
  return apiFetch("/billing/demo-activate", {
    method: "POST",
    body: JSON.stringify({ tier, credit_package: creditPackage }),
  });
}

async function getTransactions() {
  return apiFetch("/billing/transactions");
}

async function getRevenue() {
  return apiFetch("/billing/revenue");
}
