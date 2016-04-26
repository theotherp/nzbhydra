
clean:
	@find . -name "*.pyc" -exec rm -rf {} \;

test:
	python startTests.py
