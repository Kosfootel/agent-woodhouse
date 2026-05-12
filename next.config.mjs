/** @type {import('next').NextConfig} */
const nextConfig = {
  output: "standalone",
  basePath: process.env.VIGIL_BASE_PATH || "",
  env: {
    VIGIL_API_BASE: process.env.VIGIL_API_BASE || "http://192.168.50.30:8000",
  },
  // Allow connecting to the GX-10 API
  async rewrites() {
    return [];
  },
};

export default nextConfig;
