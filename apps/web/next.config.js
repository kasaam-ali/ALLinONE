// Next.js config: standalone output and a dev/prod proxy from /api/v1 to the backend.
const target = process.env.API_PROXY_TARGET || "http://localhost:8000/api/v1";
module.exports = {
  output: "standalone",
  async rewrites() {
    return [{ source: "/api/v1/:path*", destination: `${target}/:path*` }];
  },
};
