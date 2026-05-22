# overview
this is the framework for a LAMP stack that runs an API.  (here, i'm using LAMP to stand for Linux + Apache + MySQL + Python.)  this whole thing can run in a docker container; this file has my notes on building and running the docker container and connecting it to other things like a MySQL server and a file system.

# building the container
i've had success building this with a simple command, but you may want to add/use more options, as appropriate for your service:
```bash
cd /path/to/this/repo/dockered_lamp/api
docker build .
```

# running the container
like with building the container, i've kept things as simple as possible, but you may not want to. i grabbed the image id from the output of the `docker build` command above; best practices involve tagging your images with `docker build`'s `-t` option.
```bash
docker run -it -p 8080:8080 $image_id
```

## notes
the `-it` option in the run command will pipe the api's stdout to the stdout of whatever terminal you run that command from. if you do that, you can disconnect from the container by sending a SIGTERM with ctrl+c; alternatively, you can replace `-it` with `-d`, which will run the container disconnected.

if your host box is running a unix system and you're disconnected from the container, you can watch api logs by opening a terminal on the host box (or in an ssh session that's connected to the host box) and running `docker exec $container_id /bin/bash -c 'tail -f /var/log/service/out.log'` (but you might have to replace "service" with the name of your service if you renamed that folder).  i've found this helpful when i'm debugging the python scripts.

# connecting to MySQL
this is never as simple as i want.  the `/mysql_messages` endpoint will throw errors until this is set up correctly (and that may be ok if you don't want to use MySQL). for what it's worth, this is the version info i got from MySQL:
```commandline
# mysql --version
mysql  Ver 15.1 Distrib 10.5.29-MariaDB, for debian-linux-gnu (x86_64) using  EditLine wrapper
```

## scope
this only covers connecting an api running in a docker container to a MySQL daemon running outside the docker container; it doesn't cover things like recommended practices for things like multithreading and row locking.

also, note that this repo assumes that the MySQL daemon will be running outside the docker container and could be accessible from multiple docker containers.

## configuring the MySQL server
this is tangential to this repo, but i had to do some work on my MySQL server config to allow a docker image to connect to it.
1. comment out the line that sets the `bind-adress` config value to `127.0.0.1`.  (that means that the MySQL server software will only accept connections from localhost on the loopback adapter, which isn't what we want here.)
1. uncomment the line that sets the `bind-address` config value to `0.0.0.0`. (that makes it so that the MySQL daemon will accept connections on any interface. in the default config when i installed MySQL, that was in a different file from the line in the previous step.)

## database setup
for the example that starts in dockered_lamp/api/interface/mysql_message, i used this SQL to create the backing table (after replacing `$USER_PASSWORD` and `$ADMIN_PASSWORD` with actual passwords):
```MySQL
CREATE DATABASE sample_service CHARACTER SET UTF8mb4 COLLATE utf8mb4_bin;
USE sample_service;

CREATE USER 'service_user'@'%'  IDENTIFIED BY $USER_PASSWORD;
CREATE USER 'service_admin'@'%' IDENTIFIED BY $ADMIN_PASSWORD;

CREATE TABLE mysql_messages
(
  id BIGINT unsigned not null primary key auto_increment,
  content TEXT not null
);

GRANT SELECT ON sample_service.mysql_messages TO 'service_user'@'%';
GRANT INSERT ON sample_service.mysql_messages TO 'service_admin'@'%';
GRANT SELECT ON sample_service.mysql_messages TO 'service_admin'@'%';
GRANT UPDATE ON sample_service.mysql_messages TO 'service_admin'@'%';
GRANT DELETE ON sample_service.mysql_messages TO 'service_admin'@'%';
```
note that using `'%'` for a user's host is less secure than setting the host to the docker container's ip address, but using the docker container's ip address introduces complications that i don't want to deal with at the moment.