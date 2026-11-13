import Link from "next/link";
import { cn } from "@/lib/utils";

type Variant = "primary" | "dark" | "paper";

/* All class names are written out statically so Tailwind can see them. */
const styles: Record<
  Variant,
  {
    fill: string;
    text: string;
    panel: string;
    hoverText: string;
    reduceHoverText: string;
  }
> = {
  primary: {
    fill: "bg-green-light",
    text: "text-ink",
    panel: "bg-green-dark",
    hoverText: "group-hover:text-paper",
    reduceHoverText: "motion-reduce:group-hover:text-paper",
  },
  dark: {
    fill: "bg-green-dark",
    text: "text-paper",
    panel: "bg-ink",
    hoverText: "group-hover:text-paper",
    reduceHoverText: "motion-reduce:group-hover:text-paper",
  },
  paper: {
    fill: "bg-paper",
    text: "text-ink",
    panel: "bg-green-light",
    hoverText: "group-hover:text-ink",
    reduceHoverText: "motion-reduce:group-hover:text-ink",
  },
};

type BrutalButtonProps = {
  children: React.ReactNode;
  href?: string;
  variant?: Variant;
  type?: "button" | "submit";
  className?: string;
  disabled?: boolean;
  onClick?: () => void;
};

/**
 * The shared button for the whole app: flat fill, 3px black border, hard
 * shadow. On hover a second color panel slides in behind the label (from the
 * left in LTR, from the right in RTL) and the text color flips for contrast.
 * On press the button moves toward its shadow.
 *
 * Respects prefers-reduced-motion: no slide, instant color change.
 */
export function BrutalButton({
  children,
  href,
  variant = "primary",
  type = "button",
  className,
  disabled,
  onClick,
}: BrutalButtonProps) {
  const s = styles[variant];

  const classes = cn(
    "group relative inline-flex items-center justify-center overflow-hidden",
    "border-[3px] border-ink px-6 py-3",
    "font-heading text-base font-bold uppercase tracking-wide",
    "shadow-brutal transition-transform duration-150",
    "active:translate-x-[4px] active:translate-y-[4px] active:shadow-none",
    "motion-reduce:transition-none",
    "disabled:pointer-events-none disabled:opacity-60",
    s.fill,
    s.text,
    className,
  );

  const inner = (
    <>
      {/* Sliding panel — hidden entirely when reduced motion is requested.
          Slide direction (LTR/RTL) is handled by .brutal-panel in globals.css. */}
      <span aria-hidden className={cn("brutal-panel absolute inset-0 motion-reduce:hidden", s.panel)} />
      {/* Reduced-motion fallback: instant background swap on hover */}
      <span
        aria-hidden
        className={cn(
          "absolute inset-0 opacity-0",
          "motion-reduce:group-hover:opacity-100",
          s.panel,
        )}
      />
      <span
        className={cn(
          "relative transition-colors duration-300 motion-reduce:transition-none",
          s.hoverText,
          s.reduceHoverText,
        )}
      >
        {children}
      </span>
    </>
  );

  if (href) {
    return (
      <Link href={href} className={classes}>
        {inner}
      </Link>
    );
  }

  return (
    <button type={type} className={classes} disabled={disabled} onClick={onClick}>
      {inner}
    </button>
  );
}
