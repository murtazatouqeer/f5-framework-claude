---
name: dockerfile-java
description: Production-ready Java Dockerfile templates
applies_to: docker
variables:
  - java_version: Java version (17, 21)
  - build_tool: Maven, Gradle
  - app_port: Application port
---

# Java Dockerfile Templates

## Spring Boot with Maven

```dockerfile
# syntax=docker/dockerfile:1

# ===== Build Stage =====
FROM eclipse-temurin:{{java_version}}-jdk-alpine AS builder

WORKDIR /app

# Copy Maven wrapper and pom
COPY mvnw pom.xml ./
COPY .mvn .mvn

# Download dependencies
RUN ./mvnw dependency:go-offline -B

# Copy source and build
COPY src src
RUN ./mvnw package -DskipTests -B

# ===== Production Stage =====
FROM eclipse-temurin:{{java_version}}-jre-alpine

WORKDIR /app

# Security: Non-root user
RUN addgroup -g 1001 spring && \
    adduser -u 1001 -G spring -D spring

# Copy JAR
COPY --from=builder --chown=spring:spring /app/target/*.jar app.jar

USER spring

EXPOSE {{app_port}}

HEALTHCHECK --interval=30s --timeout=3s --start-period=30s --retries=3 \
  CMD wget --no-verbose --tries=1 --spider http://localhost:{{app_port}}/actuator/health || exit 1

ENTRYPOINT ["java", "-jar", "app.jar"]
```

## Spring Boot with Gradle

```dockerfile
# syntax=docker/dockerfile:1

FROM eclipse-temurin:{{java_version}}-jdk-alpine AS builder

WORKDIR /app

COPY gradlew build.gradle settings.gradle ./
COPY gradle gradle

RUN ./gradlew dependencies --no-daemon

COPY src src

RUN ./gradlew bootJar --no-daemon -x test

FROM eclipse-temurin:{{java_version}}-jre-alpine

WORKDIR /app

RUN addgroup -g 1001 spring && \
    adduser -u 1001 -G spring -D spring

COPY --from=builder --chown=spring:spring /app/build/libs/*.jar app.jar

USER spring

EXPOSE {{app_port}}

ENTRYPOINT ["java", "-jar", "app.jar"]
```

## With Layered JAR (Spring Boot)

```dockerfile
# syntax=docker/dockerfile:1

FROM eclipse-temurin:{{java_version}}-jdk-alpine AS builder

WORKDIR /app

COPY mvnw pom.xml ./
COPY .mvn .mvn
RUN ./mvnw dependency:go-offline -B

COPY src src
RUN ./mvnw package -DskipTests -B

# Extract layers
RUN java -Djarmode=layertools -jar target/*.jar extract

FROM eclipse-temurin:{{java_version}}-jre-alpine

WORKDIR /app

RUN addgroup -g 1001 spring && \
    adduser -u 1001 -G spring -D spring

# Copy layers separately (better caching)
COPY --from=builder --chown=spring:spring /app/dependencies/ ./
COPY --from=builder --chown=spring:spring /app/spring-boot-loader/ ./
COPY --from=builder --chown=spring:spring /app/snapshot-dependencies/ ./
COPY --from=builder --chown=spring:spring /app/application/ ./

USER spring

EXPOSE {{app_port}}

ENTRYPOINT ["java", "org.springframework.boot.loader.launch.JarLauncher"]
```

## With JVM Optimization

```dockerfile
# syntax=docker/dockerfile:1

FROM eclipse-temurin:{{java_version}}-jdk-alpine AS builder

WORKDIR /app

COPY mvnw pom.xml ./
COPY .mvn .mvn
RUN ./mvnw dependency:go-offline -B

COPY src src
RUN ./mvnw package -DskipTests -B

FROM eclipse-temurin:{{java_version}}-jre-alpine

WORKDIR /app

RUN addgroup -g 1001 spring && \
    adduser -u 1001 -G spring -D spring

COPY --from=builder --chown=spring:spring /app/target/*.jar app.jar

USER spring

EXPOSE {{app_port}}

# JVM optimization flags
ENV JAVA_OPTS="-XX:+UseContainerSupport \
  -XX:MaxRAMPercentage=75.0 \
  -XX:+UseG1GC \
  -XX:+UseStringDeduplication \
  -Djava.security.egd=file:/dev/./urandom"

ENTRYPOINT ["sh", "-c", "java $JAVA_OPTS -jar app.jar"]
```

## Native Image (GraalVM)

```dockerfile
# syntax=docker/dockerfile:1

FROM ghcr.io/graalvm/native-image-community:{{java_version}} AS builder

WORKDIR /app

COPY mvnw pom.xml ./
COPY .mvn .mvn
RUN ./mvnw dependency:go-offline -B

COPY src src

# Build native image
RUN ./mvnw -Pnative native:compile -DskipTests -B

FROM gcr.io/distroless/base-debian12

WORKDIR /app

COPY --from=builder /app/target/myapp /app/myapp

USER nonroot:nonroot

EXPOSE {{app_port}}

ENTRYPOINT ["/app/myapp"]
```

## Quarkus

```dockerfile
# syntax=docker/dockerfile:1

FROM eclipse-temurin:{{java_version}}-jdk-alpine AS builder

WORKDIR /app

COPY mvnw pom.xml ./
COPY .mvn .mvn
RUN ./mvnw dependency:go-offline -B

COPY src src

RUN ./mvnw package -DskipTests -B

FROM eclipse-temurin:{{java_version}}-jre-alpine

WORKDIR /app

RUN addgroup -g 1001 quarkus && \
    adduser -u 1001 -G quarkus -D quarkus

COPY --from=builder --chown=quarkus:quarkus /app/target/quarkus-app/lib/ /app/lib/
COPY --from=builder --chown=quarkus:quarkus /app/target/quarkus-app/*.jar /app/
COPY --from=builder --chown=quarkus:quarkus /app/target/quarkus-app/app/ /app/app/
COPY --from=builder --chown=quarkus:quarkus /app/target/quarkus-app/quarkus/ /app/quarkus/

USER quarkus

EXPOSE {{app_port}}

ENV JAVA_OPTS="-Dquarkus.http.host=0.0.0.0"

ENTRYPOINT ["java", "-jar", "/app/quarkus-run.jar"]
```

## Quarkus Native

```dockerfile
# syntax=docker/dockerfile:1

FROM quay.io/quarkus/ubi-quarkus-mandrel-builder-image:jdk-{{java_version}} AS builder

WORKDIR /app

COPY --chown=quarkus:quarkus mvnw pom.xml ./
COPY --chown=quarkus:quarkus .mvn .mvn

USER quarkus
RUN ./mvnw dependency:go-offline -B

COPY --chown=quarkus:quarkus src src

RUN ./mvnw package -Pnative -DskipTests -B

FROM quay.io/quarkus/quarkus-micro-image:2.0

WORKDIR /app

COPY --from=builder /app/target/*-runner /app/application

USER 1001

EXPOSE {{app_port}}

ENTRYPOINT ["./application", "-Dquarkus.http.host=0.0.0.0"]
```

## With BuildKit Cache

```dockerfile
# syntax=docker/dockerfile:1

FROM eclipse-temurin:{{java_version}}-jdk-alpine AS builder

WORKDIR /app

COPY mvnw pom.xml ./
COPY .mvn .mvn

# Cache Maven dependencies
RUN --mount=type=cache,target=/root/.m2 \
    ./mvnw dependency:go-offline -B

COPY src src

RUN --mount=type=cache,target=/root/.m2 \
    ./mvnw package -DskipTests -B

FROM eclipse-temurin:{{java_version}}-jre-alpine

WORKDIR /app

RUN addgroup -g 1001 spring && \
    adduser -u 1001 -G spring -D spring

COPY --from=builder --chown=spring:spring /app/target/*.jar app.jar

USER spring

EXPOSE {{app_port}}

ENTRYPOINT ["java", "-jar", "app.jar"]
```

## Development Template

```dockerfile
# syntax=docker/dockerfile:1

FROM eclipse-temurin:{{java_version}}-jdk-alpine

WORKDIR /app

# Copy dependencies
COPY mvnw pom.xml ./
COPY .mvn .mvn
RUN ./mvnw dependency:go-offline -B

# Copy source
COPY src src

EXPOSE {{app_port}}
EXPOSE 5005

# Debug port enabled
ENTRYPOINT ["./mvnw", "spring-boot:run", "-Dspring-boot.run.jvmArguments=-agentlib:jdwp=transport=dt_socket,server=y,suspend=n,address=*:5005"]
```

## .dockerignore

```dockerignore
# Build outputs
target
build
*.jar
*.war
*.class

# IDE
.idea
*.iml
.vscode
*.swp
.project
.classpath
.settings

# Git
.git
.gitignore

# Docker
Dockerfile*
docker-compose*
.dockerignore

# Environment
.env
.env.*

# Logs
*.log

# Documentation
docs
*.md
!README.md

# OS
.DS_Store
Thumbs.db

# Test reports
test-output
surefire-reports
```

## Build Commands

```bash
# Basic build
docker build -t myapp:latest .

# Skip tests explicitly
docker build --build-arg SKIP_TESTS=true -t myapp:latest .

# With memory limit for build
docker build --memory=4g -t myapp:latest .

# Multi-platform
docker buildx build \
  --platform linux/amd64,linux/arm64 \
  -t myapp:latest \
  --push .
```

## docker-compose for Development

```yaml
services:
  app:
    build:
      context: .
      target: builder
    ports:
      - "{{app_port}}:{{app_port}}"
      - "5005:5005"  # Debug port
    volumes:
      - ./src:/app/src
      - maven-cache:/root/.m2
    environment:
      - SPRING_PROFILES_ACTIVE=dev
    command: ./mvnw spring-boot:run -Dspring-boot.run.jvmArguments="-agentlib:jdwp=transport=dt_socket,server=y,suspend=n,address=*:5005"

volumes:
  maven-cache:
```
