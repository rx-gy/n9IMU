###############################################################################
# Makefile for the project $(NAME) for an arduino target
###############################################################################

## General Flags
PROJECT = n9IMU
#MCU = atmega328p
NAME = n9IMU
TARGET = ../bin/$(NAME).elf
MAIN = main
CC = avr-gcc


### AVRDUDE STUFF BELOW ###

ARDUINO_VERSION = pro328
AVRDUDE_PORT=/dev/ttyUSB0
AVRDUDE=avrdude

MCU := $(shell grep $(ARDUINO_VERSION).build.mcu boards.txt | cut -d= -f2)
F_CPU := $(shell grep $(ARDUINO_VERSION).build.f_cpu boards.txt | cut -d= -f2)

AVRDUDE_PROGRAMER := $(shell grep $(ARDUINO_VERSION).upload.protocol boards.txt | cut -d= -f2)

# dirty hack to accomidate the arduino boards.txt file being wrong.
# can you believe they do this in the code rather than fixing their config file?
ifeq ($(AVRDUDE_PROGRAMER),stk500)
AVRDUDE_PROGRAMER=arduino
endif

AVRDUDE_SPEED := $(shell grep $(ARDUINO_VERSION).upload.speed boards.txt | cut -d= -f2)

AVRDUDE_MAXSIZE := $(shell grep $(ARDUINO_VERSION).upload.max_size boards.txt | cut -d= -f2)

AVRDUDE_FLAGS = -p $(MCU) -P $(AVRDUDE_PORT) -c $(AVRDUDE_PROGRAMER) -b $(AVRDUDE_SPEED)
AVRDUDE_WRITE_FLASH = -U flash:w:$(TARGET).hex



###-###


## Options common to compile, link and assembly rules
COMMON = -mmcu=$(MCU)

## Compile options common for all C compilation units.
CFLAGS = $(COMMON) -DTRUE=1 -DFALSE=0
CFLAGS += -Wall -Wstrict-prototypes -gdwarf-2 -Os -std=gnu99 -funsigned-char -funsigned-bitfields -fpack-struct -fshort-enums
CFLAGS += -MD -MP -MT $(*F).o -MF dep/$(@F).d -DF_CPU=$(F_CPU)

## Assembly specific flags
ASMFLAGS = $(COMMON)
ASMFLAGS += $(CFLAGS)
ASMFLAGS += -x assembler-with-cpp -Wa,-gdwarf2

## Linker flags
LDFLAGS = $(COMMON)
LDFLAGS +=  -Wl,-Map=$(NAME).map -lm


## Intel Hex file production flags
HEX_FLASH_FLAGS = -R .eeprom -R .fuse -R .lock -R .signature

HEX_EEPROM_FLAGS = -j .eeprom
HEX_EEPROM_FLAGS += --set-section-flags=.eeprom="alloc,load"
HEX_EEPROM_FLAGS += --change-section-lma .eeprom=0 --no-change-warnings


## Objects that must be built in order to link
OBJECTS = $(NAME).o TIMER.o UART.o 

## Objects explicitly added by the user
LINKONLYOBJECTS = 



## Build
all: $(TARGET) ../bin/$(NAME).hex $(NAME).eep $(NAME).lss size

## Compile
$(NAME).o: ../source/$(MAIN).c
	$(CC) $(INCLUDES) -o $(NAME).o $(CFLAGS) -c  $<


%.o: ../source/%.c
	$(CC) $(INCLUDES) $(CFLAGS) -c  $<

UART.o: ../lib/UART.c
	$(CC) $(INCLUDES) $(CFLAGS) -c $<

TIMER.o: ../lib/TIMER.c
	$(CC) $(INCLUDES) $(CFLAGS) -c $<

##Link
$(TARGET): $(OBJECTS)
	 $(CC) $(LDFLAGS) $(OBJECTS) $(LINKONLYOBJECTS) $(LIBDIRS) $(LIBS) -o $(TARGET)

%.hex: $(TARGET)
	avr-objcopy -O ihex $(HEX_FLASH_FLAGS)  $< $@

%.eep: $(TARGET)
	-avr-objcopy $(HEX_EEPROM_FLAGS) -O ihex $< $@ || exit 0

%.lss: $(TARGET)
	avr-objdump -h -S $< > $@

size: ${TARGET}
	@echo
	@avr-size  ${TARGET} #-C --mcu=${MCU}

# rule for uploading firmware:
program: $(TARGET).hex
	$(AVRDUDE) $(AVRDUDE_FLAGS) $(AVRDUDE_WRITE_FLASH) 


## Clean target
.PHONY: clean
clean:
	-rm -rf $(OBJECTS) $(NAME).elf dep/* ../bin/* $(NAME).hex $(NAME).eep $(NAME).lss $(NAME).map *.lst $(MAIN).*


## Other dependencies
-include $(shell mkdir dep 2>/dev/null & mkdir ../build 2>/dev/null & mkdir ../bin 2>/dev/null) $(wildcard dep/*)

