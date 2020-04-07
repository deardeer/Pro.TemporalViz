from sklearn.decomposition import PCA
import pandas as pd
import numpy as np


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
	data = np.concatenate(data_by_step)
	max_coors = data.max(axis=0)
	min_coors = data.min(axis=0)
	diffs = max_coors - min_coors
	r = diffs.max()
	mean_dist = get_mean_dist(data_by_step)
	alpha = r / mean_dist if r < 1 else r
	return alpha


def get_mean_dist(data_by_step):
	diffs = np.abs(data_by_step[-1] - data_by_step[0])
	return diffs.mean()
