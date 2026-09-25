FROM caddy:2.10.2-alpine

COPY --chown=1000:1000 app /srv/app
COPY --chown=1000:1000 ui /srv/ui
COPY --chown=1000:1000 deploy/web/config.js /srv/app/config.js
COPY deploy/web/Caddyfile /etc/caddy/Caddyfile

USER 1000:1000
