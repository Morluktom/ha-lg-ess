FROM homeassistant/home-assistant:2026.3

# inotify-tools für Auto-Reload bei Dateiänderungen
RUN apk add --no-cache inotify-tools

COPY ./start.sh /start.sh
RUN chmod +x /start.sh

ENTRYPOINT ["/start.sh"]
