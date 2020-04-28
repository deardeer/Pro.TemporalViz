import umap
from sklearn.decomposition import PCA
import pandas as pd
import numpy as np
from sklearn.manifold import TSNE


def pca(data_by_step):
	pca = PCA(n_components=2)
	data_array = np.concatenate(data_by_step)
	data2d = pca.fit_transform(data_array)
	data2d_df = data2d_to_df(data2d, len(data_by_step), data_by_step[0].shape[0])
	return data2d_df


def translate_data(data_by_step, diffs_between_steps, translation_factor):
	translated_data = [data_by_step[0]]
	for i in range(len(diffs_between_steps)):
		data_i = translated_data[i]
		translated_data_i = data_i.copy()
		translated_data_i += translation_factor * diffs_between_steps[i]
		translated_data.append(translated_data_i)
	return translated_data


def t_pca(data_by_step, diffs_between_steps, translation_factor):
	translated_data = translate_data(data_by_step, diffs_between_steps, translation_factor)
	pca = PCA(n_components=2)
	pca.fit(np.concatenate(translated_data))
	translated_data2d = pca.transform(np.concatenate(data_by_step))
	data2d_df = data2d_to_df(translated_data2d, len(data_by_step), data_by_step[0].shape[0])
	return data2d_df


def tsne(data_by_step):
	tsne = TSNE(n_components=2)
	data_array = np.concatenate(data_by_step)
	data2d = tsne.fit_transform(data_array)
	data2d_df = data2d_to_df(data2d, len(data_by_step), data_by_step[0].shape[0])
	return data2d_df


def u_map(data_by_step):
	umap_reducer = umap.UMAP()
	data_array = np.concatenate(data_by_step)
	data2d = umap_reducer.fit_transform(data_array)
	data2d_df = data2d_to_df(data2d, len(data_by_step), data_by_step[0].shape[0])
	return data2d_df



def data2d_to_df(data_array, num_steps, amount_data_per_step):
	data2d_df = pd.DataFrame(data_array)
	data2d_df['t'] = 0
	for t in range(num_steps):
		data2d_df.loc[t * amount_data_per_step:(t+1) * amount_data_per_step, 't'] = t
	data2d_df.index = data2d_df.index % amount_data_per_step
	data2d_df.insert(loc=0, column='item', value=data2d_df.index)
	data2d_df.columns = data2d_df.columns.astype(str)
	return data2d_df


def get_translation_factor(data_by_step):
	std = get_std_dist(data_by_step)
	mean_dist = get_mean_dist(data_by_step)
	alpha = std / mean_dist
	return alpha


def get_mean_dist(data_by_step):
	diffs = np.abs(data_by_step[-1] - data_by_step[0])
	return diffs.mean()

def get_std_dist(data_by_step):
	distances = []
	for t in range(len(data_by_step)):
		distances_t = []
		data_t = data_by_step[t]
		for i in range(data_t.shape[0]):
			dists_i = [np.sqrt(np.sum((data_t[i] - data_t[j]) ** 2)) for j in range(i + 1, data_t.shape[0])]
			distances_t.extend(dists_i)
		distances.append(distances_t)
	distances_array = np.array(distances)
	return distances_array.std()


