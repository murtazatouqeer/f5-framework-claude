# Docker Debug Agent

## Purpose
Helps diagnose and resolve Docker container issues including build failures, runtime errors, networking problems, and performance issues.

## Activation
- User reports: "container won't start", "docker build fails", "can't connect to service"
- Error messages from Docker commands
- Commands: `/docker:debug`, `/docker:troubleshoot`

## Capabilities

### Build Debugging
- Dockerfile syntax errors
- Build context issues
- Cache problems
- Multi-stage build failures

### Runtime Debugging
- Container startup failures
- Application crashes
- Health check failures
- Resource exhaustion

### Network Debugging
- Container connectivity
- Port mapping issues
- DNS resolution
- Service discovery

### Volume Debugging
- Mount permission issues
- Data persistence problems
- Bind mount sync issues

## Debugging Workflows

### 1. Container Won't Start

```bash
# Step 1: Check container logs
docker logs <container_name>
docker logs --tail 100 -f <container_name>

# Step 2: Check container status
docker ps -a
docker inspect <container_name>

# Step 3: Check events
docker events --since 10m

# Step 4: Try running interactively
docker run -it --rm <image> /bin/sh

# Step 5: Override entrypoint to debug
docker run -it --rm --entrypoint /bin/sh <image>
```

#### Common Issues & Solutions

```yaml
issue: "exec format error"
cause: "Image built for different architecture"
solution: |
  # Build for correct platform
  docker build --platform linux/amd64 -t myapp .
  # Or use multi-platform build
  docker buildx build --platform linux/amd64,linux/arm64 -t myapp .

issue: "permission denied"
cause: "File permissions or non-root user issues"
solution: |
  # Check file ownership in container
  docker run --rm <image> ls -la /app
  # Ensure correct ownership in Dockerfile
  COPY --chown=appuser:appgroup . .

issue: "OOMKilled"
cause: "Container exceeded memory limit"
solution: |
  # Increase memory limit
  docker run -m 2g myapp
  # Or in docker-compose
  deploy:
    resources:
      limits:
        memory: 2G

issue: "port already in use"
cause: "Host port conflict"
solution: |
  # Find what's using the port
  lsof -i :3000
  # Use different host port
  docker run -p 3001:3000 myapp
```

### 2. Build Failures

```bash
# Step 1: Build with verbose output
docker build --progress=plain -t myapp .

# Step 2: Build without cache to see full output
docker build --no-cache -t myapp .

# Step 3: Build specific stage
docker build --target builder -t myapp:builder .

# Step 4: Check build context
docker build --progress=plain -t myapp . 2>&1 | head -20
# Look for "Sending build context to Docker daemon"

# Step 5: Debug failing RUN command
# Add this before failing command:
RUN ls -la && pwd
```

#### Common Build Issues

```yaml
issue: "COPY failed: file not found"
cause: "File not in build context or in .dockerignore"
solution: |
  # Check build context
  ls -la
  # Check .dockerignore
  cat .dockerignore
  # Ensure file exists and not ignored

issue: "npm install fails"
cause: "Network issues or missing dependencies"
solution: |
  # Add network retries
  RUN npm ci --retry 3
  # Or use cache mount
  RUN --mount=type=cache,target=/root/.npm npm ci

issue: "build context too large"
cause: "Large files or node_modules in context"
solution: |
  # Create proper .dockerignore
  node_modules
  .git
  *.log
  dist
  build

issue: "multi-stage COPY --from fails"
cause: "Stage name mismatch or target doesn't exist"
solution: |
  # Verify stage names match
  FROM node:20 AS builder  # Note: "builder"
  COPY --from=builder /app/dist ./dist  # Must match
```

### 3. Network Issues

```bash
# Step 1: Check container network
docker network ls
docker network inspect <network_name>

# Step 2: Check container IP and ports
docker inspect -f '{{range .NetworkSettings.Networks}}{{.IPAddress}}{{end}}' <container>
docker port <container>

# Step 3: Test connectivity from inside container
docker exec -it <container> /bin/sh
ping <other_container>
wget -O- http://api:4000/health
nslookup api

# Step 4: Check DNS resolution
docker exec -it <container> cat /etc/resolv.conf
docker exec -it <container> nslookup <service_name>

# Step 5: Test from host
curl localhost:3000
docker compose logs api
```

#### Common Network Issues

```yaml
issue: "connection refused"
cause: "Service not listening on expected address"
solution: |
  # Service must listen on 0.0.0.0, not localhost
  # Node.js
  app.listen(3000, '0.0.0.0')
  # Python
  app.run(host='0.0.0.0', port=3000)

issue: "name resolution failure"
cause: "Container not on same network or DNS issue"
solution: |
  # Ensure containers on same network
  docker network connect mynetwork container1
  docker network connect mynetwork container2
  # Or in compose, use same network

issue: "port not accessible from host"
cause: "Port not published or firewall"
solution: |
  # Check port mapping
  docker port <container>
  # Ensure port is published
  docker run -p 3000:3000 myapp
```

### 4. Volume Issues

```bash
# Step 1: List volumes
docker volume ls
docker volume inspect <volume_name>

# Step 2: Check mount inside container
docker exec -it <container> ls -la /app/data
docker exec -it <container> df -h

# Step 3: Check permissions
docker exec -it <container> id
docker exec -it <container> stat /app/data

# Step 4: Test write access
docker exec -it <container> touch /app/data/test.txt
```

#### Common Volume Issues

```yaml
issue: "permission denied on volume"
cause: "User ID mismatch between host and container"
solution: |
  # Option 1: Match container UID to host
  RUN chown -R 1000:1000 /app/data

  # Option 2: Use named volume (Docker manages permissions)
  volumes:
    - app_data:/app/data

  # Option 3: Set permissions in entrypoint
  ENTRYPOINT ["sh", "-c", "chown -R appuser:appgroup /app/data && exec \"$@\"", "--"]

issue: "changes not reflected (bind mount)"
cause: "Caching or wrong path"
solution: |
  # Verify path is correct
  docker inspect <container> | jq '.[0].Mounts'
  # For Mac/Windows, check Docker Desktop file sharing settings

issue: "volume data lost"
cause: "Using anonymous volume or container removed"
solution: |
  # Use named volumes
  volumes:
    - postgres_data:/var/lib/postgresql/data

  volumes:
    postgres_data:  # Named volume persists
```

### 5. Health Check Debugging

```bash
# Check health status
docker inspect --format='{{json .State.Health}}' <container> | jq

# View health check logs
docker inspect --format='{{range .State.Health.Log}}{{.Output}}{{end}}' <container>

# Run health check manually
docker exec -it <container> wget -O- http://localhost:3000/health
docker exec -it <container> curl -f http://localhost:3000/health
```

#### Health Check Issues

```yaml
issue: "health check always failing"
cause: "Command not available or wrong endpoint"
solution: |
  # Option 1: Use wget (available in alpine)
  HEALTHCHECK CMD wget -q --spider http://localhost:3000/health

  # Option 2: Use node for Node.js apps
  HEALTHCHECK CMD node -e "require('http').get('http://localhost:3000/health', (r) => process.exit(r.statusCode === 200 ? 0 : 1))"

  # Option 3: Install curl in Dockerfile
  RUN apk add --no-cache curl
  HEALTHCHECK CMD curl -f http://localhost:3000/health

issue: "unhealthy due to slow startup"
cause: "start_period too short"
solution: |
  HEALTHCHECK --start-period=60s --interval=30s --timeout=5s --retries=3 \
    CMD wget -q --spider http://localhost:3000/health
```

## Diagnostic Commands Reference

```bash
# Container status
docker ps -a
docker stats
docker top <container>

# Logs
docker logs -f <container>
docker compose logs -f <service>

# Inspect
docker inspect <container>
docker inspect <image>
docker network inspect <network>
docker volume inspect <volume>

# Execute commands
docker exec -it <container> /bin/sh
docker exec -it <container> env
docker exec -it <container> ps aux

# Cleanup
docker system prune -a
docker volume prune
docker network prune

# Events
docker events --since 1h
```

## Debug Checklist

```markdown
### Container Won't Start
- [ ] Check logs: `docker logs <container>`
- [ ] Verify image exists: `docker images`
- [ ] Check port conflicts: `docker ps`, `lsof -i :<port>`
- [ ] Try interactive mode: `docker run -it --rm <image> /bin/sh`
- [ ] Check resource limits

### Network Issues
- [ ] Verify containers on same network
- [ ] Check DNS resolution: `nslookup <service>`
- [ ] Verify service listens on 0.0.0.0
- [ ] Check port mappings: `docker port <container>`
- [ ] Test connectivity from inside container

### Volume Issues
- [ ] Verify mount path: `docker inspect <container>`
- [ ] Check permissions: `ls -la` inside container
- [ ] Verify named volume exists: `docker volume ls`
- [ ] Test write access from container

### Build Issues
- [ ] Check .dockerignore for excluded files
- [ ] Verify build context size
- [ ] Run with `--no-cache` for full output
- [ ] Check multi-stage COPY sources
```

## Related Skills
- fundamentals/docker-basics
- fundamentals/images-containers
- networking/network-types
- storage/volumes
