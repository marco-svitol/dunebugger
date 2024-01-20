// changes clock stretch timout for a given chip
// use: i2c_set_tout base_address delay
// where base_address depends on i2cn and chip type
// delay is in uS, e.g 50000 is 0.5 seconds
// -----------------------------------------------------------------------------
// Code modified from raspihats 'i2c1_set_clkt_tout.c':
// https://raspihats.com/i2c-hat/2016/02/16/raspberry-pi-i2c-clock-stretch-timeout.html
// base address depends on type
// ARM11 based (BCM2835) 0x20804000
// Raspberry Pi B
// Raspberry Pi B2
// Raspberry Pi A+
// Raspberry Pi B+
// Raspberry Pi Zero
// Cortex-A7 based (BCM2836)  ?????
// Raspberry Pi 2 B
// Cortex-A53 based (BCM2837) ?????
// Raspberry Pi 3 B

#include<stdio.h>
#include<stdint.h>
#include<stdlib.h>
#include<fcntl.h>
#include<sys/mman.h>
#include<unistd.h>
#include<errno.h>
#include<stdio.h>

//#define I2C1_BASE (0x20804000) //chip 2835  
#define BLOCK_SIZE (4*8)

typedef struct {
	uint32_t C;
	uint32_t S;
	uint32_t DLEN;
	uint32_t A;
	uint32_t FIFO;
	uint32_t DIV;
	uint32_t DEL;
	uint32_t CLKT;
} i2c_reg_map_t;


int main(int argc, char *argv[]) {
	char buffer[100];
	int file_ref;
	void *map;
	i2c_reg_map_t *i2c_reg_map;
	int tout;
    uint32_t i2c_base;

	if(argc != 3) {
        printf("%s","ERROR use: i2c_set_tout base_address delay\n");
		return 1;
	}
	
	tout = atoi(argv[2]);
	i2c_base = atoi(argv[1]);
	
	if((tout <= 0) || (tout > 65535)) {
        printf("ERROR timeout value must be 0 to 65535\n");
		return 1;
	}

	if((file_ref = open("/dev/mem", O_RDWR | O_SYNC)) == -1) {
		printf("ERROR driver open FAILED (try sudo)");
		return 1;
	}

	map = mmap(	NULL, //auto choose address
			BLOCK_SIZE, //map length
			PROT_READ | PROT_WRITE, //enable read, write
			MAP_SHARED, //shared with other process
			file_ref, // file reference
			i2c_base // offset to I2C1
	);

	if(map == MAP_FAILED) {
		printf("ERROR mmap FAILED");
		return 1;
	}

	i2c_reg_map = (i2c_reg_map_t *)map;

	i2c_reg_map->CLKT = tout;
	//sprintf(buffer, "CLKT.TOUT = 0x%.8X", i2c_reg_map->CLKT);
	sprintf(buffer, "OK CLKT.TOUT = %d", i2c_reg_map->CLKT);
	printf(buffer);
	
    // Don't forget to free the mmapped memory
    if (munmap(map, BLOCK_SIZE) == -1) {
		printf("ERROR munmap FAILED");
		return 1;
    }

    // Un-mmaping doesn't close the file, so we still need to do that
    close(file_ref);
	
	return 0;
}
// compile with gcc -o i2c_set_tout i2c_set_tout.c
