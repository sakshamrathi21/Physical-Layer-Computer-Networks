import numpy as np
import pyaudio
from scipy.fft import fft
from time import sleep, time

class Receiver:
    """
    A class used to representthe Receiver that receives a bit-string with the possibility of error and corrects it (for upto 2 bit errors) using the CRC


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
    Threshold : int
        Threshold for frequency detection
    Ratio_of_Sender_Receiver : int
        Ratio of bit duration to receiver's check interval
    Preamble_length : int
        Length of the preamble 
    Frequency_filter : int
        Frequency filter to ignore low frequencies
    Ratio_Threshold : int
        Tolerance for bit length ratio
    CRC_polynomial : str
        The polynomial CRC to be used (The default one is used by us to ensure that it can correct upto 2 bit errors for input strings of max length 20 bits)
    Frequency_1 : int
        Frequency for '1' bit in Hz
    Frequency_0 : int
        Frequency for '0' bit in Hz
    Freq_bin_string : dict[int -> str]
        Mapping frequencies to their respective binary strings
    """

    def __init__(self) -> None:
        """Initialises the member variables of the class"""
        self.Sample_rate : int = 16000
        self.Bit_duration : int = 0.7
        self.Preamble_duration : float = 0.05
        self.Preamble_frequency : int = 5000
        self.Threshold : int = 100
        self.Preamble_length : int = 6
        self.CRC_polynomial : str = "010111010111"
        self.Frequency_1 = 8200
        self.Frequency_0 = 7900
        self.Ratio_of_Sender_Receiver = 6
        self.Ratio_Threshold = 3
        self.freq_bin_string = {
            self.Frequency_0 : "0",
            self.Frequency_1 : "1"
        }
        self.Frequency_filter = 1000
        for i in range(0,16):
            self.freq_bin_string[4300+ i*200] = bin(i)[2:].zfill(4)

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

    def Receive_bitstring(self)->None:
        """
        Start listening for the audio and also do error correction to print the correct output
        """
        p = pyaudio.PyAudio()

        preamble_stream = p.open(format=pyaudio.paInt16,
                        channels=1,
                        rate=self.Sample_rate,
                        input=True,
                        frames_per_buffer=int(self.Sample_rate * self.Preamble_duration))

        def detect_preamble(Preamble_frequency, Sample_rate, Threshold):
            """
            Detect the preamble signal in the audio stream.

            Args:
            Preamble_frequency : int
                Frequency of the preamble signal in Hz
            Sample_rate : int 
                Sample rate in Hz
            Threshold : int 
                Threshold for frequency detection
            """
            
            while True:
                # Read preamble as input
                data = preamble_stream.read(int(Sample_rate * self.Preamble_duration))
                frame = np.frombuffer(data, dtype=np.int16)
                frame = frame / np.max(np.abs(frame))
                
                spectrum = np.abs(fft(frame))
                freqs = np.fft.fftfreq(len(spectrum), 1 / Sample_rate)
                
                # Detect the peak frequency
                peak_freq = freqs[np.argmax(spectrum)]

                if abs(peak_freq - Preamble_frequency) <  Threshold:
                    break

        # Detect preamble before starting the main signal detection
        print("Listening for preamble...")
        for _ in range(self.Preamble_length):
            detect_preamble(self.Preamble_frequency, self.Sample_rate, self.Threshold)
        print("Preamble detected")
        preamble_stream.stop_stream()
        preamble_stream.close()

        # Start main signal detection after preamble
        stream = p.open(format=pyaudio.paInt16,
                        channels=1,
                        rate=self.Sample_rate,
                        input=True,
                        frames_per_buffer=int(self.Sample_rate * self.Bit_duration)*2
                        )
        print("Listening for audio signal...")

        binary_data = ""
        previous_bit = "?"
        current_bit = "0"
        current_bit_length = 0
        data_length = -1

        # Main loop to recieve the main signal
        while True:
            data = stream.read(int(self.Sample_rate * self.Bit_duration))
            frame = np.frombuffer(data, dtype=np.int16)
            frame = frame / np.max(np.abs(frame))
            spectrum = np.abs(fft(frame))
            freqs = np.fft.fftfreq(len(spectrum), 1 / self.Sample_rate)

            # Filter the spectrum and frequencies to consider only those > Frequency_filter
            valid_indices = freqs > self.Frequency_filter
            filtered_spectrum = spectrum[valid_indices]
            filtered_freqs = freqs[valid_indices]

            # Find the peak frequency among the filtered frequencies
            peak_freq = filtered_freqs[np.argmax(filtered_spectrum)]
            freq_found = peak_freq

            # Determine the current bit based on detected frequency
            found = False
            for freq in self.freq_bin_string:
                if abs(freq_found - freq) <= self.Threshold:
                    current_bit = self.freq_bin_string[freq]
                    found = True
                    break
            if not found:
                current_bit = "?"

            # Process the detected bit
            if current_bit == previous_bit:
                current_bit_length += 1
                if current_bit_length >= self.Ratio_of_Sender_Receiver:
                    current_bit_length = 0
                    binary_data += previous_bit
            else:
                if abs(current_bit_length - self.Ratio_of_Sender_Receiver) <= self.Ratio_Threshold:
                    binary_data += previous_bit
                current_bit_length = 1
                previous_bit = current_bit

            # Determine the data length from the first 8 bits
            if data_length == -1 and len(binary_data) > 8:
                data_length = int(binary_data[:8], 2)
                binary_data = binary_data[8:]

            # Terminate the loop when full message is recieved
            if data_length != -1 and len(binary_data) >= data_length:
                break

        bits_flipped = []
        
        # Print the received bitsting, along with zero padding
        print("The received bitstring along with zero padding: ", binary_data) 
        # Check for error in the zero padding at the end
        for i in range(data_length, len(binary_data)):
            if binary_data[i] == '1':
                bits_flipped.append(i+1)
        # Extract the relevant bits of detected data
        binary_data = binary_data[:data_length]
        print("Received data from sender after removing zero padding:", binary_data)

        # CRC Polynomial
        initial_filler = "0"*(len(self.CRC_polynomial)-1)
        correct_check_code = binary_data
        # CRC check for errors and correction
        if not self.crc_check(binary_data, self.CRC_polynomial):
            for i in range(len(binary_data)):
                check_code = self.flip_bit(binary_data, i)
                if self.crc_check(check_code, self.CRC_polynomial):
                    bits_flipped.append(i+1)
                    correct_check_code = check_code
                    
            for i in range(len(binary_data)):
                for j in range(i+1, len(binary_data)):
                    check_code = self.flip_bit(binary_data, i)
                    check_code = self.flip_bit(check_code, j)
                    if self.crc_check(check_code, self.CRC_polynomial):
                        bits_flipped.append(i+1)
                        bits_flipped.append(j+1)
                        correct_check_code = check_code

        bits_flipped = sorted(bits_flipped)
        if len(bits_flipped) == 1:
            print("Only 1 bit was flipped which is: ", bits_flipped[0])
            print("Received Data from sender after removing bit flips:", correct_check_code)
            print("The correct message is: ", correct_check_code[0:-len(initial_filler)])
        elif len(bits_flipped) == 2:
            print("2 bits were flipped which are: ", bits_flipped[0], bits_flipped[1])
            print("Received Data from sender after removing bit flips:", correct_check_code)
            print("The correct message is: ", correct_check_code[0:-len(initial_filler)])
        else:
            print("No errors were present. The correct message is: ", binary_data[0:-len(initial_filler)])

        stream.stop_stream()
        stream.close()
        p.terminate()


if __name__ == "__main__":
    r = Receiver()
    r.Receive_bitstring()