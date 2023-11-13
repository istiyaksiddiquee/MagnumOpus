docker rm -f $(docker ps -aq)
docker rmi $(docker image ls -q)
docker volume rm $(docker volume ls -q)
docker system prune --force