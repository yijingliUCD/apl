"""
extract_breath_meta
~~~~~~~~~~~~~~~~~~~~~

Creates aptv files which are necessary for annotation purposes.

Essentially just grabs all the metadata in a raw breath file and sticks it
into a separate file that can be consumed by flask at execution.
"""
import argparse
import csv
import os
from datetime import datetime
from os.path import basename, dirname, splitext
import time

from ventmap.breath_meta import get_experimental_breath_meta, get_production_breath_meta
from ventmap.raw_utils import extract_raw
from DCA import cal_slope_dyna,cal_slope_static,median_flow_dyna,find_flat_num,find_flat_df,repeatingNumbers
import defaults as config
from sklearn.linear_model import LinearRegression
from itertools import groupby




def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("filename")
    args = parser.parse_args()
    filename = args.filename

    base = basename(filename)
    base = splitext(base)[0]
    apfile = base + '_atv.csv'
    apfile = os.path.join(dirname(__file__), config.APTV_OUTPUT_DIR, apfile)

    peep_prev     = 'N/A'
    start_time = time.time()
    rel_time = 0.02

    with open (filename, 'rU') as out, open(apfile, 'wt') as ap:
        generator = extract_raw(out, False)
        aptv_writer = csv.writer(ap, delimiter=',', quoting=csv.QUOTE_NONE)

        for breath in generator:
            meta = get_production_breath_meta(breath)
            meta_exp = get_experimental_breath_meta(breath)
            # set datetime format
            if len(breath['ts']) != 0:
                desired_format = "%Y-%m-%d %H:%M:%S.%f"
                as_dt = datetime.strptime(breath['ts'][0], "%Y-%m-%d %H-%M-%S.%f")
                abs_bs_time = as_dt.strftime(desired_format)
            else:
                abs_bs_time = ""
            # meta 9 is tvi, meta 10 is tve, meta 6 is iTime, 7 is eTime
            # 35 is min pressure, 17 is peep,
            fbit = meta[6] 
            pbit = meta_exp[-1]
            fbit_pbit = fbit/pbit
            #
            slope_dyna=cal_slope_dyna(breath)

            slope_static=cal_slope_static(breath)
            flow_median = median_flow_dyna(breath)
            #
            aptv_writer.writerow([
                breath['rel_bn'], 
                round(meta[9], 1), 
                round(meta[10], 1),
                breath['vent_bn'], 
                round(meta[7], 2), 
                round(meta[6], 2), 
                peep_prev,
                round(meta[35], 2), 
                round(meta[17], 2), 
                rel_time, 
                abs_bs_time, 
                round(fbit_pbit,2),
                round(slope_dyna,2),
                round(slope_static,2),
                round(flow_median,2),
                round(pbit,2),# LYJ: add new feature 
            ])
            peep_prev = round(meta[17], 2)
            rel_time = round(rel_time + breath['frame_dur'], 2)

    print("--- APTV file created in {} seconds ---".format(time.time() - start_time))


if __name__ == "__main__":
    main()




