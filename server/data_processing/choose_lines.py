import os

import numpy as np
import pandas as pd
from tqdm import tqdm


COORDINATES_COLUMNS = ['0', '1']

data_processing_dir_prefix = os.path.dirname(os.path.realpath(__file__)).split("Pro.TemporalViz")[0]
data_processing_dir_prefix = os.path.join(data_processing_dir_prefix, "Pro.TemporalViz", "server/data_processing")


def get_point_by_dist(line_df, d):
    segments_length = (line_df.set_index('t').diff() ** 2).sum(axis=1)
    line_length = segments_length.sum()
    change_direction_points = []
    precentage = 0
    for l in segments_length:
        precentage += l / line_length
        change_direction_points.append(precentage)
    precentage_on_segment = d
    seg_index = 0
    while seg_index < len(change_direction_points) and d >= change_direction_points[seg_index]:
        precentage_on_segment = d -  change_direction_points[seg_index]
        seg_index += 1

    if d == 1:
        point = np.array(line_df[line_df.t == seg_index - 1][COORDINATES_COLUMNS])
    else:
        point = np.array(line_df[line_df.t == seg_index - 1][COORDINATES_COLUMNS]) + \
                precentage_on_segment * (np.array(line_df[line_df.t == seg_index][COORDINATES_COLUMNS]) -
                                         np.array(line_df[line_df.t == seg_index - 1][COORDINATES_COLUMNS]))
    return point


def get_lines_distance(line1, line2):
    ds = [i / line1.t.max() for i in range(line1.t.max() + 1)]
    point1 = np.array([get_point_by_dist(line1, d)for d in ds])
    point2 = np.array([get_point_by_dist(line2, d) for d in ds])
    dist = ((point2 - point1) ** 2).sum()
    return np.sqrt(dist)


def get_all_lines_distances(indices, df, cache_name=None):
    save_cache = False
    if cache_name:
        if os.path.exists(os.path.join(data_processing_dir_prefix, f"cache/{cache_name}.csv")):
            print(f"For choosing strokes, distances are loaded from cahce file 'data_processing/cache/{cache_name}.csv'")
            distances_df = pd.read_csv(os.path.join(data_processing_dir_prefix, f"cache/{cache_name}.csv"))
            return distances_df
        else:
            save_cache = True
    distances = {}
    for i in tqdm(range(len(indices))):
        for j in range(i + 1, len(indices)):
            line1 = df[df["item"] == i][COORDINATES_COLUMNS + ['t']]
            line2 = df[df["item"] == j][COORDINATES_COLUMNS + ['t']]
            dist_i_j = get_lines_distance(line1, line2)
            distances[(i, j)] = dist_i_j
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


def get_line_prob(num_neighbors, length):
    prob = np.log(length + 1) / (2 * (num_neighbors + 0.1))
    prob = np.minimum(1, prob)
    return prob


def to_show_line(num_neighbors, length):
    prob = np.log(length + 1) / (2 * (num_neighbors + 0.1))
    prob = np.minimum(1, prob)
    to_show = np.random.binomial(1, prob)
    return to_show == 1


def get_lines_indices_to_show(df, tag_to_id, distances_cache_name, dist_threshold=0.05):
    first_time_step = df[df.t == df.t.min()]
    last_time_step = df[df.t == df.t.max()]
    lines_distances = get_all_lines_distances(df.item.unique(), df,
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
    num_lines_per_tag = int((len(line_to_length) * 0.15) / len(tag_to_id))
    for tag in set(tag_to_id.keys()):
        tag_probs = []
        for id in tag_to_id[tag]:
            prob = get_line_prob(num_neighbors=line_to_neighbors[id], length=line_to_length[id])
            tag_probs.append((id, prob))
        tag_mean_prob_goal = num_lines_per_tag / len(tag_to_id[tag])
        tag_mean_prob = sum([p for _, p in tag_probs]) / len(tag_probs)
        tag_probs = [(id, min(0.99, p * (tag_mean_prob_goal) / tag_mean_prob)) for (id, p) in tag_probs]
        lines_indices_to_show.extend([id for (id, p) in tag_probs if np.random.binomial(1, p) == 1])
    print(lines_indices_to_show)
    return lines_indices_to_show


if __name__ == '__main__':
    data_df = pd.read_csv("countries_our_method_2d.csv")
    data_df = data_df.rename(columns={"country_id": "item"})
    data_df1 = data_df[data_df["t"] == 0]
    data_df2 = data_df[data_df["t"] == 1]

