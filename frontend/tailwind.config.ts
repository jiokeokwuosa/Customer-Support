import type { Config } from "tailwindcss";

/** Professional support palette — mirrored in globals.css @theme tokens. */
const config = {
  theme: {
    extend: {
      colors: {
        surface: {
          DEFAULT: "#ffffff",
          muted: "#f8fafc",
          elevated: "#f1f5f9",
        },
        ink: {
          DEFAULT: "#0f172a",
          muted: "#475569",
          subtle: "#64748b",
        },
        primary: {
          DEFAULT: "#1d4ed8",
          hover: "#1e40af",
          subtle: "#dbeafe",
        },
        border: {
          DEFAULT: "#e2e8f0",
          strong: "#cbd5e1",
        },
        success: {
          DEFAULT: "#15803d",
          subtle: "#dcfce7",
        },
        warning: {
          DEFAULT: "#b45309",
          subtle: "#fef3c7",
        },
        danger: {
          DEFAULT: "#b91c1c",
          subtle: "#fee2e2",
        },
      },
      borderRadius: {
        card: "0.75rem",
        button: "0.5rem",
      },
      boxShadow: {
        card: "0 1px 3px 0 rgb(15 23 42 / 0.08), 0 1px 2px -1px rgb(15 23 42 / 0.08)",
      },
    },
  },
} satisfies Config;

export default config;
