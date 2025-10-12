# Docker Deployment for Dunebugger on Raspberry Pi 4

## Prerequisites

1. **Docker and Docker Compose installed on Raspberry Pi 4**
   ```bash
   curl -fsSL https://get.docker.com -o get-docker.sh
   sudo sh get-docker.sh
   sudo apt-get install docker-compose-plugin
   ```

2. **Add your user to the docker group**
   ```bash
   sudo usermod -aG docker $USER
   # Logout and login again for changes to take effect
   ```

3. **Create local directories for volume mounts**
   ```bash
   sudo mkdir -p /home/pi/dunebugger/{config,music,sfx,sequences}
   sudo chown -R $USER:$USER /home/pi/dunebugger/
   ```

## Services Included

The Docker Compose setup includes two services:

1. **NATS Server** - Message queue for dunebugger communication
   - Port 4222: NATS client connections
   - Port 8222: HTTP monitoring interface
   - Web monitoring: http://localhost:8222

2. **Dunebugger App** - Main application with GPIO control
   - GPIO and audio device access
   - Volume mounts for local directories
   - Depends on NATS server health check

## Building and Running

### Option 1: Using Docker Compose (Recommended)

1. **Build and start all services**
   ```bash
   docker-compose up -d --build
   ```

2. **View logs for specific services**
   ```bash
   # View dunebugger logs
   docker-compose logs -f dunebugger
   
   # View NATS server logs
   docker-compose logs -f nats-server
   
   # View all logs
   docker-compose logs -f
   ```

3. **Check service status**
   ```bash
   docker-compose ps
   ```

4. **Stop all services**
   ```bash
   docker-compose down
   ```

### Option 2: Using Docker directly

If you prefer to run containers individually:

1. **Create the network first**
   ```bash
   docker network create dunebugger-network --driver bridge --subnet 172.20.0.0/16
   ```

2. **Start NATS server**
   ```bash
   docker run -d \
     --name nats-server \
     --network dunebugger-network \
     -p 4222:4222 \
     -p 8222:8222 \
     --restart unless-stopped \
     nats -m 8222 -DV
   ```

3. **Build the dunebugger image**
   ```bash
   docker build -t dunebugger-app .
   ```

4. **Run the dunebugger container**
   ```bash
   docker run -d \
     --name dunebugger-app \
     --privileged \
     --device /dev/gpiomem:/dev/gpiomem \
     --device /dev/mem:/dev/mem \
     --device /dev/snd:/dev/snd \
     -v /home/pi/dunebugger/config:/app/app/config:rw \
     -v /home/pi/dunebugger/music:/app/music:rw \
     -v /home/pi/dunebugger/sfx:/app/sfx:rw \
     -v /home/pi/dunebugger/sequences:/app/sequences:rw \
     -v /run/user/1000/pulse:/run/user/1000/pulse \
     --network dunebugger-network \
     --cap-add SYS_RAWIO \
     --cap-add SYS_ADMIN \
     --security-opt seccomp:unconfined \
     -e PULSE_RUNTIME_PATH=/run/user/1000/pulse \
     --restart unless-stopped \
     dunebugger-app
   ```

## Service Communication

The dunebugger application connects to NATS using:
- **Host:** `nats-server` (container hostname)
- **Port:** `4222`
- **Full URL:** `nats://nats-server:4222`

## Monitoring

### NATS Server Monitoring
- **Web Interface:** http://localhost:8222 (when running on Raspberry Pi)
- **Health Check:** Built-in health check ensures NATS is ready before starting dunebugger
- **Command Line:** `docker exec -it nats-server nats-server --help`

### Container Health
```bash
# Check if all services are healthy
docker-compose ps

# View detailed container information
docker inspect dunebugger-app
docker inspect nats-server
```

## Connecting Other Containers

To connect other containers to the same network:

```yaml
# In another docker-compose.yml file
services:
  your-other-service:
    # ... your service configuration
    networks:
      - dunebugger-network

networks:
  dunebugger-network:
    external: true
```

Or using docker run:
```bash
docker run --network dunebugger-network your-other-container
```

## Volume Mounts

The following directories are mounted from the Raspberry Pi host:

- `/home/pi/dunebugger/config` → `/app/app/config` (Configuration files)
- `/home/pi/dunebugger/music` → `/app/music` (Music files)
- `/home/pi/dunebugger/sfx` → `/app/sfx` (Sound effects)
- `/home/pi/dunebugger/sequences` → `/app/sequences` (Sequence files)

Make sure these directories exist on your Raspberry Pi and contain the necessary files.

## GPIO Access

The container is configured with:
- Privileged mode for full hardware access
- GPIO device mounts (`/dev/gpiomem`, `/dev/mem`)
- Required capabilities (`SYS_RAWIO`, `SYS_ADMIN`)

## Audio Support

Audio support is enabled through:
- VLC installation in the container
- ALSA device mounting (`/dev/snd`)
- PulseAudio socket mounting (if using PulseAudio)

## Troubleshooting

1. **Service Startup Issues**
   ```bash
   # Check if NATS server started correctly
   docker-compose logs nats-server
   
   # Check if dunebugger is waiting for NATS
   docker-compose logs dunebugger
   
   # Restart specific service
   docker-compose restart nats-server
   docker-compose restart dunebugger
   ```

2. **NATS Connection Issues**
   ```bash
   # Test NATS connectivity from dunebugger container
   docker exec -it dunebugger-app ping nats-server
   
   # Check NATS server status
   curl http://localhost:8222/varz
   ```

3. **GPIO Permission Issues**
   ```bash
   # Check if gpio group exists and add user
   sudo groupadd gpio
   sudo usermod -a -G gpio $USER
   ```

4. **Audio Issues**
   ```bash
   # Test audio devices in container
   docker exec -it dunebugger-app aplay -l
   ```

5. **Volume Mount Issues**
   ```bash
   # Check if directories exist and have correct permissions
   ls -la /home/pi/dunebugger/
   sudo chown -R $USER:$USER /home/pi/dunebugger/
   ```

6. **Network Issues**
   ```bash
   # Check network exists
   docker network ls | grep dunebugger
   
   # Inspect network details
   docker network inspect dunebugger-network
   ```

7. **Container Status**
   ```bash
   # Check container health
   docker-compose ps
   
   # Interactive debugging
   docker exec -it dunebugger-app /bin/bash
   docker exec -it nats-server /bin/sh
   ```

## Network Configuration

The custom network `dunebugger-network` uses subnet `172.20.0.0/16`. You can modify this in the docker-compose.yml file if it conflicts with your existing network setup.

### Service Discovery
- **NATS Server:** Available at `nats-server:4222` from dunebugger container
- **Dunebugger App:** Available at `dunebugger:8080` (if you expose ports) from other containers

## Configuration Updates

When updating your dunebugger application:

1. **Code changes:** Use `docker-compose up -d --build` to rebuild and restart
2. **Config file changes:** Files are mounted as volumes, so changes are immediate
3. **NATS server updates:** `docker-compose pull nats-server && docker-compose up -d`

## Service Dependencies

The startup order is managed automatically:
1. **NATS Server** starts first and health check ensures it's ready
2. **Dunebugger** starts only after NATS server is healthy
3. Both services restart automatically if they fail (`restart: unless-stopped`)