# -*- coding: utf-8 -*-
"""
Created on Wed Feb 12 00:14:22 2020

@author: Libra


@author: Libra

Generate transient sustained percentage pie chart
Depends on intermediate data from CQTransient.py-> CQ_transient.m

For 1D and 2D decoding, use sus_transient_decoding.py

"""

import os
import h5py
import csv
import sys
import numpy as np
import matplotlib.pyplot as plt
import scipy.stats as stats
import su_region_align as align


class per_sec_stats:
    def __init__(self):
        self.per_sec_sel = None  # 7 x SU , sample + 6s delay
        self.per_sec_prefS1 = None  # 7 x SU , sample + 6s delay
        self.per_sec_prefS2 = None  # 7 x SU , sample + 6s delay
        self.non_sel_mod = None  # 7 x SU
        self.non_mod = None  # 7 x SU

        self.use_ranksum = True

    def bool_stats_test(self, A, B):
        ### TODO alternative use of perm_test
        if self.use_ranksum:
            try:
                # flatten is used instead of mean to control for variance
                # ranksum is supposedly insensitive to length of data
                (stat, p) = stats.mannwhitneyu(
                    A.flatten(),
                    B.flatten(),
                    alternative="two-sided",
                )
                return p < (0.05 / 7)

            except ValueError:
                return False

    def exact_mc_perm_test(self, xs, ys, nmc):
        n, k = len(xs), 0
        diff = np.abs(np.mean(xs) - np.mean(ys))
        zs = np.concatenate([xs, ys])
        for j in range(nmc):
            np.random.shuffle(zs)
            k += diff < np.abs(np.mean(zs[:n]) - np.mean(zs[n:]))
        return k / nmc

    def processGLMStats(self, trial_FR, trials, welltrain_window=None, correct_resp=None, delay=6):

        # trial_FR [bin, trial, SU]
        ### TODO: when variables are none

        ### TODO: 3s delay branch

        firing_rate_6 = trial_FR[:, (trials[:, 5] == 6) & welltrain_window & correct_resp, :]
        firing_rate_3 = trial_FR[:, (trials[:, 5] == 3) & welltrain_window & correct_resp, :]
        trial_perf_sel_6 = trials[(trials[:, 5] == 6) & welltrain_window & correct_resp, :]
        trial_perf_sel_3 = trials[(trials[:, 5] == 3) & welltrain_window & correct_resp, :]

        trial_sel_left_6 = trial_perf_sel_6[:, 2] == 4
        trial_sel_left_3 = trial_perf_sel_3[:, 2] == 4

        self.per_sec_sel = np.zeros((7, trial_FR.shape[2]))
        self.per_sec_prefS1 = np.zeros_like(self.per_sec_sel)
        self.per_sec_prefS2 = np.zeros_like(self.per_sec_sel)
        self.non_sel_mod = np.zeros_like(self.per_sec_sel)

        for su_idx in range(trial_FR.shape[2]):
            onesu_6 = np.squeeze(firing_rate_6[:, :, su_idx]).T
            onesu_3 = np.squeeze(firing_rate_3[:, :, su_idx]).T
            left_trials_6 = onesu_6[trial_sel_left_6, :]
            right_trials_6 = onesu_6[~trial_sel_left_6, :]

            left_trials_3 = onesu_3[trial_sel_left_3, :]
            right_trials_3 = onesu_3[~trial_sel_left_3, :]

            # SP = np.arange(12, 16) ED = np.arange(18, 28) LD = np.arange(28, 38)
            if delay == 6:
                for bin_idx in range(0, 7):
                    bins = np.arange(bin_idx * 4 + 12, bin_idx * 4 + 16)
                    self.per_sec_sel[bin_idx, su_idx] = self.bool_stats_test(left_trials_6[:, bins],
                                                                             right_trials_6[:, bins])
                    if self.per_sec_sel[bin_idx, su_idx]:
                        if np.mean(left_trials_6[:, bins]) > np.mean(right_trials_6[:, bins]):
                            self.per_sec_prefS1[bin_idx, su_idx] = 1
                        else:
                            self.per_sec_prefS2[bin_idx, su_idx] = 1

                    self.non_sel_mod[bin_idx, su_idx] = ((not self.per_sec_sel[bin_idx, su_idx]) and
                                                         self.bool_stats_test(onesu_6[:, bins],
                                                                              onesu_6[:, 6:10]))
            elif delay == 3:
                for bin_idx in range(0, 4):
                    bins = np.arange(bin_idx * 4 + 12, bin_idx * 4 + 16)
                    self.per_sec_sel[bin_idx, su_idx] = self.bool_stats_test(left_trials_3[:, bins],
                                                                             right_trials_3[:, bins])
                    if self.per_sec_sel[bin_idx, su_idx]:
                        if np.mean(left_trials_3[:, bins]) > np.mean(right_trials_3[:, bins]):
                            self.per_sec_prefS1[bin_idx, su_idx] = 1
                        else:
                            self.per_sec_prefS2[bin_idx, su_idx] = 1

                    self.non_sel_mod[bin_idx, su_idx] = ((not self.per_sec_sel[bin_idx, su_idx]) and
                                                         self.bool_stats_test(onesu_3[:, bins],
                                                                              onesu_3[:, 6:10]))
                # self.non_mod[bin_idx, su_idx] = not (
                #         self.per_sec_sel[bin_idx, su_idx] or self.non_sel_mod[bin_idx, su_idx])

    def getFeatures(self):
        return (self.per_sec_sel, self.non_sel_mod, self.per_sec_prefS1, self.per_sec_prefS2)


### all brain region entry point

def prepare_data(delay=6):
    # TODO: 3s delay branch
    curr_stats = per_sec_stats()
    per_sec_sel_list = []
    non_sel_mod_list = []
    perfS1_list = []
    perfS2_list = []
    # non_mod_list = []
    reg_list = []
    dpath = align.get_root_path()
    for path in sorted(align.traverse(dpath)):
        print(path)
        # SU_ids = []
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
                    # dset = ffr["SU_id"]
                    # SU_ids = np.array(dset, dtype="uint16")
                    dset = ffr["FR_All"]
                    trial_FR = np.array(dset, dtype="double")
                    dset = ffr["Trials"]
                    trials = np.array(dset, dtype="double").T
                done_read = True
            except OSError:
                print("h5py read error handled")
        if trials is None:
            continue
        suid_reg = []
        with open(os.path.join(path, "su_id2reg.csv")) as csvfile:
            l = list(csv.reader(csvfile))[1:]
            suid_reg = [list(i) for i in zip(*l)]

        (perf_desc, perf_code, welltrain_window, correct_resp) = align.judgePerformance(trials)

        if perf_code != 3:
            continue

        curr_stats.processGLMStats(trial_FR, trials, welltrain_window, correct_resp, delay=delay)

        (per_sec_sel, non_sel_mod, perfS1, perfS2) = curr_stats.getFeatures()
        per_sec_sel_list.append(per_sec_sel)
        non_sel_mod_list.append(non_sel_mod)
        # non_mod_list.append(non_sel_mod)
        perfS1_list.append(perfS1)
        perfS2_list.append(perfS2)
        reg_list.extend(suid_reg[1])
    return (per_sec_sel_list, non_sel_mod_list, perfS1_list, perfS2_list, reg_list)


def prepare_data_sync():
    dpath = align.get_root_path()
    syncdata = []
    for path in align.traverse(dpath):
        print(path)
        SU_ids = []
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
                    dset = ffr["SU_id"]
                    SU_ids = np.array(dset, dtype="uint16")
                    dset = ffr["Trials"]
                    trials = np.array(dset, dtype="double").T
                done_read = True
            except OSError:
                print("h5py read error handled")
        if trials is None:
            continue
        suid_reg = []
        with open(os.path.join(path, "su_id2reg.csv")) as csvfile:
            l = list(csv.reader(csvfile))[1:]
            suid_reg = [list(i) for i in zip(*l)]

        (perf_desc, perf_code, welltrain_window, correct_resp) = align.judgePerformance(trials)

        if perf_code != 3:
            continue
        ### TODO: export per su per file alignment file

        for one_su in SU_ids.flatten():
            # breakpoint()
            # print(path+','+one_su.astype(np.str))
            syncdata.append([path, one_su])

    with open("su_list.csv", "w", newline="") as cf:
        cwriter = csv.writer(cf, dialect="excel")
        for row in syncdata:
            cwriter.writerow(row)

    return syncdata


def plot_features():
    # TODO: move figure plot here
    pass


# %% main
def process_all(denovo=False, toPlot=False, toExport=False, delay=6):
    per_sec_sel_arr = None
    non_sel_mod_arr = None
    perfS1_arr = None
    perfS2_arr = None
    reg_arr = None
    if denovo:
        ### save raw data file
        ### TODO need a 3s delay branck
        (per_sec_list, non_sel_mod_list, perfS1_list, perfS2_list, reg_list) = prepare_data(delay=delay)
        per_sec_sel_arr = np.hstack(per_sec_list)
        non_sel_mod_arr = np.hstack(non_sel_mod_list)
        perfS1_arr = np.hstack(perfS1_list)
        perfS2_arr = np.hstack(perfS2_list)

        np.savez_compressed(f'per_sec_sel_{delay}.npz', per_sec_sel_arr=per_sec_sel_arr,
                            non_sel_mod_arr=non_sel_mod_arr,
                            # non_mod_arr=non_mod_arr,
                            perfS1_arr=perfS1_arr,
                            perfS2_arr=perfS2_arr,
                            reg_arr=reg_list,
                            delay=delay)
    else:
        ### load back saved raw data
        if not os.path.isfile(f"per_sec_sel_{delay}.npz"):
            print('missing data file!')
            return
        fstr = np.load(f'per_sec_sel_{delay}.npz')
        per_sec_sel_arr = fstr['per_sec_sel_arr']
        non_sel_mod_arr = fstr['non_sel_mod_arr']
        if fstr['delay'] != delay:
            print('Delay duration mismatch')
        perfS1_arr = fstr['perfS1_arr']
        perfS2_arr = fstr['perfS2_arr']
        # reg_arr = fstr['reg_arr']

    delay_bins = None
    if delay == 6:
        delay_bins = np.arange(1, 7)
    elif delay == 3:
        delay_bins = np.arange(1, 4)

    sample_only = per_sec_sel_arr[0, :].astype(np.bool) & ~np.any(per_sec_sel_arr[delay_bins, :], axis=0)
    sample_only_count = np.count_nonzero(sample_only)
    delay_sel = np.any(per_sec_sel_arr[delay_bins, :], axis=0)
    delay_sel_count = np.count_nonzero(delay_sel)
    non_sel_mod = np.any(non_sel_mod_arr[delay_bins, :], axis=0) & np.logical_not(
        np.any(np.vstack((sample_only, delay_sel)), axis=0))
    non_sel_mod_count = np.count_nonzero(non_sel_mod)
    non_mod = np.logical_not(np.any(np.vstack((sample_only, delay_sel, non_sel_mod)), axis=0))
    non_mod_count = np.count_nonzero(non_mod)

    # output from CQ's algorithm of transient coding, both 3s and 6s obtained
    transient = None
    with h5py.File(os.path.join('transient', 'CQ_transient.hdf5'), 'r') as fr:
        if delay == 6:
            transient = np.array(fr["transient6"]).T
        elif delay == 3:
            transient = np.array(fr["transient3"]).T

    frac = [delay_sel_count, sample_only_count, non_sel_mod_count, non_mod_count]
    explode = (0.1, 0.1, 0, 0)
    labels = ('selective during delay', 'selective only during sample', 'Non-selective modulation', 'Unmodulated')
    fh = None
    axes = None
    if toPlot:
        (fh, axes) = plt.subplots(1, 2, figsize=(10, 5), dpi=200)
        axes[0].pie(frac, explode=explode, labels=labels, autopct='%1.1f%%', shadow=True)
        axes[0].axis('equal')

        explode = (0.1, 0, 0, 0)
        labels = ('sustained', 'transient', 'transient-switched', 'unclassified')

    switched = np.any(perfS1_arr[delay_bins, :], axis=0) & np.any(perfS2_arr[delay_bins, :], axis=0) & transient.astype(
        np.bool).flatten()

    sust_count = np.count_nonzero(np.all(per_sec_sel_arr[delay_bins, :], axis=0) & ~switched)
    transient_count = np.count_nonzero(np.any(per_sec_sel_arr[delay_bins, :], axis=0) & (~switched)
                                       & (~np.all(per_sec_sel_arr[delay_bins, :], axis=0)) & transient.astype(np.bool))
    switched_count = np.count_nonzero(switched)

    unclassified_count = np.count_nonzero(np.any(per_sec_sel_arr[delay_bins, :], axis=0) & (~switched)
                                          & (~np.all(per_sec_sel_arr[delay_bins, :], axis=0)) & ~transient.astype(
        np.bool))
    if toPlot:
        axes[1].pie([sust_count, transient_count, switched_count, unclassified_count], explode=explode, labels=labels,
                    autopct='%1.1f%%',
                    radius=np.sqrt(delay_sel_count / per_sec_sel_arr.shape[1]), shadow=True)
        axes[1].axis('equal')
        axes[0].set_xlim((-1.25, 1.25))
        axes[1].set_xlim((-1.25, 1.25))
        fh.suptitle(f'{delay}s delay')
        fh.savefig(f'sus_trans_pie_{delay}.png')
        plt.show()

    ### export list
    sust_list = np.all(per_sec_sel_arr[delay_bins, :], axis=0) & ~switched
    transient_list = (np.any(per_sec_sel_arr[delay_bins, :], axis=0) & (~switched)
                      & (~np.all(per_sec_sel_arr[delay_bins, :], axis=0)) & transient.astype(np.bool).flatten())
    switched_list = switched
    unclassified_list = (np.any(per_sec_sel_arr[delay_bins, :], axis=0) & (~switched)
                         & (~np.all(per_sec_sel_arr[delay_bins, :], axis=0)) & ~transient.astype(np.bool).flatten())

    export_arr = np.vstack((sust_list, transient_list, switched_list, unclassified_list)).T.astype(np.int8)
    np.savez_compressed(f'sus_trans_pie_{delay}.npz', sust_list=sust_list, transient_list=transient_list,
                        switched_list=switched_list, unclassified_list=unclassified_list, sample_only=sample_only,
                        non_sel_mod=non_sel_mod, non_mod=non_mod)

    if toExport:
        np.savetxt(f'transient_{delay}.csv', export_arr, fmt='%d', delimiter=',',
                   header='Sustained,transient,switched,unclassified')
    return export_arr


def venn():
    # load and align 6s 3s delay selectivity data
    fstr6 = np.load('sus_trans_pie_6.npz')
    fstr3 = np.load('sus_trans_pie_3.npz')
    sample_only_3 = fstr3['sample_only']
    sample_only_6 = fstr6['sample_only']

    np.count_nonzero(sample_only_3)
    np.count_nonzero(sample_only_6)
    np.count_nonzero(sample_only_3 & sample_only_6)

    sus_3 = fstr3['sust_list']
    sus_6 = fstr6['sust_list']

    np.count_nonzero(sus_3)
    np.count_nonzero(sus_6)
    np.count_nonzero(sus_3 & sus_6)

    transient_3 = fstr3['transient_list']
    transient_6 = fstr6['transient_list']

    np.count_nonzero(transient_3)
    np.count_nonzero(transient_6)
    np.count_nonzero(transient_3 & transient_6)

    np.count_nonzero(sus_3 & transient_6)

    switched_3 = fstr3['switched_list']
    switched_6 = fstr6['switched_list']

    np.count_nonzero(switched_3)
    np.count_nonzero(switched_6)
    np.count_nonzero(switched_3 & switched_6)

    non_sel_mod_3 = fstr3['non_sel_mod']
    non_sel_mod_6 = fstr6['non_sel_mod']

    np.count_nonzero(non_sel_mod_3)
    np.count_nonzero(non_sel_mod_6)
    np.count_nonzero(non_sel_mod_3 & non_sel_mod_6)

    non_mod_3 = fstr3['non_mod']
    non_mod_6 = fstr6['non_mod']

    np.count_nonzero(non_mod_3)
    np.count_nonzero(non_mod_6)
    np.count_nonzero(non_mod_3 & non_mod_6)


if __name__ == "__main__":
    # prepare_data_sync()
    process_all(denovo=False, toPlot=True, toExport=False, delay=6)
    process_all(denovo=False, toPlot=True, toExport=False, delay=3)
