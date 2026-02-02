.PHONY: run sync docker-build docker-run

run:
	rye run lightcode

sync:
	rye sync

docker-build:
	docker build -t lightcode .

docker-run:
	docker run -it --rm -e OPENAI_API_KEY=$(OPENAI_API_KEY) lightcode
