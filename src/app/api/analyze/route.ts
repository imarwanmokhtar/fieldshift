import { createClient } from "@/lib/supabase/server";

// Allow time for a sleeping engine to wake up (Vercel function limit).
export const maxDuration = 90;

/**
 * Starts an analysis. Server only: the browser never talks to the Python engine.
 * 1. checks the login, 2. creates a pending `analyses` row, 3. asks the engine to fill it.
 * Body (optional): { "lang": "ar" | "en" }
 */
export async function POST(request: Request) {
  const supabase = await createClient();
  const {
    data: { user },
  } = await supabase.auth.getUser();
  if (!user) return Response.json({ error: "unauthorized" }, { status: 401 });

  const engineUrl = process.env.ENGINE_URL;
  const engineKey = process.env.ENGINE_API_KEY;
  if (!engineUrl || !engineKey) {
    return Response.json({ error: "engine_not_configured" }, { status: 500 });
  }

  let lang: "ar" | "en" = "ar";
  try {
    const body = await request.json();
    if (body?.lang === "en") lang = "en";
  } catch {
    // empty body is fine
  }

  const { data: profile } = await supabase
    .from("field_profiles")
    .select("status")
    .eq("user_id", user.id)
    .maybeSingle();
  if (profile?.status !== "completed") {
    return Response.json({ error: "profile_incomplete" }, { status: 400 });
  }

  // Re-use a run that is really still in progress (double clicks, refreshes).
  // A pending row the engine never picked up within a minute, or a running row
  // with no progress for 3 minutes, is stuck: drop it and start a fresh run.
  // (The results page uses the same limits to show its "stuck" message.)
  const now = Date.now();
  const fiveMinutesAgo = new Date(now - 5 * 60 * 1000).toISOString();
  const { data: active } = await supabase
    .from("analyses")
    .select("id,status,created_at,updated_at")
    .eq("user_id", user.id)
    .eq("lang", lang)
    .in("status", ["pending", "running"])
    .gte("created_at", fiveMinutesAgo)
    .order("created_at", { ascending: false })
    .limit(1)
    .maybeSingle();
  if (active) {
    const alive =
      active.status === "pending"
        ? now - Date.parse(active.created_at) < 60_000
        : now - Date.parse(active.updated_at ?? active.created_at) < 180_000;
    if (alive) return Response.json({ id: active.id });
    if (active.status === "pending") {
      await supabase.from("analyses").delete().eq("id", active.id);
    }
  }

  const { data: analysis, error } = await supabase
    .from("analyses")
    .insert({ user_id: user.id, lang })
    .select("id")
    .single();
  if (error || !analysis) {
    return Response.json({ error: error?.message ?? "insert_failed" }, { status: 500 });
  }

  // The engine answers 202 immediately and keeps working in the background.
  try {
    const res = await fetch(`${engineUrl.replace(/\/$/, "")}/analyze`, {
      method: "POST",
      headers: { "Content-Type": "application/json", "X-API-Key": engineKey },
      body: JSON.stringify({ analysis_id: analysis.id, user_id: user.id, lang }),
      // Free hosting tiers sleep when idle and need ~1 minute to wake up.
      signal: AbortSignal.timeout(75_000),
    });
    if (!res.ok) throw new Error(`engine responded ${res.status}`);
  } catch (err) {
    await supabase.from("analyses").delete().eq("id", analysis.id);
    console.error("[analyze] engine unreachable:", err);
    return Response.json({ error: "engine_unreachable" }, { status: 502 });
  }

  return Response.json({ id: analysis.id });
}
