/** @type {import('next').NextConfig} */
const nextConfig = {
  output: "standalone",
  // Allow connecting to the GX-10 API
  async rewrites() {
    return [];
  },
};

export default nextConfig;
