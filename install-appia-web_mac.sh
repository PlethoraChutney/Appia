#!/bin/bash

if ! command -v docker &> /dev/null
then
	echo You must install docker: https://www.docker.com/products/docker-desktop/
	exit
fi

echo Downloading docker files from github
rm docker-compose.yml &> /dev/null
rm local.ini &> /dev/null
wget https://raw.githubusercontent.com/PlethoraChutney/Appia/main/docker-compose.yml &> /dev/null
wget https://raw.githubusercontent.com/PlethoraChutney/Appia/main/local.ini &> /dev/null

if [ -f "launch-appia.sh" ]; then
	echo Found old launch-appia file
	source ./launch-appia.sh nolaunch
fi

if [ -z "${COUCHDB_USER}" ]
then
	echo What would you like your CouchDB username to be?
	read COUCHDB_USER
fi

if [ -z "${COUCHDB_PASSWORD}" ]
then
	echo What would you like your CouchDB password to be?
	read COUCHDB_PASSWORD
fi

if [ "$(uname -m)" = "arm64" ]
then
	APPIA_ARCH="arm64-"
else
	APPIA_ARCH=""
fi

# create launch-appia
cat <<EOF > launch-appia.sh
#!/bin/bash

if ( ! docker stats --no-stream &>/dev/null ); then
	open /Applications/Docker.app

	while ( ! docker stats --no-stream&>/dev/null ); do
		echo Waiting for docker to launch...
		sleep 1
	done
fi

export COUCHDB_USER=${COUCHDB_USER}
export COUCHDB_PASSWORD=${COUCHDB_PASSWORD}
export APPIA_ARCH=${APPIA_ARCH}
cd $(pwd)

if [ "$#" -eq 0 ]; then
	docker-compose up -d
fi
EOF

chmod +x launch-appia.sh
echo All set! You can launch Appia by running ./launch-appia.sh

