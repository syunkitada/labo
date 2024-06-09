name = bobcat-nova-compute

.PHONY: all
all:
	@make image
	@make push

.PHONY: image
image:
	sudo docker image build -t local/$(name) .

.PHONY: push
push:
	sudo docker image tag local/$(name) localhost:5050/local/$(name):latest
	sudo docker push localhost:5050/local/$(name):latest
