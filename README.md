# Physical Layer - Audio Network

This repository contains the implementation and design document for **CS 378 Assignment 2**, focusing on reliable signal transmission between a sender and receiver. The project addresses issues related to synchronization, error detection, and correction, optimizing data transmission efficiency.

## Overview

The system ensures reliable signal transmission using several techniques, including:
- **Preamble**: Helps the receiver synchronize with the sender.
- **Synchronization**: Aligns the receiver's listening window with the sender's bit transmission.
- **Error Correction**: Utilizes CRC-based methods to detect and correct errors.
- **Efficiency Optimizations**: Groups 4 bits into one and transmits them using 16 different frequency values.

### 1. Preamble
The transmission starts with a preamble, which is a sine wave at a distinct frequency (8000 Hz) from those used for actual data (4000 Hz for '0' and 6000 Hz for '1'). This frequency difference helps the receiver identify the start of a transmission and lock onto the signal.

### 2. Synchronization
Synchronization is crucial for accurate data interpretation. The preamble is transmitted at a shorter bit duration (0.02 seconds), followed by the actual data bits with a longer duration (0.3 seconds). This timing difference allows the receiver to adjust and interpret the message correctly.

### 3. Error Correction

The system uses a **CRC (Cyclic Redundancy Check)** based error detection method to ensure message integrity. A generator polynomial (`0x5d7`) is used, which can detect and correct up to two errors in the message.

- **Encoding Algorithm**: The message is encoded by appending a CRC remainder, calculated using the CRC generator polynomial. The total transmitted message length, including the CRC and preamble, is 37 bits.
  
- **Decoding and Error Correction**: A trial-and-error method is employed to detect and correct up to two errors in the message. The decoding algorithm flips bits and recalculates the CRC remainder until a valid message is found.

### 4. Testing
The system was tested for various scenarios, simulating potential transmission errors. The tests ensure that there is only one valid message corresponding to any corrupted bitstring. The testing code verifies that the encoding, error detection, and correction algorithms work as expected.

### 5. Optimizations

1. **Bit Grouping**: To improve efficiency, we group 4 bits together and assign different frequency values to represent 16 different combinations of these bits. This reduces the overall transmission time.
   
2. **Preamble Enhancement**: The preamble now also includes the message length to inform the receiver when to stop recording.

## Instructions to Run the Code

### Sender
1. Run the following command in your terminal:
   ```bash
   python sender.py```
2. Enter the two real numbers a and b (as per the project specifications), followed by the message to be transmitted.

### Receiver
Run the following command in your terminal:
```bash
python receiver.py
```
The receiver will begin listening and processing the transmitted signal, decoding the message and correcting any errors.


