.PHONY: execute
execute:
	@mkdir data
	@python3 crawl.py
	@python3 clean.py
	@python3 analyze.py
