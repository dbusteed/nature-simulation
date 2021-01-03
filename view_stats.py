#!/usr/bin/python3.8

import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd

df = pd.read_csv("stats.csv")

df['female ratio'] = df['female population'] / df['population']
# df['population density'] = df['population'] / df['world area']

fig, axs = plt.subplots(ncols=2, nrows=2)

# top left
sns.lineplot(data=df, x="time", y="population", linewidth=2, color="black", ax=axs[0][0])
sns.lineplot(data=df, x="time", y="female population", linewidth=2, color="gray", ax=axs[0][0])
axs[0][0].set_ylabel("Population (black)\nFemale ppl (gray)")

# top right
sns.lineplot(data=df, x="time", y="resources", linewidth=2, color="green", ax=axs[0][1])
# sns.lineplot(data=df, x="time", y="allegiance", linewidth=2, color="green", ax=axs[0][1])
# sns.lineplot(data=df, x="time", y="plant count", linewidth=2, color="green", ax=axs[0][1])

# bottom left
sns.lineplot(data=df, x="time", y="sense", linewidth=2, color="blue", ax=axs[1][0])

# bottom right
sns.lineplot(data=df, x="time", y="stamina", linewidth=2, color="red", ax=axs[1][1])

fig.suptitle("Simulation Results")
plt.show()