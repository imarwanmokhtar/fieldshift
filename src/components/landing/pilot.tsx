import type { Dictionary } from "@/lib/i18n";

export function Pilot({ dict }: { dict: Dictionary }) {
  return (
    <section className="border-b-4 border-ink bg-paper">
      <div className="mx-auto max-w-6xl px-6 py-16 md:py-24">
        <div className="border-[3px] border-ink bg-green-dark p-8 text-paper shadow-brutal-lg md:p-12">
          <p className="font-heading text-sm font-bold uppercase tracking-widest text-green-light">
            {dict.pilot.label}
          </p>
          <p className="mt-2 font-heading text-4xl font-bold uppercase md:text-5xl">
            {dict.pilot.name}
          </p>
          <p className="mt-4 max-w-3xl text-base md:text-lg">{dict.pilot.body}</p>
        </div>
      </div>
    </section>
  );
}
