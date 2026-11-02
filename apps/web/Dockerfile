# Web image: builds the Next.js app and runs the standalone server.
FROM node:20-alpine AS build
WORKDIR /app
COPY package.json package-lock.json* ./
RUN npm install
COPY . .
ARG API_PROXY_TARGET=http://api:8000/api/v1
ENV API_PROXY_TARGET=$API_PROXY_TARGET
RUN npm run build
FROM node:20-alpine
WORKDIR /app
ENV NODE_ENV=production
COPY --from=build /app/.next/standalone ./
COPY --from=build /app/.next/static ./.next/static
EXPOSE 3000
CMD ["node", "server.js"]
