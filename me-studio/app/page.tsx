"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";
import { loadPersona } from "@/lib/store";

// Sends you wherever you left off.
export default function Home() {
  const router = useRouter();
  useEffect(() => {
    const p = loadPersona();
    router.replace(!p ? "/setup" : p.state === "ready" ? "/create" : "/training");
  }, [router]);
  return <main className="page no-tabs" aria-busy="true" />;
}
