.PHONY: run sync docker-build docker-run

SANDBOX_DIR := $(CURDIR)/sandbox
LOGS_DIR := $(CURDIR)/logs
LOG_FILE := session_$(shell date +%Y%m%d_%H%M%S).jsonl

run:
	rye run lightcode --no-permissions --web-search --log-file $(LOGS_DIR)/$(LOG_FILE)

sync:
	rye sync

docker-build:
	docker build -t lightcode .

docker-run:
	@mkdir -p $(SANDBOX_DIR) $(LOGS_DIR)
	@docker run -it --rm \
		-e OPENAI_API_KEY=$(OPENAI_API_KEY) \
		-e TAVILY_API_KEY=$(TAVILY_API_KEY) \
		-v $(SANDBOX_DIR):/sandbox \
		-v $(LOGS_DIR):/logs \
		-w /sandbox \
		lightcode --no-permissions --web-search --log-file /logs/$(LOG_FILE)

docker-run-completion:
	@mkdir -p $(SANDBOX_DIR) $(LOGS_DIR)
	@docker run -it --rm \
		-e OPENAI_API_KEY=$(OPENAI_API_KEY) \
		-e TAVILY_API_KEY=$(TAVILY_API_KEY) \
		-v $(SANDBOX_DIR):/sandbox \
		-v $(LOGS_DIR):/logs \
		-w /sandbox \
		lightcode --no-permissions --web-search --api completion --log-file /logs/$(LOG_FILE)
