import { Source_Serif_4 } from "next/font/google";

/**
 * Serif used for assistant prose. Exposes the `--font-serif` CSS variable,
 * which tailwind.config maps to `font-serif`.
 *
 * Apply `sourceSerif.variable` to a wrapping element (or <html> in layout.tsx):
 *   <html className={sourceSerif.variable}>
 */
export const sourceSerif = Source_Serif_4({
  subsets: ["latin"],
  weight: ["300", "400", "500", "600"],
  variable: "--font-serif",
  display: "swap",
});
