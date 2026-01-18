import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  // Use standalone output for Azure Static Web Apps with SSR support
  output: 'standalone',
};

export default nextConfig;
