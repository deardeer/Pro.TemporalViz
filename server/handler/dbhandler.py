
import tornado.web
from tornado.options import options
from sklearn import decomposition
from numpy import array
import numpy as np
import io
import os.path
import json
import pandas as pd

from data_processing.choose_lines import get_lines_indices_to_show
from data_processing.data_loaders import get_data, get_tags
from data_processing.dimensional_reduction import t_pca, pca, get_translation_factor


def convert(o):
    if isinstance(o, np.int64): return int(o)
    raise TypeError


class getPlotHandler(tornado.web.RequestHandler):
	def post(self):
		self.set_header('Access-Control-Allow-Origin', '*');

		dataset = "synthetic_2"  # options: countries, coronavirus_china, coronavirus_us, synthetic_1, synthetic_2, synthetic_3
		dimensional_reduction = "t_pca"  # options: t_pca, pca

		print(f"dataset={dataset}, method={dimensional_reduction}")
		print(f"Loading Data...")
		if os.path.exists(f"data_processing/cache/{dimensional_reduction}_{dataset}.csv"):
			print(f"Data is loaded from cache file 'data_processing/cache/{dimensional_reduction}_{dataset}.csv'")
			data2d = pd.read_csv(f"data_processing/cache/{dimensional_reduction}_{dataset}.csv")
		elif dimensional_reduction == "t_pca":
			data_by_step, diffs_between_steps = get_data(dataset)
			translation_factor = get_translation_factor(data_by_step)
			data2d = t_pca(data_by_step, diffs_between_steps, translation_factor=translation_factor)
			data2d.to_csv(f"data_processing/cache/{dimensional_reduction}_{dataset}.csv", index=False)
		else:  # dimensional_reduction is pca
			data_by_step, _ = get_data(dataset)
			data2d = pca(data_by_step)
			data2d.to_csv(f"data_processing/cache/{dimensional_reduction}_{dataset}.csv", index=False)

		bound_x = [min(data2d['0']), max(data2d['0'])]
		bound_y = [min(data2d['1']), max(data2d['1'])]

		print("Choose Strokes Indices...")
		if dataset == "countries":
			dist_threshold = 0.05
		elif dataset == "synthetic_3":
			dist_threshold = 10000
		elif dataset.startswith("synthetic"):
			dist_threshold = 1000
		elif dataset.startswith("coronavirus"):
			dist_threshold = 50
		else:
			dist_threshold = 10
		lines_indices_to_show = get_lines_indices_to_show(data2d, distances_cache_name=f"{dataset}_distances_cache",
																		dist_threshold=dist_threshold)

		id_to_tag = get_tags(dataset, data2d['item'])

		return self.write({'data': data2d.values.tolist(),
		'ids': list(map(int, data2d['item'].tolist())),
		'tags': id_to_tag,
		'steps': list(map(int, list(set(data2d['t'])))),
		'drawids': list(map(int, lines_indices_to_show)),
		'bound': [bound_x, bound_y]})


class getODataHandler(tornado.web.RequestHandler):

	def computeDispaces(self, df, timeStep, nDim):
		data = {}
		for i in range(1, timeStep):
			for j in range(nDim):
				attrName1 = 'x_' + str(i - 1) + '_' + str(j)
				attrName2 = 'x_' + str(i) + '_' + str(j)
				dis = df[attrName2] - df[attrName1]
				data['dis_' + str(i - 1) + '_' + str(j)] = dis
		df_dis = pd.DataFrame(data)
		return df_dis

	def getPCA(self, data):
		pca1 = decomposition.PCA(n_components=3)
		pca1.fit(data)
		data_pca = pca1.transform(data)
		originDot = np.mean(data,0)
		dirLen = 40
		principleDir1 = pca1.components_[0]
		principleDir2 = pca1.components_[1]
		axis1 = [list(principleDir1 * 0.5 * dirLen + originDot), list(principleDir1 * (-0.5) * dirLen + originDot)]
		axis2 = [list(principleDir2 * 0.3 * dirLen + originDot), list(principleDir2 * (-0.3) * dirLen + originDot)]
		print('axes12', principleDir1, principleDir2)
		return data_pca, pca1, list(originDot), principleDir1, principleDir2, [axis1, axis2]

	def getProjected(self, liSubDf, originDot, temp_pca, nDim):
		liTimestepPCA = []
		align = 2
		for i in range(len(liSubDf)):
			df_timestep = liSubDf[i]
			timestep_pca = np.array((df_timestep.values - originDot) * np.linalg.inv(np.matrix(temp_pca.components_)))
			if(nDim == 2):
				if(align == 0):
					constantList = np.zeros(len(list(timestep_pca[:,0]))) + np.random.random(len(list(timestep_pca[:,0]))) * 2
					constantList = constantList + 10 * i
					liTimestepPCA.append([list(constantList), list(timestep_pca[:,1])])
				elif(align == 1):
					xList = timestep_pca[:,0]/6 + 10 * i
					liTimestepPCA.append([list(xList), list(timestep_pca[:,1])])
				else:
					liTimestepPCA.append([list(timestep_pca[:,0]), list(timestep_pca[:,1])])
			elif(nDim == 3):
					liTimestepPCA.append([list(timestep_pca[:,0]), list(timestep_pca[:,1]), list(timestep_pca[:, 2])])

		return liTimestepPCA

	def post(self):
		print(' load data suite ');
		self.set_header('Access-Control-Allow-Origin', '*');

		# filename = 'data_4_3.csv'
		filename = 'split_4_3.csv'
		df = pd.read_csv('../data/' + filename);

		align = True;

		liData = []
		timeStep = int(filename.split('.')[0].split("_")[1])
		nDim = int(filename.split('.')[0].split("_")[2])
		print('file=',filename)
		print('#TStep=', timeStep,'#NDim=',nDim, '#Dot=', len(df))

		originDataBag = {}
		pcaBag = {}

		for i in range(timeStep):
			data_TS = []
			for j in range(nDim):
				data_TS.append(list(df['x_'+str(i)+'_'+str(j)]))
			liData.append(data_TS)
		originDataBag['datalist'] = liData

		#base
		basedf = df[df.columns[0:nDim]]
		basedf_pca, bpca, originDot, pDir1, pDir2, axes = self.getPCA(basedf)

		#displacement
		liSubDf = []
		df_dis = self.computeDispaces(df, timeStep, nDim)

		df_dis_concate = pd.DataFrame(columns=range(nDim))
		df_data_concate = pd.DataFrame(columns=range(nDim))

		for i in range(timeStep):
			print('compute displacement', nDim * i, (i+1)*nDim)
			subdata = pd.DataFrame(df[df.columns[nDim * i:(i+1) * nDim]].values, columns=range(nDim))
			liSubDf.append(subdata)
			df_data_concate = pd.concat([df_data_concate, subdata],axis=0,ignore_index=True)
			if(i == timeStep - 1):
				break
			subdis = pd.DataFrame(df_dis[df_dis.columns[nDim * i:(i+1) * nDim]].values, columns=range(nDim))
			df_dis_concate = pd.concat([df_dis_concate,subdis],axis=0,ignore_index=True)

		originDataBag['data'] = [[list(df_data_concate.iloc[:,0]), list(df_data_concate.iloc[:,1]), list(df_data_concate.iloc[:,2])]],
		originDataBag['disdata'] = [[list(df_dis_concate.iloc[:,0]), list(df_dis_concate.iloc[:, 1]), list(df_dis_concate.iloc[:, 2])]],
		df_data_c_mean = df_data_concate - np.mean(df_data_concate.values, 0)
		temp = df_data_c_mean.values
		originDataBag['data_tomean'] = [[list(temp[:,0]), list(temp[:,1]), list(temp[:,2])]]
		df_data_c_std = df_data_c_mean / max(np.std(df_data_concate.values, 0))
		temp = df_data_c_std.values
		originDataBag['data_stand'] = [[list(temp[:,0]), list(temp[:,1]), list(temp[:,2])]]
		df_dis_c_mean = df_dis_concate - np.mean(df_dis_concate.values, 0)
		temp = df_dis_c_mean.values
		originDataBag['dis_tomean'] = [[list(temp[:,0]), list(temp[:,1]), list(temp[:,2])]]
		df_dis_c_std = df_dis_c_mean / max(np.std(df_dis_concate.values,0))
		temp = df_dis_c_std.values
		originDataBag['dis_stand'] = [[list(temp[:,0]), list(temp[:,1]), list(temp[:,2])]]

		df_all = pd.DataFrame(columns=range(nDim))
		df_all = pd.concat([df_data_concate, df_dis_concate],axis=0,ignore_index=True)

		#by Base 3D PCA
		temp_data, temp_pca, temp_center, temp_dir1, temp_dir2, temp_axes = self.getPCA(liSubDf[0])
		pcaBag['base3DPCA'] = self.getProjected(liSubDf, np.mean(liSubDf[0].values, 0), temp_pca, 3)


		#by Base PCA
		temp_data, temp_pca, temp_center, temp_dir1, temp_dir2, temp_axes = self.getPCA(liSubDf[0])
		pcaBag['basePCA'] = self.getProjected(liSubDf, np.mean(liSubDf[0].values, 0), temp_pca, 2)
		print('here???', temp_data)

		#by all data
		temp_data, temp_pca, temp_center, temp_dir1, temp_dir2, temp_axes = self.getPCA(df_data_concate)
		pcaBag['dataPCA'] = self.getProjected(liSubDf, np.mean(df_data_concate.values, 0), temp_pca, 2)

		#by diff
		temp_data, temp_pca, temp_center, temp_dir1, temp_dir2, temp_axes = self.getPCA(df_dis_concate)
		pcaBag['diffPCA'] = self.getProjected(liSubDf, np.mean(df_dis_concate.values, 0), temp_pca, 2)

		#by All-considered (Dis, Data) PCA
		temp_data, temp_pca, temp_center, temp_dir1, temp_dir2, temp_axes = self.getPCA(df_all)
		print('all=', df_all.head(), len(df_all), temp_pca.components_)
		pcaBag['allPCA'] = self.getProjected(liSubDf, np.mean(df_all.values, 0), temp_pca, 2)

		#by tomean
		df_all_mean = pd.concat([df_data_c_mean, df_dis_c_mean])
		temp_data, temp_pca, temp_center, temp_dir1, temp_dir2, temp_axes = self.getPCA(df_all_mean)
		print('mean=', df_all_mean.head(), len(df_all_mean), temp_pca.components_)
		pcaBag['meanPCA'] = self.getProjected(liSubDf, np.mean(df_all_mean.values, 0), temp_pca, 2)

		#by standard
		df_all_stand = pd.concat([df_data_c_std, df_dis_c_std])
		temp_data, temp_pca, temp_center, temp_dir1, temp_dir2, temp_axes = self.getPCA(df_all_stand)
		print('std=', df_all_stand.head(), len(df_all_stand), temp_pca.components_)
		pcaBag['standPCA'] = self.getProjected(liSubDf, np.mean(df_all_stand.values, 0), temp_pca, 2)

		#sum-displacement
		Condis_pca, Condispca, ConoriginDot_dis, ConpDir1_dis, ConpDir2_dis, CondisAxes = self.getPCA(df_all)

		#project to PCA
		print('bpca.components_',bpca.components_.shape, bpca.components_)
		print('conpca.components_',Condispca.components_.shape, Condispca.components_)

		#balanced PCA
		balanceComponents = Condispca.components_

		data_originpca = np.array((df_data_concate.values - np.mean(df_all.values, 0)) * np.linalg.inv(np.matrix(balanceComponents)))
		diff_originpca = np.array((df_dis_concate.values - np.mean(df_all.values, 0)) * np.linalg.inv(np.matrix(balanceComponents)))

		# print('#data=',len(df_data_concate), '#dif=', len(df_dis_concate), '#all=', len(df_all))
		liTimestepPCA_Origin = [[list(data_originpca[:,0]), list(data_originpca[:,1])], [list(diff_originpca[:,0]), list(diff_originpca[:,1])]]

		self.write({
			'originDataBag': originDataBag,
			'pcaBag': pcaBag,
			'baseAxes': axes,
			'baseCenter': originDot,
			'basepca': [list(basedf_pca[:,0]), list(basedf_pca[:,1])],
			'condata': [list(Condis_pca[:,0]),list(Condis_pca[:,1])],
			# 'result2DData': liTimestepPCA,
			'result2DOriginPCA': liTimestepPCA_Origin,
			'conAxes': CondisAxes,
			})
