FROM node:18-alpine

RUN apk add --no-cache curl bash

RUN npm install -g @frangoteam/fuxa-min@1.2.6

COPY fuxa-project.json add-user-*.json settings.json /config/
COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

EXPOSE 1881
ENTRYPOINT ["/entrypoint.sh"]
