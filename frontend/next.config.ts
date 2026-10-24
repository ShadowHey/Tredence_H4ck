import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  // The app is routinely opened through both localhost and 127.0.0.1 during
  // local development. Explicitly trust the loopback IP so Next's development
  // HMR connection is accepted and client-side pages can hydrate correctly.
  allowedDevOrigins: ["127.0.0.1"],
  cacheComponents: true,
  partialPrefetching: true,
  turbopack: {
    rules: {
      "*.css": {
        loaders: ["@tailwindcss/turbopack"],
        as: "*.css",
      },
    },
  },
};

export default nextConfig;
