FROM alpine:3.19

RUN apk add --no-cache g++ make
RUN adduser -D -u 1000 sandboxuser
USER sandboxuser
WORKDIR /home/sandboxuser

CMD ["sh", "-c", "g++ -O2 -std=c++17 solution.cpp -o solution && ./solution"]
