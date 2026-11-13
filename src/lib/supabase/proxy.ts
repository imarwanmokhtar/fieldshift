import { createServerClient } from "@supabase/ssr";
import { NextResponse, type NextRequest } from "next/server";
import { defaultLocale, isLocale } from "@/lib/i18n";

/**
 * Refreshes the Supabase session on every request and enforces route
 * protection:
 *   - /:locale/dashboard, /:locale/onboarding   require a session, otherwise redirect to /:locale/login
 *   - /:locale/login, /:locale/signup  redirect to /:locale/onboarding when signed in
 *   - paths without a locale prefix redirect to the default locale (Arabic)
 *
 * Note: `middleware.ts` was renamed to `proxy.ts` in Next.js 16. The behavior
 * is identical; the helper lives here so `src/proxy.ts` stays small.
 */
export async function updateSession(request: NextRequest) {
  let supabaseResponse = NextResponse.next({ request });

  const supabase = createServerClient(
    process.env.NEXT_PUBLIC_SUPABASE_URL!,
    process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!,
    {
      cookies: {
        getAll() {
          return request.cookies.getAll();
        },
        setAll(cookiesToSet) {
          cookiesToSet.forEach(({ name, value }) =>
            request.cookies.set(name, value),
          );
          supabaseResponse = NextResponse.next({ request });
          cookiesToSet.forEach(({ name, value, options }) =>
            supabaseResponse.cookies.set(name, value, options),
          );
        },
      },
    },
  );

  // IMPORTANT: do not run any code between createServerClient and getUser().
  const {
    data: { user },
  } = await supabase.auth.getUser();

  const { pathname } = request.nextUrl;

  // The auth callback and API routes (non-page routes): refresh only, never
  // redirect or prefix a locale.
  if (pathname.startsWith("/auth/") || pathname.startsWith("/api/")) {
    return supabaseResponse;
  }

  const firstSegment = pathname.split("/")[1];

  // No locale prefix (e.g. "/", "/login") → default locale (Arabic).
  if (!isLocale(firstSegment)) {
    const url = request.nextUrl.clone();
    url.pathname = `/${defaultLocale}${pathname === "/" ? "" : pathname}`;
    return NextResponse.redirect(url);
  }

  const locale = firstSegment;
  const rest = pathname.slice(locale.length + 1) || "/";
  const isDashboard = rest.startsWith("/dashboard");
  const isOnboarding = rest.startsWith("/onboarding");
  const isAuthPage = rest === "/login" || rest === "/signup";

  if ((isDashboard || isOnboarding) && !user) {
    const url = request.nextUrl.clone();
    url.pathname = `/${locale}/login`;
    return NextResponse.redirect(url);
  }

  if (isAuthPage && user) {
    const url = request.nextUrl.clone();
    url.pathname = `/${locale}/onboarding`;
    return NextResponse.redirect(url);
  }

  return supabaseResponse;
}
