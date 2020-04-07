# -*- coding: utf-8 -*-
"""
Created on Wed Feb 12 00:38:49 2020

@author: Libra

summs up coding features with the current form. relays on GLM_stats module. For similar function but weights more on delay period, see GLM_delay_stats.py
"""
import os
import h5py
import csv
# import itertools
from GLM_stats import GLM_stats
import numpy as np
import su_region_align as align


def prepare_GLM():
    curr_stats = GLM_stats()
    all_sess_list = []
    reg_list = []
    dpath = align.get_root_path()
    for path in align.traverse(dpath):
        print(path)
        trial_FR = None
        trials = None
        if not os.path.isfile(os.path.join(path, "su_id2reg.csv")):
            continue
        done_read = False
        while not done_read:
            try:
                with h5py.File(os.path.join(path, "FR_All.hdf5"), "r") as ffr:
                    # print(list(ffr.keys()))
                    if not "SU_id" in ffr.keys():
                        done_read = True
                        print("missing su_id key in path ", path)
                        continue
                    dset = ffr["FR_All"]
                    trial_FR = np.array(dset, dtype="double")
                    dset = ffr["Trials"]
                    trials = np.array(dset, dtype="double").T
                done_read = True
            except OSError:
                print("h5py read error handled")

        suid_reg = None
        with open(os.path.join(path, "su_id2reg.csv")) as csvfile:
            lines = list(csv.reader(csvfile))[1:]
            suid_reg = [list(line) for line in zip(*lines)]

        (perf_desc, perf_code, welltrain_window, correct_resp) = align.judgePerformance(trials)

        if perf_code != 3:
            continue

        curr_stats.processGLMStats(trial_FR, trials, welltrain_window, correct_resp)
        one_session = curr_stats.getFeatures()
        all_sess_list.append(one_session)
        reg_list.extend(suid_reg[1])

    return (all_sess_list, reg_list)


# %% main
def process_all(denovo=False):
    all_sess_arr = None
    reg_arr = None
    if denovo:
        ### save raw data file
        (all_sess_list, reg_list) = prepare_GLM()
        all_sess_arr = np.concatenate(tuple(all_sess_list), axis=1)
        reg_arr = np.array(reg_list)
        np.savez_compressed('GLM_stats.npz', all_sess_arr=all_sess_arr, reg_arr=reg_arr)
    else:
        ### load back saved raw data
        if not os.path.isfile("GLM_stats.npz"):
            print('missing data file!')
            return
        np.load('GLM_stats.npz')
        fstr = np.load('GLM_stats.npz')
        reg_arr = fstr['reg_arr']
        all_sess_arr = fstr['all_sess_arr']

    su_factors = []
    reg_set = list(set(reg_arr.tolist()))
    su_factors.append(reg_set)
    plot_figure = False
    if plot_figure:
        reg_n = []
        for i in range(len(reg_set)):
            reg_n.append(f'{np.count_nonzero(reg_arr == reg_set[i])} SU {reg_set[i]}')
        feature_tag = ['sample selective during sample',
                       'sample selective during early delay',
                       'sample selective during late delay',
                       'sample selective ONLY during late delay',
                       'sample selective during decision making',
                       'test selective during decision making',
                       'pair selective during decision making',
                       'pair selective ONLY during reward',
                       'nonselective modulation during late delay',
                       'nonselective modulation during decision making',
                       'unmodulated']
        import matplotlib.pyplot as plt
        fh = plt.figure(figsize=(11.34, 40), dpi=300)

    for feature in range(11):
        per_region_su_factor = np.zeros_like(reg_set, dtype=np.float64)
        for i in range(len(reg_set)):
            per_region_su_factor[i] = np.mean(all_sess_arr[feature, reg_arr == reg_set[i]])
        su_factors.append(per_region_su_factor.tolist())

        if plot_figure:
            reg_idx = np.argsort(per_region_su_factor)
            ax = plt.subplot(11, 1, feature + 1)
            plt.bar(np.arange(len(reg_set)), per_region_su_factor[reg_idx])
            ax.set_xticks(np.arange(len(reg_set)))
            ax.set_xticklabels(np.array(reg_n)[reg_idx], rotation=90, ha='center', va='top', fontsize=7.5)
            ax.set_xlim(-1, len(reg_set))
            ax.set_ylabel(feature_tag[feature])

    if plot_figure:
        plt.tight_layout(rect=[0, 0, 1, 0.95])
        fh.savefig("coding_feature.png", dpi=300, bbox_inches="tight")
        plt.show()

    su_factors = [list(i) for i in zip(*su_factors)]

    ### export csv for matlab GLM
    with open("glm_coding_features.csv", "w", newline="") as cf:
        cwriter = csv.writer(cf, dialect="excel")
        for row in su_factors:
            cwriter.writerow(row)
