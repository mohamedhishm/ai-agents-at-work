import axios from "axios";
import { mock } from "./mock";
const USE_MOCK = process.env.NEXT_PUBLIC_USE_MOCK !== "false";
const api = axios.create({ baseURL: process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000" });
const isBrowser = () => typeof window !== "undefined";
api.interceptors.request.use((c) => { const t = isBrowser() && localStorage.getItem("token"); if (t) c.headers.Authorization = `Bearer ${t}`; return c; });
api.interceptors.response.use((r) => r, (e) => { if (e.response?.status === 401 && isBrowser() && !location.pathname.startsWith("/login")) { localStorage.clear(); location.href = "/login"; } return Promise.reject(e); });
export const AuthAPI = USE_MOCK ? { login: mock.login, register: mock.register, me: mock.me } : { login: (d) => api.post("/auth/login", d), register: (d) => api.post("/auth/register", d), me: () => api.get("/auth/me") };
export const AgentAPI = USE_MOCK ? { message: mock.message, activity: mock.activity } : { message: (message) => api.post("/agents/message", { message }), activity: () => api.get("/agents/activity") };
export const TaskAPI = USE_MOCK
  ? {
      list: mock.list,
      approve: mock.approve,
      cancel: mock.cancel,
    }
  : {
      list: () => api.get("/tasks"),
      approve: (id, approved) =>
        api.post(`/tasks/${id}/approval`, { approved }),
      cancel: (id) =>
        api.post(`/tasks/${id}/cancel`),
    };
export const IS_MOCK = USE_MOCK;
export default api;
