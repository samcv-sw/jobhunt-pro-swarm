/** @type {import('next').NextConfig} */
const nextConfig = {
  // Required for Cloudflare Pages static export
  output: "export",
  trailingSlash: true,
  images: {
    // Static export does not support next/image optimization — use unoptimized
    unoptimized: true,
  },
};

export default nextConfig;
