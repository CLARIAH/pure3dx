# Local deployment

This document guides you through the steps to get Pure3d deployed on your local machine.

## Prerequisites

#### Clone the repo

It is recommended to put the clone in exactly the folder as indicated below.

``` sh
mkdir -p ~/github/CLARIAH
cd ~/github/CLARIAH
git clone https://github.com/CLARIAH/pure3dx
```

#### Get smartk8s

Smartk8s is a set of shell functions and variable values that helps with the
deployment, on k8s and locally.

Yoe need to be behind the firewall.

Clone the repo:

``` sh
mkdir -p ~/code.huc.knaw.nl/tt
cd ~/code.huc.knaw.nl/tt
git clone https://code.huc.knaw.nl/tt/smart-k8s.git
```

Add commands to your `~.zshrc` file.

If you do not have a `~.zshrc`, create one.

Make sure that your `~.zprofile` file includes the `~.zshrc` file, by putting this
at the top of `~.zprofile`:

```
source ~/.zshrc
```

Then add the following lines to your `~.zshrc` files.

```
function k {
    if [[ "$1" == "" ]]; then
        source ~/code.huc.knaw.nl/tt/smart-k8s/scripts/k8s.sh
        echo "k-suite enabled"
    else
        echo "First do k without arguments in order to load the k-suite"
    fi
}
```

Now open a new shell to apply these settings.

Then enable smart-k8s:

``` sh
k
```

You will see:

```
k-suite enabled
```

Then select the pure3d application:

```
kset pure3d author
```

#### Get a container app and start it and configure it

You can choose between the Docker App and Rancher Desktop.
This manual is based on Rancher Desktop.
For the purposes of this app, both are nearly equivalent, and we do not use any
k8s functionality of these apps.

The `.runlocal.sh` script has a command `host` which will start rancher desktop.

The smart-k8s suite has this command for you within easy reach:

``` sh
runlocal host
```

You'll see that Rancher desktop starts, its GUI will pop up, and it will take a while
before it is ready.

Here is an overview of *preferences* that are recommended on an Apple Silicon machine:

*  **Virtual Machine** - *Volumes* : `virtiofs`
*  **Virtual Machine** - *Emulation* : `VZ` with Rosetta support enabled
*  **Container Engine** - *General* : `dockerd` (WASM not enabled)
*  **Kubernetes** : Disabled

You can close the GUI screen, the app stays running.

#### Create environment variables

We do this by putting a `.env` file in place at the toplevel of the repo.
Start with the existing `env_template` and copy it to `.env` in the same directory.

All values will do for local development.
Variables starting with `backup` are not looked at.

The only value to pay attention to is the docker tag.

#### Build docker images

The Pure3d app uses one custom image that needs building: for the authoring app.
The editions app uses a vanilla nginx image which will serve static files from
a specified location.

The image for the authoring app is very simple: it has python and a few other
basic software packages installed, such as git, rsync, less and vim.

Later, we'll use that image with Docker-Compose to mount volumes that contain the
source code. 

So, when you change the source code, you do not need to rebuild the image, but you
have to copy the source code to the right volume.

Let's build:

``` sh
runlocal buildlocal
```

#### Provision the volumes

You might want to have a look at the `docker-compose.yml` file.
There you see how parts of the directory structure of the repo are mounted.

The toplevel directory of the repo is mounted as `/app`, so the source code
is within reach.


#### Run Pure3d

We can now run Pure3d via Docker compose (`runlocal up prod`). When the app
starts up, the script `src/start.sh` will be executed

#### Log in

If you did `runlocal up prod` you have to log in via CLARIAH authentication.

If you used an other mode instead op `prod`, e.g. `test`, `custom`, `pilot`, there
will be a row of buttons by means of which you can log in as a specific user
with specific roles.

#### Import the database
```
docker exec -it pure3d_author src/importdb.sh
```

#### Give a user root access

If you are using mode `prod`, everybody that logs in through the CLARIAH infrastructure
is a normal user. If there are not yet users on the system with role `owner` or `admin`,
you can make yourself `owner` or `admin`.

1. Open the web app: http://localhost:8000
1. Login via CLARIAH.
1. Go to the My Work page, and find the Users section
1. Make yourself `admin` or `owner` (this works if you are no admins or owners yet)

If this option is unavailable, you can resort to the following procedure

1. keep `runlocal up prod` running in its terminal window;
1. open a new terminal window and given the commands `k` and `kset pure3d author`
1. now say: `runlocal mongo prod` to enter a mongo shell on the production database;
   after the prompt, give the command: `db.user.find()` to get a list of users;
   identify a user by its `user` property. Say you want to adapt the role of user
   `de826af76e3b67294982b016741da04901fae967`. Then give the command

```
db.user.update({'user': 'de826af76e3b67294982b016741da04901fae967'}, {'$set' : {'role': 'root'}})
```
