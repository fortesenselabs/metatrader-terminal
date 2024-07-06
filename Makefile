NAMESPACE=metatrader-terminal

build:
	docker build -f metatrader-5/Dockerfile.mt5 -t fortesenselabsmt metatrader-5/

run: build
	docker run --rm -dit -p 5900:5900 -p 5901:5901 -p 8000:8000 --name fortesenselabsmt -v fortesenselabsmt:/data fortesenselabsmt

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