import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  // Enable static export for Azure Static Web Apps
  output: 'export',

  // Disable image optimization for static export
  images: {
    unoptimized: true,
  },
};

export default nextConfig;
