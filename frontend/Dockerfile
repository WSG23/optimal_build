FROM node:20-alpine AS builder

WORKDIR /workspace/frontend

ARG VITE_API_BASE_URL
ENV VITE_API_BASE_URL=${VITE_API_BASE_URL}

COPY frontend/package.json frontend/pnpm-lock.yaml ./
RUN corepack enable && corepack prepare pnpm@10.17.1 --activate
RUN pnpm install --frozen-lockfile

COPY frontend/ .
COPY core/design-tokens /workspace/core/design-tokens
RUN pnpm run build


FROM nginx:1.27-alpine AS runtime

RUN apk add --no-cache gettext

COPY --from=builder /workspace/frontend/dist /usr/share/nginx/html
COPY frontend/nginx/default.conf.template /etc/nginx/templates/default.conf.template
COPY frontend/nginx/entrypoint.sh /entrypoint.sh

RUN chmod +x /entrypoint.sh

ENV PORT=8080
EXPOSE 8080

ENTRYPOINT ["/entrypoint.sh"]
