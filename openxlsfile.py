import pandas as pd

dataframe=pd.read_excel("eigenxls.xlsx")


housing = dataframe.iloc[:, [1]].dropna().astype(int).squeeze().tolist()
out = dataframe.iloc[:, [3]].dropna().astype(int).squeeze().tolist()
pinion = dataframe.iloc[:, [5]].dropna().astype(int).squeeze().tolist()


print(housing)
print(type(housing),type(out),type(pinion))