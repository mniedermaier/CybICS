#include <fcntl.h>
#include <unistd.h>
#include <stdlib.h>
#include <stdio.h>

#define FLASH_DEV   "/dev/mmcblk0"
#define LUKS_DEV    "/dev/mmcblk0p2"
#define MAPPER_NAME "firmware"
#define BASE_INIT   0x80
#define KEY_LENGTH  32

int main(void) {
    unsigned char key[KEY_LENGTH];
    char key_path[] = "/tmp/.fwkey_XXXXXX";
    char cmd[256];
    int fd, kfd;

    fd = open(FLASH_DEV, O_RDONLY);
    lseek(fd, BASE_INIT, SEEK_SET);
    read(fd, key, KEY_LENGTH);
    close(fd);

    kfd = mkstemp(key_path);
    write(kfd, key, KEY_LENGTH);
    close(kfd);

    snprintf(cmd, sizeof(cmd),
        "cryptsetup open --type luks2 --key-file %s %s %s",
        key_path, LUKS_DEV, MAPPER_NAME);
    system(cmd);

    unlink(key_path);
    return 0;
}