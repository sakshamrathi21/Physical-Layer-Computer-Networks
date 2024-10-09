import numpy as np
import pyaudio
from time import sleep, time
import math 

class Sender:
    """
    A class used to represent a Sender that sends a bit-string with the possibility of error and attaches a checksum using CRC that makes it possible to correctly transcribe the received bitstrings


    Attributes
    ----------
    Sample_rate : int
        Sample rate in Hz (Number of measurements in a second)
    Bit_duration : float
        Duration of each bit in seconds
    Preamble_duration : float
        the sound that the animal makes
    Preamble_frequency : int
        Frequency of preamble tone
    Amplitude : float
        Amplitude of the signal
    Preamble_length : int
        Length of the preamble 
    Bit_flips : list[float]
        List of the 1-indexed positions where the bits are flipped
    Input_bitstring : str
        The data to be sent
    CRC_polynomial : str
        The polynomial CRC to be used (The default one is used by us to ensure that it can correct upto 2 bit errors for input strings of max length 20 bits)
    """

    def __init__(self, input_string : str, list_of_bitflips : list[float]) -> None:
        """Initialises the member variables of the class"""

        self.Sample_rate : int = 44100
        self.Bit_duration : float = 0.6
        self.Preamble_duration : float = 0.01
        self.Preamble_frequency : int = 5000
        self.Amplitude : float = 4.0
        self.Preamble_length : int = 6
        self.Bit_flips : list[float] = list_of_bitflips
        self.Input_bitstring : str = input_string
        self.CRC_polynomial : str = "010111010111"

        # The sine wave generating function requires the below values to be multiplied by 4
        self.Bit_duration *= 4
        self.Preamble_duration *= 4
        
    
    def map_freq(self, bit_string : str) -> int:
        """
        This functions maps a 4-bit bitstring to a frequency.
        Frequency ranges from 4300 to 7300.
        """
        index = int(bit_string, 2)
        return 4300 + index * 200

    def crc_remainder(self, input_bitstring : str, polynomial_bitstring : str, initial_filler : str) -> str:
        """
        Calculate the CRC remainder of a string of bits using a chosen polynomial.
        
        Arguments
        ---------------
        input_bitstring : str
            The data to be divided
        polynomial_bitstring : str
            The divisor in binary form
        initial_filler : str 
            The string of bits to be used as initial filler

        Returns
        ---------
        CRC_remainder : str
            The remainder of the division as a binary string
        """

        # Initial setup
        len_input = len(input_bitstring)
        len_polynomial = len(polynomial_bitstring)

        # Append initial filler (zeros) to the input bit string
        augmented_bitstring = input_bitstring + initial_filler

        # Perform modulo-2 division (XOR operation)
        for i in range(len_input):
            if augmented_bitstring[i] == '1':  # Only if the current bit is 1
                for j in range(len_polynomial):
                    augmented_bitstring = (augmented_bitstring[:i + j] +
                                        str(int(augmented_bitstring[i + j]) ^ int(polynomial_bitstring[j])) +
                                        augmented_bitstring[i + j + 1:])

        # The remainder is the last 'len_polynomial - 1' bits of the augmented bit string
        remainder = augmented_bitstring[-(len_polynomial - 1):]
        return remainder

    def crc_check(self, received_bitstring : str, polynomial_bitstring : str) -> bool:
        """
        Check if the received bitstring has an error using the CRC method.
        
        Arguments
        ------------------
        received_bitstring : str 
            The received data including the CRC code
        polynomial_bitstring : str
            The divisor in binary form

        Returns
        ----------------
        boolean_val : bool
            True if no error is detected, False otherwise
        """
        # Perform the same modulo-2 division (XOR operation) as in the sender's end
        len_received = len(received_bitstring)
        len_polynomial = len(polynomial_bitstring)

        # Perform division
        for i in range(len_received - len_polynomial + 1):
            if received_bitstring[i] == '1':  # Only if the current bit is 1
                for j in range(len_polynomial):
                    received_bitstring = (received_bitstring[:i + j] +
                                        str(int(received_bitstring[i + j]) ^ int(polynomial_bitstring[j])) +
                                        received_bitstring[i + j + 1:])

        # If the remainder is all zeros, the data is considered to be correct
        remainder = received_bitstring[-(len_polynomial - 1):]
        return remainder == '0' * (len_polynomial - 1)

    def flip_bit(self, bitstring : str, index : int) -> str:
        """
        Flip a specific bit in the bitstring
        
        Arguments
        ------------------
        bitstring : str 
            The bitstring that we have to flip the bit in
        index : int
            The 0-based index of the bit to be flipped

        Returns
        ----------------
        flipped_bitstring : str
            The bitstring with the bit flipped at the index
        """
        if index < 0 or index >= len(bitstring):
            return bitstring
        flipped = list(bitstring)
        flipped[index] = '1' if bitstring[index] == '0' else '0'
        return ''.join(flipped)

    def generate_sine_wave(self, frequency : int, duration : float, amplitude : float, sample_rate : int) -> np.float32:
        """
        This function generates a sine wave according to the arguments
        """
        t = np.linspace(0, duration, int(sample_rate * duration), False)
        sine_wave = amplitude * np.sin(2 * np.pi * frequency * t)
        return sine_wave.astype(np.float32)
    
    def convert_to_binary(self, n : int) -> str:
        """
        Conversion of a decimal number of binary (used to encode length)
        """
        return bin(n)[2:].zfill(8)

    def send_message(self):
        """
        Sends the message, along with the errors 
        """
        # Initialize PyAudio
        p = pyaudio.PyAudio()

        stream = p.open(format=pyaudio.paFloat32,
                        channels=1,
                        rate=self.Sample_rate,
                        output=True)
        
        Initial_filler = "0"*(len(self.CRC_polynomial)-1)
        # CRC Code is message to be sent along with the CRC Remainderck
        crc_code = self.Input_bitstring + self.crc_remainder(self.Input_bitstring, self.CRC_polynomial, Initial_filler)
        # Sending length via hexadecimal bits
        length = len(crc_code)
        length_preamble = self.convert_to_binary(length)
        
        length_mod_4 = length % 4
        binary_data = crc_code
        if length_mod_4 == 0:
            length_mod_4 = 4
        # Making the length as the multiple of 4 (Ending Padding)
        binary_data += "0" * (4 - length_mod_4)
        print(f"Length of binary data to be sent is {len(binary_data)} bits.")

        print("Transmission Data Before Bit Flips:", binary_data)
        
        # Flipping the bits that are indexed
        for index in self.Bit_flips:
            binary_data = self.flip_bit(binary_data, math.ceil(index*len(binary_data)) - 1) # We do index - 1 to account for 1-indexing
            print(f"{math.ceil(index*len(binary_data))}th bit position will be flipped.")

        print("Transmission Data After Bit Flips:", binary_data)

        

        # This dictionary contains mapping from frequency to array of sound data to be sent
        tones = {}

        # Calculating the "tones" dictionary
        for freq in range(4100, 8000, 200):
            tones[freq] = self.generate_sine_wave(freq, self.Bit_duration, self.Amplitude, self.Sample_rate)

        # Main transmission logic
        print("Starting transmission...")

        # Send preamble
        PREAMBLE = self.generate_sine_wave(self.Preamble_frequency, self.Preamble_duration, self.Amplitude, self.Sample_rate)
        for _ in range(self.Preamble_length):
            stream.write(PREAMBLE)

        # Sending the first 4 MSB bits of binary form of length of binary_data
        # print(f"Sending {length_preamble[:4]} at {self.map_freq(length_preamble[:4])}")
        stream.write(tones[self.map_freq(length_preamble[:4])])

        # Sending the last 4 LSB bits of binary form of length of binary_data
        # print(f"Sending {length_preamble[4:]} at {self.map_freq(length_preamble[4:])}")
        stream.write(tones[self.map_freq(length_preamble[4:])])

        # Sending the message now
        for i in range(0, len(binary_data), 4):
            # print(f"Sending {binary_data[i:i+4]} at {self.map_freq(binary_data[i:i+4])}")
            stream.write(tones[self.map_freq(binary_data[i:i+4])])

        # Close the stream
        stream.stop_stream()
        stream.close()
        p.terminate()

        print("Binary data sent.")
    
if __name__ == "__main__":
    # Take two indices which can be corrupted
    list_of_indices = []
    a = float(input("Write a real number: "))
    list_of_indices.append(a)
    b = float(input("Write a real number: "))
    if b != 0:
        list_of_indices.append(b)
        num_flips = 2
    else:
        num_flips = 1

    transmit_bitstring = input("Transmission message: ")

    s = Sender(transmit_bitstring,list_of_indices)
    s.send_message()