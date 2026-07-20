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
  // Removed output: "export" to deploy to Vercel and use full Next.js SSR & ISR
  trailingSlash: true,
  images: {
    // Enable WebP & AVIF for smaller image sizes on supported browsers
    formats: ['image/avif', 'image/webp'],
    unoptimized: true, // Needs to be removed if using Vercel Image Optimization, but keeping for now
  },
  compress: true,
  experimental: {
    optimizePackageImports: ['lucide-react', 'date-fns', 'lodash'],
  },
  compiler: {
    removeConsole: process.env.NODE_ENV === 'production' ? { exclude: ['error'] } : false,
  }
};

export default withBundleAnalyzer(withPWA(nextConfig));
