from data_processing.data_loaders import get_data, load_data
from data_processing.choose_lines import get_lines_indices_to_show
import pandas as pd


dataset = "synthetic_cross"

data = load_data(dataset, tags=True)
data.columns = ['item', 'label', 't', '0', '1', '2']
indices = get_lines_indices_to_show(data, distances_cache_name=f"{dataset}_dup", dist_threshold=100)

rows_to_duplicate = data[data.item.isin(indices)]
max_item = data.item.max()
dfs_to_add = []
for i in range(70):
    df  = rows_to_duplicate.copy()
    df['item'] = df['item'] + (i + 1) * max_item
    dfs_to_add.append(df)

new_data = pd.concat([data] + dfs_to_add)
new_data.columns = ['id', 'label', 't', '0', '1', '2']
new_data.to_csv(f"{dataset}_duplicated.csv", index=False)
print()
