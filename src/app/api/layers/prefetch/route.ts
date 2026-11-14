import { createClient } from "@/lib/supabase/server";

/**
 * Starts the NASA satellite requests (AppEEARS) for the farmer's field as soon as the
 * pin is dropped, so the data is ready by the time they run the analysis.
 * Server only: the browser never talks to the Python engine. Body: { field_id, lat, lng }.
 * Best effort: failures are reported but never block onboarding.
 */
export async function POST(request: Request) {
  const supabase = await createClient();
  const {
    data: { user },
  } = await supabase.auth.getUser();
  if (!user) return Response.json({ error: "unauthorized" }, { status: 401 });

  const engineUrl = process.env.ENGINE_URL;
  const engineKey = process.env.ENGINE_API_KEY;
  if (!engineUrl || !engineKey) return Response.json({ error: "engine_not_configured" }, { status: 500 });

  const body = (await request.json().catch(() => null)) as { field_id?: unknown; lat?: unknown; lng?: unknown } | null;
  const fieldId = typeof body?.field_id === "string" ? body.field_id : "";
  if (!/^[0-9a-f-]{36}$/i.test(fieldId)) return Response.json({ error: "invalid_field" }, { status: 400 });
  // The field must belong to this user (RLS limits the read to their own rows).
  const { data: field } = await supabase.from("field_profiles").select("id").eq("id", fieldId).maybeSingle();
  if (!field) return Response.json({ error: "field_not_found" }, { status: 404 });
  const lat = Number(body?.lat);
  const lng = Number(body?.lng);
  if (!Number.isFinite(lat) || !Number.isFinite(lng) || Math.abs(lat) > 90 || Math.abs(lng) > 180) {
    return Response.json({ error: "invalid_coordinates" }, { status: 400 });
  }

  try {
    const res = await fetch(`${engineUrl.replace(/\/$/, "")}/layers/prefetch`, {
      method: "POST",
      headers: { "Content-Type": "application/json", "X-API-Key": engineKey },
      body: JSON.stringify({ field_id: fieldId, user_id: user.id, lat, lng }),
      signal: AbortSignal.timeout(30_000),
    });
    const data = await res.json().catch(() => ({}));
    return Response.json(data, { status: res.ok ? 200 : 502 });
  } catch (err) {
    console.error("[layers/prefetch] engine unreachable:", err);
    return Response.json({ error: "engine_unreachable" }, { status: 502 });
  }
}
