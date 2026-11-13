import type { Dictionary } from "@/lib/i18n";

export function DataSources({ dict }: { dict: Dictionary }) {
  return (
    <section className="border-b-4 border-ink bg-paper">
      <div className="mx-auto max-w-6xl px-6 py-16 md:py-24">
        <h2 className="font-heading text-3xl font-bold uppercase tracking-tight md:text-4xl">
          {dict.data.title}
        </h2>
        <div className="mt-10 grid gap-6 sm:grid-cols-2 lg:grid-cols-3">
          {dict.data.sources.map((source) => (
            <div
              key={source.name}
              className="border-[3px] border-ink bg-green-light p-6 shadow-brutal"
            >
              <p className="font-heading text-lg font-bold uppercase">{source.name}</p>
              <p className="mt-3 text-base">{source.body}</p>
            </div>
          ))}
          <div className="flex items-center border-[3px] border-ink bg-ink p-6 text-paper shadow-brutal">
            <p className="text-base">{dict.data.explain}</p>
          </div>
        </div>
        <p className="mt-10 max-w-3xl text-sm italic">{dict.data.note}</p>
      </div>
    </section>
  );
}
