NAMESPACE=metatrader-terminal

build:
	docker build -f services/Dockerfile.mt5 -t fortesenselabsmt services/

run: build
	docker run --rm -dit -p 5900:5900 -p 8000:8000 --name fortesenselabsmt -v fortesenselabsmt:/data fortesenselabsmt

shell: 
	docker exec -it fortesenselabsmt sh

users: build
	docker exec -it fortesenselabsmt adduser novouser
	
startkube:
	minikube start

stopkube:
	minikube stop

delete:
	kubectl delete --all deployments
	minikube delete