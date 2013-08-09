/****************************************************************************
* main.c - n9IMU Project v0.5 for AVR (libc)                                *
* Copyright 2011 Nixotic                                                    *
* http://...                                                                *
* Based on work by Filipe Vieira & various contributors                     *
* http://code.google.com/p/itg-3200driver                                   *
* Based on work by Joerg Wunsch <joerg@FreeBSD.ORG>                         *
* http://www.nongnu.org/avr-libc/user-manual/group__twi__demo.html          *
*                                                                           *
* This library is free software: you can redistribute it and/or modify      *
* it under the terms of the GNU Lesser General Public License as published  *
* by the Free Software Foundation, either version 3 of the License, or      *
* (at your option) any later version.                                       *
*                                                                           *
* This program is distributed in the hope that it will be useful,           *
* but WITHOUT ANY WARRANTY; without even the implied warranty of            *
* MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the             *
* GNU Lesser General Public License for more details.                       *
*                                                                           *
* You should have received a copy of the GNU Lesser General Public License  *
* along with this program.  If not, see <http://www.gnu.org/licenses/>.     *
****************************************************************************/
/****************************************************************************
* Tested on Arduino Mega with ITG-3200 Breakout                             *
* SCL     -> pin 21     (no pull up resistors)                              *
* SDA     -> pin 20     (no pull up resistors)                              *
* CLK & GND -> pin GND                                                      *
* INT       -> not connected  (but can be used)                             *
* VIO & VDD -> pin 3.3V                                                     *
*****************************************************************************/


/* Calculate TWBR 
 * 
 * TWBR = (fcpu / fscl -16) / 2 
 * Apparently for I2C master TWBR should be at least 10... This needs a reference..
 */

#include <avr/io.h>
#include <avr/interrupt.h>
#include <math.h>
#include <util/twi.h>
#include <stdlib.h>
#include "../lib/UART.h"
#include "../lib/TIMER.h"
#include "../source/n9_ITG3200.h"


#define gyro_addr ( ITG3200_ADDR_AD0_HIGH << 1 )

void debug_int( int16_t val )
{
	uint8_t debug[6];
	uint8_t i=0;
	itoa( val, debug, 10 );
	while( ( debug[i] != 0x00 ) && ( i++ < 6 ) );
	UART_QueueTXBuffer( debug, i );
	UART_TransmitByte( '\n' );
}

void debug_float( double val )
{
	uint8_t debug[16];
	uint8_t i=0;
	dtostrf( val, 15, 5, debug );
	while( ( debug[i] != 0x00 ) && ( i++ < 16 ) );
	UART_QueueTXBuffer( debug, i );
	UART_TransmitByte( '\n' );
}

#define TWI_BUFFER_SIZE 8

volatile uint8_t __attribute__ ((aligned(TWI_BUFFER_SIZE))) TWI_buffer[TWI_BUFFER_SIZE] ;

#define TWI_RX 0
#define TWI_TX 1
#define TWI_START_SENT 2
#define TWI_ADDR_SENT 3
#define TWI_REG_SENT 4
#define TWI_SET_DIRECTION 5
#define TWI_TRANSFER_IN_PROG 6
#define TWI_STOP_SENT 7

#define TWI_STATE 0
#define TWI_ADDR 1
#define TWI_REG 2
#define TWI_NUM_BYTES 3
#define TWI_DATA 4

uint8_t twi_init( uint8_t baud ) //not actually baud - fix this.
{
	/* init i2c */
	PORTC |= _BV( PC4 ) | _BV( PC5 ); //enable pull up resistors
	TWI_buffer[TWI_STATE] = 0;
	TWSR = 0; // Set the prescaler to 1
	TWBR = baud; // 80kHz. 2 would gives fscl of 400kHz. fscl = (8e6/4e5 - 16) / 2
	TWCR |= _BV(TWIE);
	/* end i2c init */
}

uint8_t twi_transaction( uint8_t twi_addr, uint8_t twi_reg, uint8_t *twi_data, uint8_t twi_num_bytes, uint8_t twi_direction )
{
#define TWI_COMMS_ERROR_BUSY (int8_t) -1
#define TWI_COMMS_ERROR_OVFL (int8_t) -2
	uint8_t twi_state;
	int8_t status = 0;

	twi_state = TWI_buffer[TWI_STATE];
	if( !(twi_state==0) )return TWI_COMMS_ERROR_BUSY; //check if a twi process is already under way.

	TWI_buffer[TWI_ADDR] = twi_addr;
	TWI_buffer[TWI_REG] = twi_reg;
	TWI_buffer[TWI_NUM_BYTES] = twi_num_bytes;

	if( twi_direction == TWI_TX )
	{
		for( twi_state = 0; twi_state < twi_num_bytes; twi_state++ )
		{
			if( twi_state > 3 ) { status = TWI_COMMS_ERROR_OVFL; break; }// max transmit size is 4 bytes (two words)
			TWI_buffer[TWI_DATA+twi_state] = twi_data[twi_state];
		}
	}

	twi_state = _BV(twi_direction)|_BV(TWI_START_SENT);
	TWI_buffer[TWI_STATE] = twi_state;
	TWCR = _BV(TWIE) | _BV(TWINT) | _BV(TWSTA) | _BV(TWEN) ; /* send start condition */
	return status;
}

ISR ( TWI_vect )
{
	/* Need to determine what sort of data comms is under way and where abouts in the process we are */
	uint8_t twst,twi_num_bytes_total,twi_num_bytes_sent;
	uint8_t twi_com_st,twi_com_dir;
	twst = TW_STATUS;
	twi_com_st = TWI_buffer[TWI_STATE] & ~(_BV(TWI_TX)|_BV(TWI_RX)); //separate status and direction info
	twi_com_dir = TWI_buffer[TWI_STATE] & (_BV(TWI_TX)|_BV(TWI_RX));

	if(twst == TW_MT_ARB_LOST) goto restart;

	//TX/RX independent stuff
	switch( twi_com_st )
	{
		case _BV(TWI_START_SENT):
			// Send AD+W
			if( twst != TW_START ) goto restart;
			TWDR = TWI_buffer[TWI_ADDR] | TW_WRITE;
			TWCR = _BV(TWIE) | _BV(TWINT) | _BV(TWEN); /* clear interrupt to start transmission */
			TWI_buffer[TWI_STATE] = _BV(TWI_ADDR_SENT) | twi_com_dir; 
			goto end_interrupt;
	
		case _BV(TWI_ADDR_SENT):
			if( twst == TW_MT_SLA_NACK) goto restart;/* nack during select: device busy writing - start over */

			// Send register address
			TWDR = TWI_buffer[TWI_REG];
			TWCR = _BV(TWIE) | _BV(TWINT) | _BV(TWEN); /* clear interrupt to start transmission */
			TWI_buffer[TWI_STATE] = _BV(TWI_REG_SENT) | twi_com_dir;
			goto end_interrupt;

		case _BV(TWI_REG_SENT):
			if( twst != TW_MT_DATA_ACK ) goto restart;
			TWCR = _BV(TWIE) | _BV(TWINT) | _BV(TWSTA) | _BV(TWEN); /* send start condition */
			TWI_buffer[TWI_STATE] = _BV(TWI_SET_DIRECTION) | twi_com_dir;
			goto end_interrupt;	
			
	}

	//TX/RX specific stuff
	switch( twi_com_st )
	{
		case _BV(TWI_SET_DIRECTION):
			if( (twst != TW_START)&&(twst != TW_REP_START) ) goto restart;
			TWDR = TWI_buffer[TWI_ADDR] | (TW_READ&twi_com_dir);// use TW_READ(0x01) to mask the state variable leaving the appropriate RW bit in the LSB of the twi device address. Note: if the 7 bit TWI address must be left shifted such that the LSB is free to indicate READ/WRITE status.
			TWCR = _BV(TWIE) | _BV(TWINT) | _BV(TWEN); /* clear interrupt to start transmission */
			TWI_buffer[TWI_STATE] = _BV(TWI_TRANSFER_IN_PROG) | twi_com_dir;
			goto end_interrupt;
			
		case _BV(TWI_TRANSFER_IN_PROG):	
			twi_num_bytes_total = TWI_buffer[TWI_NUM_BYTES] & 0x0F;
			twi_num_bytes_sent = (TWI_buffer[TWI_NUM_BYTES] & 0xF0) >> 4;
			switch ( twst )
			{
				case TW_MR_SLA_ACK:
					if( twi_num_bytes_total > 1 ) TWCR = _BV(TWIE) | _BV(TWINT) | _BV(TWEN) | _BV(TWEA); /* start transmission, send ack */
					else TWCR = _BV(TWIE) | _BV(TWINT) | _BV(TWEN); /* start transmission, send nack */	
					goto end_interrupt;

				case TW_MR_SLA_NACK:
					goto restart;

				case TW_MR_DATA_ACK:
					//check how much more data we're expecting
					TWI_buffer[TWI_DATA+twi_num_bytes_sent] = TWDR;
					twi_num_bytes_sent++;
					TWI_buffer[TWI_NUM_BYTES] = ( twi_num_bytes_sent << 4 ) | twi_num_bytes_total;
					if ( twi_num_bytes_sent == (twi_num_bytes_total - 1) ) TWCR = _BV(TWIE) | _BV(TWINT) | _BV(TWEN); /* if we're waiting on only 1 byte then start transmission, send nack */
					else TWCR = _BV(TWIE) | _BV(TWINT) | _BV(TWEN) | _BV(TWEA); /* start transmission, send ack */
					goto end_interrupt;

				case TW_MR_DATA_NACK:
					//confirm that the last byte was received and if so end the transmission
					//needs an error check
					TWI_buffer[TWI_DATA+twi_num_bytes_sent] = TWDR;
					twi_num_bytes_sent++;
					TWI_buffer[TWI_NUM_BYTES] = ( twi_num_bytes_sent << 4 ) | twi_num_bytes_total;
					TWI_buffer[TWI_STATE] = 0;
					TWCR = _BV(TWINT) | _BV(TWSTO) | _BV(TWEN); /* send stop condition */
					goto end_interrupt;

				case TW_MT_SLA_ACK:
					TWDR = TWI_buffer[TWI_DATA+twi_num_bytes_sent];
					twi_num_bytes_sent++;
					TWI_buffer[TWI_NUM_BYTES] = ( twi_num_bytes_sent << 4 ) | twi_num_bytes_total;
					TWCR = _BV(TWIE) | _BV(TWINT) | _BV(TWEN); /* start transmission */
					goto end_interrupt;

				case TW_MT_SLA_NACK:
					goto restart;

				case TW_MT_DATA_ACK:
					//check how much more data to transmit
					if ( twi_num_bytes_sent == twi_num_bytes_total ) 
					{
						TWCR = _BV(TWINT) | _BV(TWSTO) | _BV(TWEN); /* send stop condition */
						TWI_buffer[TWI_STATE] = 0;
						goto end_interrupt;
					}
					TWDR = TWI_buffer[TWI_DATA+twi_num_bytes_sent];
					twi_num_bytes_sent++;
					TWI_buffer[TWI_NUM_BYTES] = ( twi_num_bytes_sent << 4 ) | twi_num_bytes_total;
					TWCR = _BV(TWIE) | _BV(TWINT) | _BV(TWEN); /* start transmission, send nack */	
					goto end_interrupt;
				case TW_MT_DATA_NACK:
					//probably an error - needs better handling than this.
					TWI_buffer[TWI_STATE] = 0;
					TWCR = _BV(TWINT) | _BV(TWSTO) | _BV(TWEN); /* send stop condition */
					goto end_interrupt;

			}
	}

	restart:
	TWCR = _BV(TWIE) | _BV(TWINT) | _BV(TWSTA) | _BV(TWEN); /* send start condition */
	TWI_buffer[TWI_STATE] = _BV(TWI_START_SENT) | twi_com_dir;
	end_interrupt:
	twi_num_bytes_sent = 0; /* NOTE: this is meaningless - it's just here so that the label has something after it.*/
}
void gyro_init( void )
{
	uint8_t data_low, data_high;
	data_low = DLPFFS_FS_SEL;
	twi_transaction( gyro_addr, DLPF_FS, &data_low, 1, TWI_TX );
	data_low = INTCFG_RAW_RDY_EN | INTCFG_INT_ANYRD_2CLEAR;
	twi_transaction( gyro_addr, INT_CFG, &data_low, 1, TWI_TX );
	
}


int main( void )
{
	uint8_t data_low, data_high;
	int16_t gyro_data;
	uint8_t tx_buffer[7]; 

	twi_init( 10 );
	gyro_init();
	InitUART( 0 ); //clock=8MHz, U2X0=True, Baud=1E6
	timer0_basic( 0xFF, TIMER_PRE_1024 );
	sei();

	while( 1 )
	{
		
		while(!timer0_triggered && ( timer0_alpha < 32 ));
		timer0_alpha = 0;

		while( data_low != INTSTATUS_RAW_DATA_RDY ) 
		{
			twi_transaction( gyro_addr, INT_STATUS, data_low, 1, TWI_RX );
			while( TWI_buffer[TWI_STATE] != 0 );
			data_low = TWI_buffer[TWI_DATA];
		}


		UART_TransmitByte( 'S' );
		UART_TransmitByte( '\n' );

		twi_transaction( gyro_addr, TEMP_OUT, tx_buffer, 1, TWI_RX );
		while( TWI_buffer[TWI_STATE] != 0 );
		data_high = TWI_buffer[TWI_DATA];
		twi_transaction( gyro_addr, TEMP_OUT+1, tx_buffer, 1, TWI_RX );
		while( TWI_buffer[TWI_STATE] != 0 );
		data_low = TWI_buffer[TWI_DATA];
		gyro_data = ((int16_t) data_high << 8 ) | data_low;
		debug_int( gyro_data );

		twi_transaction( gyro_addr, GYRO_XOUT, tx_buffer, 2, TWI_RX );
		while( TWI_buffer[TWI_STATE] != 0 );
		data_high = TWI_buffer[TWI_DATA];
		data_low = TWI_buffer[TWI_DATA+1];
		gyro_data = ((int16_t) data_high << 8 ) | data_low;
		debug_int( gyro_data );


		twi_transaction( gyro_addr, GYRO_YOUT, tx_buffer, 2, TWI_RX );
		while( TWI_buffer[TWI_STATE] != 0 );
		data_high = TWI_buffer[TWI_DATA];
		data_low = TWI_buffer[TWI_DATA+1];
		gyro_data = ((int16_t) data_high << 8 ) | data_low;
		debug_int( gyro_data );


		twi_transaction( gyro_addr, GYRO_ZOUT, tx_buffer, 2, TWI_RX );
		while( TWI_buffer[TWI_STATE] != 0 );
		data_high = TWI_buffer[TWI_DATA];
		data_low = TWI_buffer[TWI_DATA+1];
		gyro_data = ((int16_t) data_high << 8 ) | data_low;
		debug_int( gyro_data );
		UART_TransmitByte( '\n' );
	}
}
