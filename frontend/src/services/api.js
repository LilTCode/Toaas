import axios from "axios";

const api = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || "/api/",
});

// These endpoints are public. Sending a stale Authorization header to them
// makes DRF reject the request during authentication — before it ever reaches
// the AllowAny permission check — so a expired token would otherwise lock a
// user out of the very screen they need to sign back in from.
const PUBLIC_PATHS = [
  "accounts/login/",
  "accounts/register/",
  "accounts/verify-otp/",
];

const clearSession = () => {
  localStorage.removeItem("toaas_access_token");
  localStorage.removeItem("toaas_refresh_token");
  localStorage.removeItem("toaas_user");
};

api.interceptors.request.use((config) => {
  const url = config.url || "";
  if (PUBLIC_PATHS.some((path) => url.includes(path))) {
    delete config.headers.Authorization;
    return config;
  }
  const token = localStorage.getItem("toaas_access_token");
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// Access tokens expire after 60 minutes and there is no refresh endpoint, so a
// returning user always arrives holding a dead token. Clear it and send them to
// the login screen instead of leaving the app in a permanently failing state.
api.interceptors.response.use(
  (response) => response,
  (error) => {
    const status = error?.response?.status;
    const code = error?.response?.data?.code;
    if (status === 401 && code === "token_not_valid") {
      clearSession();
      if (!window.location.pathname.startsWith("/auth")) {
        window.location.replace("/auth");
      }
    }
    return Promise.reject(error);
  }
);

export { clearSession };
export default api;
