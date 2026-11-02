// Job: GODMODE Frontend. Purpose: Next.js config including optional API rewrites for local MVP.
const target = process.env.API_PROXY_TARGET || "http://localhost:8000/api/v1";
module.exports = {
  output: "standalone",
  async rewrites() {
    return [{ source: "/api/v1/:path*", destination: `${target}/:path*` }];
  },
};
