# STM32 Zephyr Firmware Build - SUCCESS

## What Was Done

The STM32 Zephyr firmware Docker build has been successfully fixed and tested. The build now works correctly for ARM64 cross-compilation.

## Key Changes Made

### 1. Dockerfile (`software/stm32/Dockerfile`)
- **Cached Workspace**: The Zephyr workspace initialization (west init/update) is now in a separate Docker layer that gets cached. This means the first build takes ~12 minutes, but subsequent builds are much faster (~90 seconds).
- **Fixed Permissions**: Added `--chown=user:user` when copying files and switched to non-root user before building.
- **Environment Variables**: Set `ZEPHYR_BASE=/workspace/zephyr` to ensure CMake finds Zephyr correctly.
- **Multi-stage Build**: The build stage creates the firmware, then a minimal runtime stage contains only OpenOCD and the compiled binaries.

### 2. CMakeLists.txt (`software/stm32/CMakeLists.txt`)
- **Correct Order**: `find_package(Zephyr)` must come before `project()` for Zephyr applications.
- **Proper Hints**: Uses `HINTS $ENV{ZEPHYR_BASE}` to help CMake locate Zephyr.

## Build Results

**Successful Build Output:**
```
Memory region         Used Size  Region Size  %age Used
           FLASH:       71260 B       128 KB     54.37%
             RAM:       24568 B        36 KB     66.64%
```

**Image Created:**
- Tag: `172.17.0.1:5000/cybics-stm32:latest`
- Platform: `linux/arm64`
- Size: ~70MB runtime image

## How to Use

### Initial Build (takes ~12 minutes)
```bash
cd /home/matt/gits/CybICS/software/stm32
docker buildx build --platform linux/arm64 -t 172.17.0.1:5000/cybics-stm32:latest --load .
```

### Subsequent Builds (takes ~90 seconds)
After making changes to your source code (src/main.c, src/display.c, etc.), rebuild:
```bash
docker buildx build --platform linux/arm64 -t 172.17.0.1:5000/cybics-stm32:latest --load .
```
The Zephyr workspace layer is cached, so only your application code is recompiled.

### Build All Services
Use the main build script which will include the STM32 image:
```bash
cd /home/matt/gits/CybICS/software
./build.sh
```

## How It Works

1. **Stage 1 - Build**:
   - Uses `ghcr.io/zephyrproject-rtos/zephyr-build:v0.26.6` as the base (has all Zephyr tools)
   - Downloads and caches the entire Zephyr v3.5.0 workspace (~2GB)
   - Copies your application code
   - Builds firmware for `nucleo_g070rb` board
   - Output: `zephyr.bin` and `zephyr.elf`

2. **Stage 2 - Runtime**:
   - Uses minimal `debian:12-slim` base
   - Installs OpenOCD for flashing
   - Copies compiled firmware from build stage
   - Exposes GDB (3333) and Telnet (4444) ports
   - CMD flashes firmware and runs OpenOCD as GDB server

## Files

- `Dockerfile` - Working multi-stage build with cached workspace
- `Dockerfile.old` - Original version (kept as backup)
- `Dockerfile.prebuilt` - Failed attempt using CI image (kept for reference)
- `CMakeLists.txt` - Fixed Zephyr CMake configuration
- `prj.conf` - Zephyr project configuration
- `src/` - Application source code
- `boards/` - Board-specific overlays

## Troubleshooting

### If build fails with "Cannot specify sources for target 'app'":
- Check that `find_package(Zephyr)` comes before `project()` in CMakeLists.txt
- Ensure `ZEPHYR_BASE` environment variable is set in Dockerfile

### If workspace download fails:
- Check internet connection
- May need to retry - GitHub can sometimes be slow

### If pushing to registry fails with HTTPS error:
- The local registry uses HTTP
- Use `--load` to load to local Docker instead of pushing
- Or configure Docker daemon for insecure registries

## Next Steps

The image is ready to use. You can now:
1. Deploy to Raspberry Pi using docker-compose
2. Flash the STM32 board via OpenOCD
3. Debug via GDB on port 3333
