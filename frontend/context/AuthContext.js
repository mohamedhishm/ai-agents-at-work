"use client";
import { createContext, useContext, useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { AuthAPI } from "@/lib/api";

const Ctx = createContext(null);
export const useAuth = () => useContext(Ctx);

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);
  const router = useRouter();

  useEffect(() => {
    if (!localStorage.getItem("token")) return setLoading(false);
    AuthAPI.me().then((r) => setUser(r.data)).catch(() => localStorage.removeItem("token")).finally(() => setLoading(false));
  }, []);

  const login = async (email, password, role) => {
    const { data } = await AuthAPI.login({ email, password, role });
    if (role && data.user.role !== role) throw new Error("This account does not match the selected role.");
    localStorage.setItem("token", data.token);
    setUser(data.user);
    router.push(data.user.role === "admin" ? "/admin" : "/dashboard");
  };

  const register = async (name, email, password) => {
    const { data } = await AuthAPI.register({ name, email, password });
    localStorage.setItem("token", data.token);
    setUser(data.user);
    router.push("/dashboard");
  };

  const logout = () => { localStorage.removeItem("token"); setUser(null); router.push("/login"); };
  return <Ctx.Provider value={{ user, loading, login, register, logout }}>{children}</Ctx.Provider>;
}

export function useGuard(role) {
  const { user, loading } = useAuth();
  const router = useRouter();
  useEffect(() => {
    if (loading) return;
    if (!user) router.replace("/login");
    else if (role && user.role !== role) router.replace(user.role === "admin" ? "/admin" : "/dashboard");
  }, [user, loading, role, router]);
  return { user, ready: !loading && !!user && (!role || user.role === role) };
}
