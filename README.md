<h2>exapi</h2>
This repo contains the Coincube Exchange API Python wrappers.

<h3>Getting Started</h3>
In order to get up and running with this repo:

<h3>Gitlab SSH key setup</h3>

Follow GitLab instructions <a href="https://docs.gitlab.com/ee/gitlab-basics/create-your-ssh-keys.html" target="_blank">here</a>.

If you receive an error "Permission denied (publickey)." you need to first create an SSH key based on instructions above.

<h3>Docker Setup</h3>
You will need <a href="https://docker.com" target="_blank">Docker</a>.

Build the Docker container(s):
> `docker-compose build`

Run the Docker container(s):
> `docker-compose up`

<h3>API Documentation</h3>
Once the application is running, you can view Swagger documentation at:
<a href="http://0.0.0.0:9000/swagger-ui">http://0.0.0.0:443/swagger-ui</a><br>
JSON is available at: <a href="http://0.0.0.0:9000/swagger">http://0.0.0.0:443/swagger</a>
