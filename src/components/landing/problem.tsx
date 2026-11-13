import type { Dictionary } from "@/lib/i18n";

export function Problem({ dict }: { dict: Dictionary }) {
  return (
    <section className="border-b-4 border-ink bg-paper">
      <div className="mx-auto max-w-6xl px-6 py-16 md:py-24">
        <h2 className="font-heading text-3xl font-bold uppercase tracking-tight md:text-4xl">
          {dict.problem.title}
        </h2>
        <ul className="mt-10 grid gap-8 md:grid-cols-3">
          {dict.problem.items.map((text, i) => (
            <li
              key={i}
              className="border-[3px] border-ink bg-green-light p-6 text-base font-medium shadow-brutal"
            >
              {text}
            </li>
          ))}
        </ul>

        <h3 className="mt-20 font-heading text-2xl font-bold uppercase tracking-tight md:text-3xl">
          {dict.problem.whatTitle}
        </h3>
        <div className="mt-8 grid gap-8 md:grid-cols-3">
          {dict.problem.cards.map((card, i) => (
            <div key={i} className="border-[3px] border-ink bg-paper p-6 shadow-brutal">
              <p className="font-heading text-4xl font-bold">{String(i + 1).padStart(2, "0")}</p>
              <p className="mt-3 font-heading text-lg font-bold uppercase">{card.title}</p>
              <p className="mt-3 text-base">{card.body}</p>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}
