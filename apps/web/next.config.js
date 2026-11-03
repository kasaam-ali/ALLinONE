// Job: ALLinONE Frontend. Purpose: Next.js config with /api/v1 rewrite proxy to the FastAPI backend.
const target = process.env.API_PROXY_TARGET || "http://localhost:8010/api/v1";
module.exports = {
  output: "standalone",
  async rewrites() {
    return [{ source: "/api/v1/:path*", destination: `${target}/:path*` }];
  },
};
