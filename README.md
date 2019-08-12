# Item Catalogue Project - Udacity Full Stack Web Developer Nanodegree

This Python/Flask web application provides a list of items within a range of categories which registered users are able to create, read, update and delete. This application also provides for user registration and authentication using the Google Sign In API. Registered users will have the ability to post, edit, and delete their own items. This application also provides API endpoints in JSON format.

## Installation

It is recommended that you run this program using a virtual machine. We will be using VirtualBox and Vagrant.

### Install VirtualBox
[Virtualbox](https://www.virtualbox.org/wiki/Download_Old_Builds_5_1) is the software that runs the virtual machine. You do not need to launch VirtualBox after installing it; Vagrant will do that.

### Install Vagrant

[Vagrant](https://www.vagrantup.com/) is the software that configures the VM and lets you share files between your host computer and the VM's filesystem. Install the version for your operating system.

### Github Repository Fork / Clone

Fork this current repository in Github. Next, clone the repository in your terminal using the following command:

```
git clone https://github.com/<YOUR-USERNAME-HERE>/item-catalogue.git
```


## Running The Program

1. Now that the project has been cloned to your local machine `cd` into the project directory in your terminal. Inside, you will find another directory called **vagrant**. Change directory to the **vagrant** subdirectory.

2. From your terminal, inside the **Vagrant** subdirectory, run the command `vagrant up`. This will cause Vagrant to download and install the Linux operating system. This may take a few minutes depending on your internet connection speed.

3. When `vagrant up` has finished running, you will get your shell prompt back. Next run `vagrant ssh` to log in to your newly installed linux virtual machine. 

4. Install requirements.txt

```
sudo pip3 install -r requirements.txt
```

5. Set up the database:
```
python3 database_setup.py
```

6. Load the dummy data into the database (optional):
```
python3 dummy_data.py
```

7. Start the application with the following command:

```
python3 application.py
```

8. Visit `http://localhost:8000/` in your preferred web browser.

## JSON API endpoints

Returns JSON of all categories:

`/catalogue/categories/JSON`

Returns JSON of all items belonging to a specific category:

`/catalogue/categories/<int:category_id>/JSON`

Returns JSON for one specific item:

`/catalogue/items/<int:item_id>/JSON`


Thank you for using the Item Catalogue. If you have any issues with this application please contact me via GitHub.

Conor Bailey