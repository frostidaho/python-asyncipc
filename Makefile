mkfile_path := $(abspath $(lastword $(MAKEFILE_LIST)))
project_dir := $(dir $(mkfile_path))

.PHONY: isort
isort:
	isort --verbose --recursive src tests setup.py

.venv:
	util/new_venv.sh


.PHONY: clean
clean:
	rm -rf '$(project_dir).venv'
	rm -rf '$(project_dir)build'
	rm -rf $(project_dir)src/*.egg-info
