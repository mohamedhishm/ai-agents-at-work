"use client";
import { useEffect } from "react";
import { useRouter } from "next/navigation";
import { useAuth } from "@/context/AuthContext";
export default function Home() {
  const { user, loading } = useAuth(); const r = useRouter();
  useEffect(() => { if (!loading) r.replace(!user ? "/login" : user.role === "admin" ? "/admin" : "/dashboard"); }, [user, loading, r]);
  return null;
}
