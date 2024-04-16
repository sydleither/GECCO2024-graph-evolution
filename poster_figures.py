import matplotlib
import matplotlib.pyplot as plt
import numpy as np

matplotlib.rcParams.update({"font.size": 32})

sample_size = 100000

n = np.random.normal(loc=0.5, scale=0.1, size=sample_size)
fig, ax = plt.subplots(1, 1, figsize=(8,7), dpi=150)
ax.hist(n, color="#44935B", weights=np.ones(sample_size)/sample_size)
ax.set_ylabel("Proportion")
ax.set_xlabel("Property Value")
ax.set_title("  NSGA-II Unconstrained   \n Property Distribution")
fig.tight_layout()
plt.savefig("normal.png", transparent=True, bbox_inches="tight")

u = np.random.uniform(size=sample_size)
fig, ax = plt.subplots(1, 1, figsize=(8,7), dpi=150)
ax.hist(u, color="#44935B", weights=np.ones(sample_size)/sample_size)
ax.set_ylabel("Proportion")
ax.set_xlabel("Property Value")
ax.set_title("Map-Elites Unconstrained \n Property Distribution")
fig.tight_layout()
plt.savefig("uniform.png", transparent=True, bbox_inches="tight")