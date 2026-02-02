.PHONY: run sync docker-build docker-run

SANDBOX_DIR := $(CURDIR)/sandbox

run:
	rye run lightcode

sync:
	rye sync

docker-build:
	docker build -t lightcode .

docker-run:
	@mkdir -p $(SANDBOX_DIR)
	docker run -it --rm \
		-e OPENAI_API_KEY=$(OPENAI_API_KEY) \
		-v $(SANDBOX_DIR):/sandbox \
		-w /sandbox \
		lightcode --no-permissions
