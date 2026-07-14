/* eslint-disable @typescript-eslint/no-require-imports */
const withPWA = require('next-pwa')({
  dest: 'public',
  disable: process.env.NODE_ENV === 'development',
  register: true,
  skipWaiting: true,
});

const withBundleAnalyzer = require('@next/bundle-analyzer')({
  enabled: process.env.ANALYZE === 'true',
});

/** @type {import('next').NextConfig} */
const nextConfig = {
  // Comment out output: "export" to deploy to Vercel and use full Next.js SSR & Image Optimization
  output: "export",
  trailingSlash: true,
  images: {
    // Enable WebP & AVIF for smaller image sizes on supported browsers
    formats: ['image/avif', 'image/webp'],
    unoptimized: true,
  },
};

export default withBundleAnalyzer(withPWA(nextConfig));
