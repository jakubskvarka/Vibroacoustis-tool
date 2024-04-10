from os import path
from datetime import datetime, timezone
import argparse
import numpy as np
from kaitai.python.openapi_message import OpenapiMessage
import h5py

class Parser():
    def __init__(self,name_of_file):
        super(Parser, self).__init__()

        self.name_of_file=name_of_file

        args = argparse.Namespace()
        args.file = self.name_of_file

        print(f'Reading streaming data from file "{args.file}"...')
        file_size = path.getsize(args.file)
        file_stream = open(args.file, 'rb')

        # Processed data will be stored in this collection
        data = {}

        while True:
            # Read the next Open API message from the file
            try:
                msg = OpenapiMessage.from_io(file_stream)
            except EOFError:
                print("")
                break

            # If 'interpretation' message, then extract metadata describing how to interpret signal data
            if msg.header.message_type == OpenapiMessage.Header.EMessageType.e_interpretation:
                for i in msg.message.interpretations:
                    if i.signal_id not in data:
                        data[i.signal_id] = {}
                    data[i.signal_id][i.descriptor_type] = i.value

            # If 'signal data' message, then copy sample data to in-memory array
            elif msg.header.message_type == OpenapiMessage.Header.EMessageType.e_signal_data:
                for s in msg.message.signals:
                    if "start_time" not in data[s.signal_id]:
                        start_time = datetime.fromtimestamp(self.calc_time(msg.header.time), timezone.utc)
                        data[s.signal_id]["start_time"] = start_time
                    if "samples" not in data[s.signal_id]:
                        data[s.signal_id]["samples"] = np.array([])
                    more_samples = np.array(list(map(lambda x: x.calc_value, s.values)))
                    data[s.signal_id]["samples"] = np.append(data[s.signal_id]["samples"], more_samples)

            # If 'quality data' message, then record information on data quality issues
            elif msg.header.message_type == OpenapiMessage.Header.EMessageType.e_data_quality:
                for q in msg.message.qualities:
                    if "validity" not in data[q.signal_id]:
                        data[q.signal_id]["validity"] = []
                    dt = datetime.fromtimestamp(self.calc_time(msg.header.time), timezone.utc)
                    data[q.signal_id]["validity"].append({"time": dt, "flags": q.validity_flags})

            # Print progress
            print(f'{int(100 * file_stream.tell() / file_size)}%', end="\r")

        # Plot time- and frequency-domain data from all channels
        print(f'Plotting data...')



        for index, (key, value) in enumerate(data.items()):

            # Scale samples using the scale factor from the interpretation message
            samples = value["samples"]
            scale_factor = value[OpenapiMessage.Interpretation.EDescriptorType.scale_factor]
            scaled_samples = (samples * scale_factor) / 2 ** 23

            # Calculate FFT
            sample_period =self.calc_time(value[OpenapiMessage.Interpretation.EDescriptorType.period_time])
            print(f"sample perido is{sample_period}")
            print(f"length of samples is {len(samples)}")
            sample_rate = 1 / sample_period
            unit = value[OpenapiMessage.Interpretation.EDescriptorType.unit]





        #     # Create an HDF5 file to store the data
        #     hdf5_filename = f'{self.name_of_file}.h5'
        #     with h5py.File(hdf5_filename, 'w') as hdf5_file:
        #         signal_group = hdf5_file.create_group('Table1')
        #         signal_group.attrs['start_time'] = str(value["start_time"])
        #
        #         length_of_recording=len(samples)*sample_period
        #         print(length_of_recording)
        #
        #         time=np.linspace(0,length_of_recording,len(samples))
        #         signal_group.create_dataset('Ds01-Time', data=time)
        #
        #         for index, (key, value) in enumerate(data.items()):
        #             # Create a group for each signal
        #             # signal_group = hdf5_file.create_group(str(index + 1))  # Use index + 1 as HDF5 groups are 1-indexed
        #             # Save samples
        #             samples_dataset = signal_group.create_dataset(f'sample{index + 1}', data=value["samples"])
        #
        #
        #             # Save metadata
        #             samples_dataset.attrs['signal_id'] = key
        #             samples_dataset.attrs['InterpretationUnit'] = value[
        #                 OpenapiMessage.Interpretation.EDescriptorType.unit].data  # Save unit as a string
        #             samples_dataset.attrs['ChannelInformationSamplingPeriod'] = self.calc_time(
        #                 value[OpenapiMessage.Interpretation.EDescriptorType.period_time])
        #
        #
        # print(f'Data saved to {hdf5_filename}')
        # Vytvorí HDF5 súbor na uloženie dát
        hdf5_filename = f'{self.name_of_file}.h5'
        with h5py.File(hdf5_filename, 'w') as hdf5_file:
            signal_group = hdf5_file.create_group('Table1')
            signal_group.attrs['start_time'] = str(value["start_time"])
            # Zistí dĺžku nahrávky
            length_of_recording = len(samples) * sample_period
            # Vytvorí časový vektor s požadovanou dĺžkou a pridá ho do datasetu
            time = np.linspace(0, length_of_recording, len(samples))
            signal_group.create_dataset('Ds01-Time', data=time)
            for index, (key, value) in enumerate(data.items()):
                # Uloží vzorky
                samples_dataset = signal_group.create_dataset(f'sample{index + 1}', data=value["samples"])
                # Uloží metadáta pre každý signál
                # Signal ID
                samples_dataset.attrs['signal_id'] = key
                # Jednotka
                samples_dataset.attrs['InterpretationUnit'] = value[OpenapiMessage.Interpretation.EDescriptorType.unit].data
                # Vzorkovacia perióda
                channel_info_sampling_period = self.calc_time(value[OpenapiMessage.Interpretation.EDescriptorType.period_time])
                samples_dataset.attrs['ChannelInformationSamplingPeriod'] = np.array([channel_info_sampling_period])

        print(f'Data saved to {hdf5_filename}')

    def calc_time(self,t):
        """
        Convert an Open API 'Time' structure to a number.
        Note Kaitai doesn't support the '**' operator, or we could have implemented
        a conversion function directly in the .ksy file.
        Args:
            t: an Open API 'Time' instance
        Returns:
            the time as a built-in, numeric type
        """
        family = 2 ** t.time_family.k * 3 ** t.time_family.l * 5 ** t.time_family.m * 7 ** t.time_family.n
        return t.time_count * (1 / family)

    def get_quality_strings(self,l):
        """Given an 'l' list of validity objects, return a collection of descriptive strings."""
        strings = []
        for v in l:
            qs, prefix = "", ""
            if v["flags"].invalid:
                qs = qs + prefix + "Invalid Data"
                prefix = ", "
            if v["flags"].overload:
                qs = qs + prefix + "Overload"
                prefix = ", "
            if v["flags"].overrun:
                qs = qs + prefix + "Gap In Data"
                prefix = ", "
            if qs == "":
                qs = "OK"
            qs = f'{v["time"]}: ' + qs
            strings.append(qs)
        return strings

