import type { Config } from "tailwindcss";

const config: Config = {
  content: ["./src/**/*.{js,ts,jsx,tsx,mdx}"],
  theme: {
    extend: {
      colors: {
        ink: "#17201B",
        moss: "#426B4F",
        clay: "#B95D37",
        flax: "#E9C46A",
        paper: "#F7F5EF",
        cloud: "#EDF2F0"
      },
      boxShadow: {
        panel: "0 18px 60px rgba(23, 32, 27, 0.10)"
      }
    }
  },
  plugins: []
};

export default config;
