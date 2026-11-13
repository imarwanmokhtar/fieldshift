import { test, expect } from '@playwright/test';

/**
 * E2E auth flow against the real Supabase project.
 * Default locale is Arabic (/ar). Paths without a locale prefix redirect there.
 *
 * The full signup → dashboard → logout → login flow requires "Confirm email"
 * to be OFF in the Supabase dashboard. Run with:
 *
 *   E2E_CONFIRM_OFF=1 npx playwright test
 *
 * Without it, only the tests below run (a signup ends on the "check your
 * email" screen).
 */

const CONFIRM_OFF = process.env.E2E_CONFIRM_OFF === '1';
const timestamp = Date.now();
// Supabase rejects .test/.example domains; gmail.com-style addresses pass validation.
const randomEmail = `fieldshift.e2e.${timestamp}@gmail.com`;
const password = 'fieldshift-e2e-123';

test.describe('landing page', () => {
  test('defaults to Arabic at the root URL', async ({ page }) => {
    await page.goto('/');
    await expect(page).toHaveURL(/\/ar\/?$/);
  });

  test('renders Arabic hero with calls to action', async ({ page }) => {
    await page.goto('/ar');
    await expect(page.locator('html')).toHaveAttribute('lang', 'ar');
    await expect(page.locator('html')).toHaveAttribute('dir', 'rtl');
    await expect(page.getByRole('heading', { name: /اختر محصولك القادم/ })).toBeVisible();
    await expect(page.getByRole('link', { name: 'ابدأ الآن' })).toBeVisible();
    await expect(page.getByRole('link', { name: 'تسجيل الدخول' }).first()).toBeVisible();
  });

  test('English version renders LTR with English copy', async ({ page }) => {
    await page.goto('/en');
    await expect(page.locator('html')).toHaveAttribute('lang', 'en');
    await expect(page.locator('html')).toHaveAttribute('dir', 'ltr');
    await expect(page.getByRole('heading', { name: /choose your next crop/i })).toBeVisible();
  });

  test('language switcher toggles locale on the same page', async ({ page }) => {
    await page.goto('/ar');
    await page.getByRole('link', { name: 'English' }).click();
    await expect(page).toHaveURL(/\/en\/?$/);
    await expect(page.getByRole('heading', { name: /choose your next crop/i })).toBeVisible();
  });

  test('works at 360px width (no horizontal overflow)', async ({ page }) => {
    await page.goto('/ar');
    await page.setViewportSize({ width: 360, height: 800 });
    const overflow = await page.evaluate(
      () => document.documentElement.scrollWidth > document.documentElement.clientWidth
    );
    expect(overflow).toBe(false);
  });
});

test.describe('route protection', () => {
  test('/dashboard redirects to /ar/login when signed out', async ({ page }) => {
    await page.goto('/dashboard');
    await expect(page).toHaveURL(/\/ar\/login/);
  });
});

test.describe('signup', () => {
  test('shows the check-your-email step while confirmation is ON', async ({ page }) => {
    test.skip(CONFIRM_OFF, 'Confirmation is off; the full-flow suite covers signup instead');
    await page.goto('/signup');
    await page.fill('#email', randomEmail);
    await page.fill('#password', password);
    await page.getByRole('button', { name: /إنشاء حساب/ }).click();

    // Supabase free tier allows only ~2 confirmation emails/hour; when the
    // quota is spent the signup call returns 429. Skip instead of fail.
    const signupResponse = await page.waitForResponse(
      (r) => r.url().includes('/auth/v1/signup'),
      { timeout: 20_000 },
    );
    if (signupResponse.status() === 429) {
      test.skip(true, 'Supabase email rate limit hit; re-run later');
    }
    await expect(page.getByText(/تحقق من بريدك/)).toBeVisible({ timeout: 15_000 });
    await expect(page).toHaveURL(/\/ar\/signup/);
  });

  test('logs straight into the dashboard while confirmation is OFF', async ({ page }) => {
    test.skip(!CONFIRM_OFF, 'Confirmation is on; users must confirm by email first');
    await page.goto('/signup');
    await page.fill('#email', randomEmail);
    await page.fill('#password', password);
    await page.getByRole('button', { name: /إنشاء حساب/ }).click();
    await expect(page).toHaveURL(/\/ar\/dashboard/, { timeout: 30_000 });
    await expect(page.getByText(randomEmail, { exact: true })).toBeVisible();
  });
});

test.describe('login', () => {
  test('rejects wrong credentials with an inline error', async ({ page }) => {
    await page.goto('/login');
    await page.fill('#email', `fieldshift.e2e.badpass.${timestamp}@gmail.com`);
    await page.fill('#password', 'wrong-password');
    await page.getByRole('button', { name: /^تسجيل الدخول$/ }).click();
    await expect(page.getByText(/البريد الإلكتروني أو كلمة المرور غير صحيحة/)).toBeVisible({ timeout: 15_000 });
    await expect(page).toHaveURL(/\/ar\/login/);
  });
});

test.describe('full auth flow (confirm email OFF only)', () => {
  // Own unique email per test: tests run sequentially and an email registered
  // by one test would make the next signup fail ("User already registered").
  const makeEmail = (kind: string) => `fieldshift.e2e.${kind}.${timestamp}@gmail.com`;

  test('signup → dashboard → logout → login', async ({ page }) => {
    test.skip(!CONFIRM_OFF, 'Requires "Confirm email" OFF in Supabase; run with E2E_CONFIRM_OFF=1');
    const flowEmail = makeEmail('flow');

    // 1. Sign up → straight to the dashboard
    await page.goto('/signup');
    await page.fill('#email', flowEmail);
    await page.fill('#password', password);
    const signupResponse = page.waitForResponse((r) => r.url().includes('/auth/v1/signup'));
    await page.getByRole('button', { name: /إنشاء حساب/ }).click();
    const response = await signupResponse;
    if (response.status() !== 200) {
      console.error('signup failed:', response.status(), await response.text().catch(() => ''));
    }
    expect(response.status()).toBe(200);
    await expect(page).toHaveURL(/\/ar\/dashboard/, { timeout: 30_000 });

    // 2. Log out → back to the landing page
    await page.getByRole('button', { name: /تسجيل الخروج/ }).click();
    await expect(page).toHaveURL(/\/ar\/?$/, { timeout: 15_000 });
    await expect(page.getByRole('heading', { name: /اختر محصولك القادم/ })).toBeVisible();

    // 3. Log back in with the same credentials
    await page.goto('/login');
    await page.fill('#email', flowEmail);
    await page.fill('#password', password);
    await page.getByRole('button', { name: /^تسجيل الدخول$/ }).click();
    await expect(page).toHaveURL(/\/ar\/dashboard/, { timeout: 15_000 });
    await expect(page.getByText(flowEmail, { exact: true })).toBeVisible();
  });

  test('/login redirects to /dashboard when already signed in', async ({ page }) => {
    test.skip(!CONFIRM_OFF, 'Requires a session; only possible with "Confirm email" OFF');
    const flowEmail = makeEmail('redirect');

    await page.goto('/signup');
    await page.fill('#email', flowEmail);
    await page.fill('#password', password);
    await page.getByRole('button', { name: /إنشاء حساب/ }).click();
    await expect(page).toHaveURL(/\/ar\/dashboard/, { timeout: 15_000 });

    await page.goto('/login');
    await expect(page).toHaveURL(/\/ar\/dashboard/);
  });
});
