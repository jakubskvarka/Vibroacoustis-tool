#!/usr/bin/env python3
# pylint: disable=C0103

"""Example code to demonstrate streamed-data processing with LAN-XI Open API."""

from os import path
from datetime import datetime, timezone
import argparse
import numpy as np
import matplotlib.pyplot as plt
from kaitai.python.openapi_message import OpenapiMessage

def calc_time(t):
    """
    Convert an Open API 'Time' structure to a number.
    Note Kaitai doesn't support the '**' operator, or we could have implemented
    a conversion function directly in the .ksy file.
    Args:
        t: an Open API 'Time' instance
    Returns:
        the time as a built-in, numeric type
    """
    family = 2**t.time_family.k * 3**t.time_family.l * 5**t.time_family.m * 7**t.time_family.n
    return t.time_count * (1 / family)

def dbfft(input_vec, fs, ref=1):
    """
    Calculate spectrum on dB scale relative to specified reference.
    Args:
        input_vec: vector containing input signal
        fs: sampling frequency
        ref: reference value used for dB calculation
    Returns:
        freq_vec: frequency vector
        spec_db: spectrum in dB scale
    """
    # Calculate windowed/scaled FFT and convert to dB relative to full-scale
    window = np.hamming(len(input_vec))
    input_vec = input_vec * window
    spec = np.fft.rfft(input_vec)
    spec_mag = (np.abs(spec) * np.sqrt(2)) / np.sum(window)
    spec_db = 20 * np.log10(spec_mag / ref)
    # Generate frequency vector
    freq_vec = np.arange((len(input_vec) / 2) + 1) / (float(len(input_vec)) / fs)
    return freq_vec, spec_db

def get_quality_strings(l):
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

parser = argparse.ArgumentParser()
parser.add_argument("file", help="File containing Open API streaming data")
parser.add_argument("-s", "--save-plot", dest="save_plot", action='store_true', \
    help="Save plot to file")
args = parser.parse_args()

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
                start_time = datetime.fromtimestamp(calc_time(msg.header.time), timezone.utc)
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
            dt = datetime.fromtimestamp(calc_time(msg.header.time), timezone.utc)
            data[q.signal_id]["validity"].append({"time": dt, "flags": q.validity_flags})

    # Print progress
    print(f'{int(100 * file_stream.tell() / file_size)}%', end="\r")
print(data)
# Plot time- and frequency-domain data from all channels
print(f'Plotting data...')
#
# import json

#
figure, axis = plt.subplots(len(data), 2)
#
# # output_data=[]
# for index, (key, value) in enumerate(data.items()):
#
#     # Scale samples using the scale factor from the interpretation message
#     samples = value["samples"]
#     scale_factor = value[OpenapiMessage.Interpretation.EDescriptorType.scale_factor]
#     scaled_samples = (samples * scale_factor) / 2**23
#
#     channel_info = {
#         "channel_id": key,
#         "start_time": str(value["start_time"]),
#         "samples": value["samples"].tolist(),  # Convert NumPy array to list for JSON serialization
#         "sample_rate": 1 / calc_time(value[OpenapiMessage.Interpretation.EDescriptorType.period_time]),
#         "unit": str(value[OpenapiMessage.Interpretation.EDescriptorType.unit]),
#         "validity": [{"time": str(entry["time"]), "flags": entry["flags"]} for entry in value.get("validity", [])]
#     }
#     output_data.append(channel_info)
# with open('output_data.json', 'w') as json_file:
#         json.dump(output_data, json_file, default=str)
#
# print("Data saved to 'output_data.json'")
for index, (key, value) in enumerate(data.items()):

    # Scale samples using the scale factor from the interpretation message
    samples = value["samples"]
    scale_factor = value[OpenapiMessage.Interpretation.EDescriptorType.scale_factor]
    scaled_samples = (samples * scale_factor) / 2**23

    # Calculate FFT
    sample_rate = 1 / calc_time(value[OpenapiMessage.Interpretation.EDescriptorType.period_time])
    unit = value[OpenapiMessage.Interpretation.EDescriptorType.unit]

    import h5py

    from datetime import datetime, timezone

    # Create an HDF5 file to store the data
    hdf5_filename = '2mics2.h5'
    with h5py.File(hdf5_filename, 'w') as hdf5_file:
        signal_group= hdf5_file.create_group('Table1')
        signal_group.attrs['start_time'] = str(value["start_time"])
        for index, (key, value) in enumerate(data.items()):
            # Vytvorí skupinu pre každý kanál
            #signal_group = hdf5_file.create_group(str(index + 1))  # Use index + 1 as HDF5 groups are 1-indexed
            # Uloží vzorky
            samples_dataset = signal_group.create_dataset(f'sample{index+1}', data=value["samples"])

            # Save metadata
            samples_dataset.attrs['signal_id'] = key
            samples_dataset.attrs['InterpretationUnit'] =value[OpenapiMessage.Interpretation.EDescriptorType.unit].data  # Save unit as a string
            samples_dataset.attrs['ChannelInformationSamplingPeriod']= calc_time(value[OpenapiMessage.Interpretation.EDescriptorType.period_time])

            ## Save samples
            #samples_dataset = signal_group.create_dataset('samples', data=value["samples"])
            #
            # # Save validity information
            # validity_group = signal_group.create_group('validity')
            # for i, entry in enumerate(value.get("validity", [])):
            #     validity_group.create_dataset(f'time_{i}', data=str(entry["time"]))
            #     validity_group.create_dataset(f'flags_{i}', data=entry["flags"])


print(f'Data saved to {hdf5_filename}')


#     # with open('samples.txt','w') as fp:
#     #     json.dump(samples.tolist(),fp)
#
#
#     # Specify the filename for saving the data
#     filename = 'signal_data.pkl'
#
#     # Save the data dictionary to a Pickle file
#     with open(filename, 'wb') as file:
#         pickle.dump(data, file)
#
#     print(f'Data saved to {filename}')
#
#     # Calculate FFT
#     sample_rate = 1 / calc_time(value[OpenapiMessage.Interpretation.EDescriptorType.period_time])
#     unit = value[OpenapiMessage.Interpretation.EDescriptorType.unit]
#     if unit.data == "Pa": # Special case: Sound Pressure Level, calculate dB relative to 20 µPa
#         freq, dbfs = dbfft(scaled_samples, sample_rate, ref=20 * 10**(-6))
#         freq_label = "SPL [dB20µPa]"
#     else:
#         freq, dbfs = dbfft(scaled_samples, sample_rate, ref=0.001)
#         freq_label = f'{unit.data} [dBm]'
#
#     # Plot the first 1000 samples of the time-domain signal
#     time_axis = np.array(range(0, 1000)) / sample_rate
#     axis[index, 0].plot(time_axis, scaled_samples[0:len(time_axis)])
#     axis[index, 0].set_xlim(0, 3000)
#     axis[index, 0].set_title(f'Signal {key}')
#     plt.setp(axis[index, 0], ylabel=unit.data)
#
#     # Plot FFT
#     axis[index, 1].plot(freq, dbfs)
#     axis[index, 1].set_xlim(0, 3000)
#     axis[index, 1].set_title(f'Signal {key}')
#     plt.setp(axis[index, 1], ylabel=freq_label)
#
#     # Print information about the signal to the console
#     print(f'Signal {key}, {len(samples)} samples from {value["start_time"]}, unit {unit.data}')
#     if "validity" in value:
#         print(f'  Data Quality issues:')
#         for s in get_quality_strings(value["validity"]):
#             print(f'    {s}')
#
# plt.setp(axis[-1, 0], xlabel='Time [s]')
# plt.setp(axis[-1, 1], xlabel='Frequency [Hz]')
#
# if args.save_plot:
#     plotname = path.splitext(args.file)[0] + ".png"
#     plt.savefig(plotname, dpi = 500)
#     print(f'Plot saved as {plotname}')
# else:
#     plt.show()
