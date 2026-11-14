"use client";

import { useEffect, useMemo, useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { toast } from "sonner";
import { createClient } from "@/lib/supabase/client";
import { BrutalButton } from "@/components/brutal-button";
import { cn } from "@/lib/utils";
import type { Locale } from "@/lib/i18n";
import { CROP_OPTIONS, getLocalizedOption } from "@/lib/onboarding/questions";
import { getResultsStrings, type ResultsStrings } from "@/lib/results/strings";
import type { AnalysisRow, Criterion, Strategy, StrategyText } from "@/lib/results/types";
import { startAnalysis } from "./start-analysis";

const POLL_MS = 2000;
const SLOW_AFTER_MS = 90_000;
// A run nobody picked up, or one that stopped reporting progress, is treated as stuck.
const STALLED_PENDING_MS = 60_000;
const STALLED_RUNNING_MS = 180_000;
// Stage names written by older engine versions.
const LEGACY_STAGES: Record<string, string> = { reading_data: "fetching_climate", comparing: "scoring" };
const CRITERIA_ORDER: Criterion[] = ["water", "soil", "income", "heat", "cost", "risk", "forage"];

function cropLabel(crop: string, locale: Locale, t: ResultsStrings) {
  if (crop === "fallow") return t.fallow;
  const opt = CROP_OPTIONS.find((o) => o.value === crop);
  return opt ? getLocalizedOption(opt, locale) : crop.replace(/_/g, " ");
}

export function ResultsClient({ locale, initial }: { locale: Locale; initial: AnalysisRow }) {
  const t = getResultsStrings(locale);
  const router = useRouter();
  const [row, setRow] = useState<AnalysisRow>(initial);
  const [slow, setSlow] = useState(false);
  const [busy, setBusy] = useState(false);

  const finished = row.status === "done" || row.status === "failed";
  const now = useNow(finished ? null : 1000);
  const stalled = !finished && isStalled(row, now);

  useEffect(() => {
    if (finished) return;
    const supabase = createClient();
    const timer = setInterval(async () => {
      const { data } = await supabase
        .from("analyses")
        .select("id,status,stage,lang,result,narrative,error,created_at,updated_at")
        .eq("id", row.id)
        .maybeSingle();
      if (data) setRow(data as AnalysisRow);
    }, POLL_MS);
    const slowTimer = setTimeout(() => setSlow(true), SLOW_AFTER_MS);
    return () => {
      clearInterval(timer);
      clearTimeout(slowTimer);
    };
  }, [finished, row.id]);

  async function rerun(lang: Locale) {
    setBusy(true);
    try {
      const id = await startAnalysis(lang);
      router.push(`/${lang}/dashboard/results/${id}`);
    } catch (err) {
      toast.error(`${t.startError} (${err instanceof Error ? err.message : "unknown"})`);
      setBusy(false);
    }
  }

  return (
    <div className="mx-auto max-w-6xl px-4 py-10 md:px-6 md:py-16">
      <div className="flex flex-wrap items-center justify-between gap-4">
        <h1 className="font-heading text-3xl font-bold uppercase tracking-tight md:text-5xl">{t.pageTitle}</h1>
        <Link
          href={`/${locale}/dashboard`}
          className="border-[3px] border-ink bg-paper px-4 py-2 font-bold underline-offset-4 hover:underline"
        >
          {t.back}
        </Link>
      </div>

      {!finished && !stalled && (
        <Progress t={t} stage={row.stage ?? "pending"} createdAt={row.created_at} now={now} slow={slow} />
      )}

      {stalled && (
        <div role="alert" className="mt-10 border-[3px] border-ink bg-paper p-8 shadow-brutal-lg">
          <p className="font-heading text-xl font-bold uppercase md:text-2xl">{t.stalledTitle}</p>
          <p className="mt-3 max-w-2xl">{row.status === "pending" ? t.stalledPending : t.stalledRunning}</p>
          <div className="mt-6">
            <BrutalButton variant="dark" onClick={() => rerun(locale)} disabled={busy}>
              {busy ? t.retrying : t.retry}
            </BrutalButton>
          </div>
        </div>
      )}

      {row.status === "failed" && (
        <div role="alert" className="mt-10 border-[3px] border-ink bg-paper p-8 shadow-brutal-lg">
          <p className="font-heading text-xl font-bold uppercase md:text-2xl">{t.failedTitle}</p>
          {row.error && <p className="mt-3 max-w-2xl">{row.error}</p>}
          <div className="mt-6">
            <BrutalButton variant="dark" onClick={() => rerun(locale)} disabled={busy}>
              {busy ? t.retrying : t.retry}
            </BrutalButton>
          </div>
        </div>
      )}

      {row.status === "done" && row.result && row.narrative && (
        <Results row={row} locale={locale} t={t} busy={busy} onOtherLanguage={() => rerun(row.narrative?.lang === "ar" ? "en" : "ar")} />
      )}
    </div>
  );
}

function useNow(intervalMs: number | null) {
  const [now, setNow] = useState(() => Date.now());
  useEffect(() => {
    if (intervalMs === null) return;
    const timer = setInterval(() => setNow(Date.now()), intervalMs);
    return () => clearInterval(timer);
  }, [intervalMs]);
  return now;
}

function isStalled(row: AnalysisRow, now: number) {
  if (row.status === "pending") return now - Date.parse(row.created_at) > STALLED_PENDING_MS;
  const last = Date.parse(row.updated_at ?? row.created_at);
  return row.status === "running" && now - last > STALLED_RUNNING_MS;
}

function formatElapsed(ms: number) {
  const total = Math.max(0, Math.floor(ms / 1000));
  const m = Math.floor(total / 60);
  const s = total % 60;
  return m > 0 ? `${m}:${String(s).padStart(2, "0")}` : `${s}s`;
}

function Progress({
  t,
  stage: rawStage,
  createdAt,
  now,
  slow,
}: {
  t: ResultsStrings;
  stage: string;
  createdAt: string;
  now: number;
  slow: boolean;
}) {
  const stage = LEGACY_STAGES[rawStage] ?? rawStage;
  const steps = t.steps;
  const idx = Math.max(0, steps.findIndex((s) => s.id === stage));
  const current = steps[idx];

  // When did this stage start (client clock)? Used to keep the bar creeping
  // inside the current step, so a long step never looks frozen.
  const [stageStart, setStageStart] = useState({ stage, at: now });
  if (stageStart.stage !== stage) setStageStart({ stage, at: now });
  const inStep = 1 - Math.exp(-(now - stageStart.at) / 15_000); // 0 → 1, never reaches 1
  const pct = Math.min(99, ((idx + 0.85 * inStep) / steps.length) * 100);

  return (
    <div className="mt-10 border-[3px] border-ink bg-green-light p-6 shadow-brutal-lg md:p-8" aria-live="polite">
      <div className="flex flex-wrap items-baseline justify-between gap-2 text-sm font-bold">
        <span>{t.stepOf(idx + 1, steps.length)}</span>
        <span className="font-mono tabular-nums opacity-80">{t.elapsed(formatElapsed(now - Date.parse(createdAt)))}</span>
      </div>

      <p className="mt-2 font-heading text-xl font-bold md:text-2xl">{current.title}…</p>

      <div
        className="mt-4 h-6 w-full border-[3px] border-ink bg-paper shadow-brutal-xs"
        role="progressbar"
        aria-valuemin={0}
        aria-valuemax={100}
        aria-valuenow={Math.round(pct)}
        aria-label={current.title}
      >
        <div
          className="progress-stripes h-full bg-green-dark transition-[width] duration-1000 ease-out motion-reduce:transition-none"
          style={{ width: `${pct}%` }}
        />
      </div>

      <p key={current.id} className="mt-3 min-h-12 animate-in fade-in slide-in-from-bottom-1 duration-500">
        {current.detail}
      </p>

      <ol className="mt-6 grid gap-2 sm:grid-cols-2">
        {steps.map((step, i) => {
          const state = i < idx ? "done" : i === idx ? "current" : "todo";
          return (
            <li
              key={step.id}
              className={cn(
                "flex items-center gap-3 border-2 border-ink px-3 py-2 text-sm",
                state === "done" && "bg-paper",
                state === "current" && "bg-paper font-bold shadow-brutal-xs",
                state === "todo" && "border-dashed opacity-60",
              )}
            >
              <span
                aria-hidden
                className={cn(
                  "flex size-6 shrink-0 items-center justify-center border-2 border-ink text-xs font-bold",
                  state === "done" && "bg-green-dark text-paper",
                  state === "current" && "animate-pulse bg-green-light motion-reduce:animate-none",
                )}
              >
                {state === "done" ? "✓" : i + 1}
              </span>
              <span>{step.title}</span>
              <span className="sr-only">
                {state === "done" ? "(done)" : state === "current" ? "(in progress)" : ""}
              </span>
            </li>
          );
        })}
      </ol>

      {slow && <p className="mt-4 font-bold">{t.slow}</p>}
    </div>
  );
}

function Results({
  row,
  locale,
  t,
  busy,
  onOtherLanguage,
}: {
  row: AnalysisRow;
  locale: Locale;
  t: ResultsStrings;
  busy: boolean;
  onOtherLanguage: () => void;
}) {
  const pack = row.result!;
  const narrative = row.narrative!;
  const texts = useMemo(() => new Map(narrative.strategies.map((s) => [s.id, s])), [narrative]);
  // Recommended first, current second, then the rest in engine order.
  const ordered = useMemo(() => {
    const rec = pack.strategies.find((s) => s.id === pack.recommended_id);
    const rest = pack.strategies.filter((s) => s.id !== pack.recommended_id);
    return rec ? [rec, ...rest] : rest;
  }, [pack]);
  const textDir = narrative.lang === "ar" ? "rtl" : "ltr";

  return (
    <div className="mt-10 space-y-10">
      <section className="border-[3px] border-ink bg-green-light p-6 shadow-brutal-lg md:p-10" dir={textDir}>
        <p className="text-lg md:text-xl">{narrative.overview}</p>
        <div className="mt-4 flex flex-wrap items-center gap-3 text-sm">
          {pack.observations.climate_source !== "nasa_power" && (
            <span className="border-2 border-ink bg-paper px-2 py-1 font-bold">{t.climateFallback}</span>
          )}
          {narrative.source === "template" && (
            <span className="opacity-80">
              {t.templateNote}
              {narrative.fallback_reason && (
                <span className="block text-xs" dir="ltr">
                  {narrative.fallback_reason}
                </span>
              )}
            </span>
          )}
          <button
            type="button"
            onClick={onOtherLanguage}
            disabled={busy}
            lang={narrative.lang === "ar" ? "en" : "ar"}
            className="border-2 border-ink bg-paper px-3 py-1 font-bold hover:bg-ink hover:text-paper disabled:opacity-60"
          >
            {busy ? t.retrying : narrative.lang === "ar" ? "Show in English" : "عرض بالعربية"}
          </button>
        </div>
      </section>

      <div className="grid gap-8 lg:grid-cols-2">
        {ordered.map((s) => (
          <StrategyCard
            key={s.id}
            strategy={s}
            text={texts.get(s.id)}
            recommended={s.id === pack.recommended_id}
            locale={locale}
            textDir={textDir}
            t={t}
          />
        ))}
      </div>

      {pack.data_quality.layers_used.length > 0 && (
        <section className="border-[3px] border-ink bg-green-light p-6">
          <h2 className="font-heading text-lg font-bold uppercase">{t.dataUsed}</h2>
          <ul className="mt-3 flex flex-wrap gap-2">
            {pack.data_quality.layers_used.map((id) => (
              <li key={id} className="border-2 border-ink bg-paper px-2 py-1 text-sm font-bold">
                {t.layerNames[id] ?? id}
              </li>
            ))}
          </ul>
        </section>
      )}

      {pack.data_quality.notes.length > 0 && (
        <section className="border-[3px] border-ink bg-paper p-6">
          <h2 className="font-heading text-lg font-bold uppercase">{t.dataNotes}</h2>
          <ul className="mt-3 list-disc space-y-1 ps-6">
            {pack.data_quality.notes.map((n, i) => (
              <li key={i}>{locale === "ar" && n.text_ar ? n.text_ar : n.text}</li>
            ))}
          </ul>
        </section>
      )}

      <p className="border-s-8 border-green-dark bg-paper p-4 text-lg font-bold" dir={textDir}>
        {narrative.reminder}
      </p>
    </div>
  );
}

function StrategyCard({
  strategy: s,
  text,
  recommended,
  locale,
  textDir,
  t,
}: {
  strategy: Strategy;
  text?: StrategyText;
  recommended: boolean;
  locale: Locale;
  textDir: "rtl" | "ltr";
  t: ResultsStrings;
}) {
  const name = locale === "ar" ? s.name_ar : s.name;
  const conf = { high: "bg-green-dark text-paper", medium: "bg-green-light text-ink", low: "bg-paper text-ink" }[s.confidence];
  return (
    <article
      className={cn(
        "flex flex-col border-[3px] border-ink bg-paper p-6 shadow-brutal-lg",
        recommended && "border-[5px] outline-4 outline-offset-4 outline-green-dark",
      )}
    >
      <header className="flex flex-wrap items-start justify-between gap-3">
        <h2 className="font-heading text-2xl font-bold">{name}</h2>
        <div className="flex flex-wrap gap-2">
          {recommended && (
            <span className="border-2 border-ink bg-green-dark px-2 py-1 text-sm font-bold uppercase text-paper">{t.recommended}</span>
          )}
          <span className={cn("border-2 border-ink px-2 py-1 text-sm font-bold", conf)}>
            {t.confidence[s.confidence]} · {s.confidence_score}
          </span>
        </div>
      </header>

      <ol className="mt-4 grid grid-cols-2 gap-2 text-sm">
        {s.slots.map((sl, i) => (
          <li key={i} className={cn("border-2 border-ink px-2 py-2", sl.season === "winter" ? "bg-paper" : "bg-green-light")}>
            <span className="block text-xs font-bold uppercase opacity-70">
              {t.year} {sl.year} · {t.seasons[sl.season]}
            </span>
            <span className="font-bold">{cropLabel(sl.crop, locale, t)}</span>
          </li>
        ))}
      </ol>

      {s.practices && s.practices.length > 0 && (
        <div className="mt-4">
          <p className="text-xs font-bold uppercase opacity-70">{t.practicesLabel}</p>
          <ul className="mt-2 flex flex-wrap gap-2">
            {s.practices.map((p) => (
              <li key={p} className="border-2 border-ink bg-green-light px-2 py-1 text-sm font-bold shadow-brutal-xs">
                {t.practices[p] ?? p.replace(/_/g, " ")}
              </li>
            ))}
          </ul>
        </div>
      )}

      <div className="mt-5">
        <ScoreBar label={t.overall} value={s.scores.overall} big />
        <div className="mt-3 grid grid-cols-1 gap-x-6 gap-y-2 sm:grid-cols-2">
          {CRITERIA_ORDER.map((c) => (
            <ScoreBar key={c} label={t.criteria[c]} value={s.scores[c]} />
          ))}
        </div>
        <p className="mt-3 text-sm">
          <span className="font-bold" dir="ltr">
            {Math.round(s.metrics.water_m3_per_feddan_year).toLocaleString(locale === "ar" ? "ar-EG" : "en-US")}
          </span>{" "}
          {t.waterPerYear}
        </p>
      </div>

      {text && (
        <div className="mt-6 space-y-5 border-t-[3px] border-ink pt-5" dir={textDir}>
          <p className="font-bold">{text.summary}</p>
          <Section title={t.sections.why}>
            <p>{text.why}</p>
          </Section>
          <ListSection title={t.sections.evidence} items={text.evidence} />
          <ListSection title={t.sections.benefits} items={text.benefits} />
          <ListSection title={t.sections.gaps} items={text.gaps} />
          <ListSection title={t.sections.risks} items={text.risks} />
        </div>
      )}
    </article>
  );
}

function ScoreBar({ label, value, big }: { label: string; value: number; big?: boolean }) {
  return (
    <div>
      <div className={cn("flex justify-between font-bold", big ? "text-base" : "text-xs uppercase")}>
        <span>{label}</span>
        <span dir="ltr">{value}/100</span>
      </div>
      <div
        className={cn("mt-1 w-full border-2 border-ink bg-paper", big ? "h-5" : "h-3")}
        role="meter"
        aria-label={label}
        aria-valuemin={0}
        aria-valuemax={100}
        aria-valuenow={value}
      >
        <div className="h-full bg-green-dark" style={{ width: `${Math.max(0, Math.min(100, value))}%` }} />
      </div>
    </div>
  );
}

function Section({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <section>
      <h3 className="font-heading text-sm font-bold uppercase tracking-wide text-green-dark">{title}</h3>
      <div className="mt-1">{children}</div>
    </section>
  );
}

function ListSection({ title, items }: { title: string; items: string[] }) {
  if (!items.length) return null;
  return (
    <Section title={title}>
      <ul className="list-disc space-y-1 ps-5">
        {items.map((it, i) => (
          <li key={i}>{it}</li>
        ))}
      </ul>
    </Section>
  );
}
