FROM nginx:alpine

RUN apk add --no-cache openssl

# Full configuration, not a conf.d snippet: the file declares its own
# events/stream/http blocks because the proxy serves both a raw TCP listener
# and an HTTPS listener.
COPY nginx.conf /etc/nginx/nginx.conf
COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

# 80 is published as 8082 (plain, TCP passthrough), 443 is HTTPS.
EXPOSE 80 443

ENTRYPOINT ["/entrypoint.sh"]
