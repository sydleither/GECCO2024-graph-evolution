# GECCO2024-graph-evolution

Code from the poster "Evolving Weighted and Directed Graphs with Constrained Properties"

Paper link will appear here when it is publicly available.

Please see the [main graph-evolution repo](https://github.com/sydleither/graph-evolution) for instructions on how to run the graph-evolution tool.

The experiments included in this repo utilize Michigan State University's High Performance Computing Center. The steps to reproduce our results are as follows:
- python3 generate_configs_iter.py [location to save raw data]
	- This will generate the configs requires to run graph-evolution within the experiments/configs directory
	- This also generates a bash script experiments/run_experiments_hpcci which will be used to push multiple jobs to the HPCC at once
- chmod u+x experiments/run_experiments_hpcci
- ./experiments/run_experiments_hpcci
- Once the jobs are done...
- python3 agg_scores_iter.py [location with the raw data] save
- python3 agg_scores_iter.py [location with the raw data] save_entropy
- - python3 agg_scores_iter.py [visualization/aggregation function to run]
	- Options of functions can be found at the bottom of agg_scores_iter.py
	- The save and save_entropy args save a local copy of the raw data as a pickle in experiments/
- To view the specific replicate analysis for each individual experiment:
	- chmod u+x experiments/analyze_experimentsi
	- ./experiments/analyze_experimentsi
