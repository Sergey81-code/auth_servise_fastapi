DC = docker compose
APP_LOCAL_FILE = docker_compose/docker-compose-local.yaml
APP_CI_FILE = docker_compose/docker-compose-local.yaml



up:
	${DC} -f ${APP_LOCAL_FILE} up -d
down:
	${DC} -f ${APP_LOCAL_FILE} down && docker network prune --force
up_ci:
	${DC} -f ${APP_CI_FILE} up -d
up_ci_rebuild:
	${DC} -f ${APP_CI_FILE} up --build -d
down_ci:
	${DC} -f ${APP_CI_FILE} down --remove-orphans
