import type { Config } from "tailwindcss";

export default {
  content: ["./src/**/*.{js,ts,jsx,tsx,mdx}"],
  theme: {
    extend: {
      colors: {
        main: {
          green: "#3FA780",
          blue: "#678AFF",
          red: "#FF6767",
        },
        neutral: {
          black: "#000000",
          "1": "#26262C",
          "2": "#474653",
          "3": "#6B6A7B",
          "4": "#ADACB9",
          "5": "#CECDD5",
          "6": "#E4E4E8",
          "7": "#EFEFF1",
          "8": "#FAF9FA",
          white: "#FFFFFF",
        },
      },
      fontFamily: {
        pretendard: ["Pretendard", "sans-serif"],
      },
      fontSize: {
        xs: "12px", // Extra Small
        sm: "14px", // Small
        base: "16px", // Base
        lg: "20px", // Large
        xl: "24px", // Extra Large
        "2xl": "30px", // 2 Extra Large
      },
      fontWeight: {
        regular: "400",
        medium: "500",
        semibold: "600",
        bold: "700",
      },
    },
  },
  plugins: [],
} satisfies Config;
