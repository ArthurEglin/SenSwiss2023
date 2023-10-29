/*
    * com.h
    *
    * Created: 2017-04-20 14:04:00
*/
#ifndef COM_H_
#define COM_H_

#include <Arduino.h>

void init_com();

String read_com();

void write_com(String message);

#endif /* COM_H_ */