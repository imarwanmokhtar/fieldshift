import type { Dictionary } from "@/lib/i18n";

export function Principles({ dict }: { dict: Dictionary }) {
  return (
    <section className="border-b-4 border-ink bg-green-light">
      <div className="mx-auto max-w-6xl px-6 py-16 md:py-24">
        <h2 className="font-heading text-3xl font-bold uppercase tracking-tight md:text-4xl">
          {dict.principles.title}
        </h2>
        <ul className="card-lift mt-10 space-y-0 border-[3px] border-ink bg-paper shadow-brutal">
          {dict.principles.items.map((text, i) => (
            <li
              key={i}
              className={`px-6 py-5 font-heading text-lg font-bold md:text-xl ${
                i > 0 ? "border-t-[3px] border-ink" : ""
              }`}
            >
              <span className="mx-4 text-green-dark">{String(i + 1).padStart(2, "0")}</span>
              {text}
            </li>
          ))}
        </ul>
      </div>
    </section>
  );
}
