import pandas as pd
import numpy as np


def coronavirus_data(filter_options, time_step_indices, china=False):
	data = pd.read_csv("../data/raw/time_series_covid_19_confirmed.csv")
	for key in filter_options:
		data = data[data[key] == filter_options[key]]

	time_steps = data.columns[4:]
	data = data[["Province/State", "Lat", "Long"] + list(time_steps[time_step_indices])]

	if china:
		data_move_in_from_hubei = pd.read_csv("../data/raw/china_ratio_from_Hubei.csv")
		data_move_in = pd.read_csv("../data/raw/china_ratio_movein.csv")
		data_move_in_from_hubei = data_move_in_from_hubei[["Province/State"] + list(time_steps[time_step_indices])]
		data_move_in = data_move_in[["Province/State"] + list(time_steps[time_step_indices])]

	all_data = []
	for state in data["Province/State"]:
		for i, t in enumerate(time_step_indices):
			lat = data[data['Province/State'] == state]["Lat"].values[0]
			lon = data[data['Province/State'] == state]["Long"].values[0]
			# utm_coord1, utm_coord2, _, _ = utm.from_latlon(latitude=lat, longitude=lon)
			# data_row = [state, utm_coord1, utm_coord2]
			data_row = [state, lat, lon]
			time_step = time_steps[t]
			data_row.append(data[data['Province/State'] == state][time_step].values[0])
			if china:
				data_row.append(
					data_move_in_from_hubei[data_move_in_from_hubei['Province/State'] == state][time_step].values[0])
				data_row.append(data_move_in[data_move_in['Province/State'] == state][time_step].values[0])
			data_row.append(i)
			all_data.append(data_row)
	data_matrix = pd.DataFrame(all_data)
	return data_matrix


def population_data(years):
	data = pd.read_csv("../data/raw/population_measurments.csv")
	data = data[["Country", "Year", "Population", "LifeExp", "GDP"]]
	for i, year in enumerate(years):
		data.loc[data.index[data.Year == year], "Year"] = int(i)
	data = data[data.Year.isin(range(len(years)))]

	missing_countries = []
	for country in data["Country"]:
		for year in range(len(years)):
			if len(data[(data.Country == country) & (data.Year == year)]) == 0:
				missing_countries.append(country)
	data = data[~data.Country.isin(set(missing_countries))]
	data["Population"] = data["Population"] / data["Population"].max()
	data["LifeExp"] = data["LifeExp"] / data["LifeExp"].max()
	data["GDP"] = data["GDP"] / data["GDP"].max()
	return data


def load_data(data_source, time_steps=None):
	if data_source == "coronavirus_china":
		if time_steps is None:
			time_steps = list(range(6))
		data = coronavirus_data({"Country/Region": "China"}, time_steps, china=True)
		data.columns = ['item', 0, 1, 2, 3, 4, 't']
		data[[3, 4]] *= 20
		data[[0, 1]] *= 50

	elif data_source == "coronavirus_us":
		if time_steps is None:
			time_steps = [47, 48, 49, 50, 51, 52]
		data = coronavirus_data({"Country/Region": "US"}, time_steps)
		data.columns = ['item', 0, 1, 2, 't']
		data[[0, 1]] *= 100

	elif data_source == "countries":
		if time_steps is None:
			time_steps = [1960, 1970, 1980, 1990, 2000, 2010]
		data = population_data(years=time_steps)
		data.columns = ['item', 't', 0, 1, 2]

	else:
		raise NotImplementedError
	return data


def split_data_by_step(data):
	time_step_indices = range(len(data.t.unique()))
	features_indices = range(len(data.columns) - 2)

	data_by_step = []
	for i in time_step_indices:
		data_i = data[data.t == i]
		data_i_array = np.array(data_i[features_indices])
		data_by_step.append(data_i_array)

	diffs_between_steps = []
	for i in range(len(data_by_step) - 1):
		diff_i = data_by_step[i + 1] - data_by_step[i]
		diffs_between_steps.append(diff_i)

	return data_by_step, diffs_between_steps


def get_data(dataset):
	data = load_data(dataset)
	data_by_step, diffs_between_steps = split_data_by_step(data)
	return data_by_step, diffs_between_steps


if __name__ == '__main__':
	df = load_data("coronavirus_us")
	print()
