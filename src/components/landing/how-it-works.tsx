import type { Dictionary } from "@/lib/i18n";

export function HowItWorks({ dict }: { dict: Dictionary }) {
  return (
    <section className="border-b-4 border-ink bg-green-dark text-paper">
      <div className="mx-auto max-w-6xl px-6 py-16 md:py-24">
        <h2 className="font-heading text-3xl font-bold uppercase tracking-tight md:text-4xl">
          {dict.how.title}
        </h2>
        <ol className="mt-10 grid gap-8 md:grid-cols-3">
          {dict.how.steps.map((step, i) => (
            <li key={i} className="border-[3px] border-paper p-6">
              <p className="font-heading text-sm font-bold uppercase tracking-widest text-green-light">
                {dict.how.stepLabel} {i + 1}
              </p>
              <p className="mt-2 font-heading text-2xl font-bold uppercase">{step.title}</p>
              <p className="mt-3 text-base text-paper">{step.body}</p>
            </li>
          ))}
        </ol>
      </div>
    </section>
  );
}
