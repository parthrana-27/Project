FROM openjdk:17-alpine

RUN adduser -D -u 1000 sandboxuser
USER sandboxuser
WORKDIR /home/sandboxuser

CMD ["sh", "-c", "javac Solution.java && java Solution"]
