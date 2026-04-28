import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  // standalone para Docker self-hosted; Vercel usa su propia infraestructura
  output: process.env.VERCEL ? undefined : "standalone",
};

export default nextConfig;
