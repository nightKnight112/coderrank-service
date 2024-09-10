FROM eclipse-temurin:17-alpine


RUN apk add --no-cache python3 py3-pip


ENV JAVA_HOME=/opt/java/openjdk
ENV PATH="$JAVA_HOME/bin:/usr/bin/python3:$PATH"


ENTRYPOINT ["/bin/sh", "-c"]
CMD ["while true; do sleep 1000; done"]
