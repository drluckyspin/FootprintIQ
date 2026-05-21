/** @type {import('next').NextConfig} */
const nextConfig = {
  experimental: {
    // @duckdb/node-api is a native module — must be externalized in server components.
    serverComponentsExternalPackages: ["@duckdb/node-api"],
  },
  webpack: (config, { isServer }) => {
    if (!isServer) {
      // Never bundle DuckDB into the browser
      config.resolve.fallback = {
        ...config.resolve.fallback,
        "@duckdb/node-api": false,
      };
    }
    return config;
  },
};

module.exports = nextConfig;
