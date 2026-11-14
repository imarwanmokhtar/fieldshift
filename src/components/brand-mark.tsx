import Image from "next/image";

/**
 * App logo + name for the headers. The logo sits on a small white tile with the app's
 * black border, so its light-green stripe stays visible on the light-green headers.
 * The image is decorative (alt=""): the "Field Shift" text next to it names the link.
 */
export function BrandMark() {
  return (
    <>
      <span className="inline-flex size-10 shrink-0 items-center justify-center border-[3px] border-ink bg-paper">
        <Image src="/logo.png" alt="" width={32} height={32} priority />
      </span>
      <span>Field Shift</span>
    </>
  );
}
