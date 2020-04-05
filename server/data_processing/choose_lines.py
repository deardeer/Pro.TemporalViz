import os

import numpy as np
import pandas as pd
from tqdm import tqdm

COORDINATES_COLUMNS = ['0', '1']
# COORDINATES_COLUMNS = [0, 1]

data_processing_dir_prefix = os.path.dirname(os.path.realpath(__file__)).split("Pro.TemporalViz")[0]
data_processing_dir_prefix = os.path.join(data_processing_dir_prefix, "Pro.TemporalViz", "server/data_processing")

def get_lines_distance(line1_p1, line1_p2, line2_p1, line2_p2):
    line1_p1 = np.array(line1_p1)
    line1_p2 = np.array(line1_p2)
    line2_p1 = np.array(line2_p1)
    line2_p2 = np.array(line2_p2)
    p1_distnace = ((line1_p1 - line2_p1) ** 2).sum()
    p2_distance = ((line1_p2 - line2_p2) ** 2).sum()
    return p1_distnace + p2_distance


def get_all_lines_distances(indices, df1, df2, cache_name=None):
    save_cache = False
    if cache_name:
        if os.path.exists(os.path.join(data_processing_dir_prefix, f"cache/{cache_name}.csv")):
            print(f"For choosing strokes, distances are loaded from cahce file 'data_processing/cache/{cache_name}.csv'")
            distances_df = pd.read_csv(os.path.join(data_processing_dir_prefix, f"cache/{cache_name}.csv"))
            return distances_df
        else:
            save_cache = True
    distances = {}

    print("For choosing strokes, calculating distances")
    for i in tqdm(indices):
        for j in indices:
            if i == j:
                continue
            line1_p1 = df1[df1["item"] == i][COORDINATES_COLUMNS]
            line1_p2 = df2[df2["item"] == i][COORDINATES_COLUMNS]
            line2_p1 = df1[df1["item"] == j][COORDINATES_COLUMNS]
            line2_p2 = df2[df2["item"] == j][COORDINATES_COLUMNS]
            distance_i_j = get_lines_distance(line1_p1, line1_p2, line2_p1, line2_p2)
            distances[(i, j)] = distance_i_j
    distances_df = pd.DataFrame([[k[0], k[1], distances[k]] for k in distances], columns=["i", "j", "dist"])
    if save_cache:
        distances_df.to_csv(os.path.join(data_processing_dir_prefix, f"cache/{cache_name}.csv"))
    return distances_df


def get_num_neighbors(lines_distances, items_indices=None, dist_threshold=0.1):
    if items_indices is None:
        items_indices = lines_distances["i"].unique()
    item_to_num_neighbors = {}
    for i in items_indices:
        line_i_distances = lines_distances[lines_distances["i"] == i]
        line_i_distances = line_i_distances[line_i_distances["dist"] < dist_threshold]
        item_to_num_neighbors[i] = len(line_i_distances)
    return item_to_num_neighbors


def get_lines_lengths(df1, df2, item_indices=None):
    if item_indices is None:
        item_indices = df1["item"].unique()
    line_to_length = {}
    for i in item_indices:
        point1 = np.array(df1[df1["item"] == i][COORDINATES_COLUMNS])
        point2 = np.array(df2[df2["item"] == i][COORDINATES_COLUMNS])
        line_to_length[i] = ((point1 - point2) ** 2).sum()
    return line_to_length


def to_show_line(num_neighbors, length):
    prob = np.log(length + 1) / (2 * (num_neighbors + 0.1))
    prob = np.minimum(1, prob)
    to_show = np.random.binomial(1, prob)
    return to_show == 1


def get_lines_indices_to_show(df, distances_cache_name, dist_threshold=0.05):
    first_time_step = df[df.t == df.t.min()]
    last_time_step = df[df.t == df.t.max()]
    lines_distances = get_all_lines_distances(df.item.unique(), first_time_step, last_time_step,
                                              cache_name=distances_cache_name)
    line_to_neighbors = get_num_neighbors(lines_distances, items_indices=first_time_step.item.unique(),
                                          dist_threshold=dist_threshold)
    line_to_length = get_lines_lengths(first_time_step, last_time_step)

    max_neighbors = max(line_to_neighbors.values())
    max_length = max(line_to_length.values())

    for line in line_to_neighbors:
        line_to_neighbors[line] /= max_neighbors
        line_to_length[line] /= max_length

    lines_indices_to_show = []
    for line in line_to_neighbors:
        if to_show_line(num_neighbors=line_to_neighbors[line], length=line_to_length[line]):
            lines_indices_to_show.append(line)
    return lines_indices_to_show


if __name__ == '__main__':
    data_df = pd.read_csv("countries_our_method_2d.csv")
    data_df = data_df.rename(columns={"country_id": "item"})
    data_df1 = data_df[data_df["t"] == 0]
    data_df2 = data_df[data_df["t"] == 1]

