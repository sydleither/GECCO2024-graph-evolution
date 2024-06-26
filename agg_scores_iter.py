from collections import Counter
import os
import pickle
import sys
import json

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy.stats import norm, expon
import seaborn as sns

import matplotlib
matplotlib.rcParams['pdf.fonttype'] = 42
matplotlib.rcParams['ps.fonttype'] = 42
sns.set_palette(sns.color_palette(["#f4a9b5", "#d68c45", "#4c956c"]))

sys.path.insert(0, "{}/graph-evolution".format(os.getcwd()))
from organism import Organism
from eval_functions import Evaluation


OBJECTIVES_OF_INTEREST = ["connectance", "average_positive_interactions_strength", "average_negative_interactions_strength",
                          "number_of_competiton_pairs", "positive_interactions_proportion", "strong_components", 
                          "proportion_of_self_loops", "in_degree_distribution", "out_degree_distribution"]


def entropy_boxplot(df, x, y, hue, group, iter_path, num_obj):
    figure, axis = plt.subplots(4, 5, figsize=(32,20))
    row = 0
    col = 0
    for g in df[group].unique():
        sns.boxplot(data=df.loc[df[group] == g], x=x, y=y, hue=hue, ax=axis[row][col])
        axis[row][col].set_yscale('log')
        row += 1
        if row % 4 == 0:
            col += 1
            row = 0
    figure.tight_layout(rect=[0, 0.03, 1, 0.95])
    figure.suptitle("Iteration path {}, {} objectives".format(iter_path, num_obj))
    plt.savefig("{}_{}.png".format(iter_path, num_obj))
    plt.close()


def mse_boxplot(df, x, y, hue, group, iter_path, num_obj):
    figure, axis = plt.subplots(4, 5, figsize=(32,20))
    row = 0
    col = 0
    for g in df[group].unique():
        sns.boxplot(data=df.loc[df[group] == g], x=x, y=y, hue=hue, ax=axis[row][col])
        axis[row][col].set_yscale('log')
        axis[row][col].set_title("Combo {}".format(g))
        row += 1
        if row % 4 == 0:
            col += 1
            row = 0
    figure.tight_layout(rect=[0, 0.03, 1, 0.95])
    figure.suptitle("Iteration path {}, {} objectives".format(iter_path, num_obj))
    plt.savefig("{}_{}.png".format(iter_path, num_obj))
    plt.close()


def save_df(data_dir):
    df_cols = ["experiment_name", "num_obj", "iter_path", "combo", "rep", "network_size", "objective", "MSE"]
    df_rows = []

    for experiment_dir in os.listdir(data_dir):
        full_obj_path = "{}/{}".format(data_dir, experiment_dir)
        if not os.path.isfile(full_obj_path):
            for rep_dir in os.listdir(full_obj_path):
                full_rep_path = "{}/{}".format(full_obj_path, rep_dir)
                if not os.path.isfile(full_rep_path):
                    #skip uncompleted experiments or read in final pop
                    if not os.path.exists("{}/final_pop.pkl".format(full_rep_path)):
                        print("Skipped {} rep {}".format(experiment_dir, rep_dir))
                        break
                    #read in fitness log
                    with open("{}/fitness_log.pkl".format(full_rep_path), "rb") as f:
                        fitness_log = pickle.load(f)
                    #get details of experiments via experiment directory name
                    parts_of_experiment_dir_name = experiment_dir.split("_")
                    experiment_name = experiment_dir
                    num_obj = parts_of_experiment_dir_name[0]
                    iter_path = parts_of_experiment_dir_name[1]
                    combo = parts_of_experiment_dir_name[2]
                    network_size = parts_of_experiment_dir_name[3]
                    #add values of interest to a list to turn into a dataframe
                    for objective,fitnesses in fitness_log.items():
                        if objective == "number_of_competiton_pairs":
                            objective = "recip neg"
                        elif objective == "average_positive_interactions_strength":
                            objective = "avg pos"
                        elif objective == "average_negative_interactions_strength":
                            objective = "avg neg"
                        elif objective == "positive_interactions_proportion":
                            objective = "pos prop"
                        elif objective == "in_degree_distribution":
                            objective = "in-dd"
                        elif objective == "out_degree_distribution":
                            objective = "out-dd"
                        elif objective == "strong_components":
                            objective = "str comp"
                        elif objective == "proportion_of_self_loops":
                            objective = "prop self"
                        df_rows.append([experiment_name, num_obj, iter_path, combo, rep_dir, 
                                        int(network_size), objective, float(fitnesses[-1])])

    df = pd.DataFrame(data=df_rows, columns=df_cols)
    df.to_pickle("experiments/df.pkl")


def save_entropy_df(data_dir):
    df_cols = ["experiment_name", "num_obj", "iter_path", "combo", "rep", "network_size", 
               "objective", "under_selection", "mse", "entropy", "num_unique", "pop_size"]
    df_rows = []

    for experiment_dir in os.listdir(data_dir):
        full_obj_path = "{}/{}".format(data_dir, experiment_dir)
        if not os.path.isfile(full_obj_path):
            for rep_dir in os.listdir(full_obj_path):
                full_rep_path = "{}/{}".format(full_obj_path, rep_dir)
                if not os.path.isfile(full_rep_path):
                    #skip uncompleted experiments or read in final pop
                    if not os.path.exists("{}/final_pop.pkl".format(full_rep_path)):
                        print("Skipped {} rep {}".format(experiment_dir, rep_dir))
                        break
                    with open("{}/final_pop.pkl".format(full_rep_path), "rb") as f:
                        final_pop = pickle.load(f)
                    #read in fitness log
                    with open("{}/fitness_log.pkl".format(full_rep_path), "rb") as f:
                        fitness_log = pickle.load(f)
                    #read in entropy csv as a dataframe
                    entropy_df = pd.read_csv("{}/entropy.csv".format(full_rep_path))
                    #get details of experiments via experiment directory name
                    parts_of_experiment_dir_name = experiment_dir.split("_")
                    experiment_name = experiment_dir
                    num_obj = parts_of_experiment_dir_name[0]
                    iter_path = parts_of_experiment_dir_name[1]
                    combo = parts_of_experiment_dir_name[2]
                    network_size = parts_of_experiment_dir_name[3]
                    #get unique counts of properties in final pop
                    config_file = json.load(open("{}/config.json".format(full_obj_path)))
                    eval_obj = Evaluation(config_file)
                    for property in OBJECTIVES_OF_INTEREST:
                        eval_func = getattr(eval_obj, property)
                        if property.endswith("distribution"):
                            orgs = [tuple(eval_func(org)) for org in final_pop]
                        else:
                            orgs = [eval_func(org) for org in final_pop]
                        unique_orgs = len(Counter(orgs))
                        entropy = entropy_df.loc[entropy_df["Name"] == property]["Entropy(bits)"].values[0]
                        if property in fitness_log:
                            under_selection = True
                            fitness = float(fitness_log[property][-1])
                        else:
                            under_selection = False
                            fitness = -1
                        if property == "number_of_competiton_pairs":
                            property = "recip neg"
                        elif property == "average_positive_interactions_strength":
                            property = "avg pos"
                        elif property == "average_negative_interactions_strength":
                            property = "avg neg"
                        elif property == "positive_interactions_proportion":
                            property = "pos prop"
                        elif property == "in_degree_distribution":
                            property = "in-dd"
                        elif property == "out_degree_distribution":
                            property = "out-dd"
                        elif property == "strong_components":
                            property = "str comp"
                        elif property == "proportion_of_self_loops":
                            property = "prop self"
                        df_rows.append([experiment_name, num_obj, iter_path, combo, rep_dir, int(network_size), 
                                        property, under_selection, fitness, float(entropy), unique_orgs, 200])

    df = pd.DataFrame(data=df_rows, columns=df_cols)
    df.to_pickle("experiments/df_entropy.pkl")


def save_mse_boxplots():
    df = pd.read_pickle("experiments/df.pkl")
    for iter_exp in df["iter_path"].unique():
        df_iter = df.loc[df["iter_path"] == iter_exp]
        for obj_num in df_iter["num_obj"].unique():
            df_iter_obj = df_iter.loc[df_iter["num_obj"] == obj_num]
            print("{}_{}".format(iter_exp, obj_num))
            mse_boxplot(df_iter_obj, "network_size", "MSE", "objective", "combo", iter_exp, obj_num)


def save_five_obj_boxplots():
    df = pd.read_pickle("experiments/df.pkl")
    df = df.loc[df["num_obj"] == "5"]
    figure, axis = plt.subplots(1, 3, figsize=(18,5))
    col = 0
    for g in df["iter_path"].unique():
        sns.boxplot(data=df.loc[df["iter_path"] == g], x="objective", y="MSE", hue="network_size", ax=axis[col])
        axis[col].set_yscale('log')
        axis[col].set_title("Set {}".format(int(g)+1))
        for tick in axis[col].xaxis.get_major_ticks()[1::2]:
            tick.set_pad(15)
        col += 1
    figure.tight_layout(rect=[0, 0.03, 1, 0.95])
    figure.suptitle("Five Objective Experiments")
    plt.savefig("five_objectives.png")
    plt.close()


def set_comparison_figure():
    matplotlib.rcParams.update({'font.size': 11})
    df = pd.read_pickle("experiments/df.pkl")
    figure, axis = plt.subplots(1, 3, figsize=(16,5))
    col = 0
    for g in sorted(df["iter_path"].unique()):
        x = sns.barplot(data=df.loc[df["iter_path"] == g], x="objective", y="MSE", hue="network_size", ax=axis[col], errorbar="ci")
        x.set(ylabel="Error")
        axis[col].set_yscale("log")
        axis[col].set_ylim(1e-10, 1e4)
        axis[col].set_title("Set {}".format(int(g)+1))
        sns.move_legend(axis[col], "upper left")
        col += 1
    figure.tight_layout(rect=[0, 0.03, 1, 0.95])
    figure.suptitle("Error of Experiments Within Each Set")
    plt.savefig("set_performance.png")
    plt.close()


def degree_dist_section_data():
    df = pd.read_pickle("experiments/df.pkl")
    network_size = 100
    iter_path = "0"
    num_obj = "4"

    df1 = df.loc[(df["iter_path"] == iter_path) & (df["network_size"] == network_size) & (df["num_obj"] == num_obj)]
    df1 = df1.loc[(df["objective"] == "in-dd") | (df["objective"] == "out-dd")]
    print(df1[["iter_path", "combo", "num_obj", "objective", "MSE"]].groupby(["iter_path", "num_obj", "combo", "objective"]).mean())
    print(np.mean(df1["MSE"].values))

    df1 = df.loc[(df["iter_path"] == iter_path)]
    dd_combos = set(df1.loc[(df1["objective"] == "in-dd") | (df1["objective"] == "out-dd")]["experiment_name"].values)
    df3 = df1[~df1.experiment_name.isin(dd_combos)]
    print("no DD: ", np.mean(df3["MSE"].values))
    df2 = df1[df1.experiment_name.isin(dd_combos)]
    print("With DD: ", np.mean(df2["MSE"].values))


def objective_interactions_data():
    df = pd.read_pickle("experiments/df.pkl")
    num_obj = "3"
    
    df1 = df.loc[(df["num_obj"] == num_obj)]
    dd_combos = set(df1.loc[(df1["objective"] == "in-dd") | (df1["objective"] == "out-dd")]["experiment_name"].values)
    df1 = df1[~df1.experiment_name.isin(dd_combos)]
    for ns in sorted(df1["network_size"].unique()):
        print(ns)
        df_ns11 = df1.loc[df1["network_size"] == ns]
        df_ns111 = df_ns11[["combo", "iter_path", "MSE"]].groupby(["iter_path", "combo"]).mean()
        ns111 = df_ns111.values
        ns111 = np.mean([x for x in ns111 if x != 0])
        #ns111 = np.mean(ns111)
        print(df_ns111)
        print(ns111)

    dd_combos = set(df.loc[(df["objective"] == "in-dd") | (df["objective"] == "out-dd")]["experiment_name"].values)
    df0 = df[~df.experiment_name.isin(dd_combos)]
    df1 = df[df.experiment_name.isin(dd_combos)]
    print(df0[["network_size", "num_obj", "MSE"]].groupby(["num_obj", "network_size"]).mean())
    print(df[["network_size", "num_obj", "MSE"]].groupby(["num_obj", "network_size"]).mean())
    print(df1[["network_size", "num_obj", "MSE"]].groupby(["num_obj", "network_size"]).mean())

    matplotlib.rcParams.update({'font.size': 12})
    df = df1
    df["num_obj"] = df["num_obj"].apply(pd.to_numeric)
    min_val = np.min(df[(df["MSE"] > 0)]["MSE"])
    max_val = np.max(df[(df["MSE"] > 0)]["MSE"])
    figure, axis = plt.subplots(1, 1, figsize=(6,5))
    x = sns.boxplot(data=df, x="num_obj", y="MSE", hue="network_size", ax=axis)
    axis.set_yscale('symlog', linthresh=min_val)
    axis.set_ylim(-min_val, max_val+min_val)
    x.set(xlabel="Number of Objectives")
    x.set(ylabel="Error")
    figure.tight_layout(rect=[0, 0.03, 1, 0.95])
    figure.suptitle("Average Error of Experiments Not Including Degree Distribution")
    plt.savefig("idk.png")
    plt.close()


def final_figures():
    df = pd.read_pickle("experiments/df.pkl")
    matplotlib.rcParams.update({'font.size': 12})
    df["num_obj"] = df["num_obj"].apply(pd.to_numeric)

    dd_combos = set(df.loc[(df["objective"] == "in-dd") | (df["objective"] == "out-dd")]["experiment_name"].values)
    df1 = df[~df.experiment_name.isin(dd_combos)]
    min_val = np.min(df1[(df1["MSE"] > 0)]["MSE"])
    max_val = np.max(df1[(df1["MSE"] > 0)]["MSE"])
    figure, axis = plt.subplots(1, 1, figsize=(6,5))
    x = sns.boxplot(data=df1, x="num_obj", y="MSE", hue="network_size", ax=axis)
    axis.set_yscale('symlog', linthresh=min_val)
    axis.set_ylim(-min_val, max_val+min_val)
    x.set(xlabel="Number of Objectives")
    x.set(ylabel="Error")
    figure.tight_layout(rect=[0, 0.03, 1, 0.95])
    figure.suptitle("Error of Experiments Not Including Degree Distribution")
    plt.savefig("idk.png")
    plt.close()

    df1 = df.loc[(df["objective"] == "in-dd") | (df["objective"] == "out-dd")]
    min_val = np.min(df1[(df1["MSE"] > 0)]["MSE"])
    max_val = np.max(df1[(df1["MSE"] > 0)]["MSE"])
    figure, axis = plt.subplots(1, 1, figsize=(6,5))
    x = sns.boxplot(data=df1, x="num_obj", y="MSE", hue="network_size", ax=axis)
    axis.set_yscale('symlog', linthresh=min_val)
    axis.set_ylim(-min_val/4, max_val+min_val*2)
    x.set(xlabel="Number of Objectives")
    x.set(ylabel="Error")
    figure.tight_layout(rect=[0, 0.03, 1, 0.95])
    figure.suptitle("Degree Distribution Error")
    plt.savefig("dd.png")
    plt.close()


def entropy_data():
    which_set = 2

    topological = ["str comp", "prop self", "connectance"]
    weight = ["recip neg", "avg pos", "avg neg", "pos prop"]

    df = pd.read_pickle("experiments/df_entropy.pkl")
    df["uniformity"] = df["entropy"] / np.log2(df["num_unique"])
    df["uniformity"] = df["uniformity"].fillna(0)
    df["spread"] = df["num_unique"] / df["pop_size"]

    perfect_runs = []
    for experiment_name in df["experiment_name"].unique():
        num_scores = df.loc[(df["experiment_name"] == experiment_name) & (df["under_selection"] == True)]
        perfect = df.loc[(df["experiment_name"] == experiment_name) & (df["under_selection"] == True) & (df["mse"] == 0)]
        if len(perfect) == len(num_scores):
            perfect_runs.append(experiment_name)
    df_perf = df[df.experiment_name.isin(perfect_runs)]

    if which_set == 0:
        df0 = df_perf.loc[(df_perf["iter_path"] == "0")]
        invalid = set(df0[df0.objective.isin(weight) & (df0["under_selection"] == True)]["experiment_name"].values)
        df0 = df0[~df0.experiment_name.isin(invalid)]
        df0 = df0.loc[(df0["under_selection"] == False) & (df0["objective"] == "avg pos")]
    else:
        df0 = df_perf.loc[(df_perf["iter_path"] == "2")]
        invalid = set(df0[df0.objective.isin(topological) & (df0["under_selection"] == True)]["experiment_name"].values)
        df0 = df0[~df0.experiment_name.isin(invalid)]
        df0 = df0.loc[(df0["under_selection"] == False) & (df0["objective"] == "connectance")]
    
    print(df0[["iter_path", "network_size", "combo", "num_obj", "objective", "num_unique", "uniformity", "spread"]].groupby(["iter_path", "network_size", "num_obj", "combo", "objective"]).mean())
    print(df0[["num_unique", "uniformity", "spread"]].mean())


def generate_dist_plots():
    num_nodes = 100
    network_size = num_nodes
    ns_inv = 1/network_size
    if network_size == 10:
        basically_exp = [ns_inv*np.floor(expon.pdf(x, loc=1, scale=network_size/5)/ns_inv) for x in range(network_size+1)]
    else:
        basically_exp = [ns_inv*np.round(expon.pdf(x, loc=1, scale=network_size/5)/ns_inv) for x in range(network_size+1)]
    basically_norm = [ns_inv*np.round(norm.pdf(x, loc=network_size/4, scale=network_size/10)/ns_inv) for x in range(network_size+1)]

    fig, ax2 = plt.subplots(1, 2, figsize=(7, 5))
    ax2[0].plot(list(range(num_nodes+1)), basically_exp, linewidth=5, color="deeppink")
    ax2[1].plot(list(range(num_nodes+1)), basically_norm, linewidth=5, color="deeppink")
    ax2[0].set_title("Exponential")
    ax2[1].set_title("Normal")
    fig.suptitle(f"Target Degree Distributions for Networks of Size {num_nodes}")
    fig.supxlabel("Degree")
    fig.supylabel("Proportion of Nodes")
    fig.tight_layout()
    plt.savefig("target_distributions.png")
    plt.close()


def poster_error():
    df = pd.read_pickle("experiments/df.pkl")
    matplotlib.rcParams.update({"font.size": 20})
    df["num_obj"] = df["num_obj"].apply(pd.to_numeric)

    figure, axis = plt.subplots(1, 1, figsize=(10,10), dpi=150)
    x = sns.barplot(data=df, x="num_obj", y="MSE", hue="network_size", ax=axis, errorbar="ci", palette="Greens_d")
    x.legend(framealpha=0.33, title="Graph Size")
    axis.set_yscale('log')
    x.set(xlabel="Number of Constrained Properties")
    x.set(ylabel="Error")
    figure.tight_layout(rect=[0, 0.03, 1, 0.95])
    figure.suptitle("Error of Experiments")
    plt.savefig("poster.png", transparent=True)
    plt.close()


def poster_diversity():
    topological = ["str comp", "prop self", "connectance"]
    weight = ["recip neg", "avg pos", "avg neg", "pos prop"]

    df = pd.read_pickle("experiments/df_entropy.pkl")
    df["uniformity"] = df["entropy"] / np.log2(df["num_unique"])
    df["uniformity"] = df["uniformity"].fillna(0)
    df["spread"] = df["num_unique"] / df["pop_size"]

    perfect_runs = []
    for experiment_name in df["experiment_name"].unique():
        num_scores = df.loc[(df["experiment_name"] == experiment_name) & (df["under_selection"] == True)]
        perfect = df.loc[(df["experiment_name"] == experiment_name) & (df["under_selection"] == True) & (df["mse"] == 0)]
        if len(perfect) == len(num_scores):
            perfect_runs.append(experiment_name)
    df_perf = df[df.experiment_name.isin(perfect_runs)]

    df_t = df_perf.loc[(df_perf["iter_path"] == "0")]
    invalid = set(df_t[df_t.objective.isin(weight) & (df_t["under_selection"] == True)]["experiment_name"].values)
    df_t = df_t[~df_t.experiment_name.isin(invalid)]
    df_t = df_t.loc[(df_t["under_selection"] == False) & (df_t["objective"] == "avg pos")]
    df_t["div_group"] = "Topological"

    df_e = df_perf.loc[(df_perf["iter_path"] == "2")]
    invalid = set(df_e[df_e.objective.isin(topological) & (df_e["under_selection"] == True)]["experiment_name"].values)
    df_e = df_e[~df_e.experiment_name.isin(invalid)]
    df_e = df_e.loc[(df_e["under_selection"] == False) & (df_e["objective"] == "connectance")]
    df_e["div_group"] = "Edge-Weight"

    df_div = pd.concat([df_e, df_t])

    diversity_measure = "spread"
    matplotlib.rcParams.update({"font.size": 20})
    figure, axis = plt.subplots(1, 1, figsize=(10,5), dpi=150)
    x = sns.barplot(data=df_div, x="div_group", y=diversity_measure, hue="network_size", ax=axis, errorbar="ci", palette="Greens_d")
    x.legend(framealpha=0.33, title="Graph Size")
    x.set(xlabel="Type of Constrained Properties")
    x.set(ylabel=diversity_measure)
    figure.tight_layout(rect=[0, 0.03, 1, 0.95])
    figure.suptitle("Diversity of Experiments")
    plt.savefig(f"{diversity_measure}.png", transparent=True)
    plt.close()


if __name__ == "__main__":
    if len(sys.argv) == 3:
        if sys.argv[-1] == "save":
            save_df(sys.argv[1])
        elif sys.argv[-1] == "save_entropy":
            save_entropy_df(sys.argv[1])
        else:
            print("Please give a valid save function.")
    elif len(sys.argv) == 2:
        if sys.argv[-1] == "mse":
            save_mse_boxplots()
        elif sys.argv[-1] == "five":
            save_five_obj_boxplots()
        elif sys.argv[-1] == "dist":
            degree_dist_section_data()
        elif sys.argv[-1] == "final":
            final_figures()
        elif sys.argv[-1] == "set":
            set_comparison_figure()
        elif sys.argv[-1] == "entropy":
            entropy_data()
        elif sys.argv[-1] == "poster1":
            poster_error()
        elif sys.argv[-1] == "poster2":
            poster_diversity()
        else:
            print("Please give a valid function to run.")
    else:
        print("Please give inputs for the script.")